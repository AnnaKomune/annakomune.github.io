#!/usr/bin/env python3
"""Synchronise data/articles.json avec le flux RSS Substack de Komune.

Lancé automatiquement par GitHub Actions (.github/workflows/substack-sync.yml).
- Les articles présents dans le flux sont mis à jour (titre, extrait, date, image de couverture).
- Les articles plus anciens, sortis du flux, sont conservés tels quels (archive).
"""
import json
import html
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import page_articles  # noqa: E402

FEED_URL = "https://komunemedia.substack.com/feed"
ARCHIVE_API = "https://komunemedia.substack.com/api/v1/archive?sort=new&search=&offset=%d&limit=%d"
ARCHIVE_PAGE = 50      # articles demandés par appel
ARCHIVE_MAX = 600      # garde-fou : on ne remonte jamais au-delà
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "articles.json"

# Substack bloque les requêtes qui ne ressemblent pas à un navigateur : on s'y présente comme Chrome.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def _items_from_rss2json():
    # rss2json va chercher le flux depuis ses propres serveurs (non bloqués par Substack).
    api = "https://api.rss2json.com/v1/api.json?rss_url=" + urllib.parse.quote(FEED_URL, safe="")
    req = urllib.request.Request(api, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if payload.get("status") != "ok":
        raise RuntimeError(payload.get("message") or "réponse inattendue")
    items = []
    for it in payload.get("items", []):
        title = html.unescape((it.get("title") or "").strip())
        url = (it.get("link") or "").strip().split("?")[0]
        excerpt = html.unescape(re.sub(r"<[^>]+>", "", it.get("description") or "").strip())
        date = (it.get("pubDate") or "").strip()[:10]
        image = (it.get("enclosure") or {}).get("link") or it.get("thumbnail") or ""
        if title and url:
            items.append({"title": title, "url": url, "excerpt": excerpt, "date": date, "image": image})
    return items


def _fetch_curl_cffi():
    # Imite l'empreinte réseau complète de Chrome (TLS/JA3), ce que Cloudflare vérifie.
    from curl_cffi import requests as cffi_requests

    resp = cffi_requests.get(FEED_URL, impersonate="chrome", timeout=30)
    if resp.status_code != 200 or not resp.content:
        raise RuntimeError(f"HTTP {resp.status_code}")
    return resp.content


def _items_from_archive(fetch):
    """L'API publique d'archive de Substack : la meme liste que le flux, en JSON,
       avec le titre, le sous-titre, la date et l'image de couverture.

       On la parcourt page par page (offset) pour ramener TOUTE l'archive, et
       pas seulement les derniers articles : c'est ce qui alimente la page
       /articles/ avec l'ensemble des publications et leurs couvertures."""
    items = []
    vus = set()
    offset = 0
    while offset < ARCHIVE_MAX:
        payload = json.loads(fetch(ARCHIVE_API % (offset, ARCHIVE_PAGE)).decode("utf-8"))
        if not isinstance(payload, list):
            raise RuntimeError("réponse inattendue de l'API d'archive")
        if not payload:
            break
        avant = len(items)
        _ajouter_archive(payload, items, vus)
        if len(payload) < ARCHIVE_PAGE or len(items) == avant:
            break
        offset += ARCHIVE_PAGE
        time.sleep(1)
    return items


def _ajouter_archive(payload, items, vus):
    for p in payload:
        title = html.unescape((p.get("title") or "").strip())
        url = (p.get("canonical_url") or "").strip().split("?")[0]
        excerpt = html.unescape((p.get("subtitle") or p.get("description") or "").strip())
        date = (p.get("post_date") or "")[:10]
        image = p.get("cover_image") or ""
        if title and url and url not in vus:
            vus.add(url)
            items.append({"title": title, "url": url, "excerpt": excerpt, "date": date, "image": image})


def _get_cffi(url):
    """Imite l'empreinte reseau complete de Chrome (TLS/JA3), ce que Cloudflare verifie."""
    from curl_cffi import requests as cffi_requests

    resp = cffi_requests.get(url, impersonate="chrome", timeout=30, headers={"Accept-Language": "fr-FR,fr;q=0.9"})
    if resp.status_code != 200 or not resp.content:
        raise RuntimeError(f"HTTP {resp.status_code}")
    return resp.content


def _get_urllib(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _via(relais):
    """Un relais public va chercher l'adresse depuis ses propres serveurs."""
    def prendre(url):
        req = urllib.request.Request(relais + urllib.parse.quote(url, safe=""), headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    return prendre


def _fetch_urllib():
    req = urllib.request.Request(FEED_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _fetch_proxy():
    # Dernier recours : un proxy public qui va chercher le flux depuis ses propres serveurs.
    proxy_url = "https://api.allorigins.win/raw?url=" + urllib.parse.quote(FEED_URL, safe="")
    req = urllib.request.Request(proxy_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def get_feed_items():
    # Un fichier XML déjà téléchargé peut être passé en argument (pratique pour tester).
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists() and Path(sys.argv[1]).stat().st_size > 0:
        return parse_items(Path(sys.argv[1]).read_bytes())
    # Substack bloque de plus en plus les adresses IP des serveurs (403), et les
    # relais publics tombent regulierement (500, 522). On multiplie donc les chemins :
    # l'API d'archive d'abord (la plus riche), le flux RSS ensuite, en direct puis
    # par relais. Le premier qui repond quelque chose gagne.
    RELAIS = (
        ("codetabs", "https://api.codetabs.com/v1/proxy/?quest="),
        ("allorigins", "https://api.allorigins.win/raw?url="),
        ("corsproxy", "https://corsproxy.io/?url="),
        ("jina", "https://r.jina.ai/"),
    )
    sources = [
        ("api d'archive (empreinte Chrome)", lambda: _items_from_archive(_get_cffi)),
        ("api d'archive (direct)", lambda: _items_from_archive(_get_urllib)),
        ("rss2json", _items_from_rss2json),
        ("flux RSS (empreinte Chrome)", lambda: parse_items(_get_cffi(FEED_URL))),
        ("flux RSS (direct)", lambda: parse_items(_get_urllib(FEED_URL))),
    ]
    for nom, relais in RELAIS:
        sources.append(("api d'archive via " + nom, (lambda r: lambda: _items_from_archive(_via(r)))(relais)))
        sources.append(("flux RSS via " + nom, (lambda r: lambda: parse_items(_via(r)(FEED_URL)))(relais)))
    sources = tuple(sources)
    last_error = None
    for name, fetcher in sources:
        try:
            items = fetcher()
            if items:
                print(f"{len(items)} articles récupérés via {name}.")
                return items
            print(f"{name} : aucun article, on essaie autre chose.")
        except Exception as exc:  # noqa: BLE001 - on tente la méthode suivante
            print(f"{name} : {exc}")
            last_error = exc
        time.sleep(2)
    raise SystemExit(f"Impossible de récupérer le flux RSS ({last_error}).")


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
    feed_items = get_feed_items()
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

    merged.sort(key=lambda a: a.get("date") or "", reverse=True)
    new_content = json.dumps(merged, ensure_ascii=False, indent=1)
    if not DATA_FILE.exists() or DATA_FILE.read_text(encoding="utf-8") != new_content:
        DATA_FILE.write_text(new_content, encoding="utf-8")
        print(f"articles.json mis à jour : {len(merged)} articles.")
    else:
        print("articles.json : aucun changement.")

    # La page /articles/ est ecrite en dur a partir de ces donnees (bon pour le referencement).
    page_articles.ecrire_page(merged)


if __name__ == "__main__":
    main()
