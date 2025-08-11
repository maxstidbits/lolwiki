from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from ..config import WIKI_BASE


def parse_items_index(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    items: Dict[str, Dict[str, Any]] = {}
    for a in soup.select("a[href]"):
        href = a["href"]
        name = a.get_text(" ", strip=True)
        if not name or len(name) > 100:
            continue
        if href.startswith("/") and not any(x in href for x in [":", "#", "redlink"]):
            if any(
                bad in name.lower()
                for bad in [
                    "rune",
                    "warding",
                    "trinket",
                    "jungle item list",
                    "mythic removed",
                ]
            ):
                continue
            url = urljoin(WIKI_BASE, href.lstrip("/"))
            if name not in items:
                items[name] = {"name": name, "url": url, "tags": []}

    for chip in soup.select(".category, .tag, .label, .mw-tag-marker"):
        tagtxt = chip.get_text(" ", strip=True)
        if not tagtxt:
            continue
        prev_link = chip.find_previous("a", href=True)
        if prev_link:
            nm = prev_link.get_text(" ", strip=True)
            if nm in items:
                items[nm]["tags"].append(tagtxt)

    return sorted(items.values(), key=lambda x: x["name"].lower())


def parse_item_page(name: str, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
    rarity = None
    cat = soup.select_one(".mw-normal-catlinks")
    if cat:
        cats = [a.get_text(" ", strip=True) for a in cat.select("a")]
        rarity = next((c for c in cats if c.lower().endswith("items")), None)
        if rarity:
            rarity = rarity.replace(" items", "").strip()

    stats: Dict[str, str] = {}
    passives: List[str] = []
    actives: List[str] = []

    def harvest_stats(node: Tag):
        for li in node.select("li"):
            t = li.get_text(" ", strip=True)
            if re.match(r"^\+?\d", t) or re.search(
                r"Ability Haste|Armor|Magic Resist|Attack Damage|Ability Power|"
                r"Health|Mana|Lethality|Omnivamp|Lifesteal|Move Speed",
                t,
                re.I,
            ):
                key = re.sub(r"^[+•\-\s]*", "", t)
                stats[key] = t
        for tr in node.select("tr"):
            t = tr.get_text(" ", strip=True)
            if re.search(
                r"(Armor|MR|AD|AP|Haste|Health|Mana|Speed|Lethality|Crit)",
                t,
                re.I,
            ):
                stats[t.split(":")[0].strip()] = t

    info = soup.select_one(
        ".infobox, .item-infobox, .portable-infobox, .pi-theme-item, .pi-box"
    )
    if info:
        harvest_stats(info)

    lead = soup.select_one("#mw-content-text")
    if lead:
        for ul in lead.select("ul"):
            harvest_stats(ul)

    body = soup.select_one("#mw-content-text") or soup
    for p in body.select("p, li"):
        txt = p.get_text(" ", strip=True)
        if re.match(r"^Passive\s*[:：\-]", txt, re.I):
            passives.append(txt)
        elif re.match(r"^Active\s*[:：\-]", txt, re.I):
            actives.append(txt)

    desc_node = None
    for sel in [
        ".pi-data-value",
        ".infobox-desc",
        ".item-desc",
        ".pi-item-spacing",
        "p",
    ]:
        desc_node = soup.select_one(sel)
        if desc_node:
            break
    desc_html = str(desc_node) if desc_node else ""
    desc_text = (
        BeautifulSoup(desc_html, "lxml").get_text(" ", strip=True)
        if desc_html
        else ""
    )

    return {
        "name": name,
        "url": url,
        "rarity": rarity,
        "stats": stats,
        "passives": passives,
        "actives": actives,
        "description_html": desc_html,
        "description_text": desc_text,
    }