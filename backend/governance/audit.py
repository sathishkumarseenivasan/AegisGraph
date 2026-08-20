"""
Audit Log Module.

Implements append-only hash-chained audit log using SHA-256.
Every important action is recorded with cryptographic integrity.
"""
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlmodel import Session, select
from models import AuditLog, AuditAction


class AuditLogger:
    """Cryptographically secure audit logging with hash chaining."""
    
    def __init__(self, session: Session):
        self.session = session
        self._last_hash: Optional[str] = None
        self._chain_index: int = self._get_current_chain_index()
    
    def _get_current_chain_index(self) -> int:
        """Get the current highest chain index."""
        statement = select(AuditLog).order_by(AuditLog.chain_index.desc()).limit(1)
        result = self.session.exec(statement).first()
        return result.chain_index if result else -1
    
    def _get_last_hash(self) -> str:
        """Get the hash of the last entry in the chain."""
        statement = select(AuditLog).order_by(AuditLog.chain_index.desc()).limit(1)
        result = self.session.exec(statement).first()
        return result.current_hash if result else "0" * 64  # Genesis block hash
    
    def _compute_hash(
        self,
        event_id: str,
        timestamp: str,
        actor: str,
        action: str,
        payload: Dict,
        previous_hash: str
    ) -> str:
        """Compute SHA-256 hash for audit entry."""
        # Create canonical string representation
        data = {
            "event_id": event_id,
            "timestamp": timestamp,
            "actor": actor,
            "action": action,
            "payload": payload,
            "previous_hash": previous_hash
        }
        
        # Serialize deterministically
        canonical = "|".join([
            str(data["event_id"]),
            str(data["timestamp"]),
            str(data["actor"]),
            str(data["action"]),
            str(sorted(data["payload"].items())),
            str(data["previous_hash"])
        ])
        
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def log(
        self,
        actor: str,
        action: AuditAction,
        payload: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> AuditLog:
        """
        Add a new entry to the audit log.
        
        Args:
            actor: User, system, or API that performed the action
            action: Type of auditable action
            payload: Action details and context
            timestamp: When the action occurred (defaults to now)
        
        Returns:
            The created AuditLog entry
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Get previous hash for chain
        previous_hash = self._get_last_hash()
        
        # Generate event ID
        event_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"
        
        # Increment chain index
        self._chain_index += 1
        
        # Compute current hash
        current_hash = self._compute_hash(
            event_id=event_id,
            timestamp=timestamp.isoformat(),
            actor=actor,
            action=action.value,
            payload=payload,
            previous_hash=previous_hash
        )
        
        # Create audit log entry
        audit_entry = AuditLog(
            event_id=event_id,
            timestamp=timestamp,
            actor=actor,
            action=action,
            payload=payload,
            previous_hash=previous_hash,
            current_hash=current_hash,
            chain_index=self._chain_index
        )
        
        self.session.add(audit_entry)
        self.session.commit()
        self.session.refresh(audit_entry)
        
        return audit_entry
    
    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify the integrity of the entire audit chain.
        
        Returns:
            Dict with 'valid' boolean and 'invalid_indices' list
        """
        statement = select(AuditLog).order_by(AuditLog.chain_index.asc())
        entries = self.session.exec(statement).all()
        
        invalid_indices = []
        expected_previous_hash = "0" * 64  # Genesis
        
        for i, entry in enumerate(entries):
            # Verify previous hash matches
            if entry.previous_hash != expected_previous_hash:
                invalid_indices.append(i)
            
            # Recompute and verify current hash
            recomputed = self._compute_hash(
                event_id=entry.event_id,
                timestamp=entry.timestamp.isoformat(),
                actor=entry.actor,
                action=entry.action.value,
                payload=entry.payload,
                previous_hash=entry.previous_hash
            )
            
            if recomputed != entry.current_hash:
                invalid_indices.append(i)
            
            expected_previous_hash = entry.current_hash
        
        return {
            "valid": len(invalid_indices) == 0,
            "total_entries": len(entries),
            "invalid_indices": invalid_indices
        }
    
    def get_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        actor: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Query audit log entries with filters."""
        statement = select(AuditLog)
        
        conditions = []
        if actor:
            conditions.append(AuditLog.actor == actor)
        if action:
            conditions.append(AuditLog.action == action)
        if start_time:
            conditions.append(AuditLog.timestamp >= start_time)
        if end_time:
            conditions.append(AuditLog.timestamp <= end_time)
        
        if conditions:
            from sqlalchemy import and_
            statement = statement.where(and_(*conditions))
        
        statement = statement.order_by(AuditLog.chain_index.desc())
        statement = statement.offset(offset).limit(limit)
        
        results = self.session.exec(statement)
        return results.all()
    
    def get_entry_by_event_id(self, event_id: str) -> Optional[AuditLog]:
        """Retrieve a specific audit entry by event ID."""
        statement = select(AuditLog).where(AuditLog.event_id == event_id)
        result = self.session.exec(statement)
        return result.first()
    
    def get_entries_by_chain_range(
        self,
        start_index: int,
        end_index: int
    ) -> List[AuditLog]:
        """Get entries within a chain index range."""
        statement = select(AuditLog).where(
            AuditLog.chain_index >= start_index,
            AuditLog.chain_index <= end_index
        ).order_by(AuditLog.chain_index.asc())
        
        results = self.session.exec(statement)
        return results.all()
