import { Entity, RiskLevel } from '@/types';

interface EntityMarkerProps {
  entity: Entity;
  onClick: (entity: Entity) => void;
}

export function getEntityColor(type: string, riskLevel?: RiskLevel): string {
  if (riskLevel === 'CRITICAL') return '#ef4444';
  if (riskLevel === 'HIGH') return '#f97316';
  if (riskLevel === 'MEDIUM') return '#f59e0b';
  
  switch (type) {
    case 'VESSEL': return '#3b82f6';
    case 'AIRCRAFT': return '#8b5cf6';
    case 'GROUND': return '#10b981';
    case 'FACILITY': return '#f59e0b';
    case 'CYBER': return '#06b6d4';
    default: return '#6b7280';
  }
}

export function getRiskColor(score: number): string {
  if (score >= 0.8) return '#ef4444';
  if (score >= 0.6) return '#f97316';
  if (score >= 0.4) return '#f59e0b';
  return '#10b981';
}

export function formatTimestamp(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDistance(meters: number): string {
  if (meters > 1000) {
    return `${(meters / 1000).toFixed(1)} km`;
  }
  return `${Math.round(meters)} m`;
}

export function formatSpeed(knots: number): string {
  return `${knots.toFixed(1)} kn`;
}
