"""Carga el reparto de sprints (docs/planning/sprints.json) y las historias (docs/planning/user-stories/).

sprints.json dice qué historia va en qué sprint, con cuántos SP y para qué equipo; el título, el MoSCoW
y las dependencias se leen siempre de user-stories/, que es la fuente de los requisitos.
"""

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PLANNING = RAIZ / "docs" / "planning"

# El texto entre el título y la prioridad no puede cruzar a la historia siguiente ("### ").
_PATRON = re.compile(r"### (HU-[\d.]+) (.+?)\n(?:(?!### ).)*?Prioridad: (\w+)[^·\n]*· Depende de: (.+?)\n", re.S)


def _leer_historias():
    historias = {}
    for archivo in sorted((PLANNING / "user-stories").glob("E*.md")):
        texto = archivo.read_text(encoding="utf-8").replace("\r", "")
        for m in _PATRON.finditer(texto):
            historias[m[1]] = {
                "titulo": m[2].strip(),
                "moscow": m[3],
                "depende": re.findall(r"HU-[\d.]+", m[4]),
            }
    return historias


def cargar():
    """Devuelve (sprints, historias, equipos).

    Cada sprint trae sus historias como tuplas (id, sp, equipo, etiqueta).
    historias[id] = {titulo, epica, moscow, valor, depende}.
    """
    datos = json.loads((PLANNING / "sprints.json").read_text(encoding="utf-8"))
    leidas = _leer_historias()
    historias = {}
    for hid, cat in datos["catalogo"].items():
        h = leidas.get(hid, {})
        historias[hid] = {
            "titulo": h.get("titulo") or cat.get("titulo", hid),
            "epica": "E" + hid[3:].split(".")[0] if hid.startswith("HU-") else "—",
            "moscow": h.get("moscow", "Must"),
            "valor": str(cat["valor"]) if cat.get("valor") is not None else "—",
            "depende": h.get("depende", []),
        }
    faltan = sorted(set(leidas) - set(historias))
    if faltan:
        raise SystemExit(f"Historias de user-stories/ sin entrada en el catálogo de sprints.json: {faltan}")

    sprints = []
    for s in datos["sprints"]:
        s = dict(s)
        s["historias"] = [(h["id"], h["sp"], h["equipo"], h.get("etiqueta")) for h in s["historias"]]
        for hid, *_ in s["historias"]:
            if hid not in historias:
                raise SystemExit(f"Sprint {s['n']}: {hid} no está en el catálogo de sprints.json")
        sprints.append(s)
    return sprints, historias, datos["equipos"]


def total(sprint):
    return sum(h[1] for h in sprint["historias"])


def dependencias_mismo_sprint(sprint, historias):
    """Para cada historia del sprint, las historias del mismo sprint de las que depende."""
    ids = {h[0] for h in sprint["historias"]}
    return {h[0]: [d for d in historias[h[0]]["depende"] if d in ids and d != h[0]] for h in sprint["historias"]}
