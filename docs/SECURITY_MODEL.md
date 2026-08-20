# AegisGraph Security Model & Safety Scope

## Executive Summary

AegisGraph is a **synthetic, demonstration-only** decision intelligence platform. It processes **no real-world sensitive, classified, or personally identifiable information (PII)**. This document outlines the threat model, trust boundaries, and explicit safety constraints.

---

## Safety Constraints (Non-Negotiable)

| Constraint | Enforcement Mechanism | Verification |
|------------|----------------------|--------------|
| **Synthetic data only** | Data generator uses seeded RNG; no external feeds | Code review of `/backend/synthetic/` |
| **No military targeting** | No weapon systems, strike recommendations, or lethality logic | Architecture review; no such modules exist |
| **No harmful autonomy** | All actions require human approval | Governance workflow enforced in code |
| **No classified data** | System designed for unclassified demo use | Data model has no classification fields |
| **No PII processing** | All names/IDs are procedurally generated | Synthetic data audit |
| **No real-time operational use** | Demo runs on historical synthetic data | Documentation + disclaimers |

---

## Threat Model (STRIDE-Lite)

### 1. Spoofing Identity

**Threat**: Attacker impersonates a user to approve malicious actions.

**Mitigations**:
- Session-based authentication (future: OAuth2/JWT)
- Audit log captures `actor` field for all state changes
- Human-in-the-loop requires explicit user ID

**Residual Risk**: Low (demo has no auth; production would add OAuth2)

---

### 2. Tampering with Data

**Threat**: Attacker modifies observations, anomalies, or audit logs.

**Mitigations**:
- **Audit Log**: SHA-256 hash chain makes tampering detectable
- **Database**: SQLite WAL mode with file permissions
- **Application**: ORM parameterization prevents SQL injection

**Verification**: Run `scripts/verify_audit.py` to check hash chain integrity.

**Residual Risk**: Medium (SQLite not encrypted; production would use TDE)

---

### 3. Repudiation

**Threat**: User denies approving an action.

**Mitigations**:
- Append-only audit log with cryptographic hashing
- Each event includes `actor`, `timestamp`, `payload`
- Hash chain prevents retroactive modification

**Residual Risk**: Low (assuming hash chain verification)

---

### 4. Information Disclosure

**Threat**: Sensitive data exposed via API or UI.

**Mitigations**:
- **No sensitive data exists**: All data is synthetic
- CORS configured for localhost only (dev)
- No logging of request bodies (avoids accidental PII capture)

**Residual Risk**: None (by design—no sensitive data to leak)

---

### 5. Denial of Service

**Threat**: Attacker overwhelms API with requests.

**Mitigations**:
- SQLite connection pooling limits concurrent writes
- WebSocket heartbeat detects stale connections
- Rate limiting TODO (production requirement)

**Residual Risk**: Medium (no rate limiting in demo)

---

### 6. Elevation of Privilege

**Threat**: User gains unauthorized approval rights.

**Mitigations**:
- No privilege tiers in demo (all users equal)
- Production would implement RBAC
- All approvals logged with actor ID

**Residual Risk**: Low (demo has no privilege escalation path)

---

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                     UNTRUSTED (External)                    │
│  ┌─────────────┐         ┌─────────────┐                   │
│  │   Browser   │         │  curl/API   │                   │
│  │   Client    │         │   Client    │                   │
│  └──────┬──────┘         └──────┬──────┘                   │
│         │                       │                           │
│         ▼                       ▼                           │
├─────────────────────────────────────────────────────────────┤
│                  TRUST BOUNDARY 1: API Validation           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              FastAPI Request Validation             │   │
│  │  • Pydantic schema enforcement                      │   │
│  │  • Type coercion & validation                       │   │
│  │  • CORS origin checking                             │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  TRUST BOUNDARY 2: Application Logic        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Core Services                          │   │
│  │  • Entity resolution (deterministic)                │   │
│  │  • Anomaly detection (explainable rules)            │   │
│  │  • AI analyst (retrieval-grounded, cited)           │   │
│  │  • Governance workflow (human approval required)    │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  TRUST BOUNDARY 3: Data Integrity           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SQLite Database                        │   │
│  │  • ORM parameterization (no SQL injection)          │   │
│  │  • Hash-chained audit log (tamper-evident)          │   │
│  │  • Foreign key constraints                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Audit Log Integrity

