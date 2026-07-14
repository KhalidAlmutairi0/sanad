# SANAD — unified design spec (landing + all app screens)

This is the single source of truth for SANAD's design. It merges the old `design-prompt.md`
(brief) and `screens.md` (screen inventory) into one, and re-skins the **entire product** —
landing page and every app screen — into one visual language: dark, calm, gold-accented, and
built so the design itself says *no finding without a source*.

> Direction note: this SUPERSEDES the earlier light/warm-paper + orange + Thmanyah direction
> in `style-guide.md`. The target is the dark/gold/Kufi language below. Adopting it is a
> redesign pass, not a done state — implement screen by screen against this spec.

Arabic-first, fully RTL (`dir="rtl"` on the root). Bilingual via one content object, Arabic
default, a small EN/ع toggle. No images anywhere — the whole look is type, thin lines, chips,
and drawn SVG lines, so it stays fast.

---

## 1. The one idea that drives everything

**SANAD never shows a finding without a source.** The design must *say* this, everywhere:
every finding card — on the landing page and inside the app — carries a **source chip tied to
it with a thin gold line** that draws itself when the card appears. No finding ever stands
alone. This is the rule of the whole product, not a landing-page flourish.

In the app this maps to the real citation model: a finding's chip resolves to a stored article
version, and the chip shows its **verification tier** (human-verified vs auto-fetched) and, on
tap, the full article text + source URL.

---

## 2. Brand & identity

- Wordmark: **سند** in Noto Kufi Arabic bold, a tiny **SANAD** in mono beneath it.
- Tagline: منصة الامتثال السيادية للقطاع المالي السعودي.
- Personality: an **instrument of record** — authoritative, sourced, calm under scrutiny. A
  legal instrument a bank would buy, not a flashy AI product.

---

## 3. Design tokens (use exactly)

**Color**
| token | value | use |
|---|---|---|
| `--bg` | `#0B0F1A` | page background (very dark navy) |
| `--card` | `#121826` | cards, panels |
| `--line` | `#2A3247` | borders, 1px dividers |
| `--ink` | `#E9E4D8` | text (warm off-white, never pure white) |
| `--muted` | `#8A93A6` | secondary text |
| `--gold` | `#C9A227` | buttons, links, active state, the source-tether line — the ONLY accent |
| `--sharia` | `#2F7D5B` | Sharia badges ONLY, nowhere else |
| severity | red / amber / neutral | finding dots: critical=red, warning=amber, low=muted |

No gradients except one very faint gold glow behind the hero visual. No glass blur, no purple,
no neon, no floating shapes.

**Type**
- Headlines: **Noto Kufi Arabic** bold (Arabic), **IBM Plex Sans** (English).
- Body: **IBM Plex Sans Arabic**, line-height ~1.8 (Arabic needs the room).
- Legal references / IDs (`SAMA-CSF 3.3.5`, `OBL-014`, `FND-031`, `PDPL — المادة ١٨`): **IBM
  Plex Mono** inside a small chip with a thin `--line` border. Legal refs must *look* legal.

**Scale:** hero title 56px desktop / 34px mobile · section titles 34px · body 17px · mono
chips 13px. Max content width 1200px. Card radius 10px, chip radius 6px. 1px `--line` dividers
between sections.

**Motion (light):** sections fade in with a small 24px slide from the **right** (RTL) via
IntersectionObserver. Numbers count up when first in view. Drawn lines animate with SVG
`stroke-dasharray`/`stroke-dashoffset`. No animation library — CSS keyframes + transitions
only. Respect `prefers-reduced-motion`: drop movement, keep fade. No parallax, nothing looping
except the hero scan.

---

## 4. Non-negotiable rules

1. **Source tether everywhere.** Every finding card has a source chip connected by a drawn
   gold line. No unsourced finding is renderable.
2. **RTL correctness.** Logical properties (`margin-inline-start`), reveals slide from the right.
3. **Bilingual, never inline-mixed.** Arabic and English are separate blocks; one content
   object; ع/EN toggle switches all copy.
4. **No images.** Type, lines, chips, drawn SVG only.
5. **Accessibility.** Visible gold focus outlines, ≥44px tap targets, semantic HTML, reduced
   motion respected, works down to 360px.
6. **Green is Sharia-only.** Gold is the only general accent.

---

## 5. Signature components (design first, reuse everywhere)

- **Source chip + tether.** Mono chip with thin border; a gold SVG line draws from the finding
  to the chip on appear. In-app the chip carries the verification tier: a subtle gold dot =
  human-verified; a hollow/outline treatment + tiny label "آلي" = auto-fetched (not yet
  human-reviewed). Tap → popover with full article text + `عرض المصدر`.
