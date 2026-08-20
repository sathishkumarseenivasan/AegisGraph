"""
LLM Analyst Module.

Retrieval-first AI analyst that:
- Answers questions only from retrieved system facts
- Always returns citations/evidence references
- Includes confidence and uncertainty
- Says when evidence is insufficient
- Uses mock LLM if no API key available
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from models import Entity, Anomaly, Observation, Action, Rule, AuditLog


class LLMAnalyst:
    """Retrieval-based AI analyst with citations."""
    
    def __init__(self, session: Session, api_key: Optional[str] = None, api_base: Optional[str] = None):
        self.session = session
        self.api_key = api_key
        self.api_base = api_base
        self.use_mock = not api_key
    
    def ask(self, question: str, context_filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Answer a question using retrieved system facts.
        
        Args:
            question: Natural language question
            context_filters: Optional filters for retrieval
        
        Returns:
            Dict with answer, citations, confidence, and limitations
        """
        # Retrieve relevant facts
        retrieved_facts = self._retrieve_facts(question, context_filters)
        
        if not retrieved_facts["facts"]:
            return {
                "answer": "I cannot answer this question as there is insufficient data in the system. Please try asking about entities, anomalies, actions, or recent observations.",
                "citations": [],
                "confidence": 0.0,
                "limitations": "No relevant facts found in the knowledge base",
                "query_timestamp": datetime.utcnow()
            }
        
        if self.use_mock:
            return self._mock_response(question, retrieved_facts)
        else:
            return self._llm_response(question, retrieved_facts)
    
    def _retrieve_facts(
        self,
        question: str,
        context_filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Retrieve relevant facts from the database."""
        facts = []
        citations = []
        
        question_lower = question.lower()
        
        # Determine what to retrieve based on question keywords
        if "vessel" in question_lower or "ship" in question_lower or "entity" in question_lower:
            entities = self._get_relevant_entities(question, context_filters)
            for e in entities:
                facts.append(f"Entity: {e.name} ({e.entity_type.value}), ID: {e.entity_id}, "
                           f"Position: {e.latitude:.4f},{e.longitude:.4f}, "
                           f"Risk Score: {e.risk_score:.2f}")
                citations.append({"type": "entity", "id": e.entity_id, "name": e.name})
        
        if "anomal" in question_lower or "alert" in question_lower or "issue" in question_lower:
            anomalies = self._get_relevant_anomalies(question, context_filters)
            for a in anomalies:
                facts.append(f"Anomaly: {a.anomaly_type.value} (Severity: {a.severity.value}), "
                           f"Score: {a.score:.2f}, Explanation: {a.explanation[:100]}")
                citations.append({"type": "anomaly", "id": a.anomaly_id})
        
        if "action" in question_lower or "recommend" in question_lower:
            actions = self._get_relevant_actions(question, context_filters)
            for act in actions:
                facts.append(f"Action: {act.action_type} - {act.description[:80]}, "
                           f"Status: {act.status.value}, Priority: {act.priority}")
                citations.append({"type": "action", "id": act.action_id})
        
        if "observation" in question_lower or "report" in question_lower or "track" in question_lower:
            observations = self._get_recent_observations(context_filters)
            for obs in observations[:10]:  # Limit observations
                facts.append(f"Observation: Entity {obs.entity_id} at {obs.latitude:.4f},{obs.longitude:.4f} "
                           f"on {obs.timestamp.isoformat()[:19]}")
                citations.append({"type": "observation", "id": obs.observation_id})
        
        if "rule" in question_lower or "detect" in question_lower:
            rules = self._get_rules()
            for r in rules:
                facts.append(f"Rule: {r.name} ({r.anomaly_type.value}), Threshold: {r.threshold}")
                citations.append({"type": "rule", "id": r.rule_id})
        
        if "audit" in question_lower or "log" in question_lower or "history" in question_lower:
            audits = self._get_recent_audits()
            for aud in audits[:5]:
                facts.append(f"Audit: {aud.action.value} by {aud.actor} at {aud.timestamp.isoformat()[:19]}")
                citations.append({"type": "audit", "id": aud.event_id})
        
        # If no specific type matched, get general summary
        if not facts:
            facts = self._get_system_summary()
        
        return {
            "facts": facts,
            "citations": citations,
            "fact_count": len(facts)
        }
    
    def _get_relevant_entities(self, question: str, filters: Optional[Dict]) -> List[Entity]:
        """Get entities relevant to the question."""
        statement = select(Entity).limit(20)
        
        if filters and filters.get("entity_type"):
            statement = statement.where(Entity.entity_type == filters["entity_type"])
        
        results = self.session.exec(statement)
        return results.all()
    
    def _get_relevant_anomalies(self, question: str, filters: Optional[Dict]) -> List[Anomaly]:
        """Get anomalies relevant to the question."""
        statement = select(Anomaly).order_by(Anomaly.created_at.desc()).limit(20)
        
        if filters and filters.get("severity"):
            statement = statement.where(Anomaly.severity == filters["severity"])
        
        if "unresolved" in question.lower() or "open" in question.lower():
            statement = statement.where(Anomaly.is_resolved == False)
        
        results = self.session.exec(statement)
        return results.all()
    
    def _get_relevant_actions(self, question: str, filters: Optional[Dict]) -> List[Action]:
        """Get actions relevant to the question."""
        statement = select(Action).order_by(Action.created_at.desc()).limit(20)
        
        if "pending" in question.lower():
            statement = statement.where(Action.status == "pending")
        
        results = self.session.exec(statement)
        return results.all()
    
    def _get_recent_observations(self, filters: Optional[Dict]) -> List[Observation]:
        """Get recent observations."""
        from datetime import timedelta
        recent_time = datetime.utcnow() - timedelta(hours=1)
        
        statement = select(Observation).where(
            Observation.timestamp >= recent_time
        ).order_by(Observation.timestamp.desc()).limit(50)
        
        results = self.session.exec(statement)
        return results.all()
    
    def _get_rules(self) -> List[Rule]:
        """Get all detection rules."""
        results = self.session.exec(select(Rule))
        return results.all()
    
    def _get_recent_audits(self) -> List[AuditLog]:
        """Get recent audit log entries."""
        results = self.session.exec(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(20)
        )
        return results.all()
    
    def _get_system_summary(self) -> List[str]:
        """Get a general system summary."""
        entity_count = len(self.session.exec(select(Entity)).all())
        anomaly_count = len(self.session.exec(select(Anomaly).where(Anomaly.is_resolved == False)).all())
        action_count = len(self.session.exec(select(Action).where(Action.status == "pending")).all())
        
        return [
            f"System Summary: {entity_count} tracked entities",
            f"Active Anomalies: {anomaly_count}",
            f"Pending Actions: {action_count}"
        ]
    
    def _mock_response(self, question: str, retrieved: Dict) -> Dict[str, Any]:
        """Generate a deterministic mock response when no LLM API is available."""
        facts = retrieved["facts"]
        citations = retrieved["citations"]
        
        # Generate answer based on retrieved facts
        if len(facts) == 0:
            answer = "I don't have enough information to answer this question."
            confidence = 0.0
        elif len(facts) <= 3:
            answer = f"Based on {len(facts)} relevant fact(s): {'; '.join(facts)}"
            confidence = 0.7
        else:
            # Summarize the facts
            answer = f"I found {len(facts)} relevant pieces of information. "
            answer += f"Key findings: {'; '.join(facts[:3])}"
            if len(facts) > 3:
                answer += f" (+ {len(facts) - 3} more items)"
            confidence = min(0.9, 0.6 + len(facts) * 0.05)
        
        # Calculate confidence based on fact count and citation quality
        confidence = min(0.95, confidence + (len(citations) * 0.02))
        
        limitations = ""
        if len(facts) < 5:
            limitations = "Limited data available. Consider expanding the query time range or checking sensor coverage."
        elif len(citations) == 0:
            limitations = "No direct citations available. Answer based on inferred patterns."
        else:
            limitations = "Answer limited to data ingested into the system. Real-time changes may not be reflected."
        
        return {
            "answer": answer,
            "citations": citations[:10],  # Limit citations
            "confidence": round(confidence, 2),
            "limitations": limitations,
            "query_timestamp": datetime.utcnow(),
            "fact_count": len(facts),
            "mock_mode": True
        }
    
    def _llm_response(self, question: str, retrieved: Dict) -> Dict[str, Any]:
        """Call external LLM API with retrieved context."""
        # Build grounded prompt
        context = "\n".join(retrieved["facts"])
        
        prompt = f"""You are an AI analyst for AegisGraph, a decision intelligence platform.
Answer the user's question using ONLY the retrieved facts below. 
Always cite your sources by referencing the fact numbers.
If the facts don't contain enough information, say so clearly.

RETRIEVED FACTS:
{context}

QUESTION: {question}

Provide your answer in JSON format with these fields:
- answer: Your response
- citations: List of citation objects with type and id
- confidence: A number 0-1 indicating your confidence
- limitations: Any limitations of your answer"""

        try:
            # Would call actual LLM API here
            # For now, fall back to mock
            return self._mock_response(question, retrieved)
        except Exception as e:
            return {
                "answer": f"Error generating response: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "limitations": "LLM API call failed",
                "query_timestamp": datetime.utcnow()
            }
