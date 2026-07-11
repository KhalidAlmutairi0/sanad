// Demo/screens-only mode. When DEMO_MODE=1 (or NEXT_PUBLIC_DEMO=1) the UI renders realistic
// sample data instead of calling the backend — no DB, no sandboxes, no LLM. For showing the
// screens only; nothing here is a real compliance result.
import type {
  AuditItem,
  Clause,
  ContractDetail,
  ContractListItem,
  EvidenceSearchItem,
  Finding,
  MonitoringEvent,
  Obligation,
} from "@/types";

export function isDemo(): boolean {
  return process.env.DEMO_MODE === "1" || process.env.NEXT_PUBLIC_DEMO === "1";
}

export const DEMO_CONTRACTS: ContractListItem[] = [
  {
    id: "demo-1",
    title: "اتفاقية معالجة بيانات مع مزود سحابي",
    status: "reviewing",
    readiness_score: 60,
    created_at: "2026-07-01T09:00:00Z",
  },
  {
    id: "demo-2",
    title: "عقد عمل دوام كامل",
    status: "reviewed",
    readiness_score: 82,
    created_at: "2026-06-24T13:30:00Z",
  },
];

const CITE_PDPL_29 = {
  regulation_version_id: "rv-pdpl-29",
  regulation_code: "PDPL",
  article_ref: "Article 29",
  article_text_ar:
    "يجوز لجهة التحكم نقل البيانات الشخصية إلى جهة خارج المملكة أو الإفصاح عنها لجهة خارجها في الحالات ووفق الضوابط التي تحددها اللوائح، بما لا يخل بأمن المملكة ومصالحها الحيوية، وبعد التحقق من توافر مستوى ملائم من الحماية للبيانات لا يقل عن المستوى المقرر في هذا النظام.",
  source_url:
    "https://sdaia.gov.sa/en/SDAIA/about/Documents/Personal%20Data%20English%20V2-23April2023-Reviewed-.pdf",
  effective_date: "2023-09-14",
};

const CITE_LABOR_98 = {
  regulation_version_id: "rv-labor-98",
  regulation_code: "LABOR",
  article_ref: "Article 98",
  article_text_ar:
    "لا يجوز تشغيل العامل تشغيلاً فعلياً أكثر من ثماني ساعات في اليوم الواحد إذا اعتمد صاحب العمل المعيار اليومي، أو أكثر من ثمان وأربعين ساعة في الأسبوع إذا اعتمد المعيار الأسبوعي.",
  source_url: "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/b7cfae89-828e-4994-b167-a9a700f2ec1d/1",
  effective_date: "2005-04-23",
};

const CITE_PDPL_35 = {
  regulation_version_id: "rv-pdpl-35",
  regulation_code: "PDPL",
  article_ref: "Article 35",
  article_text_ar:
    "يعاقب بالسجن مدة لا تزيد على سنتين وبغرامة لا تزيد على ثلاثة ملايين ريال، أو بإحدى هاتين العقوبتين، كل من أفشى بيانات شخصية حساسة أو أتاحها للغير بقصد الإضرار بصاحب البيانات أو تحقيق منفعة.",
  source_url:
    "https://sdaia.gov.sa/en/SDAIA/about/Documents/Personal%20Data%20English%20V2-23April2023-Reviewed-.pdf",
  effective_date: "2023-09-14",
};

