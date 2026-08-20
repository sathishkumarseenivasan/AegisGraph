# AegisGraph Data Model

## Ontology Overview

AegisGraph uses a unified ontology to represent multi-source intelligence data. All entities, observations, anomalies, and actions are modeled as first-class objects with explicit relationships.

## Core Entities

### 1. Entity

Represents a unified track resolved from multiple observations.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `name` | String(255) | Display name (callsign, vessel name) | Not null |
| `type` | EntityType | Enum: VESSEL, AIRCRAFT, WEATHER_STATION, PORT, CYBER_NODE, RADIO_STATION | Not null |
| `external_id` | String(100) | Source identifier (MMSI, ICAO code) | Unique, nullable |
| `latitude` | Float | Current latitude (WGS84) | -90 to 90 |
| `longitude` | Float | Current longitude (WGS84) | -180 to 180 |
| `created_at` | DateTime | First observation timestamp | UTC |
| `last_seen` | DateTime | Most recent observation | UTC |
| `confidence_score` | Float | Resolution confidence | 0.0–1.0 |
| `attributes` | JSON | Type-specific metadata (speed, altitude, etc.) | Nullable |

**Relationships:**
- `observations`: One-to-many → Observation
- `anomalies`: One-to-many → Anomaly
- `actions`: One-to-many → Action

---

### 2. Observation

Raw sensor report from a specific source.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `entity_id` | UUID | Foreign key → Entity.id | Not null |
| `source_type` | SourceType | Enum: AIS, ADSB, WEATHER, PORT_STATUS, CYBER_ALERT, RADIO_LOG | Not null |
| `timestamp` | DateTime | Observation time (UTC) | Not null |
| `latitude` | Float | Reported position | Nullable |
| `longitude` | Float | Reported position | Nullable |
| `altitude` | Float | Altitude in meters (aircraft) | Nullable |
| `speed` | Float | Speed in knots | Nullable |
| `heading` | Float | Heading in degrees | 0–360 |
| `raw_data` | JSON | Source-specific payload | Not null |
| `quality_score` | Float | Sensor reliability estimate | 0.0–1.0 |

**Relationships:**
- `entity`: Many-to-one → Entity
- `sensor_feed`: Many-to-one → SensorFeed

---

### 3. SensorFeed

Metadata about a data source.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `name` | String(255) | Feed identifier | Not null |
| `source_type` | SourceType | Enum matching Observation.source_type | Not null |
| `ingestion_rate` | Integer | Expected reports per minute | Nullable |
| `last_heartbeat` | DateTime | Last successful ingestion | Nullable |
| `status` | FeedStatus | Enum: ACTIVE, DEGRADED, OFFLINE | Default: ACTIVE |

**Relationships:**
- `observations`: One-to-many → Observation

---

### 4. Anomaly

Detected deviation from expected behavior.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `entity_id` | UUID | Foreign key → Entity.id | Not null |
| `anomaly_type` | AnomalyType | Enum (see catalog below) | Not null |
| `severity` | Severity | Enum: LOW, MEDIUM, HIGH, CRITICAL | Not null |
| `score` | Float | Detection confidence | 0.0–1.0 |
| `triggered_rules` | JSON | List of rule IDs that fired | Not null |
| `evidence_ids` | JSON | List of Observation UUIDs | Not null |
| `explanation` | Text | Human-readable description | Not null |
| `recommended_action` | Text | Suggested mitigation | Nullable |
| `uncertainty` | Float | Epistemic uncertainty estimate | 0.0–1.0 |
| `detected_at` | DateTime | Detection timestamp | UTC |
| `status` | AnomalyStatus | Enum: OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE | Default: OPEN |

**Relationships:**
- `entity`: Many-to-one → Entity
- `rule`: Many-to-one → Rule (via triggered_rules)
- `action`: One-to-one → Action

---

### 5. Rule

Definition of an anomaly detection rule.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `name` | String(255) | Rule identifier | Not null |
| `description` | Text | Human-readable explanation | Not null |
| `rule_type` | RuleType | Enum: THRESHOLD, PATTERN, STATISTICAL, ML_MODEL | Not null |
| `parameters` | JSON | Configurable thresholds | Not null |
| `enabled` | Boolean | Active status | Default: true |
| `version` | String(20) | Rule version for audit | Not null |

**Relationships:**
- `anomalies`: One-to-many → Anomaly (implicit via triggered_rules)

---

### 6. Action

Human-in-the-loop mitigation proposal.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `anomaly_id` | UUID | Foreign key → Anomaly.id | Not null |
| `action_type` | ActionType | Enum: INVESTIGATE, CONTACT, ALERT, ESCALATE, IGNORE | Not null |
| `description` | Text | Action details | Not null |
| `proposed_by` | String(100) | System or user ID | Not null |
| `status` | ActionStatus | Enum: PENDING, APPROVED, REJECTED, EXECUTED | Default: PENDING |
| `approved_by` | String(100) | Approver user ID | Nullable |
| `approved_at` | DateTime | Approval timestamp | Nullable |
| `rejection_reason` | Text | If rejected, why | Nullable |
| `executed_at` | DateTime | Execution timestamp | Nullable |

