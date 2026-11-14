#!/usr/bin/env python3
"""Build the public, read-only site (docs/index.html) served by GitHub Pages.

Takes the recipe book page (pagina/index.html) and embeds the four
collections of datos/ in it as a JSON block with id «recetario-datos».
When the page finds that block it shows the data read-only and never
touches the database.

Usage:
    python3 herramientas/publicar.py ["Site title"]
"""
import json
import pathlib
import re
import sys

COLLECTIONS = ("recipes", "ratings", "menus", "history", "freezer")
DEFAULT_TITLE = "Recetas de Karen y Javi"
MARKER = "<script>\n(() => {"


def main(argv):
    root = pathlib.Path(__file__).resolve().parent.parent
    title = argv[1] if len(argv) > 1 else DEFAULT_TITLE
    page = (root / "pagina" / "index.html").read_text(encoding="utf-8")
    if page.count(MARKER) != 1:
        print("error: cannot find the page's main script")
        return 1
    if "recetario-datos" not in page:
        print("error: this version of the page has no read-only mode")
        return 1

    data = {}
    for name in COLLECTIONS:
        path = root / "datos" / f"{name}.json"
        data[name] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    stamp_file = root / "datos" / "exportado.txt"
    data["exportedAt"] = stamp_file.read_text(encoding="utf-8").strip() if stamp_file.exists() else ""
    # "</" must not appear inside a script element; "<\/" is the same string once parsed as JSON
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    block = f'<script type="application/json" id="recetario-datos">{blob}</script>\n'

    page = page.replace(MARKER, block + MARKER)
    page, replaced = re.subn(r"<title>.*?</title>", lambda _: f"<title>{title}</title>", page, count=1, flags=re.S)
    if not replaced:
        print("error: the page has no <title>")
        return 1
    page = page.replace("<html>", '<html lang="es">', 1)

    out = root / "docs"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    counts = ", ".join(f"{len(data[name])} {name}" for name in COLLECTIONS)
    print(f"docs/index.html: {len(page.encode('utf-8'))} bytes ({counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