- **Finding card.** Severity dot (red/amber/muted) + mono ID + finding text + tethered source
  chip. Optional Accept/Reject in-app.
- **Mono ID chip.** For `FND-031`, `OBL-014`, regulation refs.
- **Readiness gauge.** Half-circle gauge, gold fill, big number 0–100. Computed from reviewed
  findings only.
- **Deal-breaker radar pill.** GO / REVIEW / STOP (green-neutral / amber / red — STOP uses red,
  not Sharia green).
- **Scan / OCR badge.** Small mono badge "مستند ممسوح ضوئياً · قُرئ بالتعرّف الضوئي".

---

## 6. The landing page (`/`)

Single-file React + Tailwind, RTL root, EN/ع toggle, all content in one object (Arabic
default). Motion via CSS keyframes + IntersectionObserver; drawn lines via SVG dashoffset. Only
goal: **book a demo.** Sections in order:

### 6.1 Navbar
Sticky, dark with slight blur, thin bottom border. RTL-start: wordmark سند (Kufi) + tiny mono
SANAD. Links: المنتج · المسارات الخمسة · السيادة · الأسعار. Left: EN/ع toggle + gold button
**اطلب عرضًا تجريبيًا**.

### 6.2 Hero (two columns; stacked on mobile, text first)
- Mono label: `نظام تشغيل الامتثال السعودي`
- Title: **"كل نتيجة بمصدرها. دائمًا."** (EN: "Every finding, with its source. Always.")
- Sub: "سند يراجع عقودك، يراقب التزاماتك التنظيمية، ويربط كل نتيجة بمرجعها الرسمي، داخل بنيتك
  التحتية ودون أن تغادر بياناتك منشأتك."
- Gold **اطلب عرضًا تجريبيًا** + ghost **شاهد كيف يعمل**.
- Mono line: `استضافة ذاتية كاملة · لا نتائج بدون مصدر`

**Visual column (built in code, no screenshot):** a document panel with this clause:
> "يحق للطرف الثاني تخزين ومعالجة بيانات العملاء لدى مزود خدمات سحابية خارج المملكة العربية
> السعودية متى اقتضت الحاجة التشغيلية ذلك."

A thin gold scan line sweeps down (~6s, pause, repeat). At the clause, it highlights and a
finding card slides out, tethered to its source chip:
- `FND-031` (red): "البند يسمح بنقل بيانات العملاء خارج المملكة، ويتعارض مع متطلبات توطين
  البيانات للقطاع المالي." → chip `SAMA — متطلبات توطين البيانات`.
- Then cycle: `FND-032` (amber): "لا يحدد البند مدة الاحتفاظ بالبيانات بعد انتهاء العلاقة
  التعاقدية." → chip `PDPL — المادة ١٨`. Then a third, loop.

### 6.3 Regulatory coverage strip
Thin band "نطاق التغطية التنظيمية" with five bordered mono chips: SAMA · CMA · PDPL / سدايا ·
NCA ECC · AAOIFI. Gold underline slides in on hover. No logos.

### 6.4 Cost of a violation
Title "المخالفة أغلى من الامتثال". Big number counting to **5,000,000 ريال**, mono label "الحد
الأعلى للغرامة في نظام حماية البيانات الشخصية", source chip `PDPL — المادة ٣٦`. Three stat
cards, each with a tethered chip:
- "٤٠+ ساعة" — متوسط الوقت لمراجعة عقد واحد يدويًا · `دراسة داخلية ٢٠٢٥`
- "١٢٠+ تحديثًا تنظيميًا" — سنويًا عبر ساما وهيئة السوق المالية وسدايا · `رصد سند ٢٠٢٥`
- "٧٠٪" — من الالتزامات تُدار حتى اليوم في جداول إكسل · `مقابلات العملاء ٢٠٢٥`

### 6.5 The five tracks (المسارات الخمسة)
A numbered register: mono م-٠١ … م-٠٥, thin lines between rows. Desktop: hover a row to expand
(description + example card). Mobile: all expanded. Examples matter — they make it real:

- **م-٠١ مراجعة العقود** — "ارفع العقد، واستلم تقريرًا بكل بند يحتاج انتباهك، مع درجة جاهزية
  واحدة تلخص الموقف." Example: report header "اتفاقية خدمات سحابية — مسودة ٣" · درجة الجاهزية:
  ٦٨/١٠٠ · two finding rows reusing `FND-031`/`FND-032` with tethered chips.