const DEMO_FINDINGS: Record<string, Finding[]> = {
  "demo-1": [
    {
      id: "f1",
      clause_id: "c2",
      title_ar: "نقل بيانات العملاء خارج المملكة بدون ضوابط",
      title_en: "Sending customer data outside the Kingdom without controls",
      explanation_ar:
        "البند يسمح بنقل بيانات العملاء لخوادم خارج المملكة بدون التأكد من مستوى الحماية، وهذا يخالف اللي تشترطه المادة 29.",
      explanation_en:
        "The clause lets customer data go to servers outside the Kingdom without checking the protection level, which is exactly what Article 29 requires.",
      severity: "critical",
      category: "regulatory",
      violation_cost_ar: "غرامة تصل إلى 3 ملايين ريال",
      violation_cost_min: 0,
      violation_cost_max: 3000000,
      review_status: "accepted",
      citation: CITE_PDPL_29,
    },
    {
      id: "f2",
      clause_id: "c4",
      title_ar: "مشاركة بيانات حساسة مع أطراف خارجية",
      title_en: "Sharing sensitive data with third parties",
      explanation_ar:
        "البند يسمح بمشاركة بيانات حساسة مع الشركاء بدون أي حد، والمادة 35 تفرض على هذا عقوبات.",
      explanation_en:
        "The clause allows sharing sensitive data with partners with no limits, and Article 35 attaches criminal penalties to that.",
      severity: "high",
      category: "regulatory",
      violation_cost_ar: "سجن يصل إلى سنتين وغرامة تصل إلى 3 ملايين ريال",
      violation_cost_min: 0,
      violation_cost_max: 3000000,
      review_status: "pending",
      citation: CITE_PDPL_35,
    },
  ],
  "demo-2": [
    {
      id: "f3",
      clause_id: "c1",
      title_ar: "ساعات عمل أكثر من الحد النظامي",
      title_en: "Working hours are over the legal limit",
      explanation_ar:
        "العقد يحدد عشر ساعات عمل باليوم، والمادة 98 من نظام العمل تحدد السقف بثمان ساعات.",
      explanation_en:
        "The contract sets ten working hours a day, while Labor Law Article 98 caps it at eight.",
      severity: "medium",
      category: "regulatory",
      violation_cost_ar: null,
      violation_cost_min: null,
      violation_cost_max: null,
      review_status: "accepted",
      citation: CITE_LABOR_98,
    },
  ],
};

const DEMO_CLAUSES: Record<string, Clause[]> = {
  "demo-1": [
    { id: "c1", ordinal: 1, text_ar: "المادة 1: يلتزم الطرفان بالحفاظ على سرية البيانات المتبادلة.", text_en: null },
    { id: "c2", ordinal: 2, text_ar: "المادة 2: يحق للطرف الثاني نقل بيانات العملاء إلى خوادم خارج المملكة ومعالجتها لدى جهات خارجية.", text_en: null },
    { id: "c3", ordinal: 3, text_ar: "المادة 3: مدة الاتفاقية سنتان قابلة للتجديد.", text_en: null },
    { id: "c4", ordinal: 4, text_ar: "المادة 4: يجوز مشاركة البيانات مع الشركاء التجاريين وفق تقدير الطرف الثاني.", text_en: null },
  ],
  "demo-2": [
    { id: "c1", ordinal: 1, text_ar: "المادة 1: يعمل الموظف عشر ساعات يومياً ولمدة ستة أيام في الأسبوع.", text_en: null },
    { id: "c2", ordinal: 2, text_ar: "المادة 2: يستحق الموظف إجازة سنوية مدتها واحد وعشرون يوماً.", text_en: null },
  ],
};

export function demoContractDetail(id: string): ContractDetail {
  const item = DEMO_CONTRACTS.find((c) => c.id === id) ?? DEMO_CONTRACTS[0]!;
  const findings = DEMO_FINDINGS[id] ?? [];
  const summary = { critical: 0, high: 0, medium: 0, low: 0, pending: 0 };
  for (const f of findings) {
    summary[f.severity] += 1;
    if (f.review_status === "pending") summary.pending += 1;
  }
  return {
    id: item.id,
    title: item.title,
    status: item.status,
    readiness_score: item.readiness_score,
    findings_summary: summary,
  };
}

export function demoClauses(id: string): Clause[] {
  return DEMO_CLAUSES[id] ?? [];
}

export function demoFindings(id: string): Finding[] {
  return DEMO_FINDINGS[id] ?? [];
}

export function demoRadarVerdict(id: string): "GO" | "REVIEW" | "STOP" {
  const findings = DEMO_FINDINGS[id] ?? [];
  const accepted = findings.filter((f) => f.review_status === "accepted");
  if (accepted.some((f) => f.severity === "critical")) return "STOP";
  if (accepted.some((f) => f.severity === "high" || f.severity === "medium")) return "REVIEW";
  return "GO";
}

const SRC = "https://sdaia.gov.sa/x";

