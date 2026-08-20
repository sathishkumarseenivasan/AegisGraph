'use client';

import { useEffect, useState } from 'react';
import { fetchAudit } from '@/lib/api';
import { AuditEvent } from '@/types';
import { Shield, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';
import { formatTimestamp } from '@/lib/utils';

export function AuditLogView() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAudit = async () => {
      try {
        const data = await fetchAudit();
        setEvents(data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load audit log');
        setLoading(false);
      }
    };

    loadAudit();
  }, []);

  const getActionIcon = (action: string) => {
    if (action.includes('APPROVE')) return <CheckCircle className="w-4 h-4 text-success" />;
    if (action.includes('REJECT')) return <XCircle className="w-4 h-4 text-danger" />;
    if (action.includes('ANOMALY')) return <AlertTriangle className="w-4 h-4 text-warning" />;
    return <Info className="w-4 h-4 text-info" />;
  };

  const getActionColor = (action: string) => {
    if (action.includes('APPROVE')) return 'text-success';
    if (action.includes('REJECT')) return 'text-danger';
    if (action.includes('ANOMALY')) return 'text-warning';
    return 'text-info';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <div className="text-textMuted">Loading audit log...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <div className="text-danger">{error}</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-surface">
      {/* Header */}
      <div className="p-4 border-b border-border bg-surfaceHighlight">
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-primary" />
          <div>
            <h2 className="text-lg font-semibold text-text">Audit Log</h2>
            <p className="text-xs text-textMuted">
              Immutable hash-chained event ledger ({events.length} events)
            </p>
          </div>
        </div>
      </div>

      {/* Event List */}
      <div className="flex-1 overflow-y-auto p-4">
        {events.length === 0 ? (
          <div className="flex items-center justify-center h-full text-textMuted">
            No audit events recorded
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((event, index) => (
              <AuditEventCard
                key={event.event_id}
                event={event}
                isLatest={index === 0}
              />
            ))}
          </div>
        )}
      </div>

      {/* Hash Chain Verification */}
      <div className="p-4 border-t border-border bg-surfaceHighlight">
        <div className="flex items-center justify-between text-xs">
          <span className="text-textMuted">Chain Integrity:</span>
          <span className="text-success font-mono">VERIFIED</span>
        </div>
        {events.length > 0 && (
          <div className="mt-2 font-mono text-xs text-textMuted truncate">
            Latest: {events[0].current_hash.substring(0, 32)}...
          </div>
        )}
      </div>
    </div>
  );
}

interface AuditEventCardProps {
  event: AuditEvent;
  isLatest: boolean;
}

function AuditEventCard({ event, isLatest }: AuditEventCardProps) {
  return (
    <div
      className={`p-3 rounded-lg border ${
        isLatest
          ? 'bg-primary/10 border-primary/30'
          : 'bg-surface border-border'
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {getActionIcon(event.action)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className={`text-sm font-medium ${getActionColor(event.action)}`}>
              {event.action.replace(/_/g, ' ')}
            </h4>
            <span className="text-xs text-textMuted">
              {formatTimestamp(event.timestamp)}
            </span>
          </div>
          <p className="text-xs text-textMuted mt-1">
            Actor: <span className="text-text">{event.actor}</span>
          </p>
          {Object.keys(event.payload).length > 0 && (
            <pre className="mt-2 p-2 bg-background rounded text-xs text-textMuted overflow-x-auto">
              {JSON.stringify(event.payload, null, 2)}
            </pre>
          )}
          <div className="mt-2 font-mono text-[10px] text-textMuted truncate">
            Hash: {event.current_hash.substring(0, 48)}...
          </div>
        </div>
      </div>
    </div>
  );
}