- **م-٠٢ المراقبة المستمرة** — "سند يتابع مصادر الجهات التنظيمية، وإذا تغيّر شيء يمسّ التزاماتك
  تعرف قبل أن يسألك أحد." Example: feed item "صدر تحديث على إطار الأمن السيبراني من ساما —
  يؤثر على ٣ التزامات في سجلك" + date + mono chip `SAMA-CSF v2 — تحديث` + gold link "راجع الأثر".
- **م-٠٣ سجل الالتزامات التنظيمية** — "كل التزام في مكان واحد: مصدره، حالته، والمسؤول عنه. لا
  شيء يضيع في الإيميلات." Example: two table rows —
  `OBL-014` · إبلاغ ساما عن الحوادث السيبرانية الجسيمة ضمن المدة المحددة · المسؤول: أمن
  المعلومات · الحالة: ملتزم (gold outline, not Sharia green) · `SAMA-CSF 3.3.15 — إدارة الحوادث`.
  `OBL-027` · تعيين مسؤول حماية البيانات الشخصية · المسؤول: الالتزام · الحالة: قيد المعالجة ·
  `PDPL — المادة ٣٠`.
- **م-٠٤ واجهة الامتثال المدمجة** — "فرق المنتجات تستدعي سند من داخل أنظمتها، فيصبح الامتثال
  جزءًا من الرحلة لا خطوة بعدها." Example: mono code block —
  ```
  POST /v1/checks
  { "document": "murabaha_v3.pdf", "check": "data_residency" }

  { "finding": "بند تخزين خارجي", "source": "SAMA — توطين البيانات", "score": 0.94 }
  ```
- **م-٠٥ طبقة الامتثال الشرعي** — "مراجعة البنود مقابل المعايير الشرعية المعتمدة، لأن الالتزام
  عندنا لا يقف عند الأنظمة." Green badge "متوافق مع معايير أيوفي". Example: clause "غرامة تأخير
  ٢٪ شهريًا على الدفعات المتأخرة تُضاف إلى إيرادات البنك." → finding "اشتراط عائد الغرامة للبنك
  لا يتوافق مع المعيار الشرعي لغرامات التأخير، والمعالجة المعتمدة صرفها في وجوه الخير." → green
  chip `أيوفي — المعيار ٨ (المرابحة)`.

### 6.6 No unsourced findings, explained
Title "لا نتائج بدون مصدر". A finding card with gold button "اشرح هذه النتيجة" → expands three
tethered steps: (1) البند: the data-residency clause; (2) المرجع: chip `SAMA — متطلبات توطين
البيانات`; (3) التفسير: "البند بصيغته الحالية يتيح نقل بيانات عملاء القطاع المالي خارج المملكة
دون قيد، بينما تشترط التعليمات بقاء هذه البيانات داخل المملكة. التعديل المقترح: حصر التخزين
والمعالجة في مراكز بيانات داخل المملكة." Caption: "إذا لم يوجد مصدر رسمي للنتيجة، فلن تظهر."

### 6.7 Sovereignty / self-hosted
Title "بياناتك لا تغادر منشأتك". Text: "سند يُنشر بالكامل داخل بنية البنك التحتية. لا واجهات
خارجية، لا بيانات تخرج، ولا اعتماد على مزود سحابي أجنبي. الجهة تملك النسخة وتشغلها بنفسها."
Diagram: bordered chips connected by thin lines that draw on scroll — المستندات ← استخراج النص
← التحليل والاسترجاع ← النتائج والسجل — inside a dashed border labeled mono "داخل منشأة العميل".
No cloud icons.

### 6.8 Numbers band
Three numbers: درجة جاهزية العقد as a half-circle gauge filling to **87**; ريال الغرامات
المتجنّبة counting up; نسبة النتائج الموثقة بمصدر counting to **١٠٠٪** with a small gold flash on
landing (it's literally the promise).

### 6.9 Final CTA
Centered, spacious. Kufi title "جاهز ترى الامتثال بمصدر؟" Gold **اطلب عرضًا تجريبيًا** + ghost
**حمّل الملف التعريفي**. One email field, mono placeholder `you@bank.sa`, button `onClick` (no
`<form>`).

### 6.10 Footer
Thin top line, three columns: wordmark + "منصة الامتثال السيادية للقطاع المالي السعودي" · links
· mono line `صُنع في الرياض`.

### Wiring "Try it now" / "اطلب عرضًا تجريبيًا"
The app is invite-only (no public demo). The landing's primary in-product CTA ("جرّب الآن" /
"Try it now" if present) routes to **`/login`** (existing users flow to `/contracts`; new users
use `/join` with an invite code). Demo-request CTAs open the email capture in 6.9.

---

## 7. The app screens (re-skinned to the language above)

