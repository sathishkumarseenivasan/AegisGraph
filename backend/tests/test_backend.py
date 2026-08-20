"""
Pytest tests for AegisGraph backend.

Tests cover:
- Entity resolution
- Anomaly detection
- Audit chain integrity
- API endpoints
"""
import pytest
import os
import sys
from datetime import datetime, timedelta
from sqlmodel import Session, create_engine, SQLModel, MetaData

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from config import settings
from database import get_session
from models import (
    Entity, EntityType, Observation, ObservationSource,
    Anomaly, AnomalyType, SeverityLevel, Rule, Action,
    AuditLog, AuditAction
)
from synthetic.synthetic_data_generator import SyntheticDataGenerator
from fusion.entity_resolver import EntityResolver
from analytics.anomaly_engine import AnomalyEngine
from governance.audit import AuditLogger


# Use separate metadata for tests to avoid conflicts
test_metadata = MetaData()


# ==================== FIXTURES ====================

@pytest.fixture(scope="function")
def test_engine():
    """Create test SQLite engine with fresh metadata."""
    # Use a unique database file for each test to avoid conflicts
    import uuid
    import tempfile
    
    db_path = tempfile.mktemp(suffix=f"_{uuid.uuid4().hex[:8]}.db")
    db_name = f"sqlite:///{db_path}"
    
    engine = create_engine(
        db_name,
        connect_args={"check_same_thread": False}
    )
    
    # Import SQLModel fresh and create tables
    from models import SQLModel
    SQLModel.metadata.create_all(engine)
    
    yield engine
    
    SQLModel.metadata.drop_all(engine)
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create test session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="function")
def seeded_session(test_session):
    """Session with synthetic data seeded."""
    generator = SyntheticDataGenerator(num_entities=20, hours=2)
    data = generator.generate_all()
    
    from ingestion.data_ingester import DataIngester
    ingester = DataIngester(test_session)
    ingester.ingest_all(data)
    
    return test_session


# ==================== ENTITY RESOLUTION TESTS ====================

class TestEntityResolver:
    """Tests for entity resolution."""
    
    def test_exact_id_match(self, seeded_session):
        """Test exact ID matching."""
        resolver = EntityResolver(seeded_session)
        
        # Get first entity
        entity = seeded_session.get(Entity, 1)
        assert entity is not None
        
        # Create observation with matching entity_id
        obs = Observation(
            observation_id="OBS-TEST-001",
            source_type=ObservationSource.AIS,
            entity_id=entity.entity_id,
            timestamp=datetime.utcnow(),
            latitude=entity.latitude or 0,
            longitude=entity.longitude or 0,
            confidence=1.0
        )
        
        matched, confidence = resolver.resolve_observation(obs)
        assert matched is not None
        assert matched.entity_id == entity.entity_id
        assert confidence == 1.0
    
    def test_geo_temporal_match(self, seeded_session):
        """Test geo-temporal association."""
        resolver = EntityResolver(seeded_session)
        
        # Get a vessel entity
        vessels = seeded_session.exec(
            seeded_session.select(Entity).where(Entity.entity_type == "vessel")
        ).all()
        
        if vessels:
            vessel = vessels[0]
            obs = Observation(
                observation_id="OBS-TEST-002",
                source_type=ObservationSource.AIS,
                entity_id=None,  # No ID - test geo match
                timestamp=datetime.utcnow(),
                latitude=vessel.latitude or 0,
                longitude=vessel.longitude or 0,
                confidence=0.9
            )
            
            # Update vessel's last_seen for temporal match
            vessel.last_seen = datetime.utcnow()
            seeded_session.add(vessel)
            seeded_session.commit()
            
            matched, confidence = resolver.resolve_observation(obs)
            # Should find based on proximity
            assert matched is not None


# ==================== ANOMALY DETECTION TESTS ====================

