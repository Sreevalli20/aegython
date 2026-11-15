import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import database  # noqa: E402


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "test.db"
    database.init_db(path)
    return path
