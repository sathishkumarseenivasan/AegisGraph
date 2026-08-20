"""
Synthetic Data Generator for AegisGraph.

Generates realistic multi-source synthetic data including:
- AIS-like vessel position reports
- ADS-B-like aircraft position reports
- Weather alerts
- Port congestion updates
- Cyber outage events
- Radio/log message metadata

Includes 10+ planted anomalies for detection testing.
"""
import random
import uuid
import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any
from config import settings


# ==================== CONSTANTS ====================

VESSEL_NAMES = [
    "ATLANTIC VOYAGER", "PACIFIC STAR", "NORTHERN LIGHT", "SOUTHERN CROSS",
    "EASTERN WIND", "WESTERN HORIZON", "OCEAN PIONEER", "SEA GUARDIAN",
    "WAVE RIDER", "STORM CHASER", "BLUE HORIZON", "GOLDEN EAGLE",
    "SILVER MOON", "IRON WILL", "SWIFT CURRENT", "DEEP EXPLORER",
    "COASTAL TRADER", "RIVER RUNNER", "HARBOR MASTER", "BAY SPIRIT"
]

AIRCRAFT_NAMES = [
    "SKY WARRIOR", "CLOUD DANCER", "WING COMMANDER", "AIR SENTINEL",
    "FLIGHT MASTER", "JET STREAM", "THUNDER BIRD", "STEALTH HAWK",
    "RAPID EAGLE", "SILENT PHANTOM", "NIGHT OWL", "DAY FALCON",
    "STORM PETREL", "ICE BREAKER", "FIRE BIRD", "SHADOW RUNNER"
]

PORT_NAMES = [
    "Port of New York", "Port of Los Angeles", "Port of Singapore",
    "Port of Rotterdam", "Port of Shanghai", "Port of Hamburg",
    "Port of Busan", "Port of Dubai", "Port of Tokyo", "Port of Sydney"
]

AIRPORT_CODES = [
    "KJFK", "KLAX", "KSFO", "KORD", "KDFW", "KDEN", "KSEA", "KMIA",
    "KBOS", "KLAS", "PHX", "PHNL", "PANC", "PAFA", "EGKK", "EDDF"
]

FLAG_CODES = ["US", "GB", "NO", "DK", "SG", "JP", "KR", "AU", "CA", "DE"]

OPERATORS = [
    "Global Shipping Co", "Maritime Logistics Inc", "Ocean Transport Ltd",
    "Air Cargo Express", "Regional Airlines", "Charter Flight Services",
    "Naval Operations Command", "Coast Guard Auxiliary", "Commercial Fleet Mgmt"
]


