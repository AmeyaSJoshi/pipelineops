// Canonical pipeline stages
export type PipelineStage =
  | "new_lead"
  | "applied"
  | "recruiter_screen"
  | "qualified"
  | "submitted_to_client"
  | "client_review"
  | "interview_scheduled"
  | "interview_completed"
  | "offer"
  | "placed"
  | "rejected"
  | "withdrawn"
  | "unknown";

export type AnomalySeverity = "low" | "medium" | "high";
export type AnomalyStatus = "open" | "approved" | "ignored" | "resolved";
export type SourceStatus = "connected" | "demo" | "needs_credentials" | "error" | "disabled";
export type JobStatus = "pending" | "running" | "completed" | "failed";
export type PayUnit = "hourly" | "salary" | "contract" | "unknown";
export type RemoteType = "onsite" | "hybrid" | "remote" | "unknown";

export interface HealthResponse {
  status: string;
  service: string;
  agentbox_ready: boolean;
  gmi_maas_configured: boolean;
  message: string;
  database: string;
  version: string;
}

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  task: string;
  progress: number;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourceAccount {
  id: number;
  source_type: string;
  display_name: string;
  status: SourceStatus;
  records_total: number;
  last_sync_at: string | null;
}

export interface JobRole {
  id: number;
  title: string;
  normalized_title: string;
  company_name: string;
  location_city: string | null;
  location_state: string | null;
  remote_type: RemoteType;
  pay_min: number | null;
  pay_max: number | null;
  pay_unit: PayUnit;
  pay_display: string | null;
  openings_count: number;
  status: string;
  recruiter_owner: string | null;
  applicant_count: number;
  submitted_count: number;
  interview_count: number;
  offer_count: number;
  placement_count: number;
  updated_at: string;
}

export interface Candidate {
  id: number;
  full_name: string;
  email_masked: string | null;
  phone_masked: string | null;
  location: string | null;
  current_title: string | null;
  application_count: number;
  current_stage: PipelineStage | null;
}

export interface Anomaly {
  id: number;
  severity: AnomalySeverity;
  category: string;
  title: string;
  explanation: string;
  recommended_fix: string;
  related_entity_type: string | null;
  related_entity_id: number | null;
  status: AnomalyStatus;
  created_at: string;
}

export interface MergeSuggestion {
  candidate_a: {
    id: number;
    full_name: string;
    email_masked: string | null;
    phone_masked: string | null;
    location: string | null;
    current_title: string | null;
  };
  candidate_b: {
    id: number;
    full_name: string;
    email_masked: string | null;
    phone_masked: string | null;
    location: string | null;
    current_title: string | null;
  };
  confidence: number;
  reason: string;
  recommended_action: string;
}

export interface Metrics {
  open_roles: number;
  active_candidates: number;
  total_applications: number;
  applicants_per_role: number;
  submitted_to_client_count: number;
  interview_count: number;
  offer_count: number;
  placement_count: number;
  submit_rate: number;
  interview_rate: number;
  offer_rate: number;
  placement_rate: number;
  overall_hit_rate: number;
  stale_role_count: number;
  missing_pay_rate_count: number;
  anomaly_count: number;
  roles_by_client: Record<string, number>;
  candidates_by_stage: Record<string, number>;
}

export interface ReportSummary {
  generated_at: string;
  metrics: Metrics;
  narrative_summary: string;
  anomaly_count: number;
  top_anomalies: Anomaly[];
  pipeline_data: JobRole[];
  recommended_actions: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  response: string;
  mode: "gmi_maas" | "demo_fallback";
  sources_used: string[];
}

export interface GMISettings {
  gmi_maas_configured: boolean;
  gmi_model: string | null;
  agentbox_ready: boolean;
  fallback_mode: boolean;
}

export interface ExportResult {
  format: string;
  message: string;
  preview?: {
    tabs: Array<{
      name: string;
      headers: string[];
      rows: unknown[][];
    }>;
  };
  sheet_url?: string;
}
