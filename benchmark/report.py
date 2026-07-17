"""Turn a benchmark result into a slide-ready markdown block. Test-set size + composition
(real vs synthetic) go on the slide by design — a bank's risk team will ask."""
from __future__ import annotations


def slide(feature: str, dataset: str, lines: list[str], *, notes: list[str] | None = None) -> str:
    out = [f"### {feature}", f"- Tested on: {dataset}"]
    out += [f"- {ln}" for ln in lines]
    for n in notes or []:
        out.append(f"- ⚠ {n}")
    return "\n".join(out)


def pending_slide(feature: str, reason: str) -> str:
    return (f"### {feature}\n"
            f"- **Not yet benchmarked — no independent ground truth.**\n"
            f"- Needed: {reason}\n"
            f"- (An honest gap is safer for the pitch than a fabricated number.)")
