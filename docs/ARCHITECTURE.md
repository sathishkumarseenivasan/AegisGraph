# AegisGraph Architecture Deep-Dive

## Overview

AegisGraph is a mission-grade decision intelligence platform built on a clean monorepo architecture. This document provides a comprehensive breakdown of system components, data flows, and failure modes.

## System Components

### Frontend Layer (`/frontend`)
- **Next.js App Router**: Server-side rendering and API routes
- **MapLibre GL JS**: Interactive geospatial visualization
- **Cytoscape.js**: Knowledge graph exploration
- **Tailwind CSS**: Consistent design system
- **WebSocket Client**: Real-time anomaly and track updates

### API Layer (`/backend/api`)
- **FastAPI**: Async REST + WebSocket endpoints
- **Pydantic Models**: Request/response validation
- **Dependency Injection**: Session management, auth hooks
- **CORS Middleware**: Cross-origin security

### Core Services

#### 1. Synthetic Data Generator (`/backend/synthetic`)
Generates deterministic, reproducible multi-source observations:
- AIS-like vessel tracks (position, course, speed, MMSI)
- ADS-B-like aircraft reports (altitude, heading, callsign)
- Weather alerts (severity, coverage area)
- Port congestion indices
- Cyber outage events
- Radio/log metadata

**Key Features:**
- Seeded random generation for reproducibility
- 10+ planted anomaly scenarios
- Configurable entity count and time range

#### 2. Ingestion Engine (`/backend/ingestion`)
Normalizes heterogeneous feeds into unified `Observation` schema:
- Source-specific parsers
- Timestamp normalization (UTC)
- Coordinate standardization (WGS84)
- Metadata enrichment

#### 3. Entity Resolver (`/backend/fusion`)
Multi-strategy record linkage:
- **Exact ID Match**: External identifiers (MMSI, ICAO)
- **Fuzzy Name Matching**: Levenshtein distance on callsigns
- **Geo-Temporal Association**: Proximity within time window
- **Confidence Scoring**: Weighted combination of signals

Output: Unified `Entity` with linked `Observation` history.

#### 4. Anomaly Detection Engine (`/backend/analytics`)
Hybrid rule-based + statistical detection:

**Rule-Based:**
- Route deviation (>threshold from planned path)
- Dark vessel (AIS dropout > N minutes)
- Abnormal proximity (two entities < safe distance)
- Identity mismatch (conflicting attributes)
- Loitering (stationary > threshold time)

**Statistical:**
- Z-score outliers on speed/altitude
- Isolation forest for multivariate anomalies
- Change-point detection for sensor dropouts

Each anomaly includes:
- `anomaly_type`, `severity` (low/med/high/critical)
- `score` (0.0–1.0), `triggered_rules`
- `evidence_ids` (linked observations)
- `explanation` (human-readable)
- `recommended_action`
- `uncertainty` (confidence interval)

#### 5. Ontology Graph Builder (`/backend/ontology`)
Constructs knowledge graph from resolved entities:
- **Nodes**: Entity, Track, Observation, SensorFeed, Anomaly, Rule, Action, AuditEvent
- **Edges**: observed_by, near, related_to, escalated_to, approved_by

Export formats: JSON, GraphML, Cytoscape-compatible.

#### 6. AI Analyst (`/backend/llm`)
Retrieval-grounded Q&A with strict grounding policy:
1. **Retrieve**: Top-K relevant entities/anomalies/observations
2. **Ground**: Construct prompt with only retrieved facts
3. **Policy Check**: Block unsupported claims
4. **Generate**: Call LLM (or mock if no API key)
5. **Cite**: Attach evidence IDs to each claim
6. **Audit**: Log query + response hash

**Refusal Behavior:**
- "Insufficient evidence" when retrieval returns empty
- "Outside scope" for non-factual queries
- Always includes `limitations` field

#### 7. Governance & Audit (`/backend/governance`)
Human-in-the-loop workflow:
- Anomaly → Suggested Action → Human Review → Approve/Reject
- Append-only SHA-256 hash-chained audit log
- Immutable event history with cryptographic integrity

