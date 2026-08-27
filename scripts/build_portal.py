#!/usr/bin/env python3
"""Gera portal/index.html a partir do template + dados do dia.

Uso:
  python3 scripts/build_portal.py [--data portal/data/YYYY-MM-DD.json]
                                  [--template portal/template.html]
                                  [--out portal/index.html]

Sem --data, usa o arquivo mais recente de portal/data/ (ordem lexicográfica
do nome, que para YYYY-MM-DD.json equivale à ordem cronológica).
"""

import argparse
import glob
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_DIR = os.path.join(REPO_ROOT, "portal", "data")
DEFAULT_TEMPLATE = os.path.join(REPO_ROOT, "portal", "template.html")
DEFAULT_OUT = os.path.join(REPO_ROOT, "portal", "index.html")
PLACEHOLDER = "__AEC_DATA__"


def latest_data_file(data_dir):
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    if not files:
        sys.exit(f"Erro: nenhum arquivo de dados encontrado em {data_dir}/")
    return files[-1]


def build_archive(data_dir):
    """Um registro por arquivo portal/data/*.json, em ordem decrescente de data.

    Cada edição recebe um número global sequencial (Nº 001 = a mais antiga),
    calculado pela posição do arquivo na ordem cronológica.
    """
    paths = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    archive = []
    for idx, path in enumerate(paths, start=1):
        date = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Aviso: ignorando {path} no arquivo morto (JSON inválido: {e})",
                  file=sys.stderr)
            continue
        meta = d.get("meta") or {}
        hero = d.get("hero") or {}
        archive.append({
            "date": date,
            "edition_number": idx,
            "revision": meta.get("revision"),
            "stories": meta.get("story_count"),
            "headline": hero.get("title"),
        })
    archive.reverse()
    return archive


def prune_old_images(data_dir, current_name, keep_days=7):
    """Remove imagens embutidas (data URIs) de edições com mais de keep_days.

    As imagens só importam na página do dia; título/URL/resumo permanecem para
    o arquivo morto e o dedup. Mantém o repositório leve (~600 KB -> ~20 KB
    por edição antiga).
    """
    import datetime as _dt
    try:
        cur = _dt.date.fromisoformat(os.path.splitext(current_name)[0])
    except ValueError:
        return
    pruned = 0
    for path in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            age = (cur - _dt.date.fromisoformat(name)).days
        except ValueError:
            continue
        if age <= keep_days:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        removed = False
        if isinstance(d.get("hero"), dict) and d["hero"].pop("image", None) is not None:
            removed = True
        for sec in d.get("sections", []):
            for it in sec.get("items", []):
                if isinstance(it, dict) and it.pop("image", None) is not None:
                    removed = True
        if removed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
                f.write("\n")
            pruned += 1
    if pruned:
        print(f"Poda: imagens removidas de {pruned} edição(ões) com mais de {keep_days} dias.")


def load_sources_list():
    """Lista de fontes de scripts/sources.json para a vista Fontes do portal."""
    path = os.path.join(REPO_ROOT, "scripts", "sources.json")
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return [{"name": s.get("name"), "type": s.get("type"),
                 "lang": s.get("lang"), "nota": s.get("nota", "")}
                for s in cfg.get("sources", [])]
    except (OSError, json.JSONDecodeError):
        return []


def _xml_escape(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def write_feed(data, out_path):
    """Gera um RSS 2.0 da edição atual (hero + todas as notícias)."""
    meta = data.get("meta") or {}
    date = meta.get("date", "")
    # DD.MM.AAAA -> RFC822 aproximado (11:00 GMT, horário da emissão)
    pub = ""
    try:
        d, m, y = date.split(".")
        import datetime as _dt
        pub = _dt.datetime(int(y), int(m), int(d), 11, 0).strftime(
            "%a, %d %b %Y %H:%M:%S GMT")
    except (ValueError, AttributeError):
        pass
    items = []
    hero = data.get("hero") or {}
    if hero.get("title"):
        items.append((hero["title"], hero.get("url", ""),
                      (hero.get("paragraphs") or [""])[0], hero.get("source", "")))
    for sec in data.get("sections", []):
        for it in sec.get("items", []):
            items.append((it.get("title", ""), it.get("url", ""),
                          it.get("summary", ""), it.get("source", "")))
    rows = []
    for title, link, desc, src in items:
        rows.append(
            "  <item>\n"
            f"   <title>{_xml_escape(title)}</title>\n"
            f"   <link>{_xml_escape(link)}</link>\n"
            f"   <guid isPermaLink=\"false\">{_xml_escape(link)}</guid>\n"
            f"   <description>{_xml_escape(desc)} (via {_xml_escape(src)})</description>\n"
            f"   <pubDate>{pub}</pubDate>\n"
            "  </item>")
    ed = meta.get("edition_number")
    xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<rss version=\"2.0\">\n"
        " <channel>\n"
        "  <title>AEC NEWS</title>\n"
        "  <link>https://claude.ai/code/artifact/a4dbeb62-d306-4a49-b262-343337bbf0b3</link>\n"
        f"  <description>Diário da construção civil — edição Nº {ed:03d} de {_xml_escape(date)}</description>\n"
        "  <language>pt-BR</language>\n"
        f"  <lastBuildDate>{pub}</lastBuildDate>\n"
        + "\n".join(rows) + "\n"
        " </channel>\n"
        "</rss>\n")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml)


