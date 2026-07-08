# style-guide.md — SANAD design system

## Design thesis

SANAD is a legal/compliance instrument for Saudi banks and government. The feeling must be: **authoritative, sourced, calm under scrutiny.** Not a flashy AI product — an instrument of record. The signature idea is **the citation**: every claim visibly tied to its source. The UI should make "this is proven" its most memorable quality.

Arabic-first. The Arabic wordmark سَنَد is the primary identity; the Latin "SANAD" is secondary.

## Color tokens

Light theme is default (this is a document-review tool used all day; light reduces fatigue and reads as "official paper"). Orange is the single accent — used with restraint, only for source/action moments.

```
--sanad-ink:        #14110E   /* near-black warm, primary text */
--sanad-paper:      #FBFAF7   /* warm off-white background */
--sanad-surface:    #FFFFFF   /* cards, panels */
--sanad-line:       #E6E1D8   /* hairline borders, dividers */
--sanad-muted:      #6B655C   /* secondary text, captions */

--sanad-orange:     #E86A2C   /* THE accent: citations, primary actions */
--sanad-orange-ink: #B44E18   /* orange text on light, hover */
--sanad-orange-bg:  #FCEEE4   /* citation highlight background */

/* Severity (findings) — muted, never alarming for its own sake */
--sanad-critical:   #B3261E
--sanad-high:       #C15613
--sanad-medium:     #8A6D1F
--sanad-low:        #5A6B4F
--sanad-ok:         #3F6B4E   /* readiness / cleared */
```

### Dark theme (mode: `.dark`)
```
--sanad-ink:        #F5F1EA
--sanad-paper:      #0E0C0A   /* black, warm */
--sanad-surface:    #17130F
--sanad-line:       #2A2420
--sanad-muted:      #A29A8D
--sanad-orange:     #F2803E   /* slightly lifted for contrast on black */
--sanad-orange-ink: #F8A66E
--sanad-orange-bg:  #2A1B10
```

Contrast: all text/background pairs meet WCAG AA (4.5:1 body, 3:1 large). Orange is never used for body text on paper — only accent, borders, and interactive elements.

## Typography

- **Primary (Arabic + Latin UI, body, and display):** **IBM Plex Sans Arabic.** One family across both scripts keeps bilingual layouts visually unified — critical when Arabic and English stack. Weights: 300 (captions), 400 (body), 500 (labels/UI), 600 (headings), 700 (wordmark, key numbers).
- **Numeric / data (scores, fine amounts, dates):** IBM Plex Mono for tabular figures — makes the Readiness Score and Violation Cost read as measured values, not marketing.

### Type scale (rem, 16px base)
```
display   2.25   / 600  / -0.01em   (page titles, score hero)
h1        1.75   / 600
h2        1.375  / 600
h3        1.125  / 500
body      1.0    / 400  / line-height 1.7 (Arabic needs generous leading)
label     0.875  / 500
caption   0.75   / 300
mono-num  1.0    / 500  (Plex Mono, tabular-nums)
```

## RTL / bilingual rules

- Default `dir="rtl"`, `lang="ar"`. English content blocks switch to `dir="ltr"` at the block level.
- Use logical properties only: `padding-inline`, `margin-inline-start`, `border-inline-end`. Never `left`/`right`.
- **Stacked bilingual, never inline-mixed:** a bilingual document renders a full Arabic block, then a full English block, each in its own direction. Never place Arabic and Latin on the same line.
- Icons that imply direction (arrows, chevrons) mirror in RTL.
- No em dashes anywhere in product copy (Arabic or English).

## Components — signature treatments

- **Citation chip:** the core element. Small orange-outlined chip attached to every finding; on hover/tap it opens a popover showing the exact stored article text + source + version date. This is the "Zero Unsourced Findings" promise made visible. A finding with no chip is a UI impossibility.
- **Readiness Score dial:** single large mono numeral 0–100, thin arc in severity color, label "reviewed findings only" beneath. Calm, not gauge-y.
- **Severity badge:** small filled dot + label, using severity tokens. Never a full red banner — this tool stays calm even when flagging critical issues.
- **Deal-breaker Radar:** three-state pill GO / STOP / REVIEW, using ok / critical / high tokens.

## Layout

- Spacing scale (px): 4, 8, 12, 16, 24, 32, 48, 64 — nothing off-scale. Section padding 48/64; card padding 24; chip padding 4×12.
- Generous margins, hairline dividers (`--sanad-line`), lots of white space — reads as official paper, not dense dashboard.
- Border-radius: 8px on cards, 6px on chips/buttons. Soft but not playful.
- Shadows: almost none; rely on hairlines and surface color. One subtle shadow allowed on popovers/modals.
- Max content width for reading views ~ 820px; review workspace is two-pane (contract | findings).

## Voice (UI copy)

- Plain, precise, sourced. "This clause conflicts with PDPL Article 29" not "Potential issue detected."
- Empty states direct action: "No contracts yet. Upload one to begin review."
- Errors state what happened and the fix, in the interface's voice, no apology.
- Every action keeps its verb through the flow: "Review" → "Reviewed"; "Verify source" → "Verified".
