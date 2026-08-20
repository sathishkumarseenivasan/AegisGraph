"""
Ontology Graph Module.

Builds and manages the knowledge graph with nodes and edges for:
- Entities
- Sensors
- Events
- Anomalies
- Actions
- Rules

Relationship types:
- observed_by
- near
- related_to
- escalated_to
- approved_by
"""
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlmodel import Session, select
from backend.models import (
    Entity, Sensor, Anomaly, Action, Rule, Observation,
    GraphNode, GraphEdge
)


class OntologyGraph:
    """Manages the ontology graph for entity relationships."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def build_graph(self) -> Dict[str, Any]:
        """Build the complete ontology graph from database entities."""
        # Clear existing graph
        self.session.exec("DELETE FROM graph_edges")
        self.session.exec("DELETE FROM graph_nodes")
        self.session.commit()
        
        # Create nodes for all entities
        self._create_entity_nodes()
        self._create_sensor_nodes()
        self._create_anomaly_nodes()
        self._create_action_nodes()
        self._create_rule_nodes()
        
        # Create edges
        self._create_observation_edges()
        self._create_proximity_edges()
        self._create_escalation_edges()
        self._create_approval_edges()
        
        return self.get_graph_data()
    
    def _create_entity_nodes(self) -> None:
        """Create graph nodes for all entities."""
        entities = self.session.exec(select(Entity)).all()
        
        for entity in entities:
            node = GraphNode(
                node_id=f"node-{entity.entity_id}",
                node_type="entity",
                ref_id=entity.entity_id,
                label=entity.name,
                properties={
                    "entity_type": entity.entity_type.value,
                    "latitude": entity.latitude,
                    "longitude": entity.longitude,
                    "is_active": entity.is_active,
                    "risk_score": entity.risk_score
                }
            )
            self.session.add(node)
        
        self.session.commit()
    
    def _create_sensor_nodes(self) -> None:
        """Create graph nodes for all sensors."""
        sensors = self.session.exec(select(Sensor)).all()
        
        for sensor in sensors:
            node = GraphNode(
                node_id=f"node-{sensor.sensor_id}",
                node_type="sensor",
                ref_id=sensor.sensor_id,
                label=sensor.name,
                properties={
                    "sensor_type": sensor.sensor_type.value,
                    "is_operational": sensor.is_operational,
                    "location_name": sensor.location_name
                }
            )
            self.session.add(node)
        
        self.session.commit()
    
    def _create_anomaly_nodes(self) -> None:
        """Create graph nodes for all anomalies."""
        anomalies = self.session.exec(select(Anomaly)).all()
        
        for anomaly in anomalies:
            node = GraphNode(
                node_id=f"node-{anomaly.anomaly_id}",
                node_type="anomaly",
                ref_id=anomaly.anomaly_id,
                label=f"{anomaly.anomaly_type.value}",
                properties={
                    "severity": anomaly.severity.value,
                    "score": anomaly.score,
                    "is_resolved": anomaly.is_resolved,
                    "anomaly_type": anomaly.anomaly_type.value
                }
            )
            self.session.add(node)
        
        self.session.commit()
    
    def _create_action_nodes(self) -> None:
        """Create graph nodes for all actions."""
        actions = self.session.exec(select(Action)).all()
        
        for action in actions:
            node = GraphNode(
                node_id=f"node-{action.action_id}",
                node_type="action",
                ref_id=action.action_id,
                label=action.action_type,
                properties={
                    "status": action.status.value,
                    "priority": action.priority,
                    "description": action.description
                }
            )
            self.session.add(node)
        
        self.session.commit()
    
    def _create_rule_nodes(self) -> None:
        """Create graph nodes for all rules."""
        rules = self.session.exec(select(Rule)).all()
        
        for rule in rules:
            node = GraphNode(
                node_id=f"node-{rule.rule_id}",
                node_type="rule",
                ref_id=rule.rule_id,
                label=rule.name,
                properties={
                    "category": rule.category,
                    "threshold": rule.threshold,
                    "enabled": rule.enabled,
                    "anomaly_type": rule.anomaly_type.value
                }
            )
            self.session.add(node)
        
        self.session.commit()
    
    def _create_observation_edges(self) -> None:
        """Create edges between entities and their observing sensors."""
        # Get recent observations
        from datetime import timedelta
        recent_time = datetime.utcnow() - timedelta(hours=1)
        
        from sqlalchemy import text
        obs_statement = select(Observation).where(
            Observation.timestamp >= recent_time
        ).limit(500)
        observations = self.session.exec(obs_statement).all()
        
        created_edges = set()
        
        for obs in observations:
            if obs.entity_id and obs.sensor_id:
                edge_key = f"{obs.entity_id}-{obs.sensor_id}"
                if edge_key not in created_edges:
                    edge = GraphEdge(
                        edge_id=f"edge-obs-{uuid.uuid4().hex[:8]}",
                        source_node_id=f"node-{obs.entity_id}",
                        target_node_id=f"node-{obs.sensor_id}",
                        relationship_type="observed_by",
                        weight=obs.confidence,
                        properties={
                            "observation_count": 1,
                            "last_observation": obs.timestamp.isoformat()
                        }
                    )
                    self.session.add(edge)
                    created_edges.add(edge_key)
        
        self.session.commit()
    
    def _create_proximity_edges(self) -> None:
        """Create edges between entities that are near each other."""
        entities = self.session.exec(
            select(Entity).where(Entity.latitude != None)
        ).all()
        
        created_edges = set()
        
        for i, e1 in enumerate(entities):
            for j, e2 in enumerate(entities):
                if i >= j:
                    continue
                
                if not e1.latitude or not e2.latitude:
                    continue
                
                # Calculate simple distance
                lat_diff = abs((e1.latitude or 0) - (e2.latitude or 0))
                lon_diff = abs((e1.longitude or 0) - (e2.longitude or 0))
                
                # Within ~50km
                if lat_diff < 0.5 and lon_diff < 0.5:
                    edge_key = tuple(sorted([e1.entity_id, e2.entity_id]))
                    if edge_key not in created_edges:
                        distance = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111  # Rough km conversion
                        
                        edge = GraphEdge(
                            edge_id=f"edge-near-{uuid.uuid4().hex[:8]}",
                            source_node_id=f"node-{e1.entity_id}",
                            target_node_id=f"node-{e2.entity_id}",
                            relationship_type="near",
                            weight=max(0, 1.0 - distance / 50),
                            properties={
                                "distance_km": round(distance, 2),
                                "entity1_type": e1.entity_type.value,
                                "entity2_type": e2.entity_type.value
                            }
                        )
                        self.session.add(edge)
                        created_edges.add(edge_key)
        
        self.session.commit()
    
    def _create_escalation_edges(self) -> None:
        """Create edges showing anomaly escalation to actions."""
        anomalies = self.session.exec(select(Anomaly)).all()
        
        for anomaly in anomalies:
            if anomaly.recommended_action_id:
                # Get the action
                action = self.session.get(Action, anomaly.recommended_action_id)
                if action:
                    edge = GraphEdge(
                        edge_id=f"edge-esc-{uuid.uuid4().hex[:8]}",
                        source_node_id=f"node-{anomaly.anomaly_id}",
                        target_node_id=f"node-{action.action_id}",
                        relationship_type="escalated_to",
                        weight=anomaly.score,
                        properties={
                            "severity": anomaly.severity.value,
                            "timestamp": anomaly.timestamp.isoformat()
                        }
                    )
                    self.session.add(edge)
        
        self.session.commit()
    
    def _create_approval_edges(self) -> None:
        """Create edges showing action approval chain."""
        actions = self.session.exec(select(Action)).all()
        
        for action in actions:
            if action.approved_by:
                # Create a virtual user node
                user_node_id = f"node-user-{action.approved_by}"
                
                # Check if user node exists
                user_node = self.session.get(GraphNode, user_node_id)
                if not user_node:
                    user_node = GraphNode(
                        node_id=user_node_id,
                        node_type="user",
                        ref_id=action.approved_by,
                        label=action.approved_by,
                        properties={"role": "approver"}
                    )
                    self.session.add(user_node)
                
                edge = GraphEdge(
                    edge_id=f"edge-apr-{uuid.uuid4().hex[:8]}",
                    source_node_id=user_node_id,
                    target_node_id=f"node-{action.action_id}",
                    relationship_type="approved_by",
                    weight=1.0,
                    properties={
                        "approved_at": action.approved_at.isoformat() if action.approved_at else None,
                        "status": action.status.value
                    }
                )
                self.session.add(edge)
        
        self.session.commit()
    
    def get_graph_data(self) -> Dict[str, Any]:
        """Get complete graph data for visualization."""
        nodes = self.session.exec(select(GraphNode)).all()
        edges = self.session.exec(select(GraphEdge)).all()
        
        return {
            "nodes": [
                {
                    "id": node.node_id,
                    "type": node.node_type,
                    "label": node.label,
                    "properties": node.properties
                }
                for node in nodes
            ],
            "edges": [
                {
                    "id": edge.edge_id,
                    "source": edge.source_node_id,
                    "target": edge.target_node_id,
                    "relationship": edge.relationship_type,
                    "weight": edge.weight,
                    "properties": edge.properties
                }
                for edge in edges
            ],
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": self._count_by_type(nodes),
                "relationship_types": self._count_by_relationship(edges)
            }
        }
    
    def _count_by_type(self, nodes: List[GraphNode]) -> Dict[str, int]:
        """Count nodes by type."""
        counts = {}
        for node in nodes:
            counts[node.node_type] = counts.get(node.node_type, 0) + 1
        return counts
    
    def _count_by_relationship(self, edges: List[GraphEdge]) -> Dict[str, int]:
        """Count edges by relationship type."""
        counts = {}
        for edge in edges:
            counts[edge.relationship_type] = counts.get(edge.relationship_type, 0) + 1
        return counts
    
    def get_node_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific node."""
        node = self.session.get(GraphNode, node_id)
        if not node:
            return None
        
        # Get connected edges
        incoming = self.session.exec(
            select(GraphEdge).where(GraphEdge.target_node_id == node_id)
        ).all()
        
        outgoing = self.session.exec(
            select(GraphEdge).where(GraphEdge.source_node_id == node_id)
        ).all()
        
        return {
            "node": {
                "id": node.node_id,
                "type": node.node_type,
                "label": node.label,
                "properties": node.properties
            },
            "incoming_edges": [
                {
                    "id": edge.edge_id,
                    "source": edge.source_node_id,
                    "relationship": edge.relationship_type,
                    "weight": edge.weight
                }
                for edge in incoming
            ],
            "outgoing_edges": [
                {
                    "id": edge.edge_id,
                    "target": edge.target_node_id,
                    "relationship": edge.relationship_type,
                    "weight": edge.weight
                }
                for edge in outgoing
            ]
        }
