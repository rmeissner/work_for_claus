import shutil
from pathlib import Path

import pytest
from stlkit import load_script

MODELS = Path(__file__).resolve().parents[3] / "models"
SCRIPTS = sorted(MODELS.glob("*/generate.py"))


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.parent.name)
def test_committed_stls_are_up_to_date(tmp_path, script):
    copy = shutil.copytree(script.parent, tmp_path / script.parent.name)
    load_script(copy / "generate.py").main()
    for stl in sorted(script.parent.glob("*.stl")):
        assert (copy / stl.name).read_bytes() == stl.read_bytes(), stl.name
