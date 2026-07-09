"""Upload type-sniffing (test-plan §3c SEC-20/25): type is decided from CONTENT, not the
client-supplied name."""
from __future__ import annotations

from app.services.sanitize import detect_extension


def test_pdf_magic_detected() -> None:
    assert detect_extension(b"%PDF-1.7\n...", "/tmp/x") == "pdf"


def test_executable_renamed_pdf_is_rejected() -> None:
    # An ELF/PE binary is neither PDF magic, nor a zip, nor valid UTF-8 text -> unsupported.
    assert detect_extension(b"\x7fELF\x02\x01\x01\x00" + bytes(range(200, 240)), "/tmp/x.pdf") is None


def test_plain_text_detected() -> None:
    assert detect_extension("عقد: بند أول".encode("utf-8"), "/tmp/x") == "txt"


def test_non_docx_zip_is_rejected(tmp_path) -> None:
    import zipfile

    p = tmp_path / "a.zip"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("notword.txt", "hi")
    assert detect_extension(p.read_bytes()[:8], str(p)) is None