def count_stories(data):
    meta = data.get("meta") or {}
    if isinstance(meta.get("story_count"), int):
        return meta["story_count"]
    n = 1 if data.get("hero") else 0
    for key in ("sections", "stories", "items", "news"):
        val = data.get(key)
        if isinstance(val, list):
            for entry in val:
                if isinstance(entry, dict) and isinstance(entry.get("items"), list):
                    n += len(entry["items"])
                else:
                    n += 1
    return n


def main(argv=None):
    p = argparse.ArgumentParser(description="Gera o portal AEC (index.html).")
    p.add_argument("--data", help="arquivo de dados YYYY-MM-DD.json "
                                  "(padrão: o mais recente em portal/data/)")
    p.add_argument("--template", default=DEFAULT_TEMPLATE,
                   help="template HTML com o placeholder __AEC_DATA__")
    p.add_argument("--out", default=DEFAULT_OUT, help="arquivo HTML de saída")
    args = p.parse_args(argv)

    data_path = args.data or latest_data_file(DEFAULT_DATA_DIR)
    data_dir = os.path.dirname(os.path.abspath(data_path)) or DEFAULT_DATA_DIR

    if not os.path.isfile(data_path):
        sys.exit(f"Erro: arquivo de dados não encontrado: {data_path}")
    if not os.path.isfile(args.template):
        sys.exit(f"Erro: template não encontrado: {args.template}")

    with open(data_path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            sys.exit(f"Erro: JSON de dados inválido ({data_path}): {e}")

    prune_old_images(data_dir, os.path.basename(data_path))

    data["archive"] = build_archive(data_dir)

    # Número global da edição (Nº 001 = a mais antiga) — complementa o campo
    # meta.revision, que conta apenas revisões DENTRO do mesmo dia (R00, R01…).
    cur_date = os.path.splitext(os.path.basename(data_path))[0]
    for entry in data["archive"]:
        if entry["date"] == cur_date:
            data.setdefault("meta", {})["edition_number"] = entry["edition_number"]
            break

    data["sources_list"] = load_sources_list()

    feed_path = os.path.join(REPO_ROOT, "portal", "feed.xml")
    try:
        write_feed(data, feed_path)
    except Exception as e:
        print(f"Aviso: falha ao gerar feed.xml: {e}", file=sys.stderr)
        feed_path = None

    with open(args.template, encoding="utf-8") as f:
        template = f.read()
    if PLACEHOLDER not in template:
        sys.exit(f"Erro: placeholder {PLACEHOLDER} não encontrado em {args.template}")

    serialized = json.dumps(data, ensure_ascii=False, indent=1)
    # '</script' dentro do JSON encerraria a tag <script> do template
    assert "</script" not in serialized, \
        "JSON serializado contém '</script' — sanitize os dados antes de gerar o portal"

    html_out = template.replace(PLACEHOLDER, serialized)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_out)

    size_kb = os.path.getsize(args.out) / 1024
    ed = (data.get("meta") or {}).get("edition_number")
    print(f"Portal gerado: {args.out}")
    print(f" - dados:    {data_path}")
    if ed:
        print(f" - edição:   Nº {ed:03d}")
    print(f" - notícias: {count_stories(data)}")
    print(f" - arquivo:  {size_kb:.1f} KB ({len(data['archive'])} dia(s) no arquivo morto)")
    if feed_path:
        print(f" - feed:     {feed_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
