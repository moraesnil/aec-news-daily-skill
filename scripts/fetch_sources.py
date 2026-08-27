#!/usr/bin/env python3
"""Coleta de fontes do portal diário AEC.

Subcomandos:
  feeds  — busca todas as fontes RSS em paralelo e imprime/grava JSON.
  image  — extrai og:image de uma matéria, comprime e imprime um data URI JPEG.

Somente stdlib + Pillow. As requisições usam `curl` via subprocess porque o
ambiente possui proxy HTTPS pré-configurado (urllib/requests podem falhar TLS).
"""

import argparse
import base64
import concurrent.futures
import datetime
import html
import io
import json
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64)"
TIMEOUT = 25          # segundos por fonte
MAX_ITEMS = 8         # itens por fonte

import os

SOURCES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources.json")

# Fallback caso scripts/sources.json não exista
FEEDS = {
    "ArchDaily Brasil": "https://feeds.feedburner.com/ArchdailyBR",
    "Dezeen": "https://www.dezeen.com/feed/",
    "Construction Dive": "https://www.constructiondive.com/feeds/news/",
    "Global Construction Review": "https://www.globalconstructionreview.com/feed/",
}


def load_feeds():
    """Carrega as fontes de scripts/sources.json (editável); fallback embutido."""
    try:
        with open(SOURCES_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        feeds = {s["name"]: s["url"] for s in cfg.get("sources", []) if s.get("url")}
        if feeds:
            return feeds
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Aviso: sources.json ilegível ({e}); usando fontes embutidas.",
              file=sys.stderr)
    return FEEDS


def curl(url, text=True, timeout=TIMEOUT, referer=None):
    """Baixa uma URL com curl. Retorna str (text=True) ou bytes."""
    cmd = ["curl", "-sL", "--max-time", str(timeout), "-A", USER_AGENT]
    if referer:
        cmd += ["-e", referer]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, timeout=timeout + 10)
    if text:
        return r.stdout.decode("utf-8", errors="replace")
    return r.stdout


# ---------------------------------------------------------------------------
# feeds
# ---------------------------------------------------------------------------

def _clean_text(txt, limit=None):
    txt = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", txt or "", flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(re.sub(r"\s+", " ", txt)).strip()
    return txt[:limit] if limit else txt


def _parse_etree(raw):
    """Parser principal: ElementTree com sanitização de & solto."""
    raw = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", "&amp;", raw)
    root = ET.fromstring(raw)
    items = []
    for node in root.iter():
        if not (node.tag.endswith("item") or node.tag.endswith("entry")):
            continue
        d = {"title": "", "link": "", "date": "", "desc": ""}
        for c in node:
            tag = c.tag.split("}")[-1]
            if tag == "title":
                d["title"] = _clean_text(c.text)
            elif tag == "link":
                d["link"] = (c.text or c.get("href") or "").strip()
            elif tag in ("pubDate", "published", "updated", "date") and not d["date"]:
                d["date"] = (c.text or "").strip()
            elif tag in ("description", "summary") and not d["desc"]:
                d["desc"] = _clean_text(c.text, 400)
        if d["title"]:
            items.append(d)
        if len(items) >= MAX_ITEMS:
            break
    return items


def _parse_regex(raw):
    """Fallback para feeds malformados (ex.: Dezeen): regex <item>/<entry>."""
    blocks = re.findall(r"<item[ >](.*?)</item>", raw, re.S)
    if not blocks:
        blocks = re.findall(r"<entry[ >](.*?)</entry>", raw, re.S)
    items = []
    for block in blocks[:MAX_ITEMS]:
        def grab(tag):
            g = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", block, re.S)
            return g.group(1) if g else ""

        link = _clean_text(grab("link"))
        if not link:
            g = re.search(r'<link[^>]*href=["\']([^"\']+)', block)
            link = g.group(1) if g else ""
        date = (_clean_text(grab("pubDate")) or _clean_text(grab("published"))
                or _clean_text(grab("updated")) or _clean_text(grab("dc:date")))
        d = {
            "title": _clean_text(grab("title")),
            "link": link,
            "date": date,
            "desc": _clean_text(grab("description"), 400) or _clean_text(grab("summary"), 400),
        }
        if d["title"]:
            items.append(d)
    return items


