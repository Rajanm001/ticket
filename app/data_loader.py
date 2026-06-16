from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings


DATA_DIR = Path(settings.data_dir)


def load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_tickets() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "tickets.json")


def load_faqs() -> list[dict[str, Any]]:
    return load_json(DATA_DIR / "faq.json")


