"""
SQLModel database models for AegisGraph.

Defines all entity types, observations, anomalies, actions, and audit records.
"""
from sqlmodel import SQLModel, Field, Relationship, JSON
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class EntityType(str, Enum):
    """Types of tracked entities."""
    VESSEL = "vessel"
    AIRCRAFT = "aircraft"
    PORT = "port"
    AIRPORT = "airport"
    WEATHER_STATION = "weather_station"
    CYBER_NODE = "cyber_node"


class ObservationSource(str, Enum):
    """Data source types for observations."""
    AIS = "ais"  # Automatic Identification System (vessels)
    ADSB = "adsb"  # Automatic Dependent Surveillance-Broadcast (aircraft)
    WEATHER = "weather"
    PORT_STATUS = "port_status"
    CYBER = "cyber"
    RADIO_LOG = "radio_log"


class AnomalyType(str, Enum):
    """Types of detected anomalies."""
    ROUTE_DEVIATION = "route_deviation"
    DARK_VESSEL = "dark_vessel"
    SENSOR_DROPOUT = "sensor_dropout"
    PORT_CONGESTION = "port_congestion"
    CYBER_OUTAGE = "cyber_outage"
    CONFLICTING_REPORTS = "conflicting_reports"
    ABNORMAL_PROXIMITY = "abnormal_proximity"
    DELAYED_FEED = "delayed_feed"
    IDENTITY_MISMATCH = "identity_mismatch"
    UNUSUAL_LOITERING = "unusual_loitering"


class SeverityLevel(str, Enum):
    """Anomaly severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(str, Enum):
    """Status of recommended actions."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class AuditAction(str, Enum):
    """Types of auditable actions."""
    ENTITY_CREATED = "entity_created"
    OBSERVATION_INGESTED = "observation_ingested"
    ANOMALY_DETECTED = "anomaly_detected"
    ACTION_RECOMMENDED = "action_recommended"
    ACTION_APPROVED = "action_approved"
    ACTION_REJECTED = "action_rejected"
    DATA_UPDATED = "data_updated"
    USER_QUERY = "user_query"
    SYSTEM_EVENT = "system_event"


# ==================== CORE MODELS ====================

class Entity(SQLModel, table=True):
    """Unified entity representing a tracked object (vessel, aircraft, facility)."""
    __tablename__ = "entities"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_id: str = Field(unique=True, index=True)  # External/resolved ID
    entity_type: EntityType
    name: str
    callsign: Optional[str] = None
    mmsi: Optional[str] = None  # Maritime Mobile Service Identity
    icao: Optional[str] = None  # International Civil Aviation Organization code
    imo: Optional[str] = None  # International Maritime Organization number
    
    # Current state
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None  # meters
    speed: Optional[float] = None  # knots or km/h
    heading: Optional[float] = None  # degrees
    course: Optional[float] = None  # degrees
    
    # Metadata
    flag: Optional[str] = None  # Country flag
    operator: Optional[str] = None
    home_port: Optional[str] = None
    destination: Optional[str] = None
    eta: Optional[datetime] = None
    
    # Status
    is_active: bool = True
    last_seen: Optional[datetime] = None
    risk_score: float = 0.0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    observations: List["Observation"] = Relationship(back_populates="entity")
    anomalies: List["Anomaly"] = Relationship(back_populates="entity")


class Sensor(SQLModel, table=True):
    """Sensor/source that provides observations."""
    __tablename__ = "sensors"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    sensor_id: str = Field(unique=True, index=True)
    sensor_type: ObservationSource
    name: str
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coverage_radius_km: Optional[float] = None
    is_operational: bool = True
    last_heartbeat: Optional[datetime] = None
    
    observations: List["Observation"] = Relationship(back_populates="sensor")


class Observation(SQLModel, table=True):
    """Raw or normalized observation from a sensor source."""
    __tablename__ = "observations"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    observation_id: str = Field(unique=True, index=True)
    source_type: ObservationSource
    entity_id: Optional[str] = Field(default=None, foreign_key="entities.entity_id")
    sensor_id: Optional[str] = Field(default=None, foreign_key="sensors.sensor_id")
    
    # Raw data fields
    raw_data: dict = Field(default_factory=dict, sa_type=JSON)
    
    # Normalized fields
    timestamp: datetime
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    course: Optional[float] = None
    
    # Additional context
    signal_strength: Optional[float] = None
    accuracy: Optional[float] = None
    confidence: float = 1.0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    entity: Optional[Entity] = Relationship(back_populates="observations")
    sensor: Optional[Sensor] = Relationship(back_populates="observations")