**Relationships:**
- `anomaly`: Many-to-one → Anomaly
- `audit_events`: One-to-many → AuditEvent

---

### 7. AuditEvent

Immutable, hash-chained log entry.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `event_id` | String(64) | Unique event identifier | Not null |
| `timestamp` | DateTime | Event time (UTC) | Not null |
| `actor` | String(100) | User or system ID | Not null |
| `action` | String(50) | Action type (CREATE, UPDATE, APPROVE, REJECT) | Not null |
| `payload` | JSON | Event data | Not null |
| `previous_hash` | String(64) | SHA-256 of previous event | Not null (except genesis) |
| `current_hash` | String(64) | SHA-256 of this event | Not null |

**Relationships:**
- None (append-only, no foreign keys)

---

### 8. Track (Derived)

Aggregated movement history for an entity.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `entity_id` | UUID | Foreign key → Entity.id | Not null, unique |
| `start_time` | DateTime | First observation | Not null |
| `end_time` | DateTime | Last observation | Not null |
| `total_distance` | Float | Cumulative distance (km) | Not null |
| `avg_speed` | Float | Mean speed (knots) | Nullable |
| `max_speed` | Float | Peak speed (knots) | Nullable |
| `waypoints` | JSON | Simplified path coordinates | Not null |

**Relationships:**
- `entity`: One-to-one → Entity

---

## Relationship Types

### observed_by
- **From**: Observation
- **To**: SensorFeed
- **Meaning**: This observation was received by this feed
- **Cardinality**: Many-to-one

### near
- **From**: Entity
- **To**: Entity
- **Meaning**: Two entities within proximity threshold at overlapping times
- **Cardinality**: Many-to-many
- **Attributes**: `distance_meters`, `time_overlap_seconds`

### related_to
- **From**: Anomaly
- **To**: Anomaly
- **Meaning**: Correlated anomalies (e.g., cyber outage + vessel dropout)
- **Cardinality**: Many-to-many
- **Attributes**: `correlation_score`

### escalated_to
- **From**: Anomaly
- **To**: Action
- **Meaning**: This anomaly prompted this action
- **Cardinality**: One-to-one

### approved_by
- **From**: Action
- **To**: AuditEvent
- **Meaning**: This action's approval was recorded in this audit event
- **Cardinality**: One-to-one

---

## Entity Types (EntityType Enum)

| Value | Description | Example Attributes |
|-------|-------------|-------------------|
| `VESSEL` | Maritime vessel | mmsi, imo, vessel_type, draft |
| `AIRCRAFT` | Airborne vehicle | icao_code, aircraft_type, flight_number |
| `WEATHER_STATION` | Weather sensor | station_id, measurement_types |
| `PORT` | Port facility | unlocode, berth_count, congestion_index |
| `CYBER_NODE` | Network infrastructure | ip_range, node_type, criticality |
| `RADIO_STATION` | Communication node | frequency, call_sign, encryption |

---

## Source Types (SourceType Enum)

| Value | Protocol/Format | Typical Fields |
|-------|-----------------|----------------|
| `AIS` | NMEA sentences | mmsi, lat, lon, sog, cog, heading |
| `ADSB` | Mode-S EHS | icao, callsign, alt, gs, track |
| `WEATHER` | CAP/JSON | event_type, severity, area_polygon |
| `PORT_STATUS` | Proprietary API | port_id, wait_time, berth_availability |
| `CYBER_ALERT` | STIX/TAXII | indicator_type, threat_actor, impact |
| `RADIO_LOG` | CSV/Text | timestamp, frequency, duration, signal_strength |

---

## Anomaly Types (AnomalyType Enum)

See `docs/ARCHITECTURE.md` § Anomaly Detection Engine for full catalog.

---

## Indexes & Performance

| Table | Index | Purpose |
|-------|-------|---------|
| Observation | `(entity_id, timestamp)` | Fast track queries |
| Observation | `(source_type, timestamp)` | Feed health monitoring |
| Anomaly | `(entity_id, severity)` | Priority queue rendering |
| Anomaly | `(status, detected_at)` | Open anomaly list |
| AuditEvent | `(timestamp)` | Chronological replay |
| Entity | `(type, last_seen)` | Filtered map views |

---

## Migration Strategy

Schema changes are managed via Alembic (production) or SQLModel auto-create (development). All migrations must:
1. Preserve existing data
2. Maintain backward compatibility for 2 versions
3. Include rollback scripts
4. Update `DATA_MODEL.md`

---

*Last updated: 2025-01-15*
