"""Upload sanitizer extraction — runs INSIDE the bubblewrap sandbox (no network).

Input: a raw file (pdf/docx/txt) bind-mounted read-only at a fixed path.
Output: plain UTF-8/NFC text on stdout. Nothing else survives — no macros, scripts,
embedded objects, or formatting. Prompt-injection strings in the text are NOT removed here
(impossible to do reliably); they are neutralized at the prompt layer by untrusted-data
tagging. This process has no network and cannot import anything network-bound.

Exit codes: 0 ok; 2 unsupported type; 3 extraction error; 4 empty result.
"""
from __future__ import annotations

import pathlib
import sys
import unicodedata

SUPPORTED = {".pdf", ".docx", ".txt"}


def _clean(text: str) -> str:
    # NFC normalize; strip control chars except tab/newline; collapse trailing whitespace.
    text = unicodedata.normalize("NFC", text)
    out = []
    for ch in text:
        if ch in ("\t", "\n"):
            out.append(ch)
            continue
        if unicodedata.category(ch).startswith("C"):
            continue  # drop control / format chars (defensive)
        out.append(ch)
    lines = [ln.rstrip() for ln in "".join(out).splitlines()]
    return "\n".join(lines).strip()


def _extract_pdf(path: pathlib.Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _extract_docx(path: pathlib.Path) -> str:
    from docx import Document

    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append("\t".join(cell.text for cell in row.cells))
    return "\n".join(parts)


def _extract_txt(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: extract.py <input_path>\n")
        return 3
    path = pathlib.Path(argv[1])
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        sys.stderr.write(f"unsupported_file_type: {suffix}\n")
        return 2
    try:
        if suffix == ".pdf":
            raw = _extract_pdf(path)
        elif suffix == ".docx":
            raw = _extract_docx(path)
        else:
            raw = _extract_txt(path)
    except Exception as exc:  # noqa: BLE001 — any parser failure is an extraction error
        sys.stderr.write(f"extraction_error: {type(exc).__name__}\n")
        return 3

    text = _clean(raw)
    if not text:
        sys.stderr.write("empty_result\n")
        return 4
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
