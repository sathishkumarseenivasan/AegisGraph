# AegisGraph 60-Second Demo Script

## Purpose

This script guides you through a narrated, 60-second demonstration of AegisGraph's core capabilities. Designed for conference booths, stakeholder reviews, or portfolio presentations.

---

## Pre-Demo Checklist

- [ ] Backend running: `make run-api` (port 8000)
- [ ] Frontend running: `make run-web` (port 3000)
- [ ] Database seeded: `make seed` (if not already done)
- [ ] Browser open to `http://localhost:3000`
- [ ] Timer visible (optional)

---

## Demo Flow (60 Seconds)

### 0:00–0:10 — Dashboard Overview

**Action**: Land on home page (Map view).

**Narration**:
> "AegisGraph fuses multi-source data—vessels, aircraft, weather, cyber—into a unified operational picture. Here you see 100 entities tracked in real-time."

**Point out**:
- Map with entity markers (color-coded by type)
- Live update counter (top-right)
- Anomaly badges (red icons)

---

### 0:10–0:20 — Anomaly Detection

**Action**: Click **Anomalies** tab in sidebar.

**Narration**:
> "Our explainable anomaly engine detects 12 planted scenarios: route deviations, dark vessels, sensor dropouts. Each anomaly includes severity, evidence, and a recommended action."

**Point out**:
- Anomaly list sorted by severity
- Click one anomaly → expansion panel
- Show `triggered_rules`, `evidence_ids`, `explanation`

---

### 0:20–0:30 — Human-in-the-Loop Action

**Action**: Select a HIGH severity anomaly → Click **Approve Action**.

**Narration**:
> "Every action requires human approval. I'll approve this 'Investigate vessel' recommendation. Notice the instant audit trail."

**Point out**:
- Approval confirmation toast
- Status changes PENDING → APPROVED
- Audit log entry appears

---

### 0:30–0:40 — Knowledge Graph

**Action**: Click **Graph** tab.

**Narration**:
> "Behind the scenes, AegisGraph builds an ontology: entities, observations, anomalies, actions—all linked. Click any node to inspect relationships."

**Point out**:
- Force-directed graph layout
- Node colors (Entity=blue, Anomaly=red, Action=green)
- Hover → tooltip with details
- Click → side panel with attributes

---

### 0:40–0:50 — AI Analyst

**Action**: Click **Analyst** tab → Type query: *"Show me all high-severity anomalies and their status."*

**Narration**:
> "Ask natural language questions. The AI retrieves facts only from our database, cites every claim, and admits uncertainty."

**Point out**:
- Query typed and submitted
- Response appears with **citations** (evidence IDs)
- Confidence meter (e.g., "High confidence")
- Limitations section ("Only covers last 24 hours")

---

### 0:50–1:00 — Audit Integrity

**Action**: Click **Audit** tab → Run verification.

**Narration**:
> "Every decision is cryptographically chained. Run the verifier to prove no tampering occurred. This is mission-grade accountability."

**Point out**:
- Audit timeline (chronological events)
- Click **Verify Hash Chain** button
- Green checkmark: "PASS - All hashes valid"

**Closing line**:
> "AegisGraph: Fuse, detect, decide, audit—all explainable, all synthetic, all safe."

---

## Post-Demo Q&A Prompts

Be ready for these questions:

1. **"Is this real data?"**
   - No, entirely synthetic. See `docs/SECURITY_MODEL.md`.

2. **"How accurate is entity resolution?"**
   - ~94% on seeded demo. Run `make eval` for metrics.

3. **"Can I add my own data sources?"**
   - Yes, extend `/backend/ingestion/parsers/`.

4. **"What LLM do you use?"**
   - Qwen-compatible API if available; otherwise deterministic mock.

5. **"How do I deploy this?"**
   - See `README.md` Quickstart. Docker Compose TODO.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Map not loading | Check browser console for CORS errors |
| No anomalies visible | Run `make seed` to regenerate data |
| AI Analyst returns empty | Verify backend logs for retrieval errors |
| Audit verify fails | Database corrupted; re-run `make seed` |

---

## Extended Demo (Optional, +2 minutes)

If you have more time:

### +0:30 — Ontology Builder
- Upload sample CSV (`backend/synthetic/sample_ontology.csv`)
- Show inferred entity types and relationships

### +0:30 — WebSocket Live Updates
- Open browser dev tools → Network → WS
- Watch live track updates every 3 seconds

### +0:30 — Failure Mode Demo
- Simulate sensor dropout in config
- Show anomaly detection triggering

---

## Recording Tips

For best video quality:
- Use 1920×1080 resolution
- Enable dark mode in browser
- Hide browser bookmarks bar
- Use cursor highlight effect (e.g., KeyCastr)
- Record at 60fps for smooth map animations

**Export**: MP4 H.264, 10 Mbps bitrate

---

*Practice timing with a stopwatch. Aim for 55 seconds to allow 5 seconds buffer.*
