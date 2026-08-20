# ADR 0001: Synthetic Data Only

## Status

Accepted

## Context

AegisGraph is designed as a demonstration platform for decision intelligence capabilities. We must ensure the system cannot accidentally process real-world sensitive, classified, or personally identifiable information (PII).

Key concerns:
- Legal/regulatory compliance (ITAR, EAR, GDPR)
- Ethical responsibility (no harmful applications)
- Reproducibility (deterministic demos)
- Safety (no operational use cases)

## Decision

**All data in AegisGraph must be synthetically generated.** No external feeds, no real-world sensors, no user-uploaded operational data.

Implementation:
- `SyntheticDataGenerator` class produces all observations
- Seeded random number generation (default seed=42) for reproducibility
- Procedurally generated names, IDs, and trajectories
- No API calls to external data sources during generation
- Clear documentation that this is a demo-only system

## Consequences

### Positive
- Zero regulatory burden (no ITAR/EAR/GDPR implications)
- Fully reproducible demonstrations
- Safe to share publicly (GitHub, conferences)
- No risk of accidental data leakage
- Deterministic testing (same seed → same dataset)

### Negative
- Cannot demonstrate real-world data integration
- Less convincing than live operational data
- Users might mistakenly treat as operational tool

### Mitigations
- Prominent disclaimers in README and UI
- Security model documentation
- No deployment instructions for production use
- Code review ensures no external feed connectors

## Compliance

This decision aligns with:
- **Safety Constraints** in `docs/SECURITY_MODEL.md`
- **Repository license** (MIT—research/education use)
- **Ethical AI principles** (no harmful autonomy)

## References

- `backend/synthetic/synthetic_data_generator.py`
- `docs/SECURITY_MODEL.md` § Safety Constraints
- `README.md` § Safety Disclaimer

---

*ADR authored: 2025-01-15*
*Review cycle: Annual*
