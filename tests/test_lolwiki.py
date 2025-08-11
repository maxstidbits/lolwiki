from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from lolwiki.cache import _DiskCache
from lolwiki.client import LolWikiClient
from lolwiki.config import TTLCacheConfig
from lolwiki.parsing.champions import parse_base_stats, parse_spells
from lolwiki.parsing.items import parse_item_page, parse_items_index


def test_disk_cache_set_get(tmp_path: Path):
    cfg = TTLCacheConfig(path=tmp_path / "cache.json", ttl_seconds=1000)
    cache = _DiskCache(cfg)
    cache.set("key", "value")
    assert cache.get("key") == "value"


def test_disk_cache_expired(tmp_path: Path):
    cfg = TTLCacheConfig(path=tmp_path / "cache.json", ttl_seconds=-1)
    cache = _DiskCache(cfg)
    cache.set("key", "value")
    assert cache.get("key") is None


@pytest.mark.asyncio
async def test_client_page_url():
    client = LolWikiClient()
    url = client._page_url("Test Page")
    assert "Test_Page" in url


def test_parse_base_stats_and_spells():
    html = """
    <html>
      <body>
        <h2>Base Stats</h2>
        <table>
          <tr><th>Health</th><td>500</td></tr>
          <tr><th>Mana</th><td>300</td></tr>
        </table>
        <h3>Q: Test Ability</h3>
        <div><p>Cooldown: 10s</p><p>Cost: 50 Mana</p><p>Range: 600</p></div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    stats = parse_base_stats(soup)
    assert stats["health"] == "500"
    spells = parse_spells(soup)
    assert spells[0]["slot"] == "Q"


def test_parse_items_index_and_item_page():
    index_html = """
    <html>
      <body>
        <a href="/Item_One">Item One</a>
        <span class="tag">Legendary</span>
      </body>
    </html>
    """
    soup_index = BeautifulSoup(index_html, "lxml")
    items = parse_items_index(soup_index)
    assert any(i["name"] == "Item One" for i in items)

    page_html = """
    <html>
      <body>
        <div class="mw-normal-catlinks">
          <a>Legendary items</a>
        </div>
        <div class="pi-theme-item">
          <li>+10 Attack Damage</li>
        </div>
        <p>Passive: Grants speed</p>
      </body>
    </html>
    """
    soup_page = BeautifulSoup(page_html, "lxml")
    item_data = parse_item_page("Item One", "http://example.com/item_one", soup_page)
    assert item_data["rarity"] == "Legendary"
    assert any("Attack Damage" in s for s in item_data["stats"].values())