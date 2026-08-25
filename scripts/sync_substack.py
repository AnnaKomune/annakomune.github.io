#!/usr/bin/env python3
"""Synchronise data/articles.json avec le flux RSS Substack de Komune.

Lancé automatiquement par GitHub Actions (.github/workflows/substack-sync.yml).
- Les articles présents dans le flux sont mis à jour (titre, extrait, date, image de couverture).
- Les articles plus anciens, sortis du flux, sont conservés tels quels (archive).
"""
import json
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED_URL = "https://komunemedia.substack.com/feed"
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "articles.json"


def fetch_feed():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "KomuneSiteSync/1.0 (+https://www.komunemedia.fr)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_items(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.iter("item"):
        title = html.unescape((item.findtext("title") or "").strip())
        url = (item.findtext("link") or "").strip().split("?")[0]
        excerpt = html.unescape(re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip())
        date = ""
        pub = item.findtext("pubDate")
        if pub:
            try:
                date = parsedate_to_datetime(pub).date().isoformat()
            except (TypeError, ValueError):
                pass
        image = ""
        enclosure = item.find("enclosure")
        if enclosure is not None:
            image = enclosure.get("url") or ""
        if title and url:
            items.append({"title": title, "url": url, "excerpt": excerpt, "date": date, "image": image})
    return items


def main():
    existing = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else []
    feed_items = parse_items(fetch_feed())
    if not feed_items:
        print("Flux vide ou illisible : on ne touche à rien.")
        return

    feed_urls = {a["url"] for a in feed_items}
    feed_items.sort(key=lambda a: a["date"], reverse=True)

    existing_by_url = {a["url"]: a for a in existing}
    merged = []
    for item in feed_items:
        old = existing_by_url.get(item["url"], {})
        # On garde l'image et l'extrait déjà connus si le flux ne les fournit plus.
        item["image"] = item["image"] or old.get("image", "")
        item["excerpt"] = item["excerpt"] or old.get("excerpt", "")
        merged.append(item)
    for article in existing:  # archives hors flux, ordre conservé
        if article["url"] not in feed_urls:
            merged.append(article)

    new_content = json.dumps(merged, ensure_ascii=False, indent=1)
    if DATA_FILE.exists() and DATA_FILE.read_text(encoding="utf-8") == new_content:
        print("Aucun changement.")
        return
    DATA_FILE.write_text(new_content, encoding="utf-8")
    print(f"articles.json mis à jour : {len(merged)} articles.")


if __name__ == "__main__":
    main()