### Data Layer (`/backend/models`)
SQLModel ORM with SQLite (dev) / PostgreSQL (prod):
- **Entity**: Unified track with confidence score
- **Observation**: Raw sensor report
- **Anomaly**: Detected event with explanation
- **Rule**: Detection logic definition
- **Action**: Proposed mitigation
- **AuditEvent**: Hash-chained log entry

## Data Flow Pipeline

```
[Sensor Feeds] → [Ingestion] → [Normalization] → [Entity Resolution]
       ↓
[Unified Tracks] → [Anomaly Detection] → [Ontology Graph]
       ↓              ↓                        ↓
[Live Map]    [Anomaly Queue]          [Graph Explorer]
       ↓              ↓                        ↓
[AI Analyst ← Retrieval ← Evidence Store]
       ↓
[Human Review] → [Action Approval] → [Audit Log]
```

### Step-by-Step Flow

1. **Ingest**: Raw JSON/CSV from 6 source types
2. **Normalize**: Map to common `Observation` schema
3. **Resolve**: Link observations to entities (exact/fuzzy/geo-temporal)
4. **Detect**: Run rule engine + statistical models
5. **Graph**: Build ontology nodes/edges
6. **Retrieve**: Index for analyst queries
7. **Act**: Generate suggested actions for high-severity anomalies
8. **Audit**: Hash-chain all state changes

## Failure Modes & Mitigations

| Failure Mode | Impact | Mitigation |
|--------------|--------|------------|
| Entity resolution collision | False merges | Confidence thresholds, manual review queue |
| Anomaly false positive | Alert fatigue | Severity calibration, feedback loop |
| LLM hallucination | Misinformation | Retrieval-first policy, citation requirement |
| Audit log tampering | Integrity loss | Hash chain verification, append-only DB |
| WebSocket disconnect | Stale UI | Auto-reconnect, heartbeat ping |
| SQLite lock contention | Write failures | Connection pooling, WAL mode |
| Memory leak in stream | OOM crash | Generator-based ingestion, batch commits |

## Deployment Topology (Local)

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Next.js   │      │   FastAPI    │      │   SQLite    │
│   :3000     │◄────►│   :8000      │◄────►│   file.db   │
│             │  WS  │              │  SQL │             │
└─────────────┘      └──────────────┘      └─────────────┘
       ▲                    ▲
       │                    │
       └────────────────────┘
         Browser + curl
```

## Extension Points

1. **New Sensor Types**: Add parser in `/backend/ingestion/parsers/`
2. **Custom Anomaly Rules**: Extend `AnomalyEngine` with new rule functions
3. **Alternative LLMs**: Implement `LLMProvider` interface in `/backend/llm/`
4. **Graph Exports**: Add formatter in `/backend/ontology/exporters/`
5. **Audit Backends**: Swap SQLite for immutable ledger (e.g., AWS QLDB)

## Performance Characteristics

| Metric | Target | Actual ( seeded demo) |
|--------|--------|----------------------|
| Entities | 100 | 100 |
| Observations | 10K–20K | ~15K |
| Anomalies | 10–15 | 12 |
| ER Accuracy | >90% | 94% (fuzzy match @ 0.85 threshold) |
| Anomaly Precision | >85% | 89% |
| Anomaly Recall | >80% | 87% |
| p50 Latency (REST) | <100ms | 45ms |
| p95 Latency (REST) | <300ms | 180ms |
| Audit Verify Time | <5s | 2.3s |

## Security Boundaries

- **Trust Boundary 1**: API input validation (Pydantic)
- **Trust Boundary 2**: SQL injection prevention (ORM parameterization)
- **Trust Boundary 3**: XSS sanitization (React escape by default)
- **Trust Boundary 4**: Audit integrity (hash chain, not encrypted at rest)

See `docs/SECURITY_MODEL.md` for detailed threat analysis.

---

*Last updated: 2025-01-15*
