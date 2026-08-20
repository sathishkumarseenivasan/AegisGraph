#!/usr/bin/env python3
"""
AegisGraph Demo Seed Script

Generates deterministic synthetic data:
- 100 entities (vessels, aircraft, weather stations, ports, cyber nodes, radio)
- ~15,000 observations over 24 hours
- 12 planted anomalies with known characteristics

Usage:
    python scripts/seed_demo.py [--seed 42] [--output db/aegisgraph.db]
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlmodel import SQLModel, create_engine, Session
from database import DATABASE_URL
from synthetic.synthetic_data_generator import SyntheticDataGenerator
from ingestion.data_ingester import DataIngester
from governance.audit import AuditLogger


def seed_database(seed: int = 42, db_path: str = None):
    """Generate and ingest synthetic data."""
    
    # Use provided path or default
    if db_path is None:
        db_path = DATABASE_URL.replace("sqlite:///", "./")
    
    print(f"🌱 Seeding AegisGraph database...")
    print(f"   Seed: {seed}")
    print(f"   Database: {db_path}")
    
    # Create engine and tables
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(engine)
    
    # Initialize audit logger (creates genesis event)
    with Session(engine) as session:
        audit = AuditLogger(session)
        audit.log(actor="system", action="SEED_INIT", payload={"seed": seed})
        session.commit()
    
    # Generate synthetic data
    print("\n📊 Generating synthetic data...")
    generator = SyntheticDataGenerator(
        num_entities=100,
        hours=24,
        seed=seed
    )
    data = generator.generate_all()
    
    print(f"   Entities: {len(data['entities'])}")
    print(f"   Observations: {len(data['observations'])}")
    print(f"   Anomalies: {len(data['anomalies'])}")
    
    # Ingest data
    print("\n📥 Ingesting data...")
    with Session(engine) as session:
        ingester = DataIngester(session)
        ingester.ingest_all(data)
        
        # Log completion
        audit = AuditLogger(session)
        audit.log(
            actor="system",
            action="SEED_COMPLETE",
            payload={
                "entities": len(data['entities']),
                "observations": len(data['observations']),
                "anomalies": len(data['anomalies'])
            }
        )
        session.commit()
    
    print("\n✅ Database seeded successfully!")
    print("\nNext steps:")
    print("   1. Start backend: make run-api")
    print("   2. Start frontend: make run-web")
    print("   3. Open http://localhost:3000")
    print("   4. Run evaluation: make eval")
    
    return {
        "entities": len(data['entities']),
        "observations": len(data['observations']),
        "anomalies": len(data['anomalies'])
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed AegisGraph demo database")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default=None, help="Output database path")
    args = parser.parse_args()
    
    try:
        stats = seed_database(seed=args.seed, db_path=args.output)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        sys.exit(1)
