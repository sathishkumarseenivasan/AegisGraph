"""
Anomaly Detection Engine.

Detects anomalies using:
- Rule-based detection
- Simple statistical methods
- Correlation analysis

Each anomaly includes:
- anomaly_type
- severity
- score
- triggered_rules
- evidence_ids
- explanation
- recommended_action
- uncertainty
"""
import uuid
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlmodel import Session, select
from models import (
    Anomaly, AnomalyType, SeverityLevel,
    Observation, Entity, Rule, Action, ActionStatus
)


class AnomalyEngine:
    """Detects and scores anomalies from observations and entities."""
    
    def __init__(self, session: Session):
        self.session = session
        self.severity_thresholds = {
            "low": 0.3,
            "medium": 0.5,
            "high": 0.7,
            "critical": 0.85
        }
    
    def detect_all(self) -> List[Anomaly]:
        """Run all detection methods and return detected anomalies."""
        anomalies = []
        
        # Load rules
        rules_statement = select(Rule).where(Rule.enabled == True)
        rules = self.session.exec(rules_statement).all()
        rules_by_type = {r.anomaly_type.value: r for r in rules}
        
        # Run rule-based detection for each type
        detection_methods = [
            (AnomalyType.ROUTE_DEVIATION, self._detect_route_deviation),
            (AnomalyType.DARK_VESSEL, self._detect_dark_vessel),
            (AnomalyType.SENSOR_DROPOUT, self._detect_sensor_dropout),
            (AnomalyType.PORT_CONGESTION, self._detect_port_congestion),
            (AnomalyType.ABNORMAL_PROXIMITY, self._detect_abnormal_proximity),
            (AnomalyType.IDENTITY_MISMATCH, self._detect_identity_mismatch),
            (AnomalyType.UNUSUAL_LOITERING, self._detect_loitering),
            (AnomalyType.CONFLICTING_REPORTS, self._detect_conflicting_reports),
        ]
        
        for anomaly_type, method in detection_methods:
            rule = rules_by_type.get(anomaly_type.value)
            detected = method(rule)
            anomalies.extend(detected)
        
        return anomalies
    
    def _calculate_severity(self, score: float) -> SeverityLevel:
        """Convert score to severity level."""
        if score >= self.severity_thresholds["critical"]:
            return SeverityLevel.CRITICAL
        elif score >= self.severity_thresholds["high"]:
            return SeverityLevel.HIGH
        elif score >= self.severity_thresholds["medium"]:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _detect_route_deviation(self, rule: Optional[Rule]) -> List[Anomaly]:
        """Detect vessels deviating from expected routes."""
        anomalies = []
        threshold = rule.threshold if rule else 0.7
        
        vessels = self.session.exec(
            select(Entity).where(Entity.entity_type == "vessel")
        ).all()
        
        for vessel in vessels:
            if not vessel.last_seen:
                continue
            
            # Get recent observations
            time_window = datetime.utcnow() - timedelta(hours=6)
            obs_statement = select(Observation).where(
                Observation.entity_id == vessel.entity_id,
                Observation.timestamp >= time_window
            )
            observations = self.session.exec(obs_statement).all()
            
            if len(observations) < 3:
                continue
            
            # Calculate route deviation (simplified)
            # Compare actual path to straight line between first and last point
            first_obs = min(observations, key=lambda x: x.timestamp)
            last_obs = max(observations, key=lambda x: x.timestamp)
            
            # Check for significant heading changes
            headings = [obs.heading for obs in observations if obs.heading]
            if len(headings) >= 3:
                heading_changes = [abs(headings[i] - headings[i-1]) for i in range(1, len(headings))]
                avg_change = sum(heading_changes) / len(heading_changes)
                
                # Normalize to 0-1 score
                deviation_score = min(1.0, avg_change / 45)  # 45 degrees avg change = 1.0
                
                if deviation_score > threshold:
                    anomaly = self._create_anomaly(
                        anomaly_type=AnomalyType.ROUTE_DEVIATION,
                        score=deviation_score,
                        entity_id=vessel.entity_id,
                        timestamp=datetime.utcnow(),
                        explanation=f"Vessel {vessel.name} showing erratic heading changes (avg {avg_change:.1f}°)",
                        evidence_ids=[obs.observation_id for obs in observations[-5:]],
                        rule=rule
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_dark_vessel(self, rule: Optional[Rule]) -> List[Anomaly]:
        """Detect vessels with transmission gaps."""
        anomalies = []
        threshold = rule.threshold if rule else 0.8
        
        vessels = self.session.exec(
            select(Entity).where(Entity.entity_type == "vessel", Entity.is_active == True)
        ).all()
        
        for vessel in vessels:
            if not vessel.last_seen:
                continue
            
            gap = datetime.utcnow() - vessel.last_seen
            gap_hours = gap.total_seconds() / 3600
            
            # Score based on gap duration
            if gap_hours > 2:
                gap_score = min(1.0, gap_hours / 6)  # 6 hours = 1.0
                
                if gap_score > threshold:
                    anomaly = self._create_anomaly(
                        anomaly_type=AnomalyType.DARK_VESSEL,
                        score=gap_score,
                        entity_id=vessel.entity_id,
                        timestamp=vessel.last_seen,
                        explanation=f"Vessel {vessel.name} has not transmitted for {gap_hours:.1f} hours",
                        evidence_ids=[],
                        rule=rule
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_sensor_dropout(self, rule: Optional[Rule]) -> List[Anomaly]:
        """Detect sensor outages."""
        # Simplified - would need sensor heartbeat tracking
        return []
    
    def _detect_port_congestion(self, rule: Optional[Rule]) -> List[Anomaly]:
        """Detect port congestion."""
        anomalies = []
        threshold = rule.threshold if rule else 0.75
        
        ports = self.session.exec(
            select(Entity).where(Entity.entity_type == "port")
        ).all()
        
        for port in ports:
            # Count vessels near port (simplified radius check)
            vessels = self.session.exec(
                select(Entity).where(
                    Entity.entity_type == "vessel",
                    Entity.latitude >= (port.latitude or 0) - 0.5,
                    Entity.latitude <= (port.latitude or 0) + 0.5,
                    Entity.longitude >= (port.longitude or 0) - 0.5,
                    Entity.longitude <= (port.longitude or 0) + 0.5
                )
            ).all()
            
            vessel_count = len(vessels)
            if vessel_count > 5:
                congestion_score = min(1.0, vessel_count / 15)
                
                if congestion_score > threshold:
                    anomaly = self._create_anomaly(
                        anomaly_type=AnomalyType.PORT_CONGESTION,
                        score=congestion_score,
                        entity_id=port.entity_id,
                        timestamp=datetime.utcnow(),
                        explanation=f"Port {port.name} has {vessel_count} vessels in vicinity",
                        evidence_ids=[v.entity_id for v in vessels],
                        rule=rule
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_abnormal_proximity(self, rule: Optional[Rule]) -> List[Anomaly]:
        """Detect vessels too close together."""
        anomalies = []
        threshold = rule.threshold if rule else 0.9
        
        vessels = self.session.exec(
            select(Entity).where(Entity.entity_type == "vessel")
        ).all()
        
        checked_pairs = set()
        
        for i, v1 in enumerate(vessels):
            for j, v2 in enumerate(vessels):
                if i >= j:
                    continue
                
                pair_key = tuple(sorted([v1.entity_id, v2.entity_id]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                
                if v1.latitude and v2.latitude:
                    distance = self._haversine_distance(
                        v1.latitude, v1.longitude,
                        v2.latitude, v2.longitude
                    )
                    
                    # Less than 1 km is concerning
                    if distance < 1.0:
                        proximity_score = max(0, 1.0 - distance)
                        
                        if proximity_score > threshold:
                            anomaly = self._create_anomaly(
                                anomaly_type=AnomalyType.ABNORMAL_PROXIMITY,
                                score=proximity_score,
                                entity_id=v1.entity_id,
                                timestamp=datetime.utcnow(),
                                explanation=f"Vessels {v1.name} and {v2.name} within {distance:.2f}km - collision risk",
                                evidence_ids=[v1.entity_id, v2.entity_id],
                                rule=rule
                            )
                            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_identity_mismatch(self, rule: Optional[Rule]) -> List[Anomaly]:
        """Detect identity inconsistencies."""
        # Simplified - would need MMSI/IMO cross-reference
        return []
    
    def _detect_loitering(self, rule: Optional[Rule]) -> List[Anomaly]:
        """Detect unusual loitering behavior."""
        anomalies = []
        threshold = rule.threshold if rule else 0.7
        
        vessels = self.session.exec(
            select(Entity).where(Entity.entity_type == "vessel")
        ).all()
        
        for vessel in vessels:
            time_window = datetime.utcnow() - timedelta(hours=8)
            obs_statement = select(Observation).where(
                Observation.entity_id == vessel.entity_id,
                Observation.timestamp >= time_window
            )
            observations = self.session.exec(obs_statement).all()
            
            if len(observations) < 5:
                continue
            
            # Calculate position variance
            lats = [obs.latitude for obs in observations]
            lons = [obs.longitude for obs in observations]
            
            lat_variance = sum((lat - sum(lats)/len(lats))**2 for lat in lats) / len(lats)
            lon_variance = sum((lon - sum(lons)/len(lons))**2 for lon in lons) / len(lons)
            
            total_variance = math.sqrt(lat_variance + lon_variance)
            
            # Low variance indicates loitering
            if total_variance < 0.01:  # Very small movement
                loiter_score = 1.0 - (total_variance * 100)
                
                if loiter_score > threshold:
                    anomaly = self._create_anomaly(
                        anomaly_type=AnomalyType.UNUSUAL_LOITERING,
                        score=loiter_score,
                        entity_id=vessel.entity_id,
                        timestamp=datetime.utcnow(),
                        explanation=f"Vessel {vessel.name} showing minimal movement over 8 hours",
                        evidence_ids=[obs.observation_id for obs in observations[-5:]],
                        rule=rule
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_conflicting_reports(self, rule: Optional[Rule]) -> List[Anomaly]:
        """Detect conflicting position reports."""
        anomalies = []
        threshold = rule.threshold if rule else 0.8
        
        # Group observations by timestamp window
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        obs_statement = select(Observation).where(
            Observation.timestamp >= recent_time
        )
        observations = self.session.exec(obs_statement).all()
        
        # Group by entity
        by_entity = {}
        for obs in observations:
            if obs.entity_id:
                if obs.entity_id not in by_entity:
                    by_entity[obs.entity_id] = []
                by_entity[obs.entity_id].append(obs)
        
        # Check for conflicts (multiple observations with different positions)
        for entity_id, entity_obs in by_entity.items():
            if len(entity_obs) < 2:
                continue
            
            # Check position spread
            lats = [obs.latitude for obs in entity_obs]
            lons = [obs.longitude for obs in entity_obs]
            
            lat_spread = max(lats) - min(lats)
            lon_spread = max(lons) - min(lons)
            
            # Significant spread indicates conflict
            if lat_spread > 0.01 or lon_spread > 0.01:
                conflict_score = min(1.0, (lat_spread + lon_spread) * 50)
                
                if conflict_score > threshold:
                    anomaly = self._create_anomaly(
                        anomaly_type=AnomalyType.CONFLICTING_REPORTS,
                        score=conflict_score,
                        entity_id=entity_id,
                        timestamp=datetime.utcnow(),
                        explanation=f"Conflicting position reports for entity {entity_id}",
                        evidence_ids=[obs.observation_id for obs in entity_obs],
                        rule=rule
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _create_anomaly(
        self,
        anomaly_type: AnomalyType,
        score: float,
        entity_id: Optional[str],
        timestamp: datetime,
        explanation: str,
        evidence_ids: List[str],
        rule: Optional[Rule]
    ) -> Anomaly:
        """Create an anomaly record with recommended action."""
        severity = self._calculate_severity(score)
        anomaly_id = f"ANM-{uuid.uuid4().hex[:8].upper()}"
        
        # Generate recommended action
        action = self._generate_action(anomaly_type, severity, entity_id)
        if action:
            self.session.add(action)
            self.session.commit()
            self.session.refresh(action)
        
        # Calculate uncertainty
        uncertainty = 0.2 if len(evidence_ids) >= 3 else 0.4
        
        anomaly = Anomaly(
            anomaly_id=anomaly_id,
            anomaly_type=anomaly_type,
            severity=severity,
            score=score,
            triggered_rule_ids=[rule.rule_id] if rule else [],
            evidence_observation_ids=evidence_ids[:10],  # Limit to 10
            explanation=explanation,
            uncertainty=uncertainty,
            entity_id=entity_id,
            location_latitude=None,
            location_longitude=None,
            timestamp=timestamp,
            recommended_action_id=action.id if action else None,
            is_resolved=False
        )
        
        return anomaly
    
    def _generate_action(
        self,
        anomaly_type: AnomalyType,
        severity: SeverityLevel,
        entity_id: Optional[str]
    ) -> Optional[Action]:
        """Generate recommended action for anomaly."""
        action_templates = {
            AnomalyType.ROUTE_DEVIATION: {
                "type": "investigate",
                "description": "Investigate route deviation - contact vessel for status update"
            },
            AnomalyType.DARK_VESSEL: {
                "type": "alert",
                "description": "Issue alert - vessel not transmitting, dispatch reconnaissance"
            },
            AnomalyType.ABNORMAL_PROXIMITY: {
                "type": "alert",
                "description": "Collision risk alert - notify both vessels immediately"
            },
            AnomalyType.PORT_CONGESTION: {
                "type": "coordinate",
                "description": "Coordinate with port authority for traffic management"
            },
            AnomalyType.UNUSUAL_LOITERING: {
                "type": "investigate",
                "description": "Investigate loitering behavior - check for suspicious activity"
            },
            AnomalyType.CONFLICTING_REPORTS: {
                "type": "verify",
                "description": "Verify entity identity through additional sensors"
            }
        }
        
        template = action_templates.get(anomaly_type)
        if not template:
            return None
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(severity.value, 3)
        
        action = Action(
            action_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
            description=template["description"],
            action_type=template["type"],
            status=ActionStatus.PENDING,
            priority=priority,
            justification=f"Recommended due to {anomaly_type.value} anomaly (severity: {severity.value})"
        )
        
        return action
    
    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points in kilometers."""
        R = 6371
        
        import math
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