export const DEMO_OBLIGATIONS: Obligation[] = [
  {
    id: "o1", title_ar: "تعيين مسؤول حماية البيانات", title_en: "Appoint a Data Protection Officer",
    owner_id: "u1", due_date: "2026-09-01", status: "open",
    citation: { regulation_version_id: "rv1", regulation_code: "PDPL", article_ref: "Article 30", source_url: SRC },
  },
  {
    id: "o2", title_ar: "سجل أنشطة المعالجة", title_en: "Processing activities record",
    owner_id: null, due_date: null, status: "in_progress",
    citation: { regulation_version_id: "rv2", regulation_code: "PDPL", article_ref: "Article 31", source_url: SRC },
  },
  {
    id: "o3", title_ar: "عقود العمل وفق ساعات النظام", title_en: "Employment contracts within legal hours",
    owner_id: "u2", due_date: "2026-08-15", status: "overdue",
    citation: { regulation_version_id: "rv3", regulation_code: "LABOR", article_ref: "Article 98", source_url: SRC },
  },
];

export const DEMO_EVENTS: MonitoringEvent[] = [
  {
    id: "e1", regulation_code: "PDPL", change_type: "amended",
    detected_at: "2026-07-11T09:00:00Z", impact_summary_ar: "تعديل مقترح على المادة 29",
    status: "detected", new_version_id: null,
  },
  {
    id: "e2", regulation_code: "LABOR", change_type: "new_article",
    detected_at: "2026-07-10T12:00:00Z", impact_summary_ar: "إضافة مادة جديدة", status: "verified",
    new_version_id: "rvx",
  },
];

export const DEMO_EVIDENCE: EvidenceSearchItem[] = [
  { regulation_version_id: "rv1", regulation_code: "PDPL", article_ref: "Article 29",
    snippet_ar: "يجوز لجهة التحكم نقل البيانات الشخصية إلى جهة خارج المملكة أو الإفصاح عنها وفق الضوابط التي تحددها اللوائح…", score: 0.91 },
  { regulation_version_id: "rv2", regulation_code: "PDPL", article_ref: "Article 5",
    snippet_ar: "لا يجوز معالجة البيانات الشخصية إلا بعد موافقة صاحبها وفقاً للأحوال والضوابط المنصوص عليها…", score: 0.83 },
  { regulation_version_id: "rv3", regulation_code: "LABOR", article_ref: "Article 98",
    snippet_ar: "لا يجوز تشغيل العامل تشغيلاً فعلياً أكثر من ثماني ساعات في اليوم الواحد…", score: 0.79 },
];

export const DEMO_AUDIT: AuditItem[] = [
  { actor: "analysis", action: "score_computed", target: "demo-1", verdict: "n-a", detail_json: { score: 60 }, at: "2026-07-11T10:20:00Z" },
  { actor: "u1", action: "finding_reviewed", target: "demo-1", verdict: "n-a", detail_json: { decision: "accepted" }, at: "2026-07-11T10:19:00Z" },
  { actor: "research-agent", action: "agent_fetch", target: "sdaia.gov.sa", verdict: "allowed", detail_json: null, at: "2026-07-11T10:00:00Z" },
  { actor: "research-agent", action: "egress_denied", target: "example.com", verdict: "denied", detail_json: { rule: "policy_drop" }, at: "2026-07-11T09:58:00Z" },
];

export const DEMO_ALLOWLIST = ["sama.gov.sa", "sdaia.gov.sa", "zatca.gov.sa", "hrsd.gov.sa", "laws.boe.gov.sa", "api.openai.com"];

export const DEMO_IDEA_REPORT = {
  report_ar:
    "الأنظمة المنطبقة: نظام حماية البيانات الشخصية، المادة 29 والمادة 5.\nالمتطلبات: خذ موافقة واضحة من المستخدم قبل المعالجة، وتأكد من مستوى الحماية قبل أي نقل خارج المملكة.\nالمخاطر: نقل البيانات لمزود خارجي بدون ضوابط يعرّض المنشأة لعقوبات.\nأسئلة مفتوحة: أين ستُخزن البيانات؟ وهل فيها بيانات حساسة؟",
  report_en:
    "Applicable regulations: PDPL Article 29 and Article 5.\nRequirements: get clear user consent before processing, and check the protection level before sending anything outside the Kingdom.\nRisks: sending data to an outside provider without controls puts the company at risk of penalties.\nOpen questions: where will the data live, and does it include sensitive data?",
  citations: [
    { regulation_version_id: "rv-pdpl-29", regulation_code: "PDPL", article_ref: "Article 29", source_url: CITE_PDPL_29.source_url },
    { regulation_version_id: "rv-pdpl-5", regulation_code: "PDPL", article_ref: "Article 5", source_url: CITE_PDPL_29.source_url },
  ],
};
