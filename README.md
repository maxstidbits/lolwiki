# lolwiki

An asynchronous Python client for scraping the official [League of Legends Wiki](https://wiki.leagueoflegends.com) with built-in disk caching.

`lolwiki` allows you to fetch structured data about champions and items from the LoL Wiki, including champion base stats, spells, item details, and item lists. All fetches are cached locally so repeated calls are efficient and avoid unnecessary requests.

---

## Features

- **Async API** built on `aiohttp`
- **Champion data**: base stats and spells
- **Item data**: full item details or item index
- **Configurable disk cache** with TTL
- **HTML parsing** handled with BeautifulSoup
- **Rate-limited async fetching** when expanding item lists

---

## Installation

```bash
pip install lolwiki
```

---

## Quick Start

### Example: Fetching a champion

```python
import asyncio
from lolwiki import LolWikiClient

async def main():
    async with LolWikiClient() as client:
        data = await client.get_champion("Ahri")
        print(data)

asyncio.run(main())
```

### Example: Fetching an item

```python
async with LolWikiClient() as client:
    item = await client.get_item("Infinity Edge")
    print(item)
```

### Example: Listing items

```python
# Just names/URLs
items = await client.list_items()
print(len(items))

# Full details for each item
items_full = await client.list_items(expand=True)
```

---

## API Overview

- `LolWikiClient(base_url=WIKI_BASE, items_index_path=ITEMS_INDEX_PATH, cache=None, session=None, user_agent="lolwiki/0.1 ...")`
- `get_champion(name: str)` → dict with `base_stats` and `spells`
- `get_item(name: str)` → dict with item details
- `list_items(expand: bool=False)` → list of item dicts; with `expand=True` fetches full details for each

See the [API Documentation](API.md) for details on return formats and field descriptions.

---

## Cache

By default, `lolwiki` caches HTML responses to `~/.cache/lolwiki/cache.json` (overridable with the `LOLWIKI_CACHE` environment variable). The default TTL is 3.5 days (`LOLWIKI_TTL`).

---

## License

MIT — see [LICENSE](LICENSE) for details.