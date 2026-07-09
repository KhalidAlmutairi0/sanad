"""extract.py behaviour (no bwrap needed). Exit codes: 0 ok, 2 unsupported, 3 error, 4 empty."""
from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("extract_mod", HERE / "extract.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["extract_mod"] = m
    spec.loader.exec_module(m)
    return m


def test_txt_extracts_and_strips_control_chars(tmp_path, capsys) -> None:
    mod = _load()
    p = tmp_path / "c.txt"
    p.write_bytes("Article 1: data\x00 clean.\r\nالبند الثاني.\n".encode("utf-8"))
    rc = mod.main(["extract.py", str(p)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "\x00" not in out and "\r" not in out
    assert "البند الثاني" in out


def test_empty_result_is_rejected(tmp_path) -> None:
    mod = _load()
    p = tmp_path / "e.txt"
    p.write_text("   \n\n  ", encoding="utf-8")
    assert mod.main(["extract.py", str(p)]) == 4  # empty_result


def test_unsupported_type_is_rejected(tmp_path) -> None:
    mod = _load()
    p = tmp_path / "x.xyz"
    p.write_text("hello", encoding="utf-8")
    assert mod.main(["extract.py", str(p)]) == 2  # unsupported_file_type
