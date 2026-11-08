from pathlib import Path

from stlkit import load_script


def test_load_script_keeps_same_named_files_apart(tmp_path: Path) -> None:
    modules = []
    for slug in ("a", "b"):
        folder = tmp_path / slug
        folder.mkdir()
        (folder / "generate.py").write_text(f"SLUG = {slug!r}\n")
        modules.append(load_script(folder / "generate.py"))
    assert [m.SLUG for m in modules] == ["a", "b"]
