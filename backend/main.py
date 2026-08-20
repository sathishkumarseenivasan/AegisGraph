"""
AegisGraph Main API Application.

FastAPI application with REST endpoints and WebSocket support.
"""
import json
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from starlette.websockets import WebSocketState

from database import create_db_and_tables, get_session
from config import settings
from models import (
    Entity, EntityRead, Anomaly, AnomalyRead, Action, ActionUpdate,
    ActionStatus, AuditLog, AuditLogRead, GraphData, GraphNodeRead,
    GraphEdgeRead, AskRequest, AskResponse, Observation, Sensor,
    Rule, AuditAction
)
from synthetic import SyntheticDataGenerator
from ingestion import DataIngester
from fusion import EntityResolver
from analytics import AnomalyEngine
from ontology import OntologyGraph
from governance import AuditLogger
from llm import LLMAnalyst


# Connection manager for WebSocket broadcasts
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                if connection.application_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                else:
                    disconnected.append(connection)
            except:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    create_db_and_tables()
    print("Database tables created")
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Mission-grade decision intelligence platform demo",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== UTILITY ENDPOINTS ====================

@app.post("/seed")
def seed_database(session: Session = Depends(get_session)):
    """Seed database with synthetic data."""
    # Generate synthetic data
    generator = SyntheticDataGenerator(num_entities=100, hours=24)
    data = generator.generate_all()
    
    # Ingest into database
    ingester = DataIngester(session)
    counts = ingester.ingest_all(data)
    
    # Run anomaly detection
    engine = AnomalyEngine(session)
    anomalies = engine.detect_all()
    
    for anomaly in anomalies:
        session.add(anomaly)
    session.commit()
    
    # Build ontology graph
    graph = OntologyGraph(session)
    graph.build_graph()
    
    # Log seeding event
    audit = AuditLogger(session)
    audit.log(
        actor="system",
        action=AuditAction.SYSTEM_EVENT,
        payload={"event": "database_seeded", "counts": counts}
    )
    
    return {
        "message": "Database seeded successfully",
        "counts": counts,
        "anomalies_detected": len(anomalies)
    }


# ==================== ENTITY ENDPOINTS ====================