class Rule(SQLModel, table=True):
    """Detection rule for anomaly identification."""
    __tablename__ = "rules"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: str = Field(unique=True, index=True)
    name: str
    description: str
    anomaly_type: AnomalyType
    category: str  # e.g., "behavioral", "technical", "correlation"
    
    # Rule configuration
    parameters: dict = Field(default_factory=dict, sa_type=JSON)
    threshold: float
    enabled: bool = True
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # No direct relationship to avoid circular dependency - using simple approach


class Anomaly(SQLModel, table=True):
    """Detected anomaly with explanation and recommended action."""
    __tablename__ = "anomalies"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    anomaly_id: str = Field(unique=True, index=True)
    anomaly_type: AnomalyType
    severity: SeverityLevel
    
    # Detection details
    score: float  # Anomaly score (0-1)
    triggered_rule_ids: List[str] = Field(default_factory=list, sa_type=JSON)
    evidence_observation_ids: List[str] = Field(default_factory=list, sa_type=JSON)
    explanation: str
    uncertainty: float = 0.0  # Uncertainty estimate (0-1)
    
    # Context
    entity_id: Optional[str] = Field(default=None, foreign_key="entities.entity_id")
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    timestamp: datetime
    
    # Recommended response
    recommended_action_id: Optional[int] = Field(default=None, foreign_key="actions.id")
    
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    entity: Optional[Entity] = Relationship(back_populates="anomalies")
    rule: Optional[Rule] = Relationship(back_populates="anomalies")


class Action(SQLModel, table=True):
    """Recommended or executed action in response to an anomaly."""
    __tablename__ = "actions"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    action_id: str = Field(unique=True, index=True)
    description: str
    action_type: str  # e.g., "investigate", "alert", "track_enhance"
    
    anomaly_id: Optional[int] = Field(default=None, foreign_key="anomalies.id")
    
    status: ActionStatus = ActionStatus.PENDING
    priority: int = 3  # 1=highest, 5=lowest
    
    assigned_to: Optional[str] = None  # User/team ID
    justification: Optional[str] = None
    
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    executed_at: Optional[datetime] = None
    execution_result: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    """Append-only hash-chained audit log."""
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str = Field(unique=True, index=True)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str  # User, system, or API
    action: AuditAction
    
    # Hash chain
    previous_hash: str
    current_hash: str
    chain_index: int = Field(index=True)
    
    payload: dict = Field(default_factory=dict, sa_type=JSON)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GraphNode(SQLModel, table=True):
    """Node in the ontology graph."""
    __tablename__ = "graph_nodes"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    node_id: str = Field(unique=True, index=True)
    node_type: str  # entity, sensor, event, anomaly, action, rule
    ref_id: str  # Reference to actual entity ID
    label: str
    properties: dict = Field(default_factory=dict, sa_type=JSON)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GraphEdge(SQLModel, table=True):
    """Edge in the ontology graph."""
    __tablename__ = "graph_edges"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    edge_id: str = Field(unique=True, index=True)
    
    source_node_id: str = Field(foreign_key="graph_nodes.node_id")
    target_node_id: str = Field(foreign_key="graph_nodes.node_id")
    
    relationship_type: str  # observed_by, near, related_to, escalated_to, approved_by
    weight: float = 1.0
    properties: dict = Field(default_factory=dict, sa_type=JSON)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== PYDANTIC SCHEMAS FOR API ====================

class EntityCreate(SQLModel):
    """Schema for creating an entity."""
    entity_id: str
    entity_type: EntityType
    name: str
    callsign: Optional[str] = None
    mmsi: Optional[str] = None
    icao: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EntityRead(SQLModel):
    """Schema for reading an entity."""
    id: int
    entity_id: str
    entity_type: EntityType
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    risk_score: float
    is_active: bool
    last_seen: Optional[datetime] = None


class AnomalyRead(SQLModel):
    """Schema for reading an anomaly."""
    id: int
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: SeverityLevel
    score: float
    explanation: str
    entity_id: Optional[str] = None
    timestamp: datetime
    uncertainty: float


class ActionUpdate(SQLModel):
    """Schema for updating an action."""
    status: ActionStatus
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class AskRequest(SQLModel):
    """Schema for AI analyst query."""
    question: str
    context_filters: Optional[dict] = None


class AskResponse(SQLModel):
    """Schema for AI analyst response."""
    answer: str
    citations: List[dict]
    confidence: float
    limitations: str
    query_timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditLogRead(SQLModel):
    """Schema for reading audit log entries."""
    event_id: str
    timestamp: datetime
    actor: str
    action: AuditAction
    payload: dict
    chain_index: int


class GraphNodeRead(SQLModel):
    """Schema for graph nodes."""
    node_id: str
    node_type: str
    label: str
    properties: dict


class GraphEdgeRead(SQLModel):
    """Schema for graph edges."""
    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    weight: float


class GraphData(SQLModel):
    """Schema for complete graph data."""
    nodes: List[GraphNodeRead]
    edges: List[GraphEdgeRead]