### Hash Chain Algorithm

```python
def compute_hash(event: AuditEvent) -> str:
    payload = {
        "event_id": event.event_id,
        "timestamp": event.timestamp.isoformat(),
        "actor": event.actor,
        "action": event.action,
        "payload": event.payload,
        "previous_hash": event.previous_hash
    }
    return sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
```

### Verification Process

1. Load all audit events ordered by timestamp
2. For each event:
   - Recompute `current_hash` from payload
   - Verify matches stored `current_hash`
   - Verify `previous_hash` matches prior event's `current_hash`
3. Report PASS/FAIL

**Command**: `python scripts/verify_audit.py`

---

## AI Analyst Grounding Policy

### Retrieval-First Design

The AI Analyst **cannot** answer questions without retrieved evidence.

**Flow**:
1. User submits query
2. Retriever searches entities, anomalies, observations
3. If no results → Return "Insufficient evidence" (no LLM call)
4. If results exist → Construct grounded prompt with citations
5. LLM generates response **only from provided facts**
6. Response includes `citations`, `confidence`, `limitations`

### Refusal Behaviors

| Query Type | Response |
|------------|----------|
| No matching evidence | "Insufficient evidence to answer this query." |
| Opinion/advice request | "I can only report factual observations from the system." |
| Future prediction | "I cannot predict future events; I only analyze historical data." |
| Outside scope (e.g., weather forecast) | "This query is outside my knowledge base." |

### Hallucination Mitigation

- **Citation requirement**: Every claim must reference an evidence ID
- **Confidence scoring**: Low confidence if evidence is weak
- **Limitations field**: Explicit statement of what the model cannot know
- **Mock fallback**: Deterministic responses when no API key (no hallucination risk)

---

## Human-in-the-Loop Governance

### Action Approval Workflow

```
[Anomaly Detected]
       ↓
[System proposes Action]
       ↓
[Status: PENDING] → [Human Review]
                          ↓
              ┌───────────┴───────────┐
              ▼                       ▼
       [APPROVE]                 [REJECT]
              │                       │
              ▼                       ▼
       [EXECUTED]            [REJECTED + reason]
              │                       │
              ▼                       ▼
       [Audit Event]           [Audit Event]
```

### Enforcement

- Actions cannot transition to `EXECUTED` without `approved_by` field
- Rejection requires `rejection_reason`
- All transitions logged in audit trail

---

## Data Lifecycle

### Creation
- All data generated by `SyntheticDataGenerator` with fixed seed
- No external API calls during generation
- Timestamps are synthetic (not real-time)

### Storage
- SQLite database file (`aegisgraph.db`)
- No encryption at rest (demo only)
- File permissions: owner read/write only

### Deletion
- `rm aegisgraph.db` removes all data
- No backups in demo configuration
- Audit log persists until manual deletion

---

## Compliance Notes

| Regulation | Applicability | Status |
|------------|---------------|--------|
| ITAR | No defense articles | Not applicable |
| EAR | No controlled tech | Not applicable |
| GDPR | No EU personal data | Not applicable |
| HIPAA | No health information | Not applicable |
| FISMA | No federal systems | Not applicable |

**Note**: This is a **demonstration project** and must not be used for operational decision-making.

---

## Production Hardening Requirements

Before deploying to production, implement:

1. **Authentication**: OAuth2 with MFA
2. **Authorization**: RBAC with least privilege
3. **Encryption**: TLS 1.3 in transit, AES-256 at rest
4. **Rate Limiting**: Per-user API quotas
5. **Logging**: Structured logs with correlation IDs
6. **Monitoring**: Alerting on anomaly detection failures
7. **Backup**: Encrypted daily backups with retention policy
8. **Audit**: Immutable ledger (e.g., AWS QLDB, blockchain)
9. **Penetration Testing**: Annual third-party assessment
10. **Incident Response**: Documented playbook for breaches

---

## Reporting Security Issues

**DO NOT** report synthetic data issues as vulnerabilities.

**DO** report:
- Actual security bugs (SQL injection, XSS, etc.)
- Audit log integrity failures
- Unauthorized access vectors

Contact: [security@example.com](mailto:security@example.com) (placeholder)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-15 | Initial security model |

---

*This document is part of the AegisGraph safety framework. See also: `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `README.md`.*
