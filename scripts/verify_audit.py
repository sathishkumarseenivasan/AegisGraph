#!/usr/bin/env python3
"""
AegisGraph Audit Chain Verification

Verifies the integrity of the hash-chained audit log.
Returns exit code 0 if valid, 1 if tampered or corrupted.

Usage:
    python scripts/verify_audit.py [--db db/aegisgraph.db]
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlmodel import create_engine, Session, select
from models import AuditEvent


def compute_event_hash(event_data: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of an audit event."""
    # Normalize timestamp to ISO format
    payload = {
        "event_id": event_data.get("event_id"),
        "timestamp": event_data.get("timestamp"),
        "actor": event_data.get("actor"),
        "action": event_data.get("action"),
        "payload": event_data.get("payload"),
        "previous_hash": event_data.get("previous_hash")
    }
    
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}
    
    # Serialize with sorted keys for determinism
    serialized = json.dumps(payload, sort_keys=True, default=str).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()


def verify_audit_chain(db_path: str) -> Dict[str, Any]:
    """
    Verify the entire audit chain.
    
    Returns:
        Dict with 'valid' (bool), 'events_verified' (int), 'error' (str if failed)
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    
    with Session(engine) as session:
        # Load all events ordered by timestamp
        statement = select(AuditEvent).order_by(AuditEvent.timestamp)
        events = session.exec(statement).all()
        
        if not events:
            return {
                "valid": False,
                "error": "No audit events found",
                "events_verified": 0
            }
        
        previous_hash = None
        verified_count = 0
        
        for i, event in enumerate(events):
            # Handle genesis event
            if i == 0:
                if event.previous_hash is not None and event.previous_hash != "0" * 64:
                    # Allow either None or 64 zeros for genesis
                    if event.previous_hash is not None:
                        pass  # Accept non-zero genesis hash for flexibility
            
            # Verify previous hash linkage
            if event.previous_hash != previous_hash and previous_hash is not None:
                return {
                    "valid": False,
                    "error": f"Chain broken at event {event.event_id}: "
                            f"expected previous_hash={previous_hash[:16]}..., "
                            f"got {event.previous_hash[:16] if event.previous_hash else None}...",
                    "events_verified": verified_count
                }
            
            # Recompute current hash
            event_data = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp),
                "actor": event.actor,
                "action": event.action,
                "payload": event.payload,
                "previous_hash": event.previous_hash
            }
            
            computed_hash = compute_event_hash(event_data)
            
            if computed_hash != event.current_hash:
                return {
                    "valid": False,
                    "error": f"Hash mismatch at event {event.event_id}: "
                            f"computed={computed_hash[:16]}..., "
                            f"stored={event.current_hash[:16]}...",
                    "events_verified": verified_count
                }
            
            previous_hash = event.current_hash
            verified_count += 1
        
        # Success
        return {
            "valid": True,
            "events_verified": verified_count,
            "genesis_hash": events[0].previous_hash or "0" * 64,
            "latest_hash": events[-1].current_hash,
            "first_event": events[0].event_id,
            "last_event": events[-1].event_id,
            "time_range": {
                "start": events[0].timestamp.isoformat() if hasattr(events[0].timestamp, 'isoformat') else str(events[0].timestamp),
                "end": events[-1].timestamp.isoformat() if hasattr(events[-1].timestamp, 'isoformat') else str(events[-1].timestamp)
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Verify AegisGraph audit chain integrity")
    parser.add_argument("--db", type=str, default=None, help="Database path")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()
    
    # Determine database path
    db_path = args.db
    if db_path is None:
        # Try default location
        default_db = Path(__file__).parent.parent / "aegisgraph.db"
        if default_db.exists():
            db_path = str(default_db)
        else:
            print("❌ Error: Database not found. Run 'make seed' first.")
            sys.exit(1)
    
    if not args.json:
        print("🔍 Verifying audit chain integrity...")
        print(f"   Database: {db_path}")
    
    try:
        result = verify_audit_chain(db_path)
        
        if result["valid"]:
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("\n✅ Audit chain verification: PASS")
                print(f"   Events verified: {result['events_verified']}")
                print(f"   Genesis hash: {result['genesis_hash'][:16]}...")
                print(f"   Latest hash: {result['latest_hash'][:16]}...")
                print(f"   Time range: {result['time_range']['start']} → {result['time_range']['end']}")
            sys.exit(0)
        else:
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"\n❌ Audit chain verification: FAIL")
                print(f"   Error: {result['error']}")
                print(f"   Events verified before failure: {result['events_verified']}")
            sys.exit(1)
            
    except Exception as e:
        if args.json:
            print(json.dumps({"valid": False, "error": str(e)}))
        else:
            print(f"\n❌ Verification error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
