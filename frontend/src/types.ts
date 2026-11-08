export interface SummaryResponse {
  total_support_tickets: number;
  total_finance_payouts: number;
  unique_refund_cases: number;
  in_both: number;
  support_only: number;
  finance_only: number;
  finance_only_amount: number;
  paid_in_support: number;
  gap_b_count: number;
  gap_b_amount: number;
  gap_c_count: number;
  gap_c_amount: number;
  gap_d_count: number;
  gap_d_amount: number;
  gap_e_count: number;
  total_escalations: number;
  open_escalations: number;
  resolved_escalations: number;
  canonical_agents_count: number;
  has_key?: boolean;
  id_format_audit?: Record<string, any>;
  amount_differs_count?: number;
  amount_differs_explained_by_deduction?: number;
  matched_missing_amount_count?: number;
  latent_count?: number;
  latent_amount?: number;
  addressable_escalations?: AddressableEscalations;
  approval_tier?: ApprovalTierResponse;
}

export interface LatentRecord {
  clean_id: string;
  raw_id?: string;
  canonical_agent: string;
  route: string;
  "Refund Amount (INR)": number;
  effective_age_days: number;
  proactive_draft: string;
}

export interface LatentResponse {
  count: number;
  total_amount: number;
  mean_age_days: number;
  over_30_days_count: number;
  records: LatentRecord[];
}

export interface AgentExposureItem {
  canonical_agent: string;
  stuck_tickets: number;
  stuck_amount: number;
  gap_b_count: number;
  gap_c_count: number;
  gap_d_count: number;
}

export interface AgentExposureResponse {
  total_stuck_value: number;
  total_stuck_tickets: number;
  total_agents: number;
  top5_share_pct: number;
  top5_amount: number;
  agents: AgentExposureItem[];
}

export interface AddressableEscalations {
  total_escalations: number;
  structural_failure_count: number;
  structural_breakdown: Record<string, number>;
  paid_matched_chases: number;
  in_progress_queues: number;
  addressable_total: number;
  addressable_share_pct: number;
}

export interface MonthlyRecord {
  Month: string;
  "Total Requests": number;
  "Support Closed": number;
  "Gap B (Closed, No Fin)": number;
  "Gap B Rate (%)": number;
  "Avg Finance Proc Days": number | null;
  "Median Finance Proc Days": number | null;
  "Finance Done (Received Mo)": number;
  "Approved Count": number;
  "Approval Share (%)": number | null;
}

export interface MonthlyResponse {
  records: MonthlyRecord[];
  footnote: string;
}

export interface GapRecord {
  clean_id: string;
  raw_id?: string;
  canonical_agent: string;
  route: string;
  clean_status: string;
  clean_payout_status: string;
  "Refund Amount (INR)": number;
  "Amount Paid (INR)": number;
  "Deduction (INR)": number;
  gap_class: string;
  owner_team: string;
  recommended_action: string;
  priority_score: number;
  effective_age_days: number;
  in_support?: boolean;
  in_finance?: boolean;
  deduction_explains?: boolean;
  parsed_request_date: string | null;
  parsed_received_on: string | null;
  parsed_processed_on: string | null;
}

export interface GapsFilterOptions {
  gap_classes: string[];
  agents: string[];
  teams: string[];
}

export interface GapsResponse {
  total_matching: number;
  records: GapRecord[];
  filters: GapsFilterOptions;
}

export interface EscalationRootCause {
  root_cause: string;
  count: number;
  share: number;
}

export interface EscalationRecord {
  clean_escalation_id: string;
  parsed_raised_on: string;
  clean_ticket_id: string;
  canonical_agent: string;
  Channel: string;
  Complaint: string;
  root_cause: string;
  clean_status: string;
  "Days Open": number;
}

export interface EscalationsResponse {
  total: number;
  root_causes: EscalationRootCause[];
  monthly_trend: Record<string, string | number>[];
  records: EscalationRecord[];
}

export interface LLMStatus {
  has_key: boolean;
  provider: string;
  model: string;
  status_banner: string;
}

export interface ParsedMessage {
  agent_name: string;
  canonical_agent: string;
  pnr: string;
  ticket_number: string;
  route: string;
  request_date: string;
  refund_amount: number | null;
  channel: string;
  raw_message: string;
}

export interface IntakeMatch {
  match_status: "UNIQUE_MATCH" | "AMBIGUOUS" | "NO_MATCH" | "SUPPORT_CLOSED_NO_FINANCE" | string;
  match_type?: string;
  matched_ticket: GapRecord | null;
  candidates: GapRecord[];
  action: string;
  draft_reply: string;
  new_ticket_id?: string;
  report_ref?: string;
  gap_b_count?: number;
  gap_b_sum?: number;
}

export interface IntakeResponse {
  llm_status: LLMStatus;
  parsed: ParsedMessage;
  match: IntakeMatch;
}

export interface Preset {
  name: string;
  channel: string;
  date: string;
  text: string;
}

export interface PresetsResponse {
  preset_a: Preset;
  preset_b: Preset;
  preset_c: Preset;
}

export interface TurnaroundMonth {
  month: string;
  completed_count: number;
  avg_proc_days: number;
}

export interface ApproverBreakdownMonth {
  month: string;
  "N. Iyer": number;
  "R. Menon": number;
  "S. Bhatt": number;
  total_approved: number;
  unapproved: number;
}

export interface StalledRecord {
  clean_id: string;
  canonical_agent: string;
  route: string;
  "Refund Amount (INR)": number;
  parsed_request_date: string;
  parsed_received_on: string;
  effective_age_days: number;
  priority_score: number;
}

export interface ApprovalTierResponse {
  threshold: number;
  pending_large_count: number;
  pending_large_amount: number;
  mean_wait_days: number;
  max_wait_days: number;
  monthly_turnaround: TurnaroundMonth[];
  approver_breakdown: ApproverBreakdownMonth[];
  pending_records: StalledRecord[];
  observation_note: string;
}
