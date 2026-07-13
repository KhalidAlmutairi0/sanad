export type Role = "reviewer" | "sharia_board" | "admin" | "service";
export type Severity = "critical" | "high" | "medium" | "low";
export type ReviewStatus = "pending" | "accepted" | "rejected";
export type ContractStatus =
  | "uploaded"
  | "sanitizing"
  | "sanitized"
  | "extracting"
  | "reviewing"
  | "reviewed"
  | "failed";

export interface UserPublic {
  id: string;
  display_name: string;
  role: Role;
}

export interface Citation {
  regulation_version_id: string;
  regulation_code: string;
  article_ref: string;
  article_text_ar: string;
  source_url: string;
  effective_date: string | null;
  verification_tier: "human_verified" | "official_fetch";
}

export interface Finding {
  id: string;
  clause_id: string | null;
  title_ar: string;
  title_en: string | null;
  explanation_ar: string | null;
  explanation_en: string | null;
  severity: Severity;
  category: "regulatory" | "sharia";
  violation_cost_ar: string | null;
  violation_cost_min: number | null;
  violation_cost_max: number | null;
  review_status: ReviewStatus;
  citation: Citation;
}

export interface Clause {
  id: string;
  ordinal: number;
  text_ar: string | null;
  text_en: string | null;
}

export interface FindingsSummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  pending: number;
}

export interface ContractListItem {
  id: string;
  title: string;
  status: ContractStatus;
  readiness_score: number | null;
  created_at: string;
}

export interface ContractDetail {
  id: string;
  title: string;
  status: ContractStatus;
  readiness_score: number | null;
  findings_summary: FindingsSummary;
}

export interface ApiError {
  error: { code: string; message_ar: string; message_en: string };
}

export interface SourceCitation {
  regulation_version_id: string;
  regulation_code: string;
  article_ref: string;
  source_url: string;
}

export interface Obligation {
  id: string;
  title_ar: string;
  title_en: string | null;
  owner_id: string | null;
  due_date: string | null;
  status: "open" | "in_progress" | "met" | "overdue";
  citation: SourceCitation;
}

export interface MonitoringEvent {
  id: string;
  regulation_code: string;
  change_type: string | null;
  detected_at: string;
  impact_summary_ar: string | null;
  status: "detected" | "verified" | "notified";
  new_version_id: string | null;
}

export interface EvidenceSearchItem {
  regulation_version_id: string;
  regulation_code: string;
  article_ref: string;
  snippet_ar: string;
  score: number;
}

export interface Invite {
  code: string;
  role: Role;
  email: string | null;
  used: boolean;
  created_at: string;
}

export interface Prompts {
  contracts_guidance: string;
  idea_guidance: string;
  contracts_contract: string | null;
  idea_contract: string | null;
}

export interface AuditItem {
  actor: string;
  action: string;
  target: string | null;
  verdict: string | null;
  detail_json: Record<string, unknown> | null;
  at: string;
}
