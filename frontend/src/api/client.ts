import {
  SummaryResponse,
  MonthlyResponse,
  GapsResponse,
  EscalationsResponse,
  IntakeResponse,
  PresetsResponse,
  LatentResponse,
  AgentExposureResponse,
  ApprovalTierResponse,
} from '../types';

const API_BASE = '/api';

export async function fetchSummary(): Promise<SummaryResponse> {
  const res = await fetch(`${API_BASE}/summary`);
  if (!res.ok) throw new Error(`Failed to fetch summary: ${res.statusText}`);
  return res.json();
}

export async function fetchMonthly(): Promise<MonthlyResponse> {
  const res = await fetch(`${API_BASE}/monthly`);
  if (!res.ok) throw new Error(`Failed to fetch monthly metrics: ${res.statusText}`);
  return res.json();
}

export async function fetchGaps(params?: {
  gap_class?: string;
  agent?: string;
  team?: string;
  limit?: number;
}): Promise<GapsResponse> {
  const query = new URLSearchParams();
  if (params?.gap_class && params.gap_class !== 'All') {
    query.set('gap_class', params.gap_class);
  }
  if (params?.agent && params.agent !== 'All') {
    query.set('agent', params.agent);
  }
  if (params?.team && params.team !== 'All') {
    query.set('team', params.team);
  }
  if (params?.limit) {
    query.set('limit', params.limit.toString());
  }

  const res = await fetch(`${API_BASE}/gaps?${query.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch action queue: ${res.statusText}`);
  return res.json();
}

export async function fetchEscalations(): Promise<EscalationsResponse> {
  const res = await fetch(`${API_BASE}/escalations`);
  if (!res.ok) throw new Error(`Failed to fetch escalations: ${res.statusText}`);
  return res.json();
}

export async function fetchPresets(): Promise<PresetsResponse> {
  const res = await fetch(`${API_BASE}/presets`);
  if (!res.ok) throw new Error(`Failed to fetch presets: ${res.statusText}`);
  return res.json();
}

export async function submitIntake(payload: {
  message: string;
  channel?: string;
  date?: string;
}): Promise<IntakeResponse> {
  const res = await fetch(`${API_BASE}/intake`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to process intake: ${res.statusText}`);
  return res.json();
}

export async function fetchLatent(): Promise<LatentResponse> {
  const res = await fetch(`${API_BASE}/latent`);
  if (!res.ok) throw new Error(`Failed to fetch latent tickets: ${res.statusText}`);
  return res.json();
}

export async function fetchAgentExposure(): Promise<AgentExposureResponse> {
  const res = await fetch(`${API_BASE}/agents/exposure`);
  if (!res.ok) throw new Error(`Failed to fetch agent exposure: ${res.statusText}`);
  return res.json();
}

export async function fetchApprovalTier(): Promise<ApprovalTierResponse> {
  const res = await fetch(`${API_BASE}/approvals/tier`);
  if (!res.ok) throw new Error(`Failed to fetch approval tier metrics: ${res.statusText}`);
  return res.json();
}

export function getLedgerDownloadUrl(): string {
  return `${API_BASE}/ledger.xlsx`;
}
