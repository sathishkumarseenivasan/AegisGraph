export interface Entity {
  id: string;
  name: string;
  type: EntityType;
  external_id?: string | null;
  latitude: number;
  longitude: number;
  created_at: string;
  last_seen: string;
  confidence_score: number;
  status?: EntityStatus;
  risk_level?: RiskLevel;
}

export type EntityType = 'VESSEL' | 'AIRCRAFT' | 'GROUND' | 'FACILITY' | 'CYBER';
export type EntityStatus = 'ACTIVE' | 'INACTIVE' | 'SUSPECTED' | 'UNKNOWN';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Observation {
  id: string;
  entity_id: string;
  source_type: SourceType;
  timestamp: string;
  latitude: number;
  longitude: number;
  altitude?: number | null;
  speed?: number | null;
  heading?: number | null;
  raw_data?: Record<string, any>;
}

export type SourceType = 'AIS' | 'ADS_B' | 'RADAR' | 'WEATHER' | 'CYBER' | 'MANUAL';

export interface Anomaly {
  id: string;
  anomaly_type: AnomalyType;
  severity: Severity;
  score: number;
  description: string;
  explanation: string;
  triggered_rules: string[];
  evidence_ids: string[];
  entity_ids: string[];
  recommended_action?: string;
  status: AnomalyStatus;
  created_at: string;
  uncertainty: number;
}

export type AnomalyType = 
  | 'ROUTE_DEVIATION'
  | 'DARK_VESSEL'
  | 'SENSOR_DROPOUT'
  | 'PORT_CONGESTION'
  | 'CYBER_OUTAGE'
  | 'CONFLICTING_REPORTS'
  | 'ABNORMAL_PROXIMITY'
  | 'DELAYED_FEED'
  | 'IDENTITY_MISMATCH'
  | 'UNUSUAL_LOITERING'
  | 'SPEED_ANOMALY'
  | 'TRAJECTORY_ANOMALY';

export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AnomalyStatus = 'PENDING' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE';

export interface Action {
  id: string;
  anomaly_id: string;
  action_type: ActionType;
  description: string;
  status: ActionStatus;
  created_at: string;
  decided_at?: string | null;
  decided_by?: string | null;
}

export type ActionType = 'INVESTIGATE' | 'ALERT' | 'TRACK' | 'IGNORE' | 'ESCALATE';
export type ActionStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  actor: string;
  action: string;
  payload: Record<string, any>;
  previous_hash: string;
  current_hash: string;
}

export interface GraphNode {
  data: {
    id: string;
    label: string;
    type: string;
    risk_level?: RiskLevel;
  };
}

export interface GraphEdge {
  data: {
    source: string;
    target: string;
    label?: string;
    type: string;
  };
}

export interface AnalystResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  limitations: string[];
}

export interface Citation {
  id: string;
  type: string;
  summary: string;
  reference: string;
}

export interface LiveUpdate {
  type: 'ENTITY_UPDATE' | 'ANOMALY_DETECTED' | 'ACTION_TAKEN' | 'AUDIT_EVENT';
  data: any;
  timestamp: string;
}
