"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, MonoChip, SourceChip, FindingCard, ReadinessGauge, FadeIn, AnimatedNumber } from "@/components/design/Shared";

const heroFindings = [
  { id: "FND-031", severity: "red" as const, text: "البند يسمح بنقل بيانات العملاء خارج المملكة، ويتعارض مع متطلبات توطين البيانات للقطاع المالي.", source: "SAMA — متطلبات توطين البيانات" },
  { id: "FND-032", severity: "amber" as const, text: "لا يحدد البند مدة الاحتفاظ بالبيانات بعد انتهاء العلاقة التعاقدية.", source: "PDPL — المادة 18" },
  { id: "FND-033", severity: "amber" as const, text: "غياب تحديد مسؤولية نقل البيانات وإعادتها بأمان فور انتهاء التعاقد.", source: "SAMA-CSF — إدارة المخاطر" },
];

export function LandingView() {
  const router = useRouter();
  const [lang, setLang] = useState<"ar" | "en">("ar");
  const [activeStep, setActiveStep] = useState(0);
  const [scanPhase, setScanPhase] = useState<"idle" | "scanning" | "found">("idle");
  const [findingIdx, setFindingIdx] = useState(0);
  const [findingVisible, setFindingVisible] = useState(false);
  const [pathIdx, setPathIdx] = useState(0);

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
    const t = setTimeout(() => {
      setFindingVisible(false);
      const t2 = setTimeout(() => { setFindingIdx((i) => (i + 1) % heroFindings.length); setFindingVisible(true); }, 400);
      return () => clearTimeout(t2);
    }, 3500);
    return () => clearTimeout(t);
  }, [scanPhase, findingIdx]);

  useEffect(() => {
    const t = setTimeout(() => setPathIdx((i) => (i + 1) % 5), 5000);
    return () => clearTimeout(t);
  }, [pathIdx]);

  const goLogin = () => router.push("/login");
  const currentFinding = heroFindings[findingIdx]!;

  const paths = [
    {
      id: "01", title: "مراجعة العقود",
      desc: "ارفع العقد، واستلم تقريرًا بكل بند يحتاج انتباهك، مع درجة جاهزية واحدة تلخص الموقف.",
      content: (
        <div className="bg-card border border-border rounded-xl p-6 flex flex-col md:flex-row gap-8 items-start">
          <div className="flex-1 space-y-3">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">الإنماء — اتفاقية خدمات سحابية × مسودة 3</span>
              <MonoChip>PDF</MonoChip>
            </div>
            <FindingCard id="FND-031" severity="red" text="السماح بنقل البيانات خارج المملكة" source="SAMA — توطين البيانات" />
            <FindingCard id="FND-032" severity="amber" text="عدم تحديد مدة الاحتفاظ بالبيانات" source="PDPL — المادة 18" />
          </div>
          <div className="bg-background border border-border p-6 rounded-lg flex-shrink-0">
            <ReadinessGauge value={68} />
          </div>
        </div>
      ),
    },
    {
      id: "02", title: "المراقبة المستمرة",
      desc: "سند يتابع مصادر الجهات التنظيمية، وإذا تغيّر شيء يمسّ التزاماتك تعرف قبل أن يسألك أحد.",
      content: (
        <div className="bg-card border border-border rounded-xl p-6 space-y-4">
          <div className="flex items-start gap-4 pb-4 border-b border-border">
            <div className="w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0 shadow-[0_0_6px_rgba(232,106,44,0.5)]" />
            <div className="flex-1">
              <p className="font-medium mb-1">صدر تحديث على إطار الأمن السيبراني من ساما</p>
              <p className="text-[13px] text-muted-foreground mb-3">يؤثر على 3 التزامات في سجلك</p>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex gap-2 flex-wrap">
                  <MonoChip>SAMA-CSF v2</MonoChip>
                  <MonoChip className="text-muted-foreground border-transparent">24 Oct 2025</MonoChip>
                </div>
                <button className="text-[13px] text-primary hover:underline">راجع الأثر</button>
              </div>
            </div>
          </div>
          <div className="flex items-start gap-4 opacity-40">
            <div className="w-2 h-2 rounded-full bg-muted-foreground mt-2 flex-shrink-0" />
            <div><p className="font-medium text-[14px]">تعديل مدد الاستجابة لطلبات أصحاب البيانات — سدايا</p><p className="text-[13px] text-muted-foreground">18 Oct 2025</p></div>
          </div>
        </div>
      ),
    },
    {
      id: "03", title: "سجل الالتزامات التنظيمية",
      desc: "كل التزام في مكان واحد: مصدره، حالته، والمسؤول عنه. لا شيء يضيع في الإيميلات.",
      content: (
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <table className="w-full text-sm text-right">
            <thead className="bg-background/50 border-b border-border text-muted-foreground text-[14px]">
              <tr>
                <th className="p-4 font-medium whitespace-nowrap">المعرّف</th>
                <th className="p-4 font-medium">الالتزام</th>
                <th className="p-4 font-medium whitespace-nowrap">الحالة</th>
                <th className="p-4 font-medium whitespace-nowrap">المصدر</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr>
                <td className="p-4 whitespace-nowrap"><MonoChip>OBL-014</MonoChip></td>
                <td className="p-4 text-[14px] font-medium">إبلاغ ساما عن الحوادث السيبرانية الجسيمة</td>
                <td className="p-4 whitespace-nowrap"><span className="px-3 py-1.5 text-[13px] font-medium border border-primary text-primary rounded-full">ملتزم</span></td>
                <td className="p-4 whitespace-nowrap"><SourceChip text="SAMA-CSF 3.3.15" /></td>
              </tr>
              <tr>
                <td className="p-4 whitespace-nowrap"><MonoChip>OBL-027</MonoChip></td>
                <td className="p-4 text-[14px] font-medium">تعيين مسؤول حماية البيانات الشخصية</td>
                <td className="p-4 whitespace-nowrap"><span className="px-3 py-1.5 text-[13px] font-medium border border-[#C15613] text-[#C15613] rounded-full">قيد المراجعة</span></td>
                <td className="p-4 whitespace-nowrap"><SourceChip text="PDPL — المادة 30" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      ),
    },
    {
      id: "04", title: "واجهة الامتثال المدمجة",
      desc: "فرق المنتجات تستدعي سند من داخل أنظمتها، فيصبح الامتثال جزءًا من الرحلة لا خطوة بعدها.",
      content: (
        <div className="bg-[#14110E] border border-border rounded-xl p-6 font-mono text-[12px] overflow-x-auto">
          <div className="text-primary mb-2">POST /v1/checks</div>
          <div className="mb-4 text-[#E9E4D8]/80">{`{ "document": "murabaha_v3.pdf", "check": "data_residency" }`}</div>
          <div className="text-[#8A93A6] border-t border-white/10 pt-4">
            <pre className="whitespace-pre-wrap">{`{\n  "finding": "بند تخزين خارجي",\n  "source": "SAMA — توطين البيانات",\n  "score": 0.94\n}`}</pre>
          </div>
        </div>
      ),
    },
    {
      id: "05", title: "طبقة الامتثال الشرعي",
      desc: "مراجعة البنود مقابل المعايير الشرعية المعتمدة، لأن الالتزام عندنا لا يقف عند الأنظمة.",
      content: (
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <span className="w-2 h-2 rounded-full bg-[#2F7D5B]" />
            <span className="text-[#2F7D5B] text-sm font-medium">متوافق مع معايير أيوفي</span>
          </div>
          <div className="space-y-4">
            <div className="p-4 bg-background border border-border rounded-lg text-sm text-muted-foreground">
              "غرامة تأخير 2% شهريًا على الدفعات المتأخرة تُضاف إلى إيرادات البنك."
            </div>
            <div className="flex items-start gap-4">
              <div className="w-6 h-6 rounded-full border border-border flex items-center justify-center text-[10px] mt-1 shrink-0">↳</div>
              <div>
                <p className="text-[15px] mb-3">اشتراط عائد الغرامة للبنك لا يتوافق مع المعيار الشرعي لغرامات التأخير، والمعالجة المعتمدة صرفها في وجوه الخير.</p>
                <span className="font-mono text-[13px] text-[#2F7D5B] bg-[#2F7D5B]/10 px-3 py-1 border border-[#2F7D5B]/30 rounded-md">
                  أيوفي — المعيار 8 (المرابحة)
                </span>
              </div>
            </div>
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="min-h-[100dvh] flex flex-col bg-background text-foreground overflow-x-hidden">
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex flex-col">
              <span className="font-bold text-xl leading-none">سند</span>
              <span className="font-mono text-[10px] text-muted-foreground leading-none mt-1">SANAD</span>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <a href="#product" className="text-[15px] text-muted-foreground hover:text-primary transition-colors">المنتج</a>
              <a href="#paths" className="text-[15px] text-muted-foreground hover:text-primary transition-colors">المسارات الخمسة</a>
              <a href="#sovereignty" className="text-[15px] text-muted-foreground hover:text-primary transition-colors">السيادة</a>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <button onClick={() => setLang(lang === "ar" ? "en" : "ar")} className="text-[13px] font-medium text-muted-foreground hover:text-foreground transition-colors">
              {lang === "ar" ? "EN" : "ع"}
            </button>
            <Link href="/login" className="text-[15px] font-medium hover:text-primary transition-colors mr-2">دخول</Link>
            <Button onClick={goLogin}>ابدأ الآن</Button>
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
                امتثال سيادي للقطاع المالي
              </span>
              <h1 className="text-[34px] md:text-[56px] leading-[1.2] font-bold">كل بندٍ وله سَنَد.</h1>
              <p className="text-[17px] text-muted-foreground max-w-[480px]">
                سند يراجع عقودك ويراقب التزاماتك تجاه ساما، يربط كل نتيجة بمرجعها النظامي، ويعمل بالكامل داخل بنيتك التحتية دون أن تغادر بياناتك المنشأة.
              </p>
              <div className="flex flex-wrap items-center gap-4 mt-4">
                <Button onClick={goLogin}>ابدأ الآن</Button>
                <a href="#paths"><Button variant="ghost">شاهد كيف يعمل</Button></a>
              </div>
              <div className="mt-8 text-[13px] font-mono text-muted-foreground">
                استضافة ذاتية كاملة · لا نتائج بدون مصدر
              </div>
            </div>

            <div className="relative bg-card border border-line rounded-2xl overflow-hidden shadow-lg hero-panel" style={{ minHeight: "440px" }}>
              {scanPhase === "scanning" && <div className="scan-beam" />}
              <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-line bg-muted/60">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-line" />
                  <div className="w-2.5 h-2.5 rounded-full bg-line" />
                  <div className="w-2.5 h-2.5 rounded-full bg-line" />
                </div>
                <span className="font-mono text-[11px] text-muted-foreground mx-auto">اتفاقية_خدمات_سحابية_v3.pdf</span>
              </div>
              <div className="p-6 space-y-3">
                <div className="p-4 rounded-xl border border-line bg-muted/20 text-[14px] leading-relaxed text-muted-foreground/40 blur-[2.5px] select-none">
                  المادة الأولى: يلتزم الطرف الأول بتقديم الخدمات المتفق عليها وفقاً لمستويات الخدمة المحددة في الملحق (أ)...
                </div>
                <div className={`relative p-4 rounded-xl border text-[14px] leading-relaxed text-foreground transition-all duration-700 ${
                  scanPhase === "found" ? "border-primary/40 bg-primary/8" : scanPhase === "scanning" ? "border-primary/20 bg-primary/4" : "border-line bg-muted/20"
                }`}>
                  {scanPhase !== "idle" && (
                    <span className="absolute -top-2.5 right-3 bg-card px-2 font-mono text-[11px] text-primary border border-primary/20 rounded">المادة 2</span>
                  )}
                  "يحق للطرف الثاني تخزين ومعالجة بيانات العملاء لدى مزود خدمات سحابية خارج المملكة العربية السعودية متى اقتضت الحاجة التشغيلية ذلك."
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
            <span className="text-[13px] text-muted-foreground whitespace-nowrap">نطاق التغطية التنظيمية:</span>
            <div className="flex items-center gap-4 overflow-x-auto w-full pb-2 md:pb-0">
              {["SAMA", "CMA", "PDPL / سدايا", "NCA ECC", "AAOIFI"].map((reg) => (
                <div key={reg} className="px-4 py-2 border border-border rounded-md font-mono text-[13px] bg-background hover:border-primary transition-colors whitespace-nowrap cursor-default">{reg}</div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24 border-b border-border" id="product">
          <div className="max-w-[1200px] mx-auto px-6">
            <FadeIn><h2 className="text-[34px] font-bold mb-16 text-center">المخالفة أغلى من الامتثال</h2></FadeIn>
            <div className="flex flex-col items-center mb-16">
              <div className="flex items-end gap-2 text-destructive">
                <span className="text-xl pb-2">SAR</span>
                <span className="text-[56px] md:text-[80px] font-bold leading-none tracking-tighter"><AnimatedNumber value={5000000} /></span>
              </div>
              <div className="flex items-center gap-3 mt-4">
                <MonoChip className="text-muted-foreground">الحد الأعلى للغرامة في نظام حماية البيانات الشخصية</MonoChip>
                <SourceChip text="PDPL — المادة 36" />
              </div>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                { val: 40, suffix: "+ ساعة", desc: "متوسط الوقت لمراجعة عقد واحد يدويًا", src: "دراسة داخلية 2025" },
                { val: 120, suffix: "+ تحديثًا", desc: "سنويًا عبر ساما وهيئة السوق المالية وسدايا", src: "رصد سند 2025" },
                { val: 70, suffix: "%", desc: "من الالتزامات تُدار حتى اليوم في جداول إكسل", src: "مقابلات العملاء 2025" },
              ].map((stat, i) => (
                <FadeIn key={stat.desc} delay={i * 100}>
                  <div className="bg-card border border-border p-6 rounded-xl h-full flex flex-col justify-between">
                    <div>
                      <div className="text-[40px] font-bold font-mono tnum text-foreground mb-2 whitespace-nowrap"><AnimatedNumber value={stat.val} suffix={stat.suffix} /></div>
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
            <FadeIn><h2 className="text-[34px] font-bold mb-12">المسارات الخمسة</h2></FadeIn>
            <div className="grid md:grid-cols-[320px_1fr] gap-8 items-start">
              <div className="space-y-1">
                {paths.map((path, i) => (
                  <button key={path.id} onClick={() => setPathIdx(i)}
                    className={`w-full text-right px-5 py-4 rounded-xl transition-all duration-200 border ${pathIdx === i ? "bg-primary/8 border-primary/15" : "border-transparent hover:bg-muted/50"}`}>
                    <div className="flex items-center gap-3">
                      <span className={`font-mono text-[11px] shrink-0 transition-colors ${pathIdx === i ? "text-primary" : "text-muted-foreground"}`}>م-{path.id}</span>
                      <span className={`font-bold text-[15px] transition-colors ${pathIdx === i ? "text-foreground" : "text-muted-foreground"}`}>{path.title}</span>
                    </div>
                    {pathIdx === i && (
                      <>
                        <p className="text-[13px] text-muted-foreground mt-2 pr-7 leading-relaxed text-right">{path.desc}</p>
                        <div className="mt-3 pr-7">
                          <div className="h-0.5 bg-line rounded overflow-hidden">
                            <div key={`bar-${pathIdx}`} className="h-full bg-primary/50 rounded progress-countdown" />
                          </div>
                        </div>
                      </>
                    )}
                  </button>
                ))}
              </div>
              <div key={pathIdx} className="fade-in-slide">{paths[pathIdx]!.content}</div>
            </div>
          </div>
        </section>

        <section className="py-24 border-b border-border">
          <div className="max-w-[1200px] mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-16">
              <FadeIn>
                <h2 className="text-[34px] font-bold mb-4">لا نتائج بدون مصدر</h2>
                <p className="text-muted-foreground">إذا لم يوجد مصدر رسمي للنتيجة، فلن تظهر. هذه قاعدتنا الذهبية.</p>
              </FadeIn>
            </div>
            <div className="max-w-3xl mx-auto flex flex-col items-center">
              {activeStep === 0 ? (
                <div className="bg-card border border-border p-6 rounded-xl w-full text-center">
                  <div className="p-4 bg-background border border-border rounded-lg text-sm text-muted-foreground mb-6">
                    "يحق للطرف الثاني تخزين ومعالجة بيانات العملاء لدى مزود خدمات سحابية خارج المملكة العربية السعودية..."
                  </div>
                  <Button onClick={() => setActiveStep(1)}>اشرح هذه النتيجة</Button>
                </div>
              ) : (
                <div className="w-full space-y-8 relative before:absolute before:top-4 before:bottom-4 before:right-[15px] md:before:right-1/2 before:w-[2px] before:bg-line before:-z-10">
                  <FadeIn delay={0}>
                    <div className="flex flex-col md:flex-row gap-6 md:items-center">
                      <div className="md:w-1/2 md:text-left flex md:justify-end items-center gap-4">
                        <div className="bg-card border border-border p-4 rounded-lg text-sm md:max-w-[280px]">1. البند المشكل</div>
                        <div className="w-8 h-8 rounded-full bg-background border-2 border-primary shrink-0 z-10 flex items-center justify-center text-xs font-bold text-primary">1</div>
                      </div>
                      <div className="md:w-1/2 text-[15px] text-muted-foreground mr-12 md:mr-0">
                        "يحق للطرف الثاني تخزين ومعالجة بيانات العملاء لدى مزود خدمات سحابية خارج المملكة العربية السعودية..."
                      </div>
                    </div>
                  </FadeIn>
                  <FadeIn delay={400}>
                    <div className="flex flex-col md:flex-row gap-6 md:items-center">
                      <div className="md:w-1/2 md:text-left flex md:justify-end items-center gap-4">
                        <div className="bg-card border border-border p-4 rounded-lg md:max-w-[280px]"><SourceChip text="SAMA — متطلبات توطين البيانات" /></div>
                        <div className="w-8 h-8 rounded-full bg-background border-2 border-primary shrink-0 z-10 flex items-center justify-center text-xs font-bold text-primary">2</div>
                      </div>
                      <div className="md:w-1/2 text-[15px] text-muted-foreground mr-12 md:mr-0">المرجع النظامي الذي يستند إليه سند في تقييم البند.</div>
                    </div>
                  </FadeIn>
                  <FadeIn delay={800}>
                    <div className="flex flex-col md:flex-row gap-6 md:items-center">
                      <div className="md:w-1/2 md:text-left flex md:justify-end items-center gap-4">
                        <div className="bg-card border border-border p-4 rounded-lg text-[13px] md:max-w-[280px]">
                          <span className="text-destructive mb-1 block">مخالفة لمتطلبات التوطين</span>
                          البند بصيغته الحالية يتيح نقل بيانات العملاء خارج المملكة دون قيد. التعديل المقترح: حصر التخزين في مراكز بيانات محلية.
                        </div>
                        <div className="w-8 h-8 rounded-full bg-background border-2 border-primary shrink-0 z-10 flex items-center justify-center text-xs font-bold text-primary">3</div>
                      </div>
                      <div className="md:w-1/2 text-[15px] text-muted-foreground mr-12 md:mr-0">التفسير والنتيجة النهائية المرتبطة بالمصدر حصرًا.</div>
                    </div>
                  </FadeIn>
                  <div className="text-center pt-8"><Button variant="ghost" onClick={() => setActiveStep(0)}>إعادة</Button></div>
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
                  <h2 className="text-[34px] font-bold mb-6">بياناتك لا تغادر منشأتك</h2>
                  <p className="text-[17px] text-muted-foreground mb-8">
                    سند يُنشر بالكامل داخل بنيتك التحتية. لا واجهات خارجية، لا بيانات تخرج، ولا اعتماد على مزود سحابي أجنبي. سيادة تامة على الامتثال.
                  </p>
                  <Button variant="ghost" onClick={goLogin}>تعرف على المتطلبات التقنية</Button>
                </FadeIn>
              </div>
              <div className="p-8 border-2 border-dashed border-line rounded-2xl relative">
                <div className="absolute top-0 right-8 -translate-y-1/2 bg-background px-4 font-mono text-[13px] text-muted-foreground">داخل منشأة العميل</div>
                <div className="flex flex-col gap-6">
                  <div className="p-4 bg-card border border-border rounded-lg text-center font-medium">المستندات والعقود</div>
                  <div className="text-center text-muted-foreground">↓</div>
                  <div className="p-4 bg-background border border-border rounded-lg text-center text-sm">قراءة الوثيقة وتفكيك بنودها</div>
                  <div className="text-center text-muted-foreground">↓</div>
                  <div className="p-4 bg-primary/10 border border-primary/30 text-primary rounded-lg text-center font-medium">التحليل والاسترجاع الآمن</div>
                  <div className="text-center text-muted-foreground">↓</div>
                  <div className="flex gap-4">
                    <div className="flex-1 p-4 bg-card border border-border rounded-lg text-center text-sm">النتائج</div>
                    <div className="flex-1 p-4 bg-card border border-border rounded-lg text-center text-sm">سجل الامتثال</div>
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
              <div className="text-[15px] font-medium mt-2">متوسط جاهزية العقود</div>
            </div>
            <div className="hidden md:block w-px h-16 bg-border" />
            <div className="flex flex-col items-center">
              <div className="text-[48px] font-bold font-mono tnum text-foreground mb-1"><AnimatedNumber value={142} prefix="+" /></div>
              <div className="text-[15px] font-medium text-muted-foreground">ساعة عمل موفّرة شهريًا</div>
            </div>
            <div className="hidden md:block w-px h-16 bg-border" />
            <div className="flex flex-col items-center">
              <div className="text-[48px] font-bold font-mono tnum text-primary mb-1"><AnimatedNumber value={100} suffix="%" /></div>
              <div className="text-[15px] font-medium text-muted-foreground">من النتائج موثقة بمصدر</div>
            </div>
          </div>
        </section>

        <section className="py-32 bg-gradient-cta">
          <div className="max-w-[800px] mx-auto px-6 text-center">
            <FadeIn>
              <h2 className="text-[40px] md:text-[56px] font-bold mb-8">كل بندٍ وله سَنَد.</h2>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-4">
                <Button className="w-full sm:w-auto text-lg px-8 py-4" onClick={goLogin}>ابدأ الآن</Button>
                <Link href="/join" className="w-full sm:w-auto"><Button variant="ghost" className="w-full text-lg px-8 py-4">إنشاء حساب</Button></Link>
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
            <p className="text-sm text-muted-foreground mb-6 max-w-[240px]">نظام تشغيل الامتثال السيادي للقطاع المالي السعودي.</p>
            <MonoChip className="text-muted-foreground">صُنع في الرياض</MonoChip>
          </div>
          <div className="grid grid-cols-2 gap-8 md:col-span-2">
            <div>
              <h4 className="font-bold mb-4">المنتج</h4>
              <ul className="space-y-3 text-[15px] text-muted-foreground">
                <li><Link href="/login" className="hover:text-primary transition-colors">مراجعة العقود</Link></li>
                <li><Link href="/login" className="hover:text-primary transition-colors">المراقبة المستمرة</Link></li>
                <li><Link href="/login" className="hover:text-primary transition-colors">سجل الالتزامات</Link></li>
                <li><Link href="/login" className="hover:text-primary transition-colors">فحص الأفكار</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">الشركة</h4>
              <ul className="space-y-3 text-[15px] text-muted-foreground">
                <li><a href="#sovereignty" className="hover:text-primary transition-colors">السيادة والتقنية</a></li>
                <li><a href="#product" className="hover:text-primary transition-colors">المنتج</a></li>
                <li><Link href="/join" className="hover:text-primary transition-colors">إنشاء حساب</Link></li>
                <li><Link href="/login" className="hover:text-primary transition-colors">تسجيل الدخول</Link></li>
              </ul>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
