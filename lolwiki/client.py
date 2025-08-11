from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urljoin

import aiohttp
from bs4 import BeautifulSoup

from .cache import _DiskCache
from .config import ITEMS_INDEX_PATH, WIKI_BASE, TTLCacheConfig
from .parsing.champions import parse_base_stats, parse_spells
from .parsing.items import parse_item_page, parse_items_index


class LolWikiClient:
    """
    Async client for scraping the LoL wiki (champions & items) with caching.
    """

    def __init__(
        self,
        base_url: str = WIKI_BASE,
        items_index_path: str = ITEMS_INDEX_PATH,
        cache: Optional[TTLCacheConfig] = None,
        session: Optional[aiohttp.ClientSession] = None,
        user_agent: str = "lolwiki/0.1 (+https://github.com/yourname/lolwiki)",
    ):
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        self.items_index_path = items_index_path
        self.cache = _DiskCache(cache or TTLCacheConfig())
        self._session = session
        self._ua = user_agent
        self._own_session = False

    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(headers={"User-Agent": self._ua})
            self._own_session = True
        return self

    async def __aexit__(self, *exc):
        await self.aclose()

    async def aclose(self):
        if self._own_session and self._session:
            await self._session.close()
            self._session = None
            self._own_session = False

    # -------------------------- Public API --------------------------

    async def get_champion(self, name: str) -> Dict[str, Any]:
        url = self._page_url(name)
        html = await self._fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        base_stats = parse_base_stats(soup)
        spells = parse_spells(soup)
        return {
            "name": name,
            "url": url,
            "base_stats": base_stats,
            "spells": spells,
        }

    async def get_item(self, name: str) -> Dict[str, Any]:
        url = self._page_url(name)
        html = await self._fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        return parse_item_page(name, url, soup)

    async def list_items(self, expand: bool = False) -> List[Dict[str, Any]]:
        url = self._page_url(self.items_index_path)
        html = await self._fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        rows = parse_items_index(soup)

        if not expand:
            return rows

        async def _load(row):
            try:
                return await self.get_item(row["name"])
            except Exception:
                return {**row, "_error": "parse_failed"}

        return await self._gather_limited([_load(r) for r in rows], limit=15)

    # -------------------------- Internals --------------------------

    async def _gather_limited(self, coros, limit: int = 10):
        sem = asyncio.Semaphore(limit)

        async def _wrap(coro):
            async with sem:
                return await coro

        return await asyncio.gather(*[_wrap(c) for c in coros])

    def _page_url(self, title: str) -> str:
        return urljoin(self.base_url, quote(title.replace(" ", "_")))

    async def _fetch_html(self, url: str) -> str:
        cached = self.cache.get(url)
        if cached:
            return cached
        if not self._session:
            self._session = aiohttp.ClientSession(headers={"User-Agent": self._ua})
            self._own_session = True
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            text = await resp.text()
            self.cache.set(url, text)
            return text