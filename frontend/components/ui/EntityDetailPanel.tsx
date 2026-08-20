'use client';

import { Entity } from '@/types';
import { formatTimestamp, formatDistance, formatSpeed } from '@/lib/utils';
import { X } from 'lucide-react';

interface EntityDetailPanelProps {
  entity: Entity | null;
  onClose: () => void;
}

export function EntityDetailPanel({ entity, onClose }: EntityDetailPanelProps) {
  if (!entity) return null;

  return (
    <div className="absolute top-4 right-4 bottom-4 w-96 bg-surface border border-border rounded-lg shadow-2xl overflow-hidden z-20">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-surfaceHighlight">
        <h2 className="text-lg font-semibold text-text">{entity.name}</h2>
        <button
          onClick={onClose}
          className="p-1 hover:bg-background rounded transition-colors"
        >
          <X className="w-5 h-5 text-textMuted" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 overflow-y-auto h-[calc(100%-80px)] space-y-4">
        {/* Basic Info */}
        <div>
          <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
            Basic Information
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-textMuted">Type</span>
              <span className="text-text">{entity.type}</span>
            </div>
            {entity.external_id && (
              <div className="flex justify-between">
                <span className="text-textMuted">External ID</span>
                <span className="text-text font-mono text-xs">{entity.external_id}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-textMuted">Status</span>
              <span className={`px-2 py-0.5 rounded text-xs ${
                entity.status === 'ACTIVE' ? 'bg-success/20 text-success' :
                entity.status === 'SUSPECTED' ? 'bg-warning/20 text-warning' :
                entity.status === 'INACTIVE' ? 'bg-surfaceHighlight text-textMuted' :
                'bg-info/20 text-info'
              }`}>
                {entity.status || 'UNKNOWN'}
              </span>
            </div>
          </div>
        </div>

        {/* Location */}
        <div>
          <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
            Location
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-textMuted">Latitude</span>
              <span className="text-text font-mono">{entity.latitude.toFixed(4)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-textMuted">Longitude</span>
              <span className="text-text font-mono">{entity.longitude.toFixed(4)}</span>
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div>
          <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
            Timeline
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-textMuted">Created</span>
              <span className="text-text">{formatTimestamp(entity.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-textMuted">Last Seen</span>
              <span className="text-text">{formatTimestamp(entity.last_seen)}</span>
            </div>
          </div>
        </div>

        {/* Confidence */}
        <div>
          <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
            Confidence
          </h3>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-surfaceHighlight rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  entity.confidence_score >= 0.8 ? 'bg-success' :
                  entity.confidence_score >= 0.6 ? 'bg-warning' :
                  'bg-danger'
                }`}
                style={{ width: `${entity.confidence_score * 100}%` }}
              />
            </div>
            <span className="text-sm text-text">{(entity.confidence_score * 100).toFixed(0)}%</span>
          </div>
        </div>

        {/* Risk Level */}
        {entity.risk_level && (
          <div>
            <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
              Risk Assessment
            </h3>
            <span className={`inline-block px-3 py-1.5 rounded text-sm font-medium ${
              entity.risk_level === 'CRITICAL' ? 'bg-danger text-white' :
              entity.risk_level === 'HIGH' ? 'bg-orange-500 text-white' :
              entity.risk_level === 'MEDIUM' ? 'bg-warning text-black' :
              'bg-success text-white'
            }`}>
              {entity.risk_level} RISK
            </span>
          </div>
        )}

        {/* Actions */}
        <div className="pt-4 border-t border-border">
          <button className="w-full px-4 py-2 bg-primary hover:bg-primaryHover text-white rounded transition-colors text-sm font-medium">
            View Full History
          </button>
        </div>
      </div>
    </div>
  );
}
