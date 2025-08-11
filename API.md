# lolwiki API Documentation

This document describes the **public API** for the asynchronous Python client `LolWikiClient` and configuration options.

---

## `LolWikiClient`

Async client for scraping the official [League of Legends Wiki](https://wiki.leagueoflegends.com) for **champion** and **item** data, with built-in disk caching.

### Constructor

```python
LolWikiClient(
    base_url: str = WIKI_BASE,
    items_index_path: str = ITEMS_INDEX_PATH,
    cache: Optional[TTLCacheConfig] = None,
    session: Optional[aiohttp.ClientSession] = None,
    user_agent: str = "lolwiki/0.1 (+https://github.com/yourname/lolwiki)",
)
```

**Parameters:**
- **base_url** *(str)*: Base URL of the wiki (default: [WIKI_BASE](lolwiki/config.py#L8)).
- **items_index_path** *(str)*: Path to the wiki's main item list (default: `"List of items"`).
- **cache** *(TTLCacheConfig)*: Optional cache configuration, defaults to `~/.cache/lolwiki/cache.json` and 3.5 days TTL.
- **session** *(aiohttp.ClientSession)*: Optionally manage your own `aiohttp` session.
- **user_agent** *(str)*: User-Agent header used for HTTP requests.

---

### `async get_champion(name: str) -> dict`

Fetch data about a champion by name.

**Returns:**
```python
{
    "name": "Ahri",
    "url": "https://wiki.leagueoflegends.com/en-us/Ahri",
    "base_stats": { ... },  # Dict with base stats
    "spells": [ ... ],      # List of spells with attributes
}
```

---

### `async get_item(name: str) -> dict`

Fetch data about an item by name.

**Returns:**
Dictionary with:
- `name` *(str)*
- `url` *(str)*
- `stats` *(dict)*
- `passives/actives` *(list)*
- etc (depends on wiki page contents)

---

### `async list_items(expand: bool = False) -> list[dict]`

List all items from the items index page.

**Arguments:**
- **expand** *(bool)*:
  - `False` — Returns only item name and URL.
  - `True` — Fetches full details for each item (multiple requests in parallel, rate-limited).

**Returns:**
List of dictionaries.

**Example:**
```python
[
    {"name": "Infinity Edge", "url": "..."},
    ...
]
```
If `expand=True`, each dict contains full item data (as per `get_item`).

---

## `TTLCacheConfig`

Defined in [`config.py`](lolwiki/config.py) as a dataclass:

```python
@dataclass
class TTLCacheConfig:
    path: Path   # Cache file path
    ttl_seconds: int  # Cache entry TTL in seconds
```

**Defaults:**
- **path**: `~/.cache/lolwiki/cache.json` (overridable via `LOLWIKI_CACHE` env var)
- **ttl_seconds**: 302400 (3.5 days, overridable via `LOLWIKI_TTL` env var)

---

## Caching Behavior

The HTML for each wiki page is cached to disk. On subsequent requests within the TTL period, the cached HTML is used instead of performing an HTTP fetch.

---

## Errors & Exceptions

- The client will raise `aiohttp` exceptions for HTTP errors.
- Parsing failures in expanded item loads result in `{"_error": "parse_failed"}` entries.

---

## Example Usage

```python
import asyncio
from lolwiki import LolWikiClient

async def main():
    async with LolWikiClient() as client:
        ahri = await client.get_champion("Ahri")
        print(ahri["base_stats"])

        items = await client.list_items(expand=True)
        print(len(items), "items fetched with details")

asyncio.run(main())