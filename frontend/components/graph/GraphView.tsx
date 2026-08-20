'use client';

import { useEffect, useState } from 'react';
import cytoscape from 'cytoscape';
import { fetchGraph } from '@/lib/api';
import { GraphNode, GraphEdge } from '@/types';

interface GraphViewProps {
  onNodeSelect: (nodeId: string, nodeType: string) => void;
}

export function GraphView({ onNodeSelect }: GraphViewProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cy: any;

    const loadGraph = async () => {
      try {
        const data = await fetchGraph();
        
        cy = cytoscape({
          container: document.getElementById('graph-container'),
          elements: {
            nodes: data.nodes || [],
            edges: data.edges || [],
          },
          style: [
            {
              selector: 'node',
              style: {
                'background-color': (ele: any) => getNodeColor(ele.data().type),
                'label': 'data(label)',
                'color': '#e5e7eb',
                'font-size': '12px',
                'text-valign': 'bottom',
                'text-halign': 'center',
                'width': 40,
                'height': 40,
                'border-width': 2,
                'border-color': '#ffffff',
              },
            },
            {
              selector: 'edge',
              style: {
                'line-color': '#2a2a3a',
                'width': 2,
                'target-arrow-color': '#2a2a3a',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'label': 'data(label)',
                'font-size': '9px',
                'color': '#9ca3af',
                'text-rotation': 'autorotate',
              },
            },
            {
              selector: 'node[risk_level = "CRITICAL"]',
              style: {
                'background-color': '#ef4444',
                'width': 50,
                'height': 50,
                'border-width': 3,
              },
            },
            {
              selector: 'node[risk_level = "HIGH"]',
              style: {
                'background-color': '#f97316',
                'width': 45,
                'height': 45,
              },
            },
            {
              selector: 'node[type = "ENTITY"]',
              style: {
                'shape': 'ellipse',
              },
            },
            {
              selector: 'node[type = "ANOMALY"]',
              style: {
                'shape': 'diamond',
              },
            },
            {
              selector: 'node[type = "SENSOR"]',
              style: {
                'shape': 'rectangle',
              },
            },
            {
              selector: 'node:selected',
              style: {
                'border-width': 4,
                'border-color': '#3b82f6',
              },
            },
          ],
          layout: {
            name: 'cose',
            animate: true,
            animationDuration: 1000,
            nodeRepulsion: 4500,
            idealEdgeLength: 100,
          },
          wheelSensitivity: 0.3,
        });

        cy.on('tap', 'node', (evt: any) => {
          const node = evt.target;
          onNodeSelect(node.id(), node.data().type);
        });

        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load graph');
        setLoading(false);
      }
    };

    loadGraph();

    return () => {
      if (cy) {
        cy.destroy();
      }
    };
  }, [onNodeSelect]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <div className="text-textMuted">Loading graph...</div>
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
    <div className="h-full w-full bg-surface">
      <div id="graph-container" className="w-full h-full" />
      <div className="absolute top-4 right-4 bg-surface/90 backdrop-blur border border-border rounded-lg p-3 shadow-xl">
        <h3 className="text-sm font-semibold text-text mb-2">Legend</h3>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-textMuted">Entity</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-textMuted">Anomaly</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-textMuted">Sensor</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500" />
            <span className="text-textMuted">Event</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function getNodeColor(type: string): string {
  switch (type) {
    case 'ENTITY':
      return '#3b82f6';
    case 'ANOMALY':
      return '#ef4444';
    case 'SENSOR':
      return '#10b981';
    case 'EVENT':
      return '#8b5cf6';
    case 'ACTION':
      return '#f59e0b';
    case 'RULE':
      return '#06b6d4';
    default:
      return '#6b7280';
  }
}