def fetch_one(name_url):
    name, url = name_url
    try:
        raw = curl(url)
        if not raw.strip():
            return name, {"ok": False, "items": [], "error": "resposta vazia da fonte"}
        try:
            items = _parse_etree(raw)
        except ET.ParseError:
            items = _parse_regex(raw)
        if not items:
            items = _parse_regex(raw)
        if not items:
            if "Just a moment" in raw or raw.lstrip()[:15].lower().startswith("<!doctype html"):
                return name, {"ok": False, "items": [],
                              "error": "acesso bloqueado pelo site (desafio Cloudflare/anti-bot)"}
            return name, {"ok": False, "items": [], "error": "nenhum item encontrado no feed"}
        return name, {"ok": True, "items": items}
    except Exception as e:
        return name, {"ok": False, "items": [], "error": f"falha ao buscar/parsear: {e}"}


def cmd_feeds(args):
    feeds = load_feeds()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(feeds)) as ex:
        sources = dict(ex.map(fetch_one, feeds.items()))
    out = {
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "sources": sources,
    }
    payload = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
        ok = sum(1 for s in sources.values() if s["ok"])
        total = sum(len(s["items"]) for s in sources.values())
        print(f"Gravado em {args.out}: {ok}/{len(sources)} fontes ok, {total} itens.")
    else:
        print(payload)
    return 0


# ---------------------------------------------------------------------------
# image
# ---------------------------------------------------------------------------

OG_PATTERNS = [
    r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)',
    r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
    r'name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)',
    r'name=["\']twitter:image:src["\'][^>]*content=["\']([^"\']+)',
]


def find_og_image(page_html):
    for pat in OG_PATTERNS:
        m = re.search(pat, page_html)
        if m:
            return html.unescape(m.group(1))
    return None


def dezeen_fallback(article_url):
    """Procura no feed da Dezeen uma imagem static.dezeen.com da matéria.

    Usado quando o site bloqueia scraping direto. Casa o slug da matéria com o
    <item> correspondente no feed e prefere a variante -822x... da imagem.
    """
    slug = urllib.parse.urlparse(article_url).path.rstrip("/").split("/")[-1]
    if not slug:
        return None
    feed = curl("https://www.dezeen.com/feed/")
    for m in re.finditer(r"<item[ >](.*?)</item>", feed, re.S):
        block = m.group(1)
        if slug not in block:
            continue
        imgs = re.findall(r'https://static\.dezeen\.com/[^\s"\'<>\\]+?\.(?:jpg|jpeg|png|webp)', block)
        if not imgs:
            return None
        for u in imgs:
            if re.search(r"-822x\d+\.", u):
                return u
        return imgs[0]
    return None


def build_data_uri(img_bytes, hero=False):
    from PIL import Image

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    width = 900 if hero else 640
    ratio = 16 / 9 if hero else 3 / 2
    if img.width > width:
        img = img.resize((width, max(1, int(img.height * width / img.width))), Image.LANCZOS)
    target_h = int(img.width / ratio)
    if img.height > target_h:
        top = (img.height - target_h) // 2
        img = img.crop((0, top, img.width, top + target_h))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=62, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def cmd_image(args):
    url = args.url
    try:
        page = curl(url)
    except Exception as e:
        print(f"Erro: falha ao baixar a página {url}: {e}", file=sys.stderr)
        return 1

    img_url = find_og_image(page)

    # Fallback Dezeen: página bloqueada (<10KB) ou sem og:image
    if (not img_url or len(page) < 10240) and "dezeen.com" in url:
        try:
            fb = dezeen_fallback(url)
            if fb:
                img_url = fb
        except Exception as e:
            print(f"Aviso: fallback Dezeen falhou: {e}", file=sys.stderr)

    if not img_url:
        print(f"Erro: nenhuma og:image/twitter:image encontrada em {url}", file=sys.stderr)
        return 1

    try:
        referer = url if "dezeen.com" in img_url else None
        img_bytes = curl(img_url, text=False, timeout=30, referer=referer)
        if not img_bytes:
            raise RuntimeError("download da imagem retornou vazio")
        print(build_data_uri(img_bytes, hero=args.hero))
        return 0
    except Exception as e:
        print(f"Erro: falha ao processar imagem {img_url}: {e}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description="Coleta de fontes do portal diário AEC.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("feeds", help="busca todas as fontes RSS em paralelo")
    pf.add_argument("--out", help="grava o JSON neste arquivo em vez de imprimir")
    pf.set_defaults(func=cmd_feeds)

    pi = sub.add_parser("image", help="extrai og:image da matéria e imprime data URI JPEG")
    pi.add_argument("--url", required=True, help="URL da matéria")
    pi.add_argument("--hero", action="store_true",
                    help="formato hero (900px, 16:9); padrão: card (640px, 3:2)")
    pi.set_defaults(func=cmd_image)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
