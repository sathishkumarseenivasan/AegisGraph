'use client';

import { GraphView } from '@/components/graph/GraphView';

export default function GraphPage() {
  const handleNodeSelect = (nodeId: string, nodeType: string) => {
    console.log('Selected node:', nodeId, nodeType);
    // Could open a detail panel here
  };

  return (
    <div className="h-full">
      <GraphView onNodeSelect={handleNodeSelect} />
    </div>
  );
}