class TestAnomalyEngine:
    """Tests for anomaly detection."""
    
    def test_detect_anomalies(self, seeded_session):
        """Test anomaly detection runs without errors."""
        engine = AnomalyEngine(seeded_session)
        anomalies = engine.detect_all()
        
        # Should return list of anomalies
        assert isinstance(anomalies, list)
        
        # Each anomaly should have required fields
        for anomaly in anomalies:
            assert anomaly.anomaly_type is not None
            assert anomaly.severity is not None
            assert anomaly.score >= 0
            assert anomaly.explanation is not None
    
    def test_severity_calculation(self, seeded_session):
        """Test severity level calculation."""
        engine = AnomalyEngine(seeded_session)
        
        # Test threshold boundaries
        assert engine._calculate_severity(0.2) == SeverityLevel.LOW
        assert engine._calculate_severity(0.5) == SeverityLevel.MEDIUM
        assert engine._calculate_severity(0.75) == SeverityLevel.HIGH
        assert engine._calculate_severity(0.9) == SeverityLevel.CRITICAL


# ==================== AUDIT CHAIN TESTS ====================

class TestAuditChain:
    """Tests for audit log integrity."""
    
    def test_hash_chain_creation(self, test_session):
        """Test that hash chain is properly created."""
        logger = AuditLogger(test_session)
        
        # Log several entries
        entry1 = logger.log(
            actor="test_user",
            action=AuditAction.SYSTEM_EVENT,
            payload={"test": "data1"}
        )
        
        entry2 = logger.log(
            actor="test_user",
            action=AuditAction.DATA_UPDATED,
            payload={"test": "data2"}
        )
        
        # Verify chain properties
        assert entry1.chain_index == 0
        assert entry2.chain_index == 1
        assert entry2.previous_hash == entry1.current_hash
    
    def test_chain_verification(self, test_session):
        """Test chain integrity verification."""
        logger = AuditLogger(test_session)
        
        # Create some entries
        for i in range(5):
            logger.log(
                actor="test_user",
                action=AuditAction.SYSTEM_EVENT,
                payload={"index": i}
            )
        
        # Verify chain
        result = logger.verify_chain()
        assert result["valid"] is True
        assert result["total_entries"] == 5
        assert len(result["invalid_indices"]) == 0
    
    def test_tampering_detection(self, test_session):
        """Test that tampering is detected."""
        logger = AuditLogger(test_session)
        
        # Create entries
        logger.log(
            actor="test_user",
            action=AuditAction.SYSTEM_EVENT,
            payload={"original": "data"}
        )
        
        # Manually corrupt an entry
        corrupted = test_session.exec(
            test_session.select(AuditLog).limit(1)
        ).first()
        
        if corrupted:
            corrupted.payload = {"tampered": "data"}
            test_session.add(corrupted)
            test_session.commit()
            
            # Verification should fail
            result = logger.verify_chain()
            assert result["valid"] is False


# ==================== SYNTHETIC DATA TESTS ====================

class TestSyntheticData:
    """Tests for synthetic data generation."""
    
    def test_generate_data(self):
        """Test synthetic data generation."""
        generator = SyntheticDataGenerator(num_entities=10, hours=1)
        data = generator.generate_all()
        
        assert len(data["entities"]) == 10
        assert len(data["sensors"]) > 0
        assert len(data["observations"]) > 0
        assert len(data["rules"]) == 10
        assert len(data["anomaly_scenarios"]) == 10
    
    def test_entity_types(self):
        """Test that multiple entity types are generated."""
        generator = SyntheticDataGenerator(num_entities=20, hours=1)
        data = generator.generate_all()
        
        types = set(e["entity_type"] for e in data["entities"])
        assert "vessel" in types
        assert "aircraft" in types


# ==================== API ENDPOINT TESTS ====================

class TestAPIEndpoints:
    """Tests for API endpoints using FastAPI TestClient."""
    
    @pytest.fixture
    def client(self, seeded_session):
        """Create test client."""
        from fastapi.testclient import TestClient
        from main import app
        
        # Override dependency
        def override_get_session():
            yield seeded_session
        
        app.dependency_overrides[get_session] = override_get_session
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()
    
    def test_health_check(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_get_entities(self, client):
        """Test entities endpoint."""
        response = client.get("/entities?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_tracks(self, client):
        """Test tracks endpoint."""
        response = client.get("/tracks")
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
    
    def test_get_anomalies(self, client):
        """Test anomalies endpoint."""
        response = client.get("/anomalies?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_ask_analyst(self, client):
        """Test AI analyst endpoint."""
        response = client.post(
            "/ask",
            json={"question": "How many vessels are being tracked?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "confidence" in data
        assert "citations" in data
    
    def test_get_audit_log(self, client):
        """Test audit log endpoint."""
        response = client.get("/audit?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
