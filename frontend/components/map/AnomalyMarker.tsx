'use client';

import { Anomaly } from '@/types';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';

interface AnomalyMarkerProps {
  anomaly: Anomaly;
  latitude: number;
  longitude: number;
}

export function AnomalyMarker({ anomaly, latitude, longitude }: AnomalyMarkerProps) {
  const getSeverityIcon = () => {
    switch (anomaly.severity) {
      case 'CRITICAL':
        return <AlertTriangle className="w-6 h-6 text-danger" />;
      case 'HIGH':
        return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'MEDIUM':
        return <AlertCircle className="w-4 h-4 text-warning" />;
      case 'LOW':
        return <Info className="w-3 h-3 text-info" />;
      default:
        return <Info className="w-3 h-3 text-textMuted" />;
    }
  };

  const getSeverityColor = () => {
    switch (anomaly.severity) {
      case 'CRITICAL':
        return 'bg-danger/20 border-danger';
      case 'HIGH':
        return 'bg-orange-500/20 border-orange-500';
      case 'MEDIUM':
        return 'bg-warning/20 border-warning';
      case 'LOW':
        return 'bg-info/20 border-info';
      default:
        return 'bg-surfaceHighlight/20 border-border';
    }
  };

  return (
    <div
      className={`relative flex items-center justify-center w-8 h-8 rounded-full border-2 ${getSeverityColor()} animate-pulse cursor-pointer hover:animate-none transition-all`}
      title={`${anomaly.anomaly_type} - ${anomaly.severity}`}
    >
      {getSeverityIcon()}
      <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-surface rounded-full border border-border" />
    </div>
  );
}
