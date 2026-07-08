export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-reading flex-col justify-center px-6 py-16">
      <p className="text-label text-orange-ink">منصة الامتثال السيادية</p>
      <h1 className="mt-4 text-display font-bold">سَنَد</h1>
      <p className="mt-6 max-w-prose text-body text-ink">
        يكشف المخالفة التنظيمية أو الشرعية في العقد، مع مصدرها النظامي الدقيق، قبل التوقيع.
        كل ملاحظة مرتبطة بنصها المصدري. لا مصدر، لا ادعاء.
      </p>
      <div dir="ltr" className="mt-8 border-t border-line pt-6">
        <p className="text-label text-muted">Sovereign AI compliance for Saudi organizations.</p>
        <p className="mt-2 text-body text-muted">
          Every finding is bound to the exact article it cites. Zero Unsourced Findings.
        </p>
      </div>
      <nav className="mt-12 flex gap-4">
        <a
          href="/contracts"
          className="rounded-chip bg-orange px-6 py-3 text-label text-white"
        >
          العقود
        </a>
        <a
          href="/idea-check"
          className="rounded-chip border border-line px-6 py-3 text-label text-ink"
        >
          فحص الفكرة
        </a>
      </nav>
    </main>
  );
}