All require sign-in except login/join. Reached via the top nav (العقود · فحص الفكرة · الالتزامات
· الرصد · الأدلة · الإدارة). Every screen inherits: dark tokens, Kufi/Plex/Mono, the source
tether, RTL, ع/EN, light-motion reveals, the same components.

### 7.1 `/login` — Sign in
Centered card on `--bg`. Wordmark سند. Fields: البريد الإلكتروني, كلمة المرور. Gold **دخول**.
Link "إنشاء حساب بدعوة" → `/join`. ع/EN toggle. Error line in red (mono-free). Rate-limited
(5/min) — on 429 show "محاولات كثيرة، جرّب بعد شوي".

### 7.2 `/join` — Create account with an invite
Same card language. Fields: رمز الدعوة (mono), البريد الإلكتروني, كلمة المرور. Gold **إنشاء
الحساب**. On success → `/contracts`. Invalid/used code → red inline error.

### 7.3 `/contracts` — Contracts list + upload (app home)
Top: title العقود + gold **رفع عقد**. List rows (thin `--line` dividers): contract title ·
status pill · readiness number (mono). Empty state: calm line "ما عندك عقود حتى الآن. ارفع عقد
وابدأ المراجعة." Upload starts the pipeline (sanitize → OCR if scanned → clauses → retrieve →
findings); rows show live status (مرفوع → جاري الفحص → قيد المراجعة → تمت المراجعة).

### 7.4 `/contracts/{id}` — Review workspace (the hero screen)
Header: contract title, the **Readiness gauge** (0–100, reviewed findings only), the
**Deal-breaker radar** pill (GO/REVIEW/STOP), and an **OCR badge** if the upload was scanned.
Two panes:
- **Contract text** (right): clauses, ordinal-numbered, RTL.
- **Findings** (left): a **finding card** per finding — severity dot, title, the **citation
  chip tethered by the gold line**, violation-cost estimate, Accept/Reject. Chip shows the
  verification tier (human-verified vs "آلي" auto-fetched) and opens the full article + source.
Empty: "ما فيه ملاحظات على هذا العقد."

### 7.5 `/idea-check` — Check an idea before building
Prompt textarea "اكتب فكرتك بكلام واضح" + gold **أرسل للفحص**. Result: a cited compliance report
(applicable regulations, requirements, risks, open questions), every claim carrying a tethered
source chip. Same source rule as findings. Empty/loading/generated states.

### 7.6 `/evidence` — Evidence cache (search the law)
Search field "ابحث في الأنظمة والمواد" + gold **بحث**. Results: article cards — regulation +
article ref (mono chip), snippet, match score. This is the 1,600+ article corpus the findings
cite; results ranked by the reranker. Empty: "اكتب كلمة للبحث."

### 7.7 `/register` — Obligation register
Table styled like the landing's م-٠٣ example: `OBL-xxx` (mono) · obligation · owner · status
(gold outline pills, not Sharia green) · tethered source chip. Filters by status. Empty: "ما
فيه التزامات مسجّلة حتى الآن."

### 7.8 `/monitoring` — Regulatory monitoring
Feed styled like م-٠٢: change items — regulation + change type + impact summary + date + mono
chip. A reviewer verifies a change (gold **تحقّق**), appending a new immutable article version.
Empty: "ما فيه تغييرات مرصودة."

### 7.9 `/admin` — Admin (admins only)
Panels on `--card`:
- **قائمة السماح للوكيل** (research-agent egress allowlist) — textarea of gov domains.
- **الدعوات** — generate invite (role + optional email) → mono code chip with copy; list.
- **توجيه التحليل** — two editable analyst-guidance boxes (contracts / idea), with the locked
  machine-contract shown read-only.
- **المخزن النظامي** (corpus panel) — table: regulation (Arabic) · authority · article count
  (mono) + "آلي" tag for auto-fetched · last-checked date (freshness).
- **سجل التدقيق** — audit rows: actor · action · verdict (allowed=gold, denied=red).

---

## 8. States, accessibility, deliverables

- **States:** every screen defines empty / loading / error. Loading = calm skeletons on
  `--card`, no spinners-as-decoration. Errors = one red line, actionable.
- **Accessibility:** visible gold focus rings, ≥44px targets, semantic HTML, reduced-motion
  fade-only, keyboard-usable popovers, 360px floor.
- **Deliverables for a redesign pass:** each screen in dark (default); the six signature
  components built once and reused; the source-tether working on every finding; the landing as
  a single-file React page; app screens implemented against the current data (citation tiers,
  OCR badge, readiness, radar, corpus, invites) so nothing regresses.