class SyntheticDataGenerator:
    """Generates synthetic multi-source data with planted anomalies."""
    
    def __init__(self, num_entities: int = None, hours: int = None):
        self.num_entities = num_entities or settings.NUM_ENTITIES
        self.hours = hours or settings.OBSERVATION_HOURS
        self.start_time = datetime.utcnow() - timedelta(hours=self.hours)
        self.end_time = datetime.utcnow()
        
        # Storage for generated data
        self.entities: List[Dict] = []
        self.sensors: List[Dict] = []
        self.observations: List[Dict] = []
        self.anomaly_scenarios: List[Dict] = []
        
        # Anomaly tracking
        self.planted_anomalies: Dict[str, Dict] = {}
        
    def generate_all(self) -> Dict[str, Any]:
        """Generate complete synthetic dataset."""
        print(f"Generating synthetic data for {self.num_entities} entities over {self.hours} hours...")
        
        # Generate base entities
        self._generate_entities()
        self._generate_sensors()
        
        # Generate observations
        self._generate_observations()
        
        # Plant anomalies
        self._plant_anomalies()
        
        # Generate additional anomaly-related observations
        self._generate_anomaly_observations()
        
        print(f"Generated {len(self.entities)} entities, {len(self.sensors)} sensors, {len(self.observations)} observations")
        print(f"Planted {len(self.planted_anomalies)} anomaly scenarios")
        
        return {
            "entities": self.entities,
            "sensors": self.sensors,
            "observations": self.observations,
            "anomaly_scenarios": list(self.planted_anomalies.values()),
            "rules": self._generate_default_rules()
        }
    
    def _generate_entities(self) -> None:
        """Generate entity records."""
        num_vessels = int(self.num_entities * 0.5)
        num_aircraft = int(self.num_entities * 0.25)
        num_facilities = self.num_entities - num_vessels - num_aircraft
        
        # Generate vessels
        for i in range(num_vessels):
            vessel_id = f"VSL-{uuid.uuid4().hex[:8].upper()}"
            mmsi = str(200000000 + i)
            name = random.choice(VESSEL_NAMES) + f" {i+1}"
            
            # Random starting position (Atlantic/Pacific regions)
            if random.random() > 0.5:
                # Atlantic
                lat = random.uniform(25, 55)
                lon = random.uniform(-80, -10)
            else:
                # Pacific
                lat = random.uniform(-30, 45)
                lon = random.uniform(120, -120)
            
            self.entities.append({
                "entity_id": vessel_id,
                "entity_type": "vessel",
                "name": name,
                "callsign": f"CALL{i:04d}",
                "mmsi": mmsi,
                "imo": f"IMO{9000000 + i}",
                "flag": random.choice(FLAG_CODES),
                "operator": random.choice(OPERATORS[:3]),
                "home_port": random.choice(PORT_NAMES),
                "latitude": lat,
                "longitude": lon,
                "speed": random.uniform(5, 25),
                "heading": random.uniform(0, 360),
                "course": random.uniform(0, 360),
                "destination": random.choice(PORT_NAMES),
                "is_active": True
            })
        
        # Generate aircraft
        for i in range(num_aircraft):
            aircraft_id = f"AIR-{uuid.uuid4().hex[:8].upper()}"
            icao = f"A{1000 + i:04X}"
            name = random.choice(AIRCRAFT_NAMES) + f" {i+1}"
            
            # Random starting position near airports
            airport_lat = random.uniform(25, 48)
            airport_lon = random.uniform(-125, -70)
            
            self.entities.append({
                "entity_id": aircraft_id,
                "entity_type": "aircraft",
                "name": name,
                "callsign": f"FLT{i:04d}",
                "icao": icao,
                "operator": random.choice(OPERATORS[3:6]),
                "latitude": airport_lat + random.uniform(-2, 2),
                "longitude": airport_lon + random.uniform(-2, 2),
                "altitude": random.uniform(20000, 40000),
                "speed": random.uniform(400, 550),
                "heading": random.uniform(0, 360),
                "course": random.uniform(0, 360),
                "destination": random.choice(AIRPORT_CODES),
                "is_active": True
            })
        
        # Generate facilities (ports, airports)
        for i, port in enumerate(PORT_NAMES[:num_facilities//2]):
            facility_id = f"PRT-{uuid.uuid4().hex[:6].upper()}"
            self.entities.append({
                "entity_id": facility_id,
                "entity_type": "port",
                "name": port,
                "latitude": random.uniform(25, 55),
                "longitude": random.uniform(-125, -70),
                "is_active": True
            })
        
        for i, airport in enumerate(AIRPORT_CODES[:num_facilities - num_facilities//2]):
            facility_id = f"APT-{uuid.uuid4().hex[:6].upper()}"
            self.entities.append({
                "entity_id": facility_id,
                "entity_type": "airport",
                "name": airport,
                "latitude": random.uniform(25, 48),
                "longitude": random.uniform(-125, -70),
                "is_active": True
            })
    
    def _generate_sensors(self) -> None:
        """Generate sensor records."""
        # AIS receivers
        for i in range(10):
            self.sensors.append({
                "sensor_id": f"AIS-RX-{i:03d}",
                "sensor_type": "ais",
                "name": f"AIS Receiver Station {i+1}",
                "location_name": random.choice(["Coastal Tower", "Offshore Platform", "Port Authority"]),
                "latitude": random.uniform(25, 55),
                "longitude": random.uniform(-125, -70),
                "coverage_radius_km": random.uniform(50, 200),
                "is_operational": True
            })
        
        # ADS-B receivers
        for i in range(8):
            self.sensors.append({
                "sensor_id": f"ADSB-RX-{i:03d}",
                "sensor_type": "adsb",
                "name": f"ADS-B Ground Station {i+1}",
                "location_name": f"Airport Zone {i+1}",
                "latitude": random.uniform(25, 48),
                "longitude": random.uniform(-125, -70),
                "coverage_radius_km": random.uniform(100, 300),
                "is_operational": True
            })
        
        # Weather stations
        for i in range(5):
            self.sensors.append({
                "sensor_id": f"WX-STN-{i:03d}",
                "sensor_type": "weather",
                "name": f"Weather Station {i+1}",
                "location_name": f"Meteorological Site {i+1}",
                "latitude": random.uniform(25, 55),
                "longitude": random.uniform(-125, -70),
                "is_operational": True
            })
        
        # Cyber nodes
        for i in range(5):
            self.sensors.append({
                "sensor_id": f"CYBER-NODE-{i:03d}",
                "sensor_type": "cyber",
                "name": f"Network Monitoring Node {i+1}",
                "location_name": f"Data Center {i+1}",
                "is_operational": True
            })
    
    def _generate_observations(self) -> None:
        """Generate observation time series for all entities."""
        obs_per_entity = (settings.OBSERVATIONS_PER_HOUR * self.hours) // self.num_entities
        
        for entity in self.entities:
            entity_id = entity["entity_id"]
            entity_type = entity["entity_type"]
            
            current_lat = entity["latitude"]
            current_lon = entity["longitude"]
            current_heading = entity.get("heading", 0)
            speed = entity.get("speed", 15)
            
            # Determine source type based on entity type
            if entity_type == "vessel":
                source_type = "ais"
                sensor_prefix = "AIS-RX"
            elif entity_type == "aircraft":
                source_type = "adsb"
                sensor_prefix = "ADSB-RX"
            else:
                continue  # Facilities don't move
            
            for j in range(obs_per_entity):
                # Time progression
                time_offset = timedelta(minutes=j * (self.hours * 60) / obs_per_entity)
                timestamp = self.start_time + time_offset
                
                # Update position with some randomness
                current_heading += random.uniform(-5, 5)
                distance_traveled = (speed * 0.01)  # Simplified distance per interval
                
                # Update position
                current_lat += (distance_traveled * math.cos(math.radians(current_heading))) * 0.01
                current_lon += (distance_traveled * math.sin(math.radians(current_heading))) * 0.01
                
                # Add some noise
                lat_noise = random.uniform(-0.001, 0.001)
                lon_noise = random.uniform(-0.001, 0.001)
                
                obs_id = f"OBS-{uuid.uuid4().hex[:12].upper()}"
                sensor_id = f"{sensor_prefix}-{random.randint(0, 9):03d}"
                
                observation = {
                    "observation_id": obs_id,
                    "source_type": source_type,
                    "entity_id": entity_id,
                    "sensor_id": sensor_id,
                    "timestamp": timestamp.isoformat(),
                    "latitude": current_lat + lat_noise,
                    "longitude": current_lon + lon_noise,
                    "altitude": entity.get("altitude") if entity_type == "aircraft" else None,
                    "speed": speed + random.uniform(-2, 2),
                    "heading": current_heading % 360,
                    "course": current_heading % 360,
                    "signal_strength": random.uniform(-90, -40),
                    "accuracy": random.uniform(5, 50),
                    "confidence": random.uniform(0.85, 1.0),
                    "raw_data": {
                        "original_format": source_type.upper(),
                        "message_type": random.choice(["Position Report", "Status Update", "Navigation Update"]),
                        "sequence_number": j
                    }
                }
                
                self.observations.append(observation)
    
    def _plant_anomalies(self) -> None:
        """Plant specific anomaly scenarios in the data."""
        
        # 1. Route Deviation - vessel significantly off planned route
        vessel_entities = [e for e in self.entities if e["entity_type"] == "vessel"]
        if vessel_entities:
            deviating_vessel = random.choice(vessel_entities)
            self.planted_anomalies["route_deviation"] = {
                "anomaly_type": "route_deviation",
                "entity_id": deviating_vessel["entity_id"],
                "description": f"Vessel {deviating_vessel['name']} deviated >50nm from planned route",
                "severity": "high",
                "timestamp": (self.start_time + timedelta(hours=12)).isoformat(),
                "evidence_count": 5
            }
        
        # 2. Dark Vessel - vessel stops transmitting
        if len(vessel_entities) > 1:
            dark_vessel = random.choice([v for v in vessel_entities if v != deviating_vessel])
            self.planted_anomalies["dark_vessel"] = {
                "anomaly_type": "dark_vessel",
                "entity_id": dark_vessel["entity_id"],
                "description": f"Vessel {dark_vessel['name']} stopped transmitting AIS signals",
                "severity": "critical",
                "timestamp": (self.start_time + timedelta(hours=8)).isoformat(),
                "gap_duration_hours": 6
            }
        
        # 3. Sensor Dropout - sensor stops reporting
        ais_sensors = [s for s in self.sensors if s["sensor_type"] == "ais"]
        if ais_sensors:
            dropout_sensor = random.choice(ais_sensors)
            self.planted_anomalies["sensor_dropout"] = {
                "anomaly_type": "sensor_dropout",
                "sensor_id": dropout_sensor["sensor_id"],
                "description": f"Sensor {dropout_sensor['name']} experienced 4-hour outage",
                "severity": "medium",
                "timestamp": (self.start_time + timedelta(hours=16)).isoformat(),
                "affected_entities": 8
            }
        
        # 4. Port Congestion
        port_entities = [e for e in self.entities if e["entity_type"] == "port"]
        if port_entities:
            congested_port = random.choice(port_entities)
            self.planted_anomalies["port_congestion"] = {
                "anomaly_type": "port_congestion",
                "entity_id": congested_port["entity_id"],
                "description": f"Port {congested_port['name']} experiencing severe congestion",
                "severity": "medium",
                "timestamp": (self.start_time + timedelta(hours=20)).isoformat(),
                "vessel_count": 15
            }
        
        # 5. Cyber Outage correlated with physical anomaly
        cyber_sensors = [s for s in self.sensors if s["sensor_type"] == "cyber"]
        if cyber_sensors and vessel_entities:
            cyber_node = random.choice(cyber_sensors)
            affected_vessel = random.choice(vessel_entities)
            self.planted_anomalies["cyber_outage"] = {
                "anomaly_type": "cyber_outage",
                "sensor_id": cyber_node["sensor_id"],
                "entity_id": affected_vessel["entity_id"],
                "description": f"Cyber outage at {cyber_node['name']} correlated with unusual vessel behavior",
                "severity": "high",
                "timestamp": (self.start_time + timedelta(hours=10)).isoformat(),
                "correlation_confidence": 0.78
            }
        
        # 6. Conflicting Reports
        if len(vessel_entities) > 2:
            conflict_vessels = random.sample(vessel_entities, 2)
            self.planted_anomalies["conflicting_reports"] = {
                "anomaly_type": "conflicting_reports",
                "entity_ids": [v["entity_id"] for v in conflict_vessels],
                "description": f"Conflicting position reports for vessels in same location",
                "severity": "high",
                "timestamp": (self.start_time + timedelta(hours=14)).isoformat(),
                "discrepancy_km": 0.5
            }
        
        # 7. Abnormal Proximity
        if len(vessel_entities) > 2:
            proximity_vessels = random.sample(vessel_entities, 2)
            self.planted_anomalies["abnormal_proximity"] = {
                "anomaly_type": "abnormal_proximity",
                "entity_ids": [v["entity_id"] for v in proximity_vessels],
                "description": f"Two vessels within 0.3nm - potential collision risk",
                "severity": "critical",
                "timestamp": (self.start_time + timedelta(hours=18)).isoformat(),
                "separation_nm": 0.28
            }
        
        # 8. Delayed Feed
        self.planted_anomalies["delayed_feed"] = {
            "anomaly_type": "delayed_feed",
            "sensor_id": "AIS-RX-005",
            "description": "Data feed delayed by 45 minutes",
            "severity": "low",
            "timestamp": (self.start_time + timedelta(hours=6)).isoformat(),
            "delay_minutes": 45
        }
        
        # 9. Identity Mismatch
        if vessel_entities:
            mismatch_vessel = random.choice(vessel_entities)
            self.planted_anomalies["identity_mismatch"] = {
                "anomaly_type": "identity_mismatch",
                "entity_id": mismatch_vessel["entity_id"],
                "description": f"Vessel transmitting inconsistent MMSI/IMO identifiers",
                "severity": "high",
                "timestamp": (self.start_time + timedelta(hours=22)).isoformat(),
                "conflicting_ids": ["MMSI:123456789", "MMSI:987654321"]
            }
        
        # 10. Unusual Loitering
        if vessel_entities:
            loitering_vessel = random.choice([v for v in vessel_entities if v != mismatch_vessel])
            self.planted_anomalies["unusual_loitering"] = {
                "anomaly_type": "unusual_loitering",
                "entity_id": loitering_vessel["entity_id"],
                "description": f"Vessel {loitering_vessel['name']} loitering in restricted area for 8+ hours",
                "severity": "medium",
                "timestamp": (self.start_time + timedelta(hours=4)).isoformat(),
                "duration_hours": 8,
                "area_description": "Sensitive maritime zone"
            }
    
    def _generate_anomaly_observations(self) -> None:
        """Generate additional observations that support anomaly detection."""
        # Add specific observations for planted anomalies
        for anomaly_type, anomaly_data in self.planted_anomalies.items():
            if anomaly_type == "route_deviation":
                # Add observations showing deviation
                entity_id = anomaly_data.get("entity_id")
                if entity_id:
                    for i in range(5):
                        self.observations.append({
                            "observation_id": f"OBS-DEV-{uuid.uuid4().hex[:8].upper()}",
                            "source_type": "ais",
                            "entity_id": entity_id,
                            "sensor_id": "AIS-RX-001",
                            "timestamp": anomaly_data["timestamp"],
                            "latitude": random.uniform(40, 50),
                            "longitude": random.uniform(-60, -40),
                            "speed": 22,
                            "heading": random.uniform(0, 360),
                            "confidence": 0.95,
                            "raw_data": {"deviation_flag": True}
                        })
            
            elif anomaly_type == "dark_vessel":
                # Gap in observations is implicit - no additional obs needed
                pass
            
            elif anomaly_type == "abnormal_proximity":
                entity_ids = anomaly_data.get("entity_ids", [])
                if len(entity_ids) >= 2:
                    shared_lat = random.uniform(35, 45)
                    shared_lon = random.uniform(-75, -60)
                    for eid in entity_ids[:2]:
                        self.observations.append({
                            "observation_id": f"OBS-PROX-{uuid.uuid4().hex[:8].upper()}",
                            "source_type": "ais",
                            "entity_id": eid,
                            "sensor_id": "AIS-RX-002",
                            "timestamp": anomaly_data["timestamp"],
                            "latitude": shared_lat + random.uniform(-0.01, 0.01),
                            "longitude": shared_lon + random.uniform(-0.01, 0.01),
                            "speed": 8,
                            "heading": random.uniform(0, 360),
                            "confidence": 0.98,
                            "raw_data": {"proximity_alert": True}
                        })
    
    def _generate_default_rules(self) -> List[Dict]:
        """Generate default detection rules."""
        rules = [
            {
                "rule_id": "RULE-001",
                "name": "Route Deviation Detection",
                "description": "Detect vessels deviating more than threshold from planned route",
                "anomaly_type": "route_deviation",
                "category": "behavioral",
                "parameters": {"max_deviation_nm": 50},
                "threshold": 0.7,
                "enabled": True
            },
            {
                "rule_id": "RULE-002",
                "name": "Dark Vessel Detection",
                "description": "Detect vessels with transmission gaps exceeding threshold",
                "anomaly_type": "dark_vessel",
                "category": "technical",
                "parameters": {"max_gap_hours": 4},
                "threshold": 0.8,
                "enabled": True
            },
            {
                "rule_id": "RULE-003",
                "name": "Sensor Health Monitor",
                "description": "Detect sensor outages and degradations",
                "anomaly_type": "sensor_dropout",
                "category": "technical",
                "parameters": {"heartbeat_interval_minutes": 5},
                "threshold": 0.6,
                "enabled": True
            },
            {
                "rule_id": "RULE-004",
                "name": "Port Capacity Monitor",
                "description": "Detect port congestion based on vessel count",
                "anomaly_type": "port_congestion",
                "category": "operational",
                "parameters": {"max_vessels": 10},
                "threshold": 0.75,
                "enabled": True
            },
            {
                "rule_id": "RULE-005",
                "name": "Cyber-Physical Correlation",
                "description": "Detect correlation between cyber events and physical anomalies",
                "anomaly_type": "cyber_outage",
                "category": "correlation",
                "parameters": {"time_window_hours": 2},
                "threshold": 0.7,
                "enabled": True
            },
            {
                "rule_id": "RULE-006",
                "name": "Report Consistency Check",
                "description": "Detect conflicting reports from multiple sources",
                "anomaly_type": "conflicting_reports",
                "category": "data_quality",
                "parameters": {"max_position_diff_km": 1},
                "threshold": 0.8,
                "enabled": True
            },
            {
                "rule_id": "RULE-007",
                "name": "Collision Risk Assessment",
                "description": "Detect abnormally close proximity between vessels",
                "anomaly_type": "abnormal_proximity",
                "category": "safety",
                "parameters": {"min_separation_nm": 0.5},
                "threshold": 0.9,
                "enabled": True
            },
            {
                "rule_id": "RULE-008",
                "name": "Feed Latency Monitor",
                "description": "Detect delayed data feeds",
                "anomaly_type": "delayed_feed",
                "category": "technical",
                "parameters": {"max_latency_minutes": 30},
                "threshold": 0.5,
                "enabled": True
            },
            {
                "rule_id": "RULE-009",
                "name": "Identity Verification",
                "description": "Detect identity mismatches in vessel records",
                "anomaly_type": "identity_mismatch",
                "category": "data_quality",
                "parameters": {"check_mmsi": True, "check_imo": True},
                "threshold": 0.85,
                "enabled": True
            },
            {
                "rule_id": "RULE-010",
                "name": "Loitering Detection",
                "description": "Detect unusual loitering behavior",
                "anomaly_type": "unusual_loitering",
                "category": "behavioral",
                "parameters": {"max_stationary_hours": 6, "radius_nm": 5},
                "threshold": 0.7,
                "enabled": True
            }
        ]
        return rules


def main():
    """Main entry point for standalone execution."""
    generator = SyntheticDataGenerator()
    data = generator.generate_all()
    
    print("\n=== Summary ===")
    print(f"Entities: {len(data['entities'])}")
    print(f"Sensors: {len(data['sensors'])}")
    print(f"Observations: {len(data['observations'])}")
    print(f"Rules: {len(data['rules'])}")
    print(f"Anomaly Scenarios: {len(data['anomaly_scenarios'])}")
    
    return data


if __name__ == "__main__":
    main()
