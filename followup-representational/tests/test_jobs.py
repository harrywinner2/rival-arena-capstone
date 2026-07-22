import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from l4_arena.jobs import require_job_id


def test_job_id_validation():
    assert require_job_id("faithful-qwen7b-001") == "faithful-qwen7b-001"
    for value in ("", "../bad", "has space", "x" * 97):
        with pytest.raises(ValueError):
            require_job_id(value)
