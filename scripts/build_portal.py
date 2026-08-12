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
    """Um registro por arquivo portal/data/*.json, em ordem decrescente de data."""
    archive = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*.json")), reverse=True):
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
            "revision": meta.get("revision"),
            "stories": meta.get("story_count"),
            "headline": hero.get("title"),
        })
    return archive


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

    data["archive"] = build_archive(data_dir)

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
    print(f"Portal gerado: {args.out}")
    print(f" - dados:    {data_path}")
    print(f" - notícias: {count_stories(data)}")
    print(f" - arquivo:  {size_kb:.1f} KB ({len(data['archive'])} dia(s) no arquivo morto)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
