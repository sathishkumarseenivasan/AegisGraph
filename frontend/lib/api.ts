const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchEntities(): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/entities`);
  if (!res.ok) throw new Error('Failed to fetch entities');
  return res.json();
}

export async function fetchEntity(id: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/entities/${id}`);
  if (!res.ok) throw new Error('Failed to fetch entity');
  return res.json();
}

export async function fetchObservations(): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/observations`);
  if (!res.ok) throw new Error('Failed to fetch observations');
  return res.json();
}

export async function fetchAnomalies(): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/anomalies`);
  if (!res.ok) throw new Error('Failed to fetch anomalies');
  return res.json();
}

export async function fetchAnomaly(id: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/anomalies/${id}`);
  if (!res.ok) throw new Error('Failed to fetch anomaly');
  return res.json();
}

export async function fetchGraph(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/graph`);
  if (!res.ok) throw new Error('Failed to fetch graph');
  return res.json();
}

export async function fetchAudit(): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/audit`);
  if (!res.ok) throw new Error('Failed to fetch audit log');
  return res.json();
}

export async function askAnalyst(question: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error('Failed to query analyst');
  return res.json();
}

export async function approveAction(id: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/actions/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error('Failed to approve action');
  return res.json();
}

export async function rejectAction(id: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/actions/${id}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error('Failed to reject action');
  return res.json();
}

export function createWebSocket(): WebSocket {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/live';
  return new WebSocket(wsUrl);
}
