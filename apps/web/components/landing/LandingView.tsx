"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { guestLogin } from "@/lib/api";
import { Button, MonoChip, SourceChip, FindingCard, ReadinessGauge, FadeIn, AnimatedNumber } from "@/components/design/Shared";

type Lang = "ar" | "en";

const T = {
  ar: {
    dir: "rtl" as const,
    nav: { product: "المنتج", paths: "المسارات الخمسة", sovereignty: "السيادة", login: "دخول", cta: "جرّب الآن" },
    hero: {
      badge: "امتثال سيادي للقطاع المالي",
      title: "كل بندٍ وله سَنَد.",
      body: "سند يراجع عقودك ويراقب التزاماتك تجاه ساما، يربط كل نتيجة بمرجعها النظامي، ويعمل بالكامل داخل بنيتك التحتية دون أن تغادر بياناتك المنشأة.",
      cta: "جرّب الآن",
      ctaBusy: "جارٍ التجهيز…",
      secondary: "شاهد كيف يعمل",
      footnote: "استضافة ذاتية كاملة · لا نتائج بدون مصدر",
      file: "اتفاقية_خدمات_سحابية_v3.pdf",
      clause1: "المادة الأولى: يلتزم الطرف الأول بتقديم الخدمات المتفق عليها وفقاً لمستويات الخدمة المحددة في الملحق (أ)...",
      clauseTag: "المادة 2",
      clause2: "\"يحق للطرف الثاني تخزين ومعالجة بيانات العملاء لدى مزود خدمات سحابية خارج المملكة العربية السعودية متى اقتضت الحاجة التشغيلية ذلك.\"",
    },
    findings: [
      { id: "FND-031", severity: "red" as const, text: "البند يسمح بنقل بيانات العملاء خارج المملكة، ويتعارض مع متطلبات توطين البيانات للقطاع المالي.", source: "SAMA — متطلبات توطين البيانات" },
      { id: "FND-032", severity: "amber" as const, text: "لا يحدد البند مدة الاحتفاظ بالبيانات بعد انتهاء العلاقة التعاقدية.", source: "PDPL — المادة 18" },
      { id: "FND-033", severity: "amber" as const, text: "غياب تحديد مسؤولية نقل البيانات وإعادتها بأمان فور انتهاء التعاقد.", source: "SAMA-CSF — إدارة المخاطر" },
    ],
    strip: "نطاق التغطية التنظيمية:",
    cost: {
      heading: "المخالفة أغلى من الامتثال",
      fineLabel: "الحد الأعلى للغرامة في نظام حماية البيانات الشخصية",
      fineSource: "PDPL — المادة 36",
      stats: [
        { suffix: "+ ساعة", desc: "متوسط الوقت لمراجعة عقد واحد يدويًا", src: "دراسة داخلية 2025" },
        { suffix: "+ تحديثًا", desc: "سنويًا عبر ساما وهيئة السوق المالية وسدايا", src: "رصد سند 2025" },
        { suffix: "%", desc: "من الالتزامات تُدار حتى اليوم في جداول إكسل", src: "مقابلات العملاء 2025" },
      ],
    },
    pathsHeading: "المسارات الخمسة",
    paths: [
      { id: "01", title: "مراجعة العقود", desc: "ارفع العقد، واستلم تقريرًا بكل بند يحتاج انتباهك، مع درجة جاهزية واحدة تلخص الموقف.",
        docTitle: "الإنماء — اتفاقية خدمات سحابية × مسودة 3", f1: "السماح بنقل البيانات خارج المملكة", s1: "SAMA — توطين البيانات", f2: "عدم تحديد مدة الاحتفاظ بالبيانات", s2: "PDPL — المادة 18" },
      { id: "02", title: "المراقبة المستمرة", desc: "سند يتابع مصادر الجهات التنظيمية، وإذا تغيّر شيء يمسّ التزاماتك تعرف قبل أن يسألك أحد.",
        e1: "صدر تحديث على إطار الأمن السيبراني من ساما", e1b: "يؤثر على 3 التزامات في سجلك", review: "راجع الأثر", e2: "تعديل مدد الاستجابة لطلبات أصحاب البيانات — سدايا" },
      { id: "03", title: "سجل الالتزامات التنظيمية", desc: "كل التزام في مكان واحد: مصدره، حالته، والمسؤول عنه. لا شيء يضيع في الإيميلات.",
        cId: "المعرّف", cObl: "الالتزام", cStatus: "الحالة", cSrc: "المصدر", o1: "إبلاغ ساما عن الحوادث السيبرانية الجسيمة", st1: "ملتزم", o2: "تعيين مسؤول حماية البيانات الشخصية", st2: "قيد المراجعة" },
      { id: "04", title: "واجهة الامتثال المدمجة", desc: "فرق المنتجات تستدعي سند من داخل أنظمتها، فيصبح الامتثال جزءًا من الرحلة لا خطوة بعدها.",
        finding: "بند تخزين خارجي", source: "SAMA — توطين البيانات" },
      { id: "05", title: "طبقة الامتثال الشرعي", desc: "مراجعة البنود مقابل المعايير الشرعية المعتمدة، لأن الالتزام عندنا لا يقف عند الأنظمة.",
        badge: "متوافق مع معايير أيوفي", clause: "\"غرامة تأخير 2% شهريًا على الدفعات المتأخرة تُضاف إلى إيرادات البنك.\"",
        note: "اشتراط عائد الغرامة للبنك لا يتوافق مع المعيار الشرعي لغرامات التأخير، والمعالجة المعتمدة صرفها في وجوه الخير.", std: "أيوفي — المعيار 8 (المرابحة)" },
    ],
    source: {
      heading: "لا نتائج بدون مصدر", sub: "إذا لم يوجد مصدر رسمي للنتيجة، فلن تظهر. هذه قاعدتنا الذهبية.",
      clause: "\"يحق للطرف الثاني تخزين ومعالجة بيانات العملاء لدى مزود خدمات سحابية خارج المملكة العربية السعودية...\"",
      explain: "اشرح هذه النتيجة", reset: "إعادة",
      s1a: "1. البند المشكل", s1b: "\"يحق للطرف الثاني تخزين ومعالجة بيانات العملاء لدى مزود خدمات سحابية خارج المملكة العربية السعودية...\"",
      s2src: "SAMA — متطلبات توطين البيانات", s2b: "المرجع النظامي الذي يستند إليه سند في تقييم البند.",
      s3title: "مخالفة لمتطلبات التوطين", s3a: "البند بصيغته الحالية يتيح نقل بيانات العملاء خارج المملكة دون قيد. التعديل المقترح: حصر التخزين في مراكز بيانات محلية.", s3b: "التفسير والنتيجة النهائية المرتبطة بالمصدر حصرًا.",
    },
    sov: {
      heading: "بياناتك لا تغادر منشأتك",
      body: "سند يُنشر بالكامل داخل بنيتك التحتية. لا واجهات خارجية، لا بيانات تخرج، ولا اعتماد على مزود سحابي أجنبي. سيادة تامة على الامتثال.",
      cta: "تعرف على المتطلبات التقنية", inside: "داخل منشأة العميل",
      f1: "المستندات والعقود", f2: "قراءة الوثيقة وتفكيك بنودها", f3: "التحليل والاسترجاع الآمن", f4a: "النتائج", f4b: "سجل الامتثال",
    },
    numbers: { readiness: "متوسط جاهزية العقود", hours: "ساعة عمل موفّرة شهريًا", sourced: "من النتائج موثقة بمصدر" },
    finalCta: { heading: "كل بندٍ وله سَنَد.", cta: "ابدأ الآن", join: "إنشاء حساب" },
    footer: {
      blurb: "نظام تشغيل الامتثال السيادي للقطاع المالي السعودي.", made: "صُنع في الرياض",
      productH: "المنتج", p1: "مراجعة العقود", p2: "المراقبة المستمرة", p3: "سجل الالتزامات", p4: "فحص الأفكار",
      companyH: "الشركة", c1: "السيادة والتقنية", c2: "المنتج", c3: "إنشاء حساب", c4: "تسجيل الدخول",
    },
  },
  en: {
    dir: "ltr" as const,
    nav: { product: "Product", paths: "Five Paths", sovereignty: "Sovereignty", login: "Sign in", cta: "Try it now" },
    hero: {
      badge: "Sovereign compliance for the financial sector",
      title: "Every clause has its سَنَد.",
      body: "SANAD reviews your contracts and monitors your SAMA obligations, binds every finding to its exact regulatory source, and runs entirely inside your own infrastructure — your data never leaves the institution.",
      cta: "Try it now",
      ctaBusy: "Preparing…",
      secondary: "See how it works",
      footnote: "Fully self-hosted · No unsourced findings",
      file: "cloud_services_agreement_v3.pdf",
      clause1: "Article 1: The First Party shall provide the agreed services in accordance with the service levels defined in Annex (A)...",
      clauseTag: "Article 2",
      clause2: "\"The Second Party may store and process customer data with a cloud provider outside the Kingdom of Saudi Arabia whenever operationally required.\"",
    },
    findings: [
      { id: "FND-031", severity: "red" as const, text: "The clause permits transferring customer data outside the Kingdom, conflicting with data-residency requirements for the financial sector.", source: "SAMA — Data Residency Requirements" },
      { id: "FND-032", severity: "amber" as const, text: "The clause does not specify a data-retention period after the contractual relationship ends.", source: "PDPL — Article 18" },
      { id: "FND-033", severity: "amber" as const, text: "No defined responsibility for securely transferring and returning data once the contract ends.", source: "SAMA-CSF — Risk Management" },
    ],
    strip: "Regulatory coverage:",
    cost: {
      heading: "A violation costs more than compliance",
      fineLabel: "Maximum fine under the Personal Data Protection Law",
      fineSource: "PDPL — Article 36",
      stats: [
        { suffix: "+ hrs", desc: "Average time to review a single contract manually", src: "Internal study 2025" },
        { suffix: "+ updates", desc: "Per year across SAMA, CMA and SDAIA", src: "SANAD monitoring 2025" },
        { suffix: "%", desc: "Of obligations are still managed in spreadsheets today", src: "Customer interviews 2025" },
      ],
    },
    pathsHeading: "The Five Paths",
    paths: [
      { id: "01", title: "Contract Review", desc: "Upload the contract and get a report on every clause that needs attention, with a single readiness score that sums up where you stand.",
        docTitle: "Alinma — Cloud Services Agreement × Draft 3", f1: "Permits data transfer outside the Kingdom", s1: "SAMA — Data Residency", f2: "No data-retention period defined", s2: "PDPL — Article 18" },
      { id: "02", title: "Continuous Monitoring", desc: "SANAD watches regulator sources, and when something changes that touches your obligations you know before anyone asks.",
        e1: "An update to SAMA's Cyber Security Framework was issued", e1b: "Affects 3 obligations in your register", review: "Review impact", e2: "Amended response windows for data-subject requests — SDAIA" },
      { id: "03", title: "Regulatory Obligation Register", desc: "Every obligation in one place: its source, its status, and its owner. Nothing lost in email threads.",
        cId: "ID", cObl: "Obligation", cStatus: "Status", cSrc: "Source", o1: "Report severe cyber incidents to SAMA", st1: "Compliant", o2: "Appoint a Personal Data Protection Officer", st2: "Under review" },
      { id: "04", title: "Embedded Compliance API", desc: "Product teams call SANAD from inside their own systems, so compliance becomes part of the journey rather than a step after it.",
        finding: "External storage clause", source: "SAMA — Data Residency" },
      { id: "05", title: "Shariah Compliance Layer", desc: "Reviewing clauses against approved Shariah standards, because for us compliance does not stop at regulations.",
        badge: "Compliant with AAOIFI standards", clause: "\"A 2% monthly late-payment penalty on overdue installments is added to the bank's revenue.\"",
        note: "Directing the penalty proceeds to the bank does not comply with the Shariah standard on late-payment penalties; the approved treatment is to donate it to charity.", std: "AAOIFI — Standard 8 (Murabaha)" },
    ],
    source: {
      heading: "No findings without a source", sub: "If there is no official source for a finding, it does not appear. That is our golden rule.",
      clause: "\"The Second Party may store and process customer data with a cloud provider outside the Kingdom of Saudi Arabia...\"",
      explain: "Explain this finding", reset: "Reset",
      s1a: "1. The problematic clause", s1b: "\"The Second Party may store and process customer data with a cloud provider outside the Kingdom of Saudi Arabia...\"",
      s2src: "SAMA — Data Residency Requirements", s2b: "The regulatory reference SANAD relies on to assess the clause.",
      s3title: "Violation of residency requirements", s3a: "As written, the clause allows customer data to move outside the Kingdom without restriction. Proposed fix: confine storage to local data centers.", s3b: "The explanation and final finding, tied to the source exclusively.",
    },
    sov: {
      heading: "Your data never leaves your institution",
      body: "SANAD is deployed entirely inside your own infrastructure. No external interfaces, no data leaving, no reliance on a foreign cloud provider. Full sovereignty over compliance.",
      cta: "See the technical requirements", inside: "Inside the client's premises",
      f1: "Documents & contracts", f2: "Read the document and decompose its clauses", f3: "Secure analysis & retrieval", f4a: "Findings", f4b: "Compliance register",
    },
    numbers: { readiness: "Average contract readiness", hours: "Work-hours saved monthly", sourced: "Of findings backed by a source" },
    finalCta: { heading: "Every clause has its سَنَد.", cta: "Get started", join: "Create account" },
    footer: {
      blurb: "The sovereign compliance operating system for the Saudi financial sector.", made: "Made in Riyadh",
      productH: "Product", p1: "Contract Review", p2: "Continuous Monitoring", p3: "Obligation Register", p4: "Idea Check",
      companyH: "Company", c1: "Sovereignty & tech", c2: "Product", c3: "Create account", c4: "Sign in",
    },
  },
};

