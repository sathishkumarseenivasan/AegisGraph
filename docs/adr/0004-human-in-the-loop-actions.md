# ADR 0004: Human-in-the-Loop Actions

## Status

Accepted

## Context

AegisGraph detects anomalies and recommends actions. However, automated execution of actions without human oversight creates risks:
- False positives could trigger unnecessary responses
- Users may not trust fully autonomous systems
- Accountability unclear if automated action causes harm
- Ethical concerns about AI-driven decisions in sensitive domains

## Decision

**All actions must require explicit human approval before execution.** The system can propose actions, but cannot execute them without a user's approve/reject decision.

Workflow:
```
[Anomaly Detected]
       ↓
[System proposes Action with recommended_action field]
       ↓
[Action created with status=PENDING]
       ↓
[Human reviews in UI]
       ↓
    ┌───────┴───────┐
    ▼               ▼
[APPROVE]      [REJECT]
    │               │
    ▼               ▼
status=APPROVED  status=REJECTED
    │              + rejection_reason
    ▼
[EXECUTED]
    │
    ▼
[AuditEvent logged]
```

State machine:
```
PENDING → APPROVED → EXECUTED
        ↘ REJECTED (terminal)
```

Enforcement rules:
1. Actions created with `status = PENDING`
2. Transition to `APPROVED` requires `approved_by` user ID
3. Transition to `REJECTED` requires `rejection_reason` text
4. Only `APPROVED` actions can transition to `EXECUTED`
5. All transitions logged in audit trail

## Consequences

### Positive
- Clear accountability (human made final decision)
- Reduces risk from false positives
- Builds user trust (system assists, doesn't replace)
- Ethically defensible (no harmful autonomy)
- Audit trail captures who approved what

### Negative
- Slower response time (requires human attention)
- Cannot handle high-frequency automated responses
- User fatigue if too many low-severity actions
- Requires UI for review/approval

### Mitigations
- Filter by severity (only HIGH/CRITICAL require approval)
- Batch similar actions for bulk approval
- Auto-dismiss LOW severity after N hours (configurable)
- Future: Trusted automation for well-understood scenarios

## Implementation

Model fields:
```python
class Action(SQLModel, table=True):
    anomaly_id: UUID  # Foreign key
    action_type: ActionType
    description: str
    proposed_by: str  # System or user
    status: ActionStatus = ActionStatus.PENDING
    approved_by: Optional[str]  # User ID (required if approved)
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]  # Required if rejected
    executed_at: Optional[datetime]
```

API endpoints:
- `POST /actions/{id}/approve` - Transition to APPROVED
- `POST /actions/{id}/reject` - Transition to REJECTED
- `POST /actions/{id}/execute` - Transition to EXECUTED (only if APPROVED)

Audit logging:
```python
def approve_action(action_id: UUID, user_id: str):
    action = get_action(action_id)
    action.status = ActionStatus.APPROVED
    action.approved_by = user_id
    action.approved_at = datetime.utcnow()
    
    audit.log(
        actor=user_id,
        action="APPROVE",
        payload={"action_id": str(action_id), "anomaly_id": str(action.anomaly_id)}
    )
```

## Alternatives Considered

### Option A: Fully Autonomous Execution (Rejected)
System executes recommended actions automatically.
- **Problem**: High risk, no accountability, user distrust
- **Exception**: May allow for LOW severity with opt-in

### Option B: Approval Only for CRITICAL (Deferred)
Require approval only for CRITICAL severity anomalies.
- **Problem**: Medium-severity issues still auto-executed
- **Future**: May implement tiered approval workflow

### Option C: Delegation with Limits (Future)
Allow users to delegate approval authority with constraints.
- Example: "Auto-approve INVESTIGATE actions for vessels with confidence > 0.9"
- **Problem**: Adds complexity, policy management overhead
- **Future**: Consider for production deployment

## Compliance

This design aligns with:
- **Safety Constraints** in `docs/SECURITY_MODEL.md` ("No harmful autonomy")
- **Governance requirements** (human oversight)
- **Ethical AI principles** (human agency preserved)

## References

- `backend/governance/action_workflow.py`
- `backend/api/action_routes.py`
- `backend/models/__init__.py` (Action model)
- `docs/SECURITY_MODEL.md` § Safety Constraints
- `README.md` § Governance & Audit

---

*ADR authored: 2025-01-15*
*Review cycle: Annual*
