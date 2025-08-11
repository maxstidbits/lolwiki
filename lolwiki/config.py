from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Constants
WIKI_BASE = "https://wiki.leagueoflegends.com/en-us/"
ITEMS_INDEX_PATH = "List of items"

# 3.5 days = 302_400 seconds
HALF_WEEK_SECONDS = 3 * 24 * 60 * 60 + 12 * 60 * 60


@dataclass
class TTLCacheConfig:
    path: Path = Path(
        os.environ.get("LOLWIKI_CACHE", "~/.cache/lolwiki/cache.json")
    ).expanduser()
    ttl_seconds: int = int(os.environ.get("LOLWIKI_TTL", HALF_WEEK_SECONDS))