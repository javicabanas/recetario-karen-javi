#!/usr/bin/env python3
"""Rebuild datos/ and recetas/ from an export of the recipe book.

The export is the JSON that the page saves as its automatic backup (decoded
with descodificar.py) or offers as text in its «Copia de seguridad» view:
{"recipes": {...}, "ratings": {...}, "menus": {...}, "history": {...}},
each collection keyed by document id.

Usage:
    python3 herramientas/importar.py recetario.json [EXPORT_DATE]

EXPORT_DATE (ISO) is written to datos/exportado.txt; when omitted, the
export's own "exportedAt" field is used if it has one.
"""
import json
import pathlib
import sys

COLLECTIONS = ("recipes", "ratings", "menus", "history", "freezer")
OPTIONAL = ("freezer",)
FRACTIONS = {0.5: "½", 0.25: "¼", 0.75: "¾"}


def fmt_number(q):
    if q == int(q):
        return str(int(q))
    return FRACTIONS.get(q, str(q).replace(".", ","))


def fmt_duration(seconds):
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    parts = []
    if hours:
        parts.append(f"{hours} h")
    if minutes:
        parts.append(f"{minutes} min")
    if secs:
        parts.append(f"{secs} s")
    return " ".join(parts)


def recipe_to_markdown(recipe):
    lines = [f"## {recipe.get('title', '')}", "", recipe.get("summary", ""), ""]
    note = f" ({recipe['servingsNote']})" if recipe.get("servingsNote") else ""
    lines.append(f"**Raciones:** {recipe.get('servings', '')}{note} · **Tiempo:** {recipe.get('time', '')}")
    lines.append(
        f"**Equipo:** {', '.join(recipe.get('equipment', []))} · **Etiquetas:** {', '.join(recipe.get('tags', []))}"
    )
    lines += ["", "## Ingredientes", ""]
    for group in recipe.get("ingredients", []):
        if group.get("group"):
            lines += [f"**{group['group']}**", ""]
        for item in group.get("items", []):
            if "amount" in item:
                amount = item["amount"]
            else:
                amount = f"{fmt_number(item['qty'])} {item.get('unit', '')}".strip()
            item_note = f" ({item['note']})" if item.get("note") else ""
            lines.append(f"- {amount} {item['name']}{item_note}")
        lines.append("")
    lines += ["## Instrucciones de compra", ""]
    for entry in recipe.get("shopping", []):
        lines.append(f"- **{entry.get('item', '')}:** {entry.get('detail', '')}")
    lines += ["", "## Preparación", ""]
    number = 0
    for phase in recipe.get("phases", []):
        if phase.get("name"):
            lines += [f"**{phase['name']}**", ""]
        for step in phase.get("steps", []):
            number += 1
            tags = []
            if step.get("level"):
                tags.append(f"inducción nivel {step['level']}")
            if step.get("timer"):
                tags.append(fmt_duration(step["timer"]))
            suffix = f" _[{' · '.join(tags)}]_" if tags else ""
            lines.append(f"{number}. {step.get('text', '')}{suffix}")
        lines.append("")
    if recipe.get("notes"):
        lines += ["## Notas", ""]
        for entry in recipe["notes"]:
            if entry.get("title"):
                lines += [f"**{entry['title']}**", ""]
            lines += [entry.get("text", ""), ""]
    if recipe.get("scaleWarning"):
        lines += ["**Al cambiar raciones**", "", recipe["scaleWarning"], ""]
    if recipe.get("origin"):
        lines += [f"_Origen: {recipe['origin']}._", ""]
    return "\n".join(lines)


def main(argv):
    if len(argv) not in (2, 3):
        print(__doc__)
        return 2
    root = pathlib.Path(__file__).resolve().parent.parent
    export = json.loads(pathlib.Path(argv[1]).read_text(encoding="utf-8"))
    missing = [name for name in COLLECTIONS if name not in OPTIONAL and not isinstance(export.get(name), dict)]
    if missing:
        print(f"error: the export lacks these collections: {', '.join(missing)}")
        return 1

    data_dir = root / "datos"
    data_dir.mkdir(exist_ok=True)
    for name in COLLECTIONS:
        docs = dict(sorted((export.get(name) or {}).items()))
        text = json.dumps(docs, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        (data_dir / f"{name}.json").write_text(text, encoding="utf-8")
        print(f"datos/{name}.json: {len(docs)}")
    stamp = argv[2] if len(argv) == 3 else str(export.get("exportedAt", ""))
    (data_dir / "exportado.txt").write_text(stamp + "\n", encoding="utf-8")

    recipes_dir = root / "recetas"
    recipes_dir.mkdir(exist_ok=True)
    wanted = {f"{rid}.md" for rid in export["recipes"]}
    for stale in recipes_dir.glob("*.md"):
        if stale.name not in wanted:
            stale.unlink()
            print(f"recetas/{stale.name}: removed (no longer in the recipe book)")
    for rid, recipe in sorted(export["recipes"].items()):
        (recipes_dir / f"{rid}.md").write_text(recipe_to_markdown(recipe), encoding="utf-8")
    print(f"recetas/: {len(wanted)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
