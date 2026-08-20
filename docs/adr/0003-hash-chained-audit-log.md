# ADR 0003: Hash-Chained Audit Log

## Status

Accepted

## Context

AegisGraph records all significant system events and human decisions. Users must be able to verify that the audit trail has not been tampered with, ensuring accountability and enabling post-incident analysis.

Key requirements:
- Tamper-evident logging
- Cryptographic integrity verification
- Append-only semantics
- Chronological ordering
- Complete event history

## Decision

**Implement an append-only audit log with SHA-256 hash chaining.** Each event includes the hash of the previous event, creating a cryptographic chain where any modification breaks the linkage.

Data model:
```python
class AuditEvent(SQLModel, table=True):
    id: UUID = PrimaryKey()
    event_id: str  # Unique identifier
    timestamp: datetime
    actor: str  # User or system ID
    action: str  # CREATE, UPDATE, APPROVE, REJECT
    payload: dict  # Event-specific data
    previous_hash: str  # SHA-256 of previous event (null for genesis)
    current_hash: str  # SHA-256 of this event
```

Hash computation:
```python
def compute_hash(event: AuditEvent, previous_hash: Optional[str]) -> str:
    payload = {
        "event_id": event.event_id,
        "timestamp": event.timestamp.isoformat(),
        "actor": event.actor,
        "action": event.action,
        "payload": event.payload,
        "previous_hash": previous_hash
    }
    return sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
```

Genesis event:
- `previous_hash` = 64 zeros (`"0" * 64`)
- Special marker in payload: `{"genesis": true}`

## Consequences

### Positive
- Tamper-evident: Any modification changes hash, breaking chain
- Verifiable: Anyone can recompute and validate
- Simple implementation: No external dependencies
- PostgreSQL/SQLite compatible: Works with any SQL database
- Immutable by design: Append-only, no updates/deletes

### Negative
- No encryption at rest (hash ≠ encryption)
- Linear verification time (must check entire chain)
- Single point of failure (database file)
- No distributed consensus (not blockchain)

### Mitigations
- Production: Add database encryption (TDE)
- Performance: Cache verified checkpoints
- Durability: Regular backups to immutable storage
- Distributed: Future migration to AWS QLDB or similar

## Verification Process

Script `scripts/verify_audit.py`:
1. Load all events ordered by timestamp
2. For each event:
   - Recompute `current_hash` from payload fields
   - Verify matches stored `current_hash`
   - Verify `previous_hash` equals prior event's `current_hash`
3. Report PASS if all checks succeed, FAIL otherwise

Expected output:
```
✓ Audit chain verification: PASS
  Events verified: 156
  Genesis hash: 0000000000000000...
  Latest hash: a3f2b8c9d4e5f6...
```

## Alternatives Considered

### Option A: Simple Timestamped Log (Rejected)
Log events with timestamps but no hashing.
- **Problem**: Easy to modify retroactively, no integrity guarantee

### Option B: Digital Signatures (Deferred)
Sign each event with private key.
- **Problem**: Adds PKI complexity, key management overhead
- **Future**: May implement for production deployment

### Option C: Blockchain Ledger (Rejected)
Use Ethereum/Hyperledger for audit storage.
- **Problem**: Massive overkill for demo, adds latency, cost
- **Future**: Consider if multi-party trust required

### Option D: AWS QLDB (Production TODO)
Amazon's managed immutable ledger service.
- **Problem**: Vendor lock-in, cost, requires AWS
- **Future**: Recommended for production deployment

## Compliance

This design aligns with:
- **Audit Integrity** requirements in `docs/SECURITY_MODEL.md`
- **Governance workflow** (all actions logged)
- **Accountability principles** (who did what, when)

## References

- `backend/governance/audit.py`
- `backend/models/__init__.py` (AuditEvent model)
- `scripts/verify_audit.py`
- `docs/SECURITY_MODEL.md` § Audit Log Integrity
- `README.md` § Governance & Audit

---

*ADR authored: 2025-01-15*
*Review cycle: Annual*