export function LandingView() {
  const router = useRouter();
  const [lang, setLang] = useState<Lang>("ar");
  const [activeStep, setActiveStep] = useState(0);
  const [scanPhase, setScanPhase] = useState<"idle" | "scanning" | "found">("idle");
  const [findingIdx, setFindingIdx] = useState(0);
  const [findingVisible, setFindingVisible] = useState(false);
  const [pathIdx, setPathIdx] = useState(0);

  const t = T[lang];
  const heroFindings = t.findings;

  useEffect(() => {
    const t1 = setTimeout(() => {
      setScanPhase("scanning");
      const t2 = setTimeout(() => { setScanPhase("found"); setFindingVisible(true); }, 2600);
      return () => clearTimeout(t2);
    }, 1200);
    return () => clearTimeout(t1);
  }, []);

  useEffect(() => {
    if (scanPhase !== "found") return;
    const timer = setTimeout(() => {
      setFindingVisible(false);
      const t2 = setTimeout(() => { setFindingIdx((i) => (i + 1) % heroFindings.length); setFindingVisible(true); }, 400);
      return () => clearTimeout(t2);
    }, 3500);
    return () => clearTimeout(timer);
  }, [scanPhase, findingIdx, heroFindings.length]);

  useEffect(() => {
    const timer = setTimeout(() => setPathIdx((i) => (i + 1) % 5), 5000);
    return () => clearTimeout(timer);
  }, [pathIdx]);

  const goLogin = () => router.push("/login");
  const [guestBusy, setGuestBusy] = useState(false);
  const goGuest = async () => {
    if (guestBusy) return;
    setGuestBusy(true);
    try {
      await guestLogin();
      router.push("/contracts");
      router.refresh();
    } catch {
      router.push("/login");
    }
  };
  const currentFinding = heroFindings[findingIdx]!;
  const p = t.paths;

  const pathContent = [
    (
      <div className="bg-card border border-border rounded-xl p-6 flex flex-col md:flex-row gap-8 items-start">
        <div className="flex-1 space-y-3">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">{p[0]!.docTitle}</span>
            <MonoChip>PDF</MonoChip>
          </div>
          <FindingCard id="FND-031" severity="red" text={p[0]!.f1!} source={p[0]!.s1!} />
          <FindingCard id="FND-032" severity="amber" text={p[0]!.f2!} source={p[0]!.s2!} />
        </div>
        <div className="bg-background border border-border p-6 rounded-lg flex-shrink-0"><ReadinessGauge value={68} /></div>
      </div>
    ),
    (
      <div className="bg-card border border-border rounded-xl p-6 space-y-4">
        <div className="flex items-start gap-4 pb-4 border-b border-border">
          <div className="w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0 shadow-[0_0_6px_rgba(232,106,44,0.5)]" />
          <div className="flex-1">
            <p className="font-medium mb-1">{p[1]!.e1}</p>
            <p className="text-[13px] text-muted-foreground mb-3">{p[1]!.e1b}</p>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex gap-2 flex-wrap">
                <MonoChip>SAMA-CSF v2</MonoChip>
                <MonoChip className="text-muted-foreground border-transparent">24 Oct 2025</MonoChip>
              </div>
              <button className="text-[13px] text-primary hover:underline">{p[1]!.review}</button>
            </div>
          </div>
        </div>
        <div className="flex items-start gap-4 opacity-40">
          <div className="w-2 h-2 rounded-full bg-muted-foreground mt-2 flex-shrink-0" />
          <div><p className="font-medium text-[14px]">{p[1]!.e2}</p><p className="text-[13px] text-muted-foreground">18 Oct 2025</p></div>
        </div>
      </div>
    ),
    (
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <table className="w-full text-sm text-start">
          <thead className="bg-background/50 border-b border-border text-muted-foreground text-[14px]">
            <tr>
              <th className="p-4 font-medium whitespace-nowrap text-start">{p[2]!.cId}</th>
              <th className="p-4 font-medium text-start">{p[2]!.cObl}</th>
              <th className="p-4 font-medium whitespace-nowrap text-start">{p[2]!.cStatus}</th>
              <th className="p-4 font-medium whitespace-nowrap text-start">{p[2]!.cSrc}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            <tr>
              <td className="p-4 whitespace-nowrap"><MonoChip>OBL-014</MonoChip></td>
              <td className="p-4 text-[14px] font-medium">{p[2]!.o1}</td>
              <td className="p-4 whitespace-nowrap"><span className="px-3 py-1.5 text-[13px] font-medium border border-primary text-primary rounded-full">{p[2]!.st1}</span></td>
              <td className="p-4 whitespace-nowrap"><SourceChip text="SAMA-CSF 3.3.15" /></td>
            </tr>
            <tr>
              <td className="p-4 whitespace-nowrap"><MonoChip>OBL-027</MonoChip></td>
              <td className="p-4 text-[14px] font-medium">{p[2]!.o2}</td>
              <td className="p-4 whitespace-nowrap"><span className="px-3 py-1.5 text-[13px] font-medium border border-[#C15613] text-[#C15613] rounded-full">{p[2]!.st2}</span></td>
              <td className="p-4 whitespace-nowrap"><SourceChip text={lang === "ar" ? "PDPL — المادة 30" : "PDPL — Article 30"} /></td>
            </tr>
          </tbody>
        </table>
      </div>
    ),
    (
      <div className="bg-[#14110E] border border-border rounded-xl p-6 font-mono text-[12px] overflow-x-auto" dir="ltr">
        <div className="text-primary mb-2">POST /v1/checks</div>
        <div className="mb-4 text-[#E9E4D8]/80">{`{ "document": "murabaha_v3.pdf", "check": "data_residency" }`}</div>
        <div className="text-[#8A93A6] border-t border-white/10 pt-4">
          <pre className="whitespace-pre-wrap">{`{\n  "finding": "${p[3]!.finding}",\n  "source": "${p[3]!.source}",\n  "score": 0.94\n}`}</pre>
        </div>
      </div>
    ),
    (
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <span className="w-2 h-2 rounded-full bg-[#2F7D5B]" />
          <span className="text-[#2F7D5B] text-sm font-medium">{p[4]!.badge}</span>
        </div>
        <div className="space-y-4">
          <div className="p-4 bg-background border border-border rounded-lg text-sm text-muted-foreground">{p[4]!.clause}</div>
          <div className="flex items-start gap-4">
            <div className="w-6 h-6 rounded-full border border-border flex items-center justify-center text-[10px] mt-1 shrink-0">↳</div>
            <div>
              <p className="text-[15px] mb-3">{p[4]!.note}</p>
              <span className="font-mono text-[13px] text-[#2F7D5B] bg-[#2F7D5B]/10 px-3 py-1 border border-[#2F7D5B]/30 rounded-md">{p[4]!.std}</span>
            </div>
          </div>
        </div>
      </div>
    ),
  ];

  return (
    <div dir={t.dir} className="min-h-[100dvh] flex flex-col bg-background text-foreground overflow-x-hidden">
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex flex-col">
              <span className="font-bold text-xl leading-none">سند</span>
              <span className="font-mono text-[10px] text-muted-foreground leading-none mt-1">SANAD</span>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <a href="#product" className="text-[15px] text-muted-foreground hover:text-primary transition-colors">{t.nav.product}</a>
              <a href="#paths" className="text-[15px] text-muted-foreground hover:text-primary transition-colors">{t.nav.paths}</a>
              <a href="#sovereignty" className="text-[15px] text-muted-foreground hover:text-primary transition-colors">{t.nav.sovereignty}</a>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <button onClick={() => setLang(lang === "ar" ? "en" : "ar")} className="text-[13px] font-medium text-muted-foreground hover:text-foreground transition-colors">
              {lang === "ar" ? "EN" : "ع"}
            </button>
            <Link href="/login" className="text-[15px] font-medium hover:text-primary transition-colors">{t.nav.login}</Link>
            <Button onClick={goGuest} disabled={guestBusy}>{t.nav.cta}</Button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="relative py-24 md:py-32 overflow-hidden border-b border-border bg-gradient-hero">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary/8 rounded-full blur-[120px] pointer-events-none" />
          <div className="max-w-[1200px] mx-auto px-6 grid md:grid-cols-2 gap-16 items-center">
            <div className="flex flex-col items-start gap-6 relative z-10">
              <span className="label-chip inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 border border-primary/20 text-primary rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                {t.hero.badge}
              </span>
              <h1 className="text-[34px] md:text-[56px] leading-[1.2] font-bold">{t.hero.title}</h1>
              <p className="text-[17px] text-muted-foreground max-w-[480px]">{t.hero.body}</p>
              <div className="flex flex-wrap items-center gap-4 mt-4">
                <Button onClick={goGuest} disabled={guestBusy}>{guestBusy ? t.hero.ctaBusy : t.hero.cta}</Button>
                <a href="#paths"><Button variant="ghost">{t.hero.secondary}</Button></a>
              </div>
              <div className="mt-8 text-[13px] font-mono text-muted-foreground">{t.hero.footnote}</div>
            </div>

            <div className="relative bg-card border border-line rounded-2xl overflow-hidden shadow-lg hero-panel" style={{ minHeight: "440px" }}>
              {scanPhase === "scanning" && <div className="scan-beam" />}
              <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-line bg-muted/60">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-line" />
                  <div className="w-2.5 h-2.5 rounded-full bg-line" />
                  <div className="w-2.5 h-2.5 rounded-full bg-line" />
                </div>
                <span className="font-mono text-[11px] text-muted-foreground mx-auto">{t.hero.file}</span>
              </div>
              <div className="p-6 space-y-3">
                <div className="p-4 rounded-xl border border-line bg-muted/20 text-[14px] leading-relaxed text-muted-foreground/40 blur-[2.5px] select-none">{t.hero.clause1}</div>
                <div className={`relative p-4 rounded-xl border text-[14px] leading-relaxed text-foreground transition-all duration-700 ${
                  scanPhase === "found" ? "border-primary/40 bg-primary/8" : scanPhase === "scanning" ? "border-primary/20 bg-primary/4" : "border-line bg-muted/20"
                }`}>
                  {scanPhase !== "idle" && (
                    <span className="absolute -top-2.5 end-3 bg-card px-2 font-mono text-[11px] text-primary border border-primary/20 rounded">{t.hero.clauseTag}</span>
                  )}
                  {t.hero.clause2}
                </div>
                <div className="bg-muted/50 border border-line rounded-xl p-4 transition-opacity duration-300"
                  style={{ opacity: findingVisible ? 1 : 0, pointerEvents: findingVisible ? "auto" : "none" }}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: currentFinding.severity === "red" ? "var(--sev-red)" : "var(--sev-amber)" }} />
                    <MonoChip>{currentFinding.id}</MonoChip>
                  </div>
                  <p className="text-[14px] leading-[1.7] mb-3 text-foreground">{currentFinding.text}</p>
                  <SourceChip text={currentFinding.source} />
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-6 border-b border-border bg-card/30">
          <div className="max-w-[1200px] mx-auto px-6 flex flex-col md:flex-row items-center gap-6">
            <span className="text-[13px] text-muted-foreground whitespace-nowrap">{t.strip}</span>
            <div className="flex items-center gap-4 overflow-x-auto w-full pb-2 md:pb-0">
              {["SAMA", "CMA", lang === "ar" ? "PDPL / سدايا" : "PDPL / SDAIA", "NCA ECC", "AAOIFI"].map((reg) => (
                <div key={reg} className="px-4 py-2 border border-border rounded-md font-mono text-[13px] bg-background hover:border-primary transition-colors whitespace-nowrap cursor-default">{reg}</div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24 border-b border-border" id="product">
          <div className="max-w-[1200px] mx-auto px-6">
            <FadeIn><h2 className="text-[34px] font-bold mb-16 text-center">{t.cost.heading}</h2></FadeIn>
            <div className="flex flex-col items-center mb-16">
              <div className="flex items-end gap-2 text-destructive" dir="ltr">
                <span className="text-xl pb-2">SAR</span>
                <span className="text-[56px] md:text-[80px] font-bold leading-none tracking-tighter"><AnimatedNumber value={5000000} /></span>
              </div>
              <div className="flex items-center gap-3 mt-4">
                <MonoChip className="text-muted-foreground">{t.cost.fineLabel}</MonoChip>
                <SourceChip text={t.cost.fineSource} />
              </div>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {t.cost.stats.map((stat, i) => (
                <FadeIn key={stat.desc} delay={i * 100}>
                  <div className="bg-card border border-border p-6 rounded-xl h-full flex flex-col justify-between">
                    <div>
                      <div className="text-[40px] font-bold font-mono tnum text-foreground mb-2 whitespace-nowrap"><AnimatedNumber value={[40, 120, 70][i]!} suffix={stat.suffix} /></div>
                      <p className="text-[15px] text-muted-foreground">{stat.desc}</p>
                    </div>
                    <div className="mt-4 pt-4 border-t border-border"><SourceChip text={stat.src} /></div>
                  </div>
                </FadeIn>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24 border-b border-border bg-card/10" id="paths">
          <div className="max-w-[1200px] mx-auto px-6">
            <FadeIn><h2 className="text-[34px] font-bold mb-12">{t.pathsHeading}</h2></FadeIn>
            <div className="grid md:grid-cols-[320px_1fr] gap-8 items-start">
              <div className="space-y-1">
                {p.map((path, i) => (
                  <button key={path.id} onClick={() => setPathIdx(i)}
                    className={`w-full text-start px-5 py-4 rounded-xl transition-all duration-200 border ${pathIdx === i ? "bg-primary/8 border-primary/15" : "border-transparent hover:bg-muted/50"}`}>
                    <div className="flex items-center gap-3">
                      <span className={`font-mono text-[11px] shrink-0 transition-colors ${pathIdx === i ? "text-primary" : "text-muted-foreground"}`}>{lang === "ar" ? "م" : "P"}-{path.id}</span>
                      <span className={`font-bold text-[15px] transition-colors ${pathIdx === i ? "text-foreground" : "text-muted-foreground"}`}>{path.title}</span>
                    </div>
                    {pathIdx === i && (
                      <>
                        <p className="text-[13px] text-muted-foreground mt-2 ps-7 leading-relaxed text-start">{path.desc}</p>
                        <div className="mt-3 ps-7">
                          <div className="h-0.5 bg-line rounded overflow-hidden">
                            <div key={`bar-${pathIdx}`} className="h-full bg-primary/50 rounded progress-countdown" />
                          </div>
                        </div>
                      </>
                    )}
                  </button>
                ))}
              </div>
              <div key={`${lang}-${pathIdx}`} className="fade-in-slide">{pathContent[pathIdx]}</div>
            </div>
          </div>
        </section>

        <section className="py-24 border-b border-border">
          <div className="max-w-[1200px] mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-16">
              <FadeIn>
                <h2 className="text-[34px] font-bold mb-4">{t.source.heading}</h2>
                <p className="text-muted-foreground">{t.source.sub}</p>
              </FadeIn>
            </div>
            <div className="max-w-3xl mx-auto flex flex-col items-center">
              {activeStep === 0 ? (
                <div className="bg-card border border-border p-6 rounded-xl w-full text-center">
                  <div className="p-4 bg-background border border-border rounded-lg text-sm text-muted-foreground mb-6">{t.source.clause}</div>
                  <Button onClick={() => setActiveStep(1)}>{t.source.explain}</Button>
                </div>
              ) : (
                <div className="w-full space-y-8 relative before:absolute before:top-4 before:bottom-4 before:end-[15px] md:before:end-1/2 before:w-[2px] before:bg-line before:-z-10">
                  <FadeIn delay={0}>
                    <div className="flex flex-col md:flex-row gap-6 md:items-center">
                      <div className="md:w-1/2 flex md:justify-end items-center gap-4">
                        <div className="bg-card border border-border p-4 rounded-lg text-sm md:max-w-[280px]">{t.source.s1a}</div>
                        <div className="w-8 h-8 rounded-full bg-background border-2 border-primary shrink-0 z-10 flex items-center justify-center text-xs font-bold text-primary">1</div>
                      </div>
                      <div className="md:w-1/2 text-[15px] text-muted-foreground ms-12 md:ms-0">{t.source.s1b}</div>
                    </div>
                  </FadeIn>
                  <FadeIn delay={400}>
                    <div className="flex flex-col md:flex-row gap-6 md:items-center">
                      <div className="md:w-1/2 flex md:justify-end items-center gap-4">
                        <div className="bg-card border border-border p-4 rounded-lg md:max-w-[280px]"><SourceChip text={t.source.s2src} /></div>
                        <div className="w-8 h-8 rounded-full bg-background border-2 border-primary shrink-0 z-10 flex items-center justify-center text-xs font-bold text-primary">2</div>
                      </div>
                      <div className="md:w-1/2 text-[15px] text-muted-foreground ms-12 md:ms-0">{t.source.s2b}</div>
                    </div>
                  </FadeIn>
                  <FadeIn delay={800}>
                    <div className="flex flex-col md:flex-row gap-6 md:items-center">
                      <div className="md:w-1/2 flex md:justify-end items-center gap-4">
                        <div className="bg-card border border-border p-4 rounded-lg text-[13px] md:max-w-[280px]">
                          <span className="text-destructive mb-1 block">{t.source.s3title}</span>
                          {t.source.s3a}
                        </div>
                        <div className="w-8 h-8 rounded-full bg-background border-2 border-primary shrink-0 z-10 flex items-center justify-center text-xs font-bold text-primary">3</div>
                      </div>
                      <div className="md:w-1/2 text-[15px] text-muted-foreground ms-12 md:ms-0">{t.source.s3b}</div>
                    </div>
                  </FadeIn>
                  <div className="text-center pt-8"><Button variant="ghost" onClick={() => setActiveStep(0)}>{t.source.reset}</Button></div>
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="py-24 border-b border-border bg-card/20" id="sovereignty">
          <div className="max-w-[1200px] mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-16 items-center">
              <div>
                <FadeIn>
                  <h2 className="text-[34px] font-bold mb-6">{t.sov.heading}</h2>
                  <p className="text-[17px] text-muted-foreground mb-8">{t.sov.body}</p>
                  <Button variant="ghost" onClick={goLogin}>{t.sov.cta}</Button>
                </FadeIn>
              </div>
              <div className="p-8 border-2 border-dashed border-line rounded-2xl relative">
                <div className="absolute top-0 end-8 -translate-y-1/2 bg-background px-4 font-mono text-[13px] text-muted-foreground">{t.sov.inside}</div>
                <div className="flex flex-col gap-6">
                  <div className="p-4 bg-card border border-border rounded-lg text-center font-medium">{t.sov.f1}</div>
                  <div className="text-center text-muted-foreground">↓</div>
                  <div className="p-4 bg-background border border-border rounded-lg text-center text-sm">{t.sov.f2}</div>
                  <div className="text-center text-muted-foreground">↓</div>
                  <div className="p-4 bg-primary/10 border border-primary/30 text-primary rounded-lg text-center font-medium">{t.sov.f3}</div>
                  <div className="text-center text-muted-foreground">↓</div>
                  <div className="flex gap-4">
                    <div className="flex-1 p-4 bg-card border border-border rounded-lg text-center text-sm">{t.sov.f4a}</div>
                    <div className="flex-1 p-4 bg-card border border-border rounded-lg text-center text-sm">{t.sov.f4b}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 border-b border-border">
          <div className="max-w-[1200px] mx-auto px-6 flex flex-col md:flex-row justify-around items-center gap-12 text-center">
            <div className="flex flex-col items-center">
              <ReadinessGauge value={87} className="mb-2" />
              <div className="text-[15px] font-medium mt-2">{t.numbers.readiness}</div>
            </div>
            <div className="hidden md:block w-px h-16 bg-border" />
            <div className="flex flex-col items-center">
              <div className="text-[48px] font-bold font-mono tnum text-foreground mb-1"><AnimatedNumber value={142} prefix="+" /></div>
              <div className="text-[15px] font-medium text-muted-foreground">{t.numbers.hours}</div>
            </div>
            <div className="hidden md:block w-px h-16 bg-border" />
            <div className="flex flex-col items-center">
              <div className="text-[48px] font-bold font-mono tnum text-primary mb-1"><AnimatedNumber value={100} suffix="%" /></div>
              <div className="text-[15px] font-medium text-muted-foreground">{t.numbers.sourced}</div>
            </div>
          </div>
        </section>

        <section className="py-32 bg-gradient-cta">
          <div className="max-w-[800px] mx-auto px-6 text-center">
            <FadeIn>
              <h2 className="text-[40px] md:text-[56px] font-bold mb-8">{t.finalCta.heading}</h2>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-4">
                <Button className="w-full sm:w-auto text-lg px-8 py-4" onClick={goGuest} disabled={guestBusy}>{guestBusy ? t.hero.ctaBusy : t.finalCta.cta}</Button>
                <Link href="/join" className="w-full sm:w-auto"><Button variant="ghost" className="w-full text-lg px-8 py-4">{t.finalCta.join}</Button></Link>
              </div>
            </FadeIn>
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-12 bg-background">
        <div className="max-w-[1200px] mx-auto px-6 grid md:grid-cols-3 gap-8">
          <div>
            <div className="flex flex-col mb-4">
              <span className="font-bold text-xl leading-none">سند</span>
              <span className="font-mono text-[10px] text-muted-foreground leading-none mt-1">SANAD</span>
            </div>
            <p className="text-sm text-muted-foreground mb-6 max-w-[240px]">{t.footer.blurb}</p>
            <MonoChip className="text-muted-foreground">{t.footer.made}</MonoChip>
          </div>
          <div className="grid grid-cols-2 gap-8 md:col-span-2">
            <div>
              <h4 className="font-bold mb-4">{t.footer.productH}</h4>
              <ul className="space-y-3 text-[15px] text-muted-foreground">
                <li><Link href="/login" className="hover:text-primary transition-colors">{t.footer.p1}</Link></li>
                <li><Link href="/login" className="hover:text-primary transition-colors">{t.footer.p2}</Link></li>
                <li><Link href="/login" className="hover:text-primary transition-colors">{t.footer.p3}</Link></li>
                <li><Link href="/login" className="hover:text-primary transition-colors">{t.footer.p4}</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">{t.footer.companyH}</h4>
              <ul className="space-y-3 text-[15px] text-muted-foreground">
                <li><a href="#sovereignty" className="hover:text-primary transition-colors">{t.footer.c1}</a></li>
                <li><a href="#product" className="hover:text-primary transition-colors">{t.footer.c2}</a></li>
                <li><Link href="/join" className="hover:text-primary transition-colors">{t.footer.c3}</Link></li>
                <li><Link href="/login" className="hover:text-primary transition-colors">{t.footer.c4}</Link></li>
              </ul>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
