'use client';

import { Anomaly, Action } from '@/types';
import { AlertTriangle, AlertCircle, Info, CheckCircle, XCircle, Clock } from 'lucide-react';
import { formatTimestamp } from '@/lib/utils';

interface AnomalyQueueProps {
  anomalies: Anomaly[];
  onSelectAnomaly: (anomaly: Anomaly) => void;
  selectedAnomaly?: Anomaly | null;
  onApproveAction: (actionId: string) => void;
  onRejectAction: (actionId: string) => void;
}

export function AnomalyQueue({
  anomalies,
  onSelectAnomaly,
  selectedAnomaly,
  onApproveAction,
  onRejectAction,
}: AnomalyQueueProps) {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return <AlertTriangle className="w-5 h-5 text-danger" />;
      case 'HIGH':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'MEDIUM':
        return <AlertCircle className="w-4 h-4 text-warning" />;
      case 'LOW':
        return <Info className="w-4 h-4 text-info" />;
      default:
        return <Info className="w-4 h-4 text-textMuted" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-warning/20 text-warning text-xs rounded">
            <Clock className="w-3 h-3" />
            PENDING
          </span>
        );
      case 'INVESTIGATING':
        return (
          <span className="px-2 py-1 bg-info/20 text-info text-xs rounded">
            INVESTIGATING
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-success/20 text-success text-xs rounded">
            <CheckCircle className="w-3 h-3" />
            RESOLVED
          </span>
        );
      case 'FALSE_POSITIVE':
        return (
          <span className="flex items-center gap-1 px-2 py-1 bg-surfaceHighlight text-textMuted text-xs rounded">
            <XCircle className="w-3 h-3" />
            FALSE POSITIVE
          </span>
        );
      default:
        return <span className="text-xs text-textMuted">{status}</span>;
    }
  };

  const pendingAnomalies = anomalies.filter(a => a.status === 'PENDING');
  const otherAnomalies = anomalies.filter(a => a.status !== 'PENDING');

  return (
    <div className="h-full flex flex-col bg-surface border-l border-border">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-text">Anomaly Queue</h2>
        <p className="text-sm text-textMuted mt-1">
          {pendingAnomalies.length} pending, {otherAnomalies.length} resolved
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Pending Anomalies */}
        {pendingAnomalies.length > 0 && (
          <div className="p-4">
            <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-3">
              Requires Attention
            </h3>
            <div className="space-y-2">
              {pendingAnomalies.map((anomaly) => (
                <AnomalyCard
                  key={anomaly.id}
                  anomaly={anomaly}
                  isSelected={selectedAnomaly?.id === anomaly.id}
                  onClick={() => onSelectAnomaly(anomaly)}
                  onApprove={onApproveAction}
                  onReject={onRejectAction}
                />
              ))}
            </div>
          </div>
        )}

        {/* Other Anomalies */}
        {otherAnomalies.length > 0 && (
          <div className="p-4 border-t border-border">
            <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-3">
              Recent Activity
            </h3>
            <div className="space-y-2">
              {otherAnomalies.slice(0, 10).map((anomaly) => (
                <AnomalyCard
                  key={anomaly.id}
                  anomaly={anomaly}
                  isSelected={selectedAnomaly?.id === anomaly.id}
                  onClick={() => onSelectAnomaly(anomaly)}
                  onApprove={onApproveAction}
                  onReject={onRejectAction}
                />
              ))}
            </div>
          </div>
        )}

        {anomalies.length === 0 && (
          <div className="flex items-center justify-center h-48 text-textMuted">
            No anomalies detected
          </div>
        )}
      </div>
    </div>
  );
}

interface AnomalyCardProps {
  anomaly: Anomaly;
  isSelected: boolean;
  onClick: () => void;
  onApprove: (actionId: string) => void;
  onReject: (actionId: string) => void;
}

function AnomalyCard({ anomaly, isSelected, onClick, onApprove, onReject }: AnomalyCardProps) {
  return (
    <div
      className={`p-3 rounded-lg border cursor-pointer transition-all ${
        isSelected
          ? 'bg-surfaceHighlight border-primary'
          : 'bg-surface border-border hover:border-surfaceHighlight'
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2 flex-1">
          {getSeverityIcon(anomaly.severity)}
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium text-text truncate">
              {anomaly.anomaly_type.replace(/_/g, ' ')}
            </h4>
            <p className="text-xs text-textMuted mt-1 line-clamp-2">
              {anomaly.explanation}
            </p>
            <div className="flex items-center gap-2 mt-2">
              {getStatusBadge(anomaly.status)}
              <span className="text-xs text-textMuted">
                Score: {(anomaly.score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions for Pending */}
      {anomaly.status === 'PENDING' && anomaly.recommended_action && (
        <div className="mt-3 pt-3 border-t border-border flex gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              // In real app, would have action ID
              onApprove(anomaly.id);
            }}
            className="flex-1 px-3 py-1.5 bg-success/20 text-success text-xs rounded hover:bg-success/30 transition-colors"
          >
            Approve Action
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onReject(anomaly.id);
            }}
            className="flex-1 px-3 py-1.5 bg-danger/20 text-danger text-xs rounded hover:bg-danger/30 transition-colors"
          >
            Reject
          </button>
        </div>
      )}

      <div className="text-xs text-textMuted mt-2">
        {formatTimestamp(anomaly.created_at)}
      </div>
    </div>
  );
}
