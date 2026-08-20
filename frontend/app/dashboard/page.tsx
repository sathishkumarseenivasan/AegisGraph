'use client';

import { useState } from 'react';
import { MapView } from '@/components/map/MapView';
import { AnomalyQueue } from '@/components/anomalies/AnomalyQueue';
import { EntityDetailPanel } from '@/components/ui/EntityDetailPanel';
import { Entity, Anomaly } from '@/types';
import { approveAction, rejectAction } from '@/lib/api';

export default function DashboardPage() {
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

  const handleApproveAction = async (actionId: string) => {
    try {
      await approveAction(actionId);
      // Update local state
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
      // Update local state
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

  return (
    <div className="flex h-full">
      {/* Map View */}
      <div className="flex-1 relative">
        <MapView
          onEntitySelect={setSelectedEntity}
          selectedEntity={selectedEntity}
        />
      </div>

      {/* Anomaly Queue Sidebar */}
      <div className="w-96 flex-shrink-0 border-l border-border">
        <AnomalyQueue
          anomalies={anomalies}
          onSelectAnomaly={setSelectedAnomaly}
          selectedAnomaly={selectedAnomaly}
          onApproveAction={handleApproveAction}
          onRejectAction={handleRejectAction}
        />
      </div>

      {/* Entity Detail Panel */}
      {selectedEntity && (
        <EntityDetailPanel
          entity={selectedEntity}
          onClose={() => setSelectedEntity(null)}
        />
      )}
    </div>
  );
}