@app.get("/entities", response_model=List[EntityRead])
def get_entities(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get all entities with optional filtering."""
    statement = select(Entity)
    
    if entity_type:
        statement = statement.where(Entity.entity_type == entity_type)
    
    statement = statement.offset(skip).limit(limit)
    results = session.exec(statement)
    return results.all()


@app.get("/entities/{entity_id}")
def get_entity(entity_id: str, session: Session = Depends(get_session)):
    """Get a specific entity by ID."""
    statement = select(Entity).where(Entity.entity_id == entity_id)
    result = session.exec(statement).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return result


# ==================== TRACK ENDPOINTS ====================

@app.get("/tracks")
def get_tracks(session: Session = Depends(get_session)):
    """Get current tracks (latest positions) for all mobile entities."""
    statement = select(Entity).where(
        Entity.entity_type.in_(["vessel", "aircraft"])
    )
    results = session.exec(statement)
    
    tracks = []
    for entity in results.all():
        tracks.append({
            "entity_id": entity.entity_id,
            "entity_type": entity.entity_type.value,
            "name": entity.name,
            "latitude": entity.latitude,
            "longitude": entity.longitude,
            "altitude": entity.altitude,
            "speed": entity.speed,
            "heading": entity.heading,
            "course": entity.course,
            "last_seen": entity.last_seen.isoformat() if entity.last_seen else None,
            "risk_score": entity.risk_score
        })
    
    return {"tracks": tracks, "count": len(tracks)}


# ==================== OBSERVATION ENDPOINTS ====================

@app.get("/observations")
def get_observations(
    skip: int = 0,
    limit: int = 100,
    entity_id: Optional[str] = None,
    source_type: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get observations with optional filtering."""
    statement = select(Observation).order_by(Observation.timestamp.desc())
    
    if entity_id:
        statement = statement.where(Observation.entity_id == entity_id)
    if source_type:
        statement = statement.where(Observation.source_type == source_type)
    
    statement = statement.offset(skip).limit(limit)
    results = session.exec(statement)
    return results.all()


# ==================== ANOMALY ENDPOINTS ====================

@app.get("/anomalies", response_model=List[AnomalyRead])
def get_anomalies(
    skip: int = 0,
    limit: int = 50,
    severity: Optional[str] = None,
    unresolved_only: bool = False,
    session: Session = Depends(get_session)
):
    """Get detected anomalies."""
    statement = select(Anomaly).order_by(Anomaly.created_at.desc())
    
    if severity:
        statement = statement.where(Anomaly.severity == severity)
    if unresolved_only:
        statement = statement.where(Anomaly.is_resolved == False)
    
    statement = statement.offset(skip).limit(limit)
    results = session.exec(statement)
    return results.all()


@app.get("/anomalies/{anomaly_id}")
def get_anomaly(anomaly_id: str, session: Session = Depends(get_session)):
    """Get a specific anomaly by ID."""
    statement = select(Anomaly).where(Anomaly.anomaly_id == anomaly_id)
    result = session.exec(statement).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    return result


# ==================== GRAPH ENDPOINTS ====================

@app.get("/graph")
def get_graph(session: Session = Depends(get_session)):
    """Get ontology graph data for visualization."""
    graph = OntologyGraph(session)
    return graph.build_graph()


# ==================== AI ANALYST ENDPOINT ====================

@app.post("/ask", response_model=AskResponse)
def ask_analyst(request: AskRequest, session: Session = Depends(get_session)):
    """Ask the AI analyst a question."""
    analyst = LLMAnalyst(
        session=session,
        api_key=settings.LLM_API_KEY,
        api_base=settings.LLM_API_BASE
    )
    
    response = analyst.ask(request.question, request.context_filters)
    
    # Log the query
    audit = AuditLogger(session)
    audit.log(
        actor="api_user",
        action=AuditAction.USER_QUERY,
        payload={
            "question": request.question,
            "confidence": response["confidence"],
            "fact_count": response.get("fact_count", 0)
        }
    )
    
    return AskResponse(
        answer=response["answer"],
        citations=response["citations"],
        confidence=response["confidence"],
        limitations=response["limitations"]
    )


# ==================== ACTION ENDPOINTS ====================

@app.post("/actions/{action_id}/approve")
def approve_action(
    action_id: str,
    user: str = "operator",
    session: Session = Depends(get_session)
):
    """Approve a recommended action."""
    statement = select(Action).where(Action.action_id == action_id)
    action = session.exec(statement).first()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    action.status = ActionStatus.APPROVED
    action.approved_by = user
    action.approved_at = datetime.utcnow()
    action.updated_at = datetime.utcnow()
    
    session.add(action)
    session.commit()
    session.refresh(action)
    
    # Log approval
    audit = AuditLogger(session)
    audit.log(
        actor=user,
        action=AuditAction.ACTION_APPROVED,
        payload={
            "action_id": action_id,
            "action_type": action.action_type,
            "description": action.description
        }
    )
    
    return {"message": "Action approved", "action": action}


@app.post("/actions/{action_id}/reject")
def reject_action(
    action_id: str,
    reason: str = "No reason provided",
    user: str = "operator",
    session: Session = Depends(get_session)
):
    """Reject a recommended action."""
    statement = select(Action).where(Action.action_id == action_id)
    action = session.exec(statement).first()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    action.status = ActionStatus.REJECTED
    action.rejected_by = user
    action.rejected_at = datetime.utcnow()
    action.rejection_reason = reason
    action.updated_at = datetime.utcnow()
    
    session.add(action)
    session.commit()
    session.refresh(action)
    
    # Log rejection
    audit = AuditLogger(session)
    audit.log(
        actor=user,
        action=AuditAction.ACTION_REJECTED,
        payload={
            "action_id": action_id,
            "reason": reason
        }
    )
    
    return {"message": "Action rejected", "action": action}


# ==================== AUDIT ENDPOINT ====================

@app.get("/audit", response_model=List[AuditLogRead])
def get_audit_log(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session)
):
    """Get audit log entries."""
    audit_logger = AuditLogger(session)
    entries = audit_logger.get_entries(limit=limit, offset=offset)
    return entries


@app.get("/audit/verify")
def verify_audit_chain(session: Session = Depends(get_session)):
    """Verify integrity of the audit chain."""
    audit_logger = AuditLogger(session)
    return audit_logger.verify_chain()


# ==================== WEBSOCKET ENDPOINT ====================

@app.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive, receive messages
            data = await websocket.receive_text()
            
            # Parse client message
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def background_broadcast():
    """Background task to broadcast updates."""
    import asyncio
    
    while True:
        try:
            # Broadcast system status
            await manager.broadcast({
                "type": "status_update",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "System operational"
            })
        except:
            pass
        
        await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)


# ==================== HEALTH CHECK ====================

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
