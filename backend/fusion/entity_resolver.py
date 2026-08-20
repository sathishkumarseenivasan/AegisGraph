"""
Entity Resolution Module.

Resolves observations into unified entities using:
- Exact ID matching
- Fuzzy name matching
- Geo-temporal association
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlmodel import Session, select
from models import Entity, Observation, EntityType


class EntityResolver:
    """Resolves observations to entities and creates unified tracks."""
    
    def __init__(self, session: Session):
        self.session = session
        self.confidence_threshold = 0.7
    
    def resolve_observation(self, observation: Observation) -> Tuple[Optional[Entity], float]:
        """
        Attempt to resolve an observation to an existing entity.
        
        Returns:
            Tuple of (matched_entity, confidence_score)
        """
        # 1. Try exact ID matching first
        if observation.entity_id:
            entity = self._exact_id_match(observation.entity_id)
            if entity:
                return entity, 1.0
        
        # 2. Try fuzzy name matching (if callsign or identifier in raw_data)
        callsign = observation.raw_data.get("callsign")
        if callsign:
            entity, confidence = self._fuzzy_name_match(callsign)
            if entity and confidence >= self.confidence_threshold:
                return entity, confidence
        
        # 3. Try geo-temporal association
        entity, confidence = self._geo_temporal_match(
            observation.timestamp,
            observation.latitude,
            observation.longitude,
            observation.source_type.value
        )
        if entity and confidence >= self.confidence_threshold:
            return entity, confidence
        
        return None, 0.0
    
    def _exact_id_match(self, entity_id: str) -> Optional[Entity]:
        """Match by exact entity ID."""
        statement = select(Entity).where(Entity.entity_id == entity_id)
        result = self.session.exec(statement)
        return result.first()
    
    def _fuzzy_name_match(self, name: str) -> Tuple[Optional[Entity], float]:
        """Match by fuzzy name comparison."""
        # Simple Levenshtein-like matching (simplified for MVP)
        statement = select(Entity)
        entities = self.session.exec(statement).all()
        
        best_match = None
        best_score = 0.0
        
        for entity in entities:
            score = self._string_similarity(name.upper(), entity.name.upper())
            if score > best_score:
                best_score = score
                best_match = entity
        
        return best_match, best_score
    
    def _geo_temporal_match(
        self,
        timestamp: datetime,
        latitude: float,
        longitude: float,
        source_type: str
    ) -> Tuple[Optional[Entity], float]:
        """Match based on geographic and temporal proximity."""
        # Find entities of appropriate type within time window
        if source_type == "ais":
            entity_type = EntityType.VESSEL
        elif source_type == "adsb":
            entity_type = EntityType.AIRCRAFT
        else:
            return None, 0.0
        
        statement = select(Entity).where(Entity.entity_type == entity_type)
        entities = self.session.exec(statement).all()
        
        best_match = None
        best_score = 0.0
        
        for entity in entities:
            if not entity.is_active:
                continue
            
            # Check if entity has recent position
            if entity.last_seen:
                time_diff = abs((timestamp - entity.last_seen).total_seconds())
                if time_diff > 3600:  # More than 1 hour old
                    continue
                
                # Calculate distance (simplified Euclidean for MVP)
                distance = self._haversine_distance(
                    latitude, longitude,
                    entity.latitude or 0,
                    entity.longitude or 0
                )
                
                # Score based on distance (closer = higher score)
                if distance < 50:  # Within 50 km
                    distance_score = max(0, 1.0 - (distance / 50))
                    
                    # Combine with time recency
                    time_score = max(0, 1.0 - (time_diff / 3600))
                    
                    combined_score = (distance_score * 0.7 + time_score * 0.3)
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_match = entity
        
        return best_match, best_score
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity ratio (simplified)."""
        if s1 == s2:
            return 1.0
        
        # Check if one contains the other
        if s1 in s2 or s2 in s1:
            return 0.8
        
        # Count common characters
        common = sum(1 for c in s1 if c in s2)
        return common / max(len(s1), len(s2)) if s1 or s2 else 0.0
    
    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points in kilometers."""
        import math
        
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def create_or_update_entity(
        self,
        observation: Observation,
        confidence: float
    ) -> Entity:
        """Create new entity or update existing based on observation."""
        existing, match_confidence = self.resolve_observation(observation)
        
        if existing:
            # Update existing entity
            existing.latitude = observation.latitude
            existing.longitude = observation.longitude
            existing.altitude = observation.altitude
            existing.speed = observation.speed
            existing.heading = observation.heading
            existing.course = observation.course
            existing.last_seen = observation.timestamp
            existing.updated_at = datetime.utcnow()
            
            # Update risk score based on confidence
            if confidence < 0.8:
                existing.risk_score = min(1.0, existing.risk_score + 0.1)
            
            self.session.add(existing)
            return existing
        else:
            # Create new entity
            entity_id = f"ENT-{uuid.uuid4().hex[:8].upper()}"
            
            entity = Entity(
                entity_id=entity_id,
                entity_type=EntityType.VESSEL if observation.source_type.value == "ais" else EntityType.AIRCRAFT,
                name=f"Unknown {observation.source_type.value.upper()} {len(self.session.exec(select(Entity)).all()) + 1}",
                latitude=observation.latitude,
                longitude=observation.longitude,
                altitude=observation.altitude,
                speed=observation.speed,
                heading=observation.heading,
                course=observation.course,
                last_seen=observation.timestamp,
                is_active=True,
                risk_score=0.0 if confidence > 0.9 else 0.3
            )
            
            self.session.add(entity)
            return entity
    
    def resolve_batch(self, observations: List[Observation]) -> Dict[str, List[Entity]]:
        """Resolve a batch of observations."""
        results = {"matched": [], "unmatched": [], "created": []}
        
        for obs in observations:
            entity, confidence = self.resolve_observation(obs)
            
            if entity:
                results["matched"].append((obs, entity, confidence))
            else:
                results["unmatched"].append(obs)
        
        return results
