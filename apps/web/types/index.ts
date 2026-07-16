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
  confidence_tier: "high" | "low" | "uncertain";
  review_status: ReviewStatus;
  citation: Citation;
}

export interface Clause {
  id: string;
  ordinal: number;
  text_ar: string | null;
  text_en: string | null;
  retrieval_insufficient: boolean;
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
  ocr_used?: boolean;
  low_ocr_confidence?: boolean;
}

export interface CorpusItem {
  code: string;
  name_ar: string;
  authority: string;
  articles: number;
  official_fetch: number;
  human_verified: number;
  last_reconciled_at: string | null;
  days_since_reconciled: number | null;
  stale: boolean;
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
  status: "open" | "in_progress" | "met" | "overdue" | "pending_reverification";
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

export interface ApplicabilityArticleRef {
  regulation_version_id: string;
  regulation_code: string;
  article_ref: string;
  source_url: string;
}

export interface ApplicabilityFinding {
  flag: "NEEDS_REMEDIATION" | "ALREADY_COMPLIANT" | "MUST_COMPLY" | "NOT_APPLICABLE" | "EXEMPT_GRANDFATHERED";
  due_date: string | null;
  source_article: ApplicabilityArticleRef;
  classification_citation: ApplicabilityArticleRef | null;
  clause: { clause_id: string; ordinal: number; text_ar: string | null } | null;
}

export interface ContractApplicability {
  contract_id: string;
  signed_date: string | null;
  needs_remediation: ApplicabilityFinding[];
  grandfathered: ApplicabilityFinding[];
  compliant: ApplicabilityFinding[];
  pending_review: number;
}

export interface MonitoringDiff {
  id: string;
  regulation_code: string;
  article_ref: string;
  change_type: string;
  live_text: string;
  source_url: string;
  status: string;
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
