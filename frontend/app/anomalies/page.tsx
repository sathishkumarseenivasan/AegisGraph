'use client';

import { useState, useEffect } from 'react';
import { AnomalyQueue } from '@/components/anomalies/AnomalyQueue';
import { fetchAnomalies, approveAction, rejectAction } from '@/lib/api';
import { Anomaly } from '@/types';
import { Filter } from 'lucide-react';

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  useEffect(() => {
    const loadAnomalies = async () => {
      try {
        const data = await fetchAnomalies();
        setAnomalies(data);
      } catch (err) {
        console.error('Failed to load anomalies:', err);
      } finally {
        setLoading(false);
      }
    };

    loadAnomalies();
  }, []);

  const handleApproveAction = async (actionId: string) => {
    try {
      await approveAction(actionId);
      setAnomalies(prev =>
        prev.map(a =>
          a.id === actionId
            ? { ...a, status: 'RESOLVED' as const }
            : a
        )
      );
    } catch (err) {
      console.error('Failed to approve action:', err);
    }
  };

  const handleRejectAction = async (actionId: string) => {
    try {
      await rejectAction(actionId);
      setAnomalies(prev =>
        prev.map(a =>
          a.id === actionId
            ? { ...a, status: 'FALSE_POSITIVE' as const }
            : a
        )
      );
    } catch (err) {
      console.error('Failed to reject action:', err);
    }
  };

  const filteredAnomalies = severityFilter === 'ALL'
    ? anomalies
    : anomalies.filter(a => a.severity === severityFilter);

  return (
    <div className="h-full flex">
      {/* Main Content - Anomaly List */}
      <div className="flex-1 flex flex-col bg-surface">
        {/* Header */}
        <div className="p-4 border-b border-border bg-surfaceHighlight">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-text">Anomaly Management</h1>
              <p className="text-sm text-textMuted mt-1">
                Review and respond to detected anomalies
              </p>
            </div>
            
            {/* Severity Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-textMuted" />
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="px-3 py-1.5 bg-background border border-border rounded text-sm text-text focus:outline-none focus:border-primary"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-4 gap-4 p-4 border-b border-border">
          <div className="p-3 bg-background rounded-lg border border-border">
            <div className="text-2xl font-bold text-text">{anomalies.length}</div>
            <div className="text-xs text-textMuted">Total</div>
          </div>
          <div className="p-3 bg-background rounded-lg border border-border">
            <div className="text-2xl font-bold text-warning">
              {anomalies.filter(a => a.status === 'PENDING').length}
            </div>
            <div className="text-xs text-textMuted">Pending</div>
          </div>
          <div className="p-3 bg-background rounded-lg border border-border">
            <div className="text-2xl font-bold text-success">
              {anomalies.filter(a => a.status === 'RESOLVED').length}
            </div>
            <div className="text-xs text-textMuted">Resolved</div>
          </div>
          <div className="p-3 bg-background rounded-lg border border-border">
            <div className="text-2xl font-bold text-danger">
              {anomalies.filter(a => a.severity === 'CRITICAL').length}
            </div>
            <div className="text-xs text-textMuted">Critical</div>
          </div>
        </div>

        {/* Anomaly Table */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-full text-textMuted">
              Loading anomalies...
            </div>
          ) : filteredAnomalies.length === 0 ? (
            <div className="flex items-center justify-center h-full text-textMuted">
              No anomalies match the selected filter
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-surface z-10">
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-textMuted font-medium">Severity</th>
                    <th className="text-left py-3 px-4 text-textMuted font-medium">Type</th>
                    <th className="text-left py-3 px-4 text-textMuted font-medium">Description</th>
                    <th className="text-left py-3 px-4 text-textMuted font-medium">Score</th>
                    <th className="text-left py-3 px-4 text-textMuted font-medium">Status</th>
                    <th className="text-left py-3 px-4 text-textMuted font-medium">Created</th>
                    <th className="text-left py-3 px-4 text-textMuted font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAnomalies.map((anomaly) => (
                    <tr
                      key={anomaly.id}
                      className="border-b border-border hover:bg-surfaceHighlight cursor-pointer"
                      onClick={() => setSelectedAnomaly(anomaly)}
                    >
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs ${
                          anomaly.severity === 'CRITICAL' ? 'bg-danger text-white' :
                          anomaly.severity === 'HIGH' ? 'bg-orange-500 text-white' :
                          anomaly.severity === 'MEDIUM' ? 'bg-warning text-black' :
                          'bg-info text-white'
                        }`}>
                          {anomaly.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-text">
                        {anomaly.anomaly_type.replace(/_/g, ' ')}
                      </td>
                      <td className="py-3 px-4 text-textMuted max-w-md truncate">
                        {anomaly.explanation}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-surfaceHighlight rounded-full w-16">
                            <div
                              className={`h-full rounded-full ${
                                anomaly.score >= 0.8 ? 'bg-danger' :
                                anomaly.score >= 0.6 ? 'bg-warning' :
                                'bg-info'
                              }`}
                              style={{ width: `${anomaly.score * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-textMuted">
                            {(anomaly.score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs ${
                          anomaly.status === 'PENDING' ? 'bg-warning/20 text-warning' :
                          anomaly.status === 'RESOLVED' ? 'bg-success/20 text-success' :
                          'bg-surfaceHighlight text-textMuted'
                        }`}>
                          {anomaly.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-textMuted">
                        {new Date(anomaly.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4">
                        {anomaly.status === 'PENDING' && anomaly.recommended_action && (
                          <div className="flex gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleApproveAction(anomaly.id);
                              }}
                              className="px-2 py-1 bg-success/20 text-success text-xs rounded hover:bg-success/30"
                            >
                              Approve
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRejectAction(anomaly.id);
                              }}
                              className="px-2 py-1 bg-danger/20 text-danger text-xs rounded hover:bg-danger/30"
                            >
                              Reject
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      {selectedAnomaly && (
        <div className="w-96 flex-shrink-0 border-l border-border bg-surface">
          <AnomalyDetailPanel
            anomaly={selectedAnomaly}
            onClose={() => setSelectedAnomaly(null)}
            onApprove={() => handleApproveAction(selectedAnomaly.id)}
            onReject={() => handleRejectAction(selectedAnomaly.id)}
          />
        </div>
      )}
    </div>
  );
}

interface AnomalyDetailPanelProps {
  anomaly: Anomaly;
  onClose: () => void;
  onApprove: () => void;
  onReject: () => void;
}

function AnomalyDetailPanel({ anomaly, onClose, onApprove, onReject }: AnomalyDetailPanelProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border bg-surfaceHighlight">
        <h2 className="text-lg font-semibold text-text">
          {anomaly.anomaly_type.replace(/_/g, ' ')}
        </h2>
        <button onClick={onClose} className="text-textMuted hover:text-text text-sm mt-1">
          Close
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div>
          <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
            Explanation
          </h3>
          <p className="text-sm text-text">{anomaly.explanation}</p>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
            Triggered Rules
          </h3>
          <div className="space-y-1">
            {anomaly.triggered_rules.map((rule, index) => (
              <div key={index} className="text-xs text-text bg-surfaceHighlight px-2 py-1 rounded">
                {rule}
              </div>
            ))}
          </div>
        </div>

        {anomaly.recommended_action && (
          <div>
            <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
              Recommended Action
            </h3>
            <p className="text-sm text-text">{anomaly.recommended_action}</p>
          </div>
        )}

        <div>
          <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
            Evidence IDs
          </h3>
          <div className="font-mono text-xs text-textMuted">
            {anomaly.evidence_ids.join(', ')}
          </div>
        </div>

        {anomaly.status === 'PENDING' && anomaly.recommended_action && (
          <div className="pt-4 border-t border-border flex gap-2">
            <button
              onClick={onApprove}
              className="flex-1 px-4 py-2 bg-success/20 text-success rounded hover:bg-success/30 transition-colors"
            >
              Approve Action
            </button>
            <button
              onClick={onReject}
              className="flex-1 px-4 py-2 bg-danger/20 text-danger rounded hover:bg-danger/30 transition-colors"
            >
              Reject
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
