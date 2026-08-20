# AegisGraph - Decision Intelligence Platform

## Implementation Summary

This implementation provides a complete decision intelligence platform with the following core capabilities:

### 1. Entity Resolution (`backend/fusion/entity_resolver.py`)

Resolves multi-source observations into unified entities using:
- **Exact ID matching** - Matches on external identifiers (AIS MMSI, ADS-B callsigns)
- **Fuzzy name matching** - Uses normalized string comparison with configurable thresholds
- **Geo-temporal association** - Haversine distance calculation with speed plausibility checks

Key features:
- Weighted confidence scoring across multiple match strategies
- Resolution to existing entities or creation of new entities
- Batch processing for unresolved observations

### 2. Anomaly Detection Engine (`backend/analytics/anomaly_engine.py`)

Detects anomalies using rule-based and statistical methods:

**Anomaly Types Implemented:**
| Type | Description | Severity Factors |
|------|-------------|------------------|
| `route_deviation` | Entity deviates from expected path | Deviation distance |
| `dark_vessel` | Vehicle stops transmitting | Time since last seen |
| `sensor_dropout` | Gaps in sensor coverage | Duration of gap |
| `port_congestion` | Unusual vessel density | Vessel count threshold |
| `cyber_outage` | Correlated system failures | Multiple source impact |
| `conflicting_reports` | Position discrepancies | Distance between reports |
| `abnormal_proximity` | Entities too close | Separation distance |
| `delayed_feed` | Latency in data feeds | Delay duration |
| `identity_mismatch` | Conflicting identifiers | Number of sources |
| `unusual_loitering` | Extended stationary behavior | Time + area |
| `speed_anomaly` | Statistical speed outliers | Z-score threshold |
| `heading_change` | Sudden course changes | Angle magnitude |

Each anomaly includes:
- `anomaly_type`, `severity`, `score`
- `triggered_rules` (explainable rules)
- `evidence_ids` (linked observations)
- `explanation` (human-readable)
- `recommended_action`
- `uncertainty` (confidence metric)

### 3. Ontology Graph (`backend/ontology/ontology_graph.py`)

Builds a knowledge graph connecting:
- **Entities** (vessels, aircraft, land vehicles)
- **Observations** (sensor reports)
- **Anomalies** (detected issues)
- **Actions** (recommended responses)
- **Source Reports** (data feed metadata)

Relationships include:
- `observed_by` - Entity to source
- `has_anomaly` - Entity to anomaly
- `based_on` - Anomaly to evidence
- `escalated_to` - Anomaly to action
- `approved_by` - Action to user
- `near` - Entity proximity edges
- `correlated_with` - Related anomalies

Output format compatible with Cytoscape.js for visualization.

### 4. Audit Log (`backend/governance/audit.py`)

Implements an append-only, hash-chained audit log:
- SHA-256 cryptographic hashing
- Each entry links to previous entry's hash
- Tamper detection via chain verification
- Event types: SYSTEM, USER, DECISION

Key methods:
- `log_event()` - Create new audit entry
- `verify_chain()` - Validate integrity
- `log_decision()` - Record human approvals/rejections

### 5. AI Analyst (`backend/llm/llm_analyst.py`)

Retrieval-first AI analyst that:
- Retrieves relevant facts before generating responses
- Answers ONLY from retrieved system data
- Always returns citations/evidence references
- Includes confidence scores and limitations
- Falls back to deterministic mock LLM when no API key available

Response structure:
```json
{
    "answer": "...",
    "citations": ["Record #123", "Entity #45"],
    "confidence": 0.85,
    "limitations": ["Data may be delayed", ...]
}
```

### 6. Synthetic Data Generator (`backend/synthetic/synthetic_data_generator.py`)

Generates 24 hours of fictional test data:
- 60 vessels, 30 aircraft, 10 land vehicles
- ~150 observations per entity
- 10+ planted anomalies (one of each type)
- Source report metadata
- Initial audit entry

### 7. REST API (`backend/api/`)

FastAPI application with endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/entities` | GET | List entities with filters |
| `/api/entities/{id}` | GET | Entity details with observations |
| `/api/anomalies` | GET | List anomalies with filters |
| `/api/anomalies/{id}` | GET | Anomaly details with evidence |
| `/api/actions` | GET | List actions |
| `/api/actions/{id}/approve` | POST | Approve action |
| `/api/actions/{id}/reject` | POST | Reject action |
| `/api/audit` | GET | Audit log entries |
| `/api/audit/verify` | GET | Verify audit chain |
| `/api/graph` | GET | Ontology graph for visualization |
| `/api/graph/node/{id}` | GET | Node details |
| `/api/ask` | POST | Query AI analyst |
| `/api/tracks` | GET | Live entity tracks |
| `/api/ingest/run` | POST | Run resolution + detection |
| `/ws/live` | WebSocket | Real-time updates |

## Directory Structure

```
backend/
├── api/
│   ├── main.py          # FastAPI application
│   └── routes.py        # API route handlers
├── analytics/
│   └── anomaly_engine.py # Anomaly detection
├── fusion/
│   └── entity_resolver.py # Entity resolution
├── governance/
│   └── audit.py         # Audit logging
├── llm/
│   └── llm_analyst.py   # AI analyst
├── models/
│   └── database.py      # SQLAlchemy models
├── ontology/
│   └── ontology_graph.py # Knowledge graph
├── synthetic/
│   └── synthetic_data_generator.py
├── config.py            # Configuration
└── database.py          # Database setup
```

## Quick Start

```bash
# Initialize database and generate synthetic data
python -m backend.synthetic.synthetic_data_generator

# Run the API server
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example Queries

```bash
# Get all HIGH severity anomalies
curl http://localhost:8000/api/anomalies?severity=HIGH

# Ask the AI analyst
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me any high-severity anomalies"}'

# Get the ontology graph
curl http://localhost:8000/api/graph

# Verify audit chain integrity
curl http://localhost:8000/api/audit/verify
```

## Key Design Decisions

1. **Explainability First**: All anomalies include triggered rules and explanations
2. **Retrieval-Augmented Generation**: AI analyst only answers from actual data
3. **Cryptographic Audit Trail**: Hash-chained logs detect tampering
4. **Confidence Scoring**: All outputs include uncertainty metrics
5. **Mock Fallback**: System works without external LLM API keys
