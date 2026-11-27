import json
from pathlib import Path

from .hexgrid import Bbox

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: Path | None = None) -> dict:
    cfg = json.loads((path or ROOT / "config" / "region.json").read_text())
    cfg["bbox"] = Bbox(**cfg["bbox"])
    return cfg
