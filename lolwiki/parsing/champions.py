from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from bs4 import BeautifulSoup, Tag


def parse_base_stats(soup: BeautifulSoup) -> Dict[str, str]:
    header = None
    for hx in soup.select("h2, h3"):
        if re.search(r"\bBase\b.*\bstat", hx.get_text(" ", strip=True), re.I):
            header = hx
            break

    table = None
    if header:
        sib = header.find_next(["table", "div"])
        while sib and not isinstance(sib, Tag):
            sib = sib.find_next(["table", "div"])
        if sib and sib.name == "table":
            table = sib
        elif sib:
            table = sib.find("table")

    stats: Dict[str, str] = {}
    candidates = []
    if table:
        candidates.append(table)
    candidates += [t for t in soup.select("table") if len(t.select("tr")) >= 5]

    def cleankey(k: str) -> str:
        k = re.sub(r"\s*\(.*?\)\s*", "", k).strip()
        return re.sub(r"\s+", "_", k.lower())

    for t in candidates:
        for tr in t.select("tr"):
            cells = tr.find_all(["th", "td"])
            if len(cells) == 2:
                k = cells[0].get_text(" ", strip=True)
                v = cells[1].get_text(" ", strip=True)
                if k and v and len(k) <= 40:
                    if any(
                        x in k.lower()
                        for x in [
                            "health",
                            "mana",
                            "armor",
                            "magic",
                            "ad",
                            "as",
                            "ms",
                            "range",
                            "hp5",
                            "mp5",
                            "crit",
                            "resist",
                        ]
                    ):
                        stats[cleankey(k)] = v
    return stats


def parse_spells(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    ability_blocks: List[Tuple[str, Tag]] = []
    for hx in soup.select("h2, h3, h4"):
        text = hx.get_text(" ", strip=True)
        m = re.match(r"^\s*(Passive|P|Q|W|E|R)\s*[:\-]?\s*(.+)?$", text, re.I)
        if m:
            slot = m.group(1).upper()
            ability_name = (m.group(2) or "").strip()
            blk = _collect_description_block(hx)
            if not ability_name:
                b = blk.find(["b", "strong"])
                if b:
                    ability_name = b.get_text(" ", strip=True)
            ability_blocks.append(("P" if slot == "PASSIVE" else slot, blk))

    if not ability_blocks:
        for card in soup.select(".ability, .skill, .pi-ability, .character-ability"):
            label = card.find(class_=re.compile(r"ability-slot|skill-key|slot", re.I))
            slot = (label.get_text(" ", strip=True) if label else "").upper()
            slot = slot if slot in {"P", "Q", "W", "E", "R"} else "?"
            ability_blocks.append((slot, card))

    parsed = []
    for slot, blk in ability_blocks:
        cd = _extract_labeled_value(blk, ["Cooldown", "CD"])
        cost = _extract_labeled_value(blk, ["Cost"])
        rng = _extract_labeled_value(blk, ["Range"])
        name = _extract_name_from_block(blk)

        desc_html = _extract_description_html(blk)
        desc_text = BeautifulSoup(desc_html, "lxml").get_text(" ", strip=True)
        parsed.append({
            "slot": slot,
            "name": name,
            "cooldown": cd,
            "cost": cost,
            "range": rng,
            "description_html": desc_html,
            "description_text": desc_text,
        })

    out = []
    seen = set()
    for p in parsed:
        if p["slot"] in seen:
            continue
        seen.add(p["slot"])
        out.append(p)
    return out


def _collect_description_block(header: Tag) -> Tag:
    container = BeautifulSoup("<div></div>", "lxml").div  # type: ignore
    node = header.find_next_sibling()
    while node and node.name not in {"h2", "h3", "h4"}:
        container.append(node.extract())
        node = header.find_next_sibling()
    return container


def _extract_labeled_value(blk: Tag, labels: List[str]) -> Any:
    pat = re.compile(rf"^({'|'.join(map(re.escape, labels))})\s*[:：]", re.I)
    for li in blk.select("li, p, tr"):
        text = li.get_text(" ", strip=True)
        if pat.search(text):
            val = re.sub(pat, "", text).strip()
            return val or None
    for dt in blk.select("dt"):
        if any(lbl.lower() in dt.get_text(" ", strip=True).lower() for lbl in labels):
            dd = dt.find_next_sibling("dd")
            if dd:
                return dd.get_text(" ", strip=True)
    return None


def _extract_name_from_block(blk: Tag) -> str:
    b = blk.find(["b", "strong"])
    if b and len(b.get_text(strip=True)) <= 80:
        return b.get_text(" ", strip=True)
    h = blk.find(["h5", "h6"])
    if h:
        return h.get_text(" ", strip=True)
    return ""


def _extract_description_html(blk: Tag) -> str:
    candidates = []
    for sel in ["p", "div", "section", ".ability-text", ".skill-text"]:
        candidates += blk.select(sel)

    if not candidates:
        return str(blk)

    def bad(n: Tag) -> bool:
        t = n.get_text(" ", strip=True).lower()
        return bool(re.match(r"^(cooldown|cd|cost|range)\b", t))

    texty = [c for c in candidates if not bad(c)]
    chosen = texty[0] if texty else candidates[0]
    return str(chosen)