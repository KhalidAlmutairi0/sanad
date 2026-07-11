# SANAD — Screen Design Prompt

Paste this into your design tool (v0 / Lovable / Figma Make / a designer brief). It is
self-contained: brand, tokens, rules, and every screen with real content.

---

## 0. Role & goal

You are a senior product designer designing **SANAD (سَنَد)**, a sovereign AI compliance
platform for Saudi banks, government entities, and enterprises. Design a cohesive set of
**Arabic-first, fully RTL** screens that feel like an **instrument of record**: authoritative,
sourced, and calm under scrutiny. Not a flashy AI product. A legal instrument.

Deliver every screen in **light (default) and dark**, desktop-first (1280–1920), gracefully
usable down to tablet. Use **real content** provided below, never lorem.

## 1. The one idea that drives the whole design

**Zero Unsourced Findings.** Every claim the product makes is tied, visibly, to the exact
legal article it cites. The **citation chip** is the signature element and must be the most
memorable, most polished thing in the UI. If a finding has no chip, that is a design bug.

## 2. Brand & identity

- Arabic wordmark **سَنَد** is the primary identity; Latin **SANAD** is secondary/smaller.
- Voice: plain, precise, sourced. Say "This clause conflicts with PDPL Article 29", never
  "Potential issue detected." Empty states direct the next action.
- Feeling: official paper, generous white space, hairline rules, near-zero shadow. Orange is
  the single accent, used only for **source and action moments** (citations, primary buttons).

## 3. Design tokens (use exactly)

**Light (default)**
```
ink       #14110E   (primary text, warm near-black)
paper     #FBFAF7   (page background, warm off-white)
surface   #FFFFFF   (cards, panels)
line      #E6E1D8   (hairline borders/dividers)
muted     #6B655C   (secondary text, captions)
orange    #E86A2C   (THE accent: citations, primary actions)
orange-ink#B44E18   (orange text on light, hover)
orange-bg #FCEEE4   (citation highlight background)
critical  #B3261E   high #C15613   medium #8A6D1F   low #5A6B4F   ok/cleared #3F6B4E
```
**Dark**
```
ink #F5F1EA   paper #0E0C0A   surface #17130F   line #2A2420   muted #A29A8D
orange #F2803E   orange-ink #F8A66E   orange-bg #2A1B10
```
All text/background pairs meet WCAG AA (4.5:1 body, 3:1 large). Orange is never body text on
paper, only accent/borders/interactive.

**Type**
- One family for Arabic + Latin: **IBM Plex Sans Arabic**. Weights 300/400/500/600/700.
- Numbers (scores, fines, dates): **IBM Plex Mono**, tabular-nums, so figures read as measured
  values.
- Scale (rem, 16px base): display 2.25/600/-0.01em · h1 1.75/600 · h2 1.375/600 · h3 1.125/500
  · body 1.0/400/line-height 1.7 · label 0.875/500 · caption 0.75/300 · mono-num 1.0/500.

**Layout**
- Spacing scale only: 4, 8, 12, 16, 24, 32, 48, 64. Section padding 48/64; card padding 24;
  chip padding 4×12.
- Radius: 8px cards, 6px chips/buttons. Shadows: none except one subtle shadow on popovers/
  modals. Rely on hairlines and surface color.
- Reading views max ~820px wide. The review workspace is **two-pane** (contract | findings).

## 4. Non-negotiable rules

1. **RTL first.** `dir="rtl"`, `lang="ar"`. Use logical properties only (margin-inline-start,
   padding-inline, border-inline-end). Never left/right. Mirror directional icons.
2. **Stacked bilingual, never inline-mixed.** When a block shows both languages, render a full
   Arabic block then a full English block, each in its own direction. Never put Arabic and
   Latin on the same line.
3. **No em dashes** anywhere in copy (Arabic or English). Use a period or comma.
4. Copy tone is natural Saudi professional, not textbook Arabic.

## 5. Signature components (design these first, reuse everywhere)

- **Citation chip** — small orange-outlined pill: `◆ PDPL Article 29`. On hover/tap it opens a
  calm popover (the one allowed shadow) showing: the exact stored **article text** (Arabic,
  generous 1.9 line-height), the **source** link, and the **version/effective date** in mono.
  This is the "this is proven" moment. Make it feel authoritative and quietly satisfying.
- **Severity badge** — a small filled dot + label using severity tokens (حرجة/عالية/متوسطة/
  منخفضة). Never a full red banner; the tool stays calm even when flagging critical issues.
- **Readiness Score dial** — one large mono numeral 0–100, a thin arc in a severity-derived
  color, and the label "الملاحظات المراجَعة فقط / reviewed findings only" beneath. Calm, not
  gauge-y. Animate a count-up + arc draw on load.
- **Deal-breaker Radar** — a three-state pill: **جاهز / للمراجعة / توقف** (GO / REVIEW / STOP)
  using ok / high / critical tokens.
- **Finding card** — severity badge top-start, citation chip top-end, title (stacked
  bilingual), explanation, violation-cost (mono), and Accept/Reject actions. Accept = ok-token
  filled button; Reject = hairline outline.
- **Status pill** — contract status (مرفوع/قيد المراجعة/تمت المراجعة/فشل) in muted or severity
  tone.

## 6. Screens

### 6.1 Login
- Centered, max 360px. Wordmark **سَنَد** (display), eyebrow "منصة الامتثال السيادية" in
  orange-ink. Email + Password fields (LTR inputs), primary orange "دخول" button. A subtle
  language toggle (EN/ع). Error state: one calm line "بيانات الدخول غير صحيحة" in critical.
- Whole page reads as calm official paper. No illustration, no gradient hero.

### 6.2 Contracts list
- Top bar: wordmark, nav (العقود · فحص الفكرة), theme + language toggles, خروج.
- Heading "العقود". An upload card: contract name field + file picker (PDF/DOCX/TXT) + orange
  "رفع عقد" button.
- List of contracts as hairline-divided rows: title, **status pill**, and readiness score
  (mono, or "—" if not computed). Row hover reveals it is clickable.
- Empty state: "ما عندك عقود حتى الآن. ارفع عقد وابدأ المراجعة."
- Real rows:
  - "اتفاقية معالجة بيانات مع مزود سحابي" · قيد المراجعة · 60
  - "عقد عمل دوام كامل" · تمت المراجعة · 82

### 6.3 Contract review workspace (the hero screen)
- Header row: contract title (h1); on the opposite side a cluster with the **Deal-breaker
  Radar** pill and the **Readiness dial**.
- Below, a **two-pane** area:
  - **Contract pane** ("نص العقد"): the clauses, numbered (mono ordinals ١، ٢، ٣). Clauses that
    have findings get a soft orange-bg highlight.
  - **Findings pane** ("الملاحظات"): a column of **finding cards**.
- Panes scroll independently. Generous margins, hairline divider between panes.
- Real finding to render:
  - Severity: حرجة (critical). Chip: `◆ PDPL Article 29`.
    Title AR: "نقل بيانات العملاء خارج المملكة بدون ضوابط".
    Title EN: "Sending customer data outside the Kingdom without controls".
    Explanation: "البند يسمح بنقل بيانات العملاء لخوادم خارج المملكة بدون التأكد من مستوى
    الحماية، وهذا يخالف اللي تشترطه المادة 29."
    Violation cost (mono): "غرامة تصل إلى 3,000,000 ريال".
    Actions: قبول / رفض. Show one card already "مقبولة" (accepted) state.
- Clicking the chip opens the **citation popover** with PDPL Article 29 full text + source +
  "نفاذ 2023-09-14".

### 6.4 Idea Check (PM feature)
- Reading-width single column. Heading "افحص الفكرة قبل ما تبنيها".
- A textarea "اكتب فكرتك بكلام واضح" + orange "أرسل للفحص" button.
- Result: a **cited report** rendered stacked bilingual (full Arabic report block, then full
  English block), sections: الأنظمة المنطبقة / المتطلبات / المخاطر / أسئلة مفتوحة. Below it, a
  row of citation chips (`◆ PDPL 29`, `◆ PDPL 5`) linking to sources.
- Empty state: "أرسل فكرة وبتوصلك مراجعة امتثال مع مصادرها."

### 6.5 (Optional, if you want depth) Evidence article view
- A single stored article: code + article ref, full Arabic text, English translation block,
  source URL, content hash (mono), fetched/effective dates. Reads like an official record.

## 7. States & motion

- Every async view has loading / empty / error states. Errors state what happened and the fix,
  in the interface's voice, no apology.
- Motion is restrained and purposeful: dial count-up + arc draw on first view, citation popover
  eases open, scroll-reveal for sections. Respect prefers-reduced-motion (no motion).
- Interactive things look interactive (hover on chips, rows, buttons). Visible keyboard focus.

## 8. Accessibility

- AA contrast in both themes. Full keyboard operability, logical focus order in RTL. Screen
  reader announces findings, chips, and score meaningfully in Arabic. Icons that imply
  direction mirror in RTL. Zoom to 200% holds.

## 9. Deliverables

Login, Contracts list, Review workspace (with the citation popover open in one variant),
Idea Check, and one Evidence article view. Each in **light and dark**. Show the signature
citation chip and its popover prominently. Keep everything on the token system above.
