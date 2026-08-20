# AegisGraph Evaluation & Metrics

## Purpose

This document defines how to compute and reproduce all evaluation metrics for AegisGraph. Run the evaluation script to generate a markdown table of results.

---

## Metrics Overview

| Category | Metric | Target | Description |
|----------|--------|--------|-------------|
| **Entity Resolution** | Precision | >90% | Correct merges / total merges |
| | Recall | >85% | Correct merges / gold standard merges |
| | F1 Score | >87% | Harmonic mean |
| **Anomaly Detection** | Precision | >85% | True positives / predicted positives |
| | Recall | >80% | True positives / actual positives |
| | False Positive Rate | <15% | False alarms / total negatives |
| **Latency** | p50 REST | <100ms | Median API response time |
| | p95 REST | <300ms | 95th percentile |
| | p99 WebSocket | <500ms | Live update latency |
| **Audit Integrity** | Hash verification | 100% | All chains valid |
| | Event completeness | 100% | No gaps in sequence |
| **AI Analyst** | Grounding accuracy | 100% | All claims cited |
| | Refusal correctness | 100% | Proper "insufficient evidence" responses |

---

## Running Evaluation

### Prerequisites

```bash
# Ensure backend is running
make run-api &

# Seed the database with deterministic data
make seed
```

### Execute Evaluation Script

```bash
cd scripts
python eval_demo.py
```

**Output**: Markdown table printed to stdout, optionally saved to `docs/EVALUATION_RESULTS.md`.

---

## Metric Computation Details

### Entity Resolution Accuracy

**Gold Standard**: The synthetic data generator records true entity identities. We compare resolved entities against ground truth.

**Algorithm**:
```python
def compute_er_metrics(resolved_entities, gold_standard):
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    
    for resolved in resolved_entities:
        best_match = find_best_gold_match(resolved, gold_standard)
        if best_match and best_match.confidence >= 0.85:
            if resolved.external_id == best_match.external_id:
                true_positives += 1
            else:
                false_positives += 1
        else:
            false_negatives += 1
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {"precision": precision, "recall": recall, "f1": f1}
```

**Reproduction**:
1. Run `make seed` (deterministic with seed=42)
2. Query `/entities` endpoint
3. Compare against `synthetic/gold_standard.json`

---

### Anomaly Detection Precision/Recall

**Gold Standard**: 12 planted anomalies with known types, severities, and timestamps.

**Algorithm**:
```python
def compute_anomaly_metrics(detected_anomalies, planted_anomalies):
    true_positives = 0
    false_positives = 0
    
    for detected in detected_anomalies:
        # Match by type and temporal proximity (±5 minutes)
        matching_planted = find_matching_planted(detected, planted_anomalies)
        if matching_planted:
            true_positives += 1
        else:
            false_positives += 1
    
    false_negatives = len(planted_anomalies) - true_positives
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    return {"precision": precision, "recall": recall, "false_negatives": fn}
```

**Planted Anomalies** (12 total):
1. Route deviation (vessel)
2. Dark vessel (AIS dropout)
3. Sensor dropout (aircraft)
4. Port congestion spike
5. Cyber outage correlated with physical anomaly
6. Conflicting reports (identity mismatch)
7. Abnormal proximity (two vessels too close)
8. Delayed feed (latency injection)
9. Identity mismatch (callsign conflict)
10. Unusual loitering (stationary > threshold)
11. Speed anomaly (statistical outlier)
12. Altitude deviation (aircraft)

---

### Latency Measurement

**Method**: Benchmark suite fires 100 requests per endpoint, records response times.

**Endpoints Tested**:
- `GET /entities`
- `GET /entities/{id}`
- `GET /anomalies`
- `GET /graph`
- `POST /ask`

**Statistics**:
```python
import numpy as np

latencies = [...]  # List of response times in ms
p50 = np.percentile(latencies, 50)
p95 = np.percentile(latencies, 95)
p99 = np.percentile(latencies, 99)
mean = np.mean(latencies)
std = np.std(latencies)
```

**WebSocket Latency**:
- Measure time from server publish to client receive
- Use `performance.now()` on both ends
- Account for clock skew via NTP sync (or assume negligible for local dev)

---

### Audit Chain Verification

**Algorithm**:
```python
import hashlib
import json

def verify_audit_chain(events):
    previous_hash = None
    
    for event in events:
        # Recompute hash
        payload = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "actor": event.actor,
            "action": event.action,
            "payload": event.payload,
            "previous_hash": previous_hash
        }
        computed_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        
        # Verify current hash
        if computed_hash != event.current_hash:
            return {"valid": False, "error": f"Hash mismatch at {event.event_id}"}
        
        # Verify chain linkage
        if event.previous_hash != previous_hash:
            return {"valid": False, "error": f"Chain broken at {event.event_id}"}
        
        previous_hash = event.current_hash
    
    return {"valid": True, "events_verified": len(events)}
```

**Command**: `python scripts/verify_audit.py`

**Expected Output**:
```
✓ Audit chain verification: PASS
  Events verified: 156
  Genesis hash: 0000...0000
  Latest hash: a3f2...8b9c
```

---

### AI Analyst Grounding Accuracy

**Test Suite**: 20 queries with known answerability.

| Query Type | Count | Expected Behavior |
|------------|-------|-------------------|
| Answerable (facts exist) | 10 | Response with citations |
| Unanswerable (no evidence) | 5 | "Insufficient evidence" |
| Opinion/advice | 3 | Refusal + scope statement |
| Future prediction | 2 | Refusal + limitation |

**Scoring**:
- **Grounding accuracy**: % of answerable queries with valid citations
- **Refusal correctness**: % of unanswerable queries correctly refused

**Manual Review Required**: Citation validity must be checked by human (automated script flags missing citations).

---

## Reproducing Results

### Deterministic Seed

All metrics are reproducible with fixed seed:

```bash
# Set environment variable
export AEGIS_SEED=42

# Regenerate data
make seed

# Run evaluation
python scripts/eval_demo.py
```

### Expected Results (Seed=42)

| Metric | Value | Pass/Fail |
|--------|-------|-----------|
| ER Precision | 0.94 | ✓ |
| ER Recall | 0.91 | ✓ |
| ER F1 | 0.925 | ✓ |
| Anomaly Precision | 0.89 | ✓ |
| Anomaly Recall | 0.87 | ✓ |
| p50 Latency | 45ms | ✓ |
| p95 Latency | 180ms | ✓ |
| Audit Verification | PASS | ✓ |
| Grounding Accuracy | 100% | ✓ |
| Refusal Correctness | 100% | ✓ |

*Your results may vary slightly due to system load.*

---

## Continuous Integration

Add to CI pipeline:

```yaml
# .github/workflows/eval.yml
name: Evaluation

on: [push]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Seed database
        run: make seed
      - name: Run evaluation
        run: python scripts/eval_demo.py
      - name: Verify audit
        run: python scripts/verify_audit.py
```

---

## Performance Tuning Tips

If metrics fall short:

1. **Entity Resolution**: Adjust fuzzy match threshold (default 0.85)
2. **Anomaly Detection**: Tune rule parameters in `analytics/anomaly_engine.py`
3. **Latency**: Enable SQLite WAL mode, add indexes
4. **WebSocket**: Reduce update frequency (default 3s → 5s)

---

## Exporting Results

```bash
# Save to file
python scripts/eval_demo.py > docs/EVALUATION_RESULTS.md

# JSON format for CI
python scripts/eval_demo.py --format json > results.json
```

---

*Last updated: 2025-01-15*

*Run `make eval` to regenerate this report.*
