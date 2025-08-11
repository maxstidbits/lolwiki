from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

from .config import TTLCacheConfig


class _DiskCache:
    def __init__(self, cfg: TTLCacheConfig):
        self.cfg = cfg
        self.cfg.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.cfg.path.exists():
            self._write({})

    def _read(self) -> Dict[str, Any]:
        try:
            with open(self.cfg.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write(self, data: Dict[str, Any]) -> None:
        tmp = self.cfg.path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        tmp.replace(self.cfg.path)

    def get(self, key: str) -> Optional[str]:
        data = self._read()
        entry = data.get(key)
        if not entry:
            return None
        ts = entry.get("ts", 0)
        if time.time() - ts > self.cfg.ttl_seconds:
            return None
        return entry.get("html")

    def set(self, key: str, html: str) -> None:
        data = self._read()
        data[key] = {"ts": time.time(), "html": html}
        self._write(data)