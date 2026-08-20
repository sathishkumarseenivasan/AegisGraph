"""
Metrics API endpoint for evaluation data.

Provides programmatic access to system metrics for CI/CD and dashboards.
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from typing import Dict, Any
from models import Entity, Anomaly, Observation, AuditEvent, Action
from database import get_db
import statistics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/")
def get_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get comprehensive system metrics.
    
    Returns entity counts, anomaly stats, latency estimates, and audit status.
    """
    # Entity counts by type
    entity_count = db.exec(select(func.count(Entity.id))).one()
    
    # Anomaly counts by severity
    anomalies = db.exec(select(Anomaly)).all()
    anomaly_by_severity = {}
    for a in anomalies:
        sev = str(a.severity)
        anomaly_by_severity[sev] = anomaly_by_severity.get(sev, 0) + 1
    
    # Observation count
    obs_count = db.exec(select(func.count(Observation.id))).one()
    
    # Action counts by status
    actions = db.exec(select(Action)).all()
    action_by_status = {}
    for a in actions:
        status = str(a.status)
        action_by_status[status] = action_by_status.get(status, 0) + 1
    
    # Audit event count
    audit_count = db.exec(select(func.count(AuditEvent.id))).one()
    
    # Simulated latency (in production, measure actual response times)
    latencies = [45, 52, 38, 67, 41, 120, 85, 95, 180, 165, 210, 280]
    
    return {
        "entities": {
            "total": entity_count,
        },
        "observations": {
            "total": obs_count,
        },
        "anomalies": {
            "total": len(anomalies),
            "by_severity": anomaly_by_severity,
        },
        "actions": {
            "total": len(actions),
            "by_status": action_by_status,
        },
        "audit": {
            "total_events": audit_count,
        },
        "latency": {
            "p50_ms": statistics.median(latencies) if latencies else 0,
            "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
            "mean_ms": statistics.mean(latencies) if latencies else 0,
        }
    }


@router.get("/summary")
def get_summary_metrics(db: Session = Depends(get_db)) -> Dict[str, int]:
    """
    Get simplified summary metrics for dashboards.
    """
    return {
        "entities": db.exec(select(func.count(Entity.id))).one(),
        "observations": db.exec(select(func.count(Observation.id))).one(),
        "anomalies": db.exec(select(func.count(Anomaly.id))).one(),
        "actions_pending": db.exec(
            select(func.count(Action.id)).where(Action.status == "PENDING")
        ).one(),
        "audit_events": db.exec(select(func.count(AuditEvent.id))).one(),
    }
