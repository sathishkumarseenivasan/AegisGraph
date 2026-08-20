'use client';

import { useEffect, useState, useCallback } from 'react';
import Map, { Marker, Popup } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Entity, Anomaly } from '@/types';
import { fetchEntities, fetchAnomalies, createWebSocket } from '@/lib/api';
import { getEntityColor } from '@/lib/utils';
import { EntityDetailPanel } from '@/components/ui/EntityDetailPanel';
import { AnomalyMarker } from '@/components/map/AnomalyMarker';

interface MapViewProps {
  onEntitySelect: (entity: Entity) => void;
  selectedEntity?: Entity | null;
}

export function MapView({ onEntitySelect, selectedEntity }: MapViewProps) {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Center on a strategic region (e.g., Strait of Hormuz area for demo)
  const [viewState, setViewState] = useState({
    longitude: 56.5,
    latitude: 26.5,
    zoom: 6,
  });

  const loadData = useCallback(async () => {
    try {
      const [entitiesData, anomaliesData] = await Promise.all([
        fetchEntities(),
        fetchAnomalies(),
      ]);
      setEntities(entitiesData);
      setAnomalies(anomaliesData);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    // Set up WebSocket for live updates
    const ws = createWebSocket();
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        if (update.type === 'ENTITY_UPDATE') {
          setEntities(prev => {
            const index = prev.findIndex(e => e.id === update.data.id);
            if (index >= 0) {
              const updated = [...prev];
              updated[index] = update.data;
              return updated;
            }
            return [...prev, update.data];
          });
        } else if (update.type === 'ANOMALY_DETECTED') {
          setAnomalies(prev => [...prev, update.data]);
        }
      } catch (err) {
        console.error('Error processing WebSocket message:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    // Poll for updates every 5 seconds as fallback
    const interval = setInterval(loadData, 5000);

    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <div className="text-textMuted">Loading map data...</div>
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
    <div className="relative h-full w-full">
      <Map
        {...viewState}
        onMove={evt => setViewState(evt.viewState)}
        style={{ width: '100%', height: '100%' }}
        mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
        attributionControl={false}
      >
        {/* Entity Markers */}
        {entities.map((entity) => (
          <Marker
            key={entity.id}
            longitude={entity.longitude}
            latitude={entity.latitude}
            anchor="center"
          >
            <button
              onClick={() => onEntitySelect(entity)}
              className={`w-4 h-4 rounded-full border-2 border-white shadow-lg transition-transform hover:scale-125 ${
                selectedEntity?.id === entity.id ? 'scale-125 z-10' : ''
              }`}
              style={{ backgroundColor: getEntityColor(entity.type, entity.risk_level) }}
              title={`${entity.name} (${entity.type})`}
            />
          </Marker>
        ))}

        {/* Anomaly Markers */}
        {anomalies
          .filter(a => a.status === 'PENDING')
          .map((anomaly) => {
            // Get first associated entity location
            const entityId = anomaly.entity_ids[0];
            const entity = entities.find(e => e.id === entityId);
            if (!entity) return null;

            return (
              <AnomalyMarker
                key={anomaly.id}
                anomaly={anomaly}
                longitude={entity.longitude}
                latitude={entity.latitude}
              />
            );
          })}

        {/* Entity Popup */}
        {selectedEntity && (
          <Popup
            longitude={selectedEntity.longitude}
            latitude={selectedEntity.latitude}
            anchor="bottom"
            offset={25}
            onClose={() => onEntitySelect(null as any)}
            closeButton={true}
          >
            <div className="p-2 min-w-[200px]">
              <h3 className="font-semibold text-text">{selectedEntity.name}</h3>
              <p className="text-sm text-textMuted">{selectedEntity.type}</p>
              {selectedEntity.external_id && (
                <p className="text-xs text-textMuted mt-1">ID: {selectedEntity.external_id}</p>
              )}
              <p className="text-xs text-textMuted mt-1">
                Last seen: {new Date(selectedEntity.last_seen).toLocaleString()}
              </p>
              {selectedEntity.risk_level && (
                <span className={`inline-block mt-2 px-2 py-1 text-xs rounded ${
                  selectedEntity.risk_level === 'CRITICAL' ? 'bg-danger' :
                  selectedEntity.risk_level === 'HIGH' ? 'bg-orange-500' :
                  selectedEntity.risk_level === 'MEDIUM' ? 'bg-warning' :
                  'bg-success'
                } text-white`}>
                  {selectedEntity.risk_level} RISK
                </span>
              )}
            </div>
          </Popup>
        )}
      </Map>

      {/* Stats Overlay */}
      <div className="absolute top-4 left-4 bg-surface/90 backdrop-blur border border-border rounded-lg p-3 shadow-xl">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-textMuted">Entities</div>
            <div className="text-xl font-bold text-text">{entities.length}</div>
          </div>
          <div>
            <div className="text-textMuted">Active Anomalies</div>
            <div className="text-xl font-bold text-danger">
              {anomalies.filter(a => a.status === 'PENDING').length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
