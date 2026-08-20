"""
Ingestion module for loading synthetic data into the database.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any
from sqlmodel import Session
from models import (
    Entity, EntityType, Sensor, Observation, ObservationSource,
    Rule, AnomalyType
)


class DataIngester:
    """Ingests synthetic data into the database."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def ingest_all(self, data: Dict[str, Any]) -> Dict[str, int]:
        """Ingest all synthetic data."""
        counts = {
            "entities": 0,
            "sensors": 0,
            "observations": 0,
            "rules": 0
        }
        
        # Ingest entities
        counts["entities"] = self._ingest_entities(data.get("entities", []))
        
        # Ingest sensors
        counts["sensors"] = self._ingest_sensors(data.get("sensors", []))
        
        # Ingest observations
        counts["observations"] = self._ingest_observations(data.get("observations", []))
        
        # Ingest rules
        counts["rules"] = self._ingest_rules(data.get("rules", []))
        
        return counts
    
    def _ingest_entities(self, entities: List[Dict]) -> int:
        """Ingest entity records."""
        count = 0
        for e in entities:
            entity_type_str = e.get("entity_type", "vessel")
            try:
                entity_type = EntityType(entity_type_str)
            except ValueError:
                entity_type = EntityType.VESSEL
            
            entity = Entity(
                entity_id=e["entity_id"],
                entity_type=entity_type,
                name=e.get("name", "Unknown"),
                callsign=e.get("callsign"),
                mmsi=e.get("mmsi"),
                icao=e.get("icao"),
                imo=e.get("imo"),
                flag=e.get("flag"),
                operator=e.get("operator"),
                home_port=e.get("home_port"),
                destination=e.get("destination"),
                latitude=e.get("latitude"),
                longitude=e.get("longitude"),
                altitude=e.get("altitude"),
                speed=e.get("speed"),
                heading=e.get("heading"),
                course=e.get("course"),
                is_active=e.get("is_active", True),
                last_seen=datetime.utcnow(),
                risk_score=0.0
            )
            self.session.add(entity)
            count += 1
        
        self.session.commit()
        return count
    
    def _ingest_sensors(self, sensors: List[Dict]) -> int:
        """Ingest sensor records."""
        count = 0
        for s in sensors:
            source_type_str = s.get("sensor_type", "ais")
            try:
                source_type = ObservationSource(source_type_str)
            except ValueError:
                source_type = ObservationSource.AIS
            
            sensor = Sensor(
                sensor_id=s["sensor_id"],
                sensor_type=source_type,
                name=s.get("name", "Unknown Sensor"),
                location_name=s.get("location_name"),
                latitude=s.get("latitude"),
                longitude=s.get("longitude"),
                coverage_radius_km=s.get("coverage_radius_km"),
                is_operational=s.get("is_operational", True),
                last_heartbeat=datetime.utcnow()
            )
            self.session.add(sensor)
            count += 1
        
        self.session.commit()
        return count
    
    def _ingest_observations(self, observations: List[Dict]) -> int:
        """Ingest observation records."""
        count = 0
        batch_size = 500
        
        for i, obs in enumerate(observations):
            source_type_str = obs.get("source_type", "ais")
            try:
                source_type = ObservationSource(source_type_str)
            except ValueError:
                source_type = ObservationSource.AIS
            
            timestamp_str = obs.get("timestamp")
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")) if timestamp_str else datetime.utcnow()
            except:
                timestamp = datetime.utcnow()
            
            observation = Observation(
                observation_id=obs["observation_id"],
                source_type=source_type,
                entity_id=obs.get("entity_id"),
                sensor_id=obs.get("sensor_id"),
                raw_data=obs.get("raw_data", {}),
                timestamp=timestamp,
                latitude=obs.get("latitude", 0.0),
                longitude=obs.get("longitude", 0.0),
                altitude=obs.get("altitude"),
                speed=obs.get("speed"),
                heading=obs.get("heading"),
                course=obs.get("course"),
                signal_strength=obs.get("signal_strength"),
                accuracy=obs.get("accuracy"),
                confidence=obs.get("confidence", 1.0)
            )
            self.session.add(observation)
            count += 1
            
            # Commit in batches
            if count % batch_size == 0:
                self.session.commit()
        
        self.session.commit()
        return count
    
    def _ingest_rules(self, rules: List[Dict]) -> int:
        """Ingest detection rule records."""
        count = 0
        for r in rules:
            anomaly_type_str = r.get("anomaly_type", "route_deviation")
            try:
                anomaly_type = AnomalyType(anomaly_type_str)
            except ValueError:
                anomaly_type = AnomalyType.ROUTE_DEVIATION
            
            rule = Rule(
                rule_id=r["rule_id"],
                name=r.get("name", "Unknown Rule"),
                description=r.get("description", ""),
                anomaly_type=anomaly_type,
                category=r.get("category", "general"),
                parameters=r.get("parameters", {}),
                threshold=r.get("threshold", 0.5),
                enabled=r.get("enabled", True)
            )
            self.session.add(rule)
            count += 1
        
        self.session.commit()
        return count
