"""Regenera el plan a partir de docs/planning/sprints.json y docs/planning/user-stories/.

    python3 docs/herramientas/generar_plan.py            # PlanMVP.md + los dos PDF (en macOS)
    python3 docs/herramientas/generar_plan.py --sin-pdf  # solo PlanMVP.md y los HTML en build/

- Reescribe en PlanMVP.md el bloque entre <!-- inicio:sprints --> y <!-- fin:sprints -->.
- Revisa que la tabla de la línea de tiempo de PlanMVP.md tenga los mismos SP por sprint.
- Escribe build/plan.html y build/trim.html y, si hay `swift` (macOS), los convierte en
  docs/planning/KilometroCero-Plan.pdf y docs/planning/TrimBreakDown.pdf.
  En otro sistema, abrir los HTML en el navegador e imprimir a PDF (tamaño carta, sin márgenes).
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from plan_datos import PLANNING, cargar, dependencias_mismo_sprint, total

AQUI = Path(__file__).resolve().parent
BUILD = AQUI / "build"
INICIO, FIN = "<!-- inicio:sprints -->", "<!-- fin:sprints -->"


def tabla(sprint, historias):
    deps = dependencias_mismo_sprint(sprint, historias)
    filas = ["| Historia | Descripción | Épica | MoSCoW | Valor | SP | Equipo |", "|---|---|---|---|---|---|---|"]
    for hid, pts, equipo, etiqueta in sprint["historias"]:
        h = historias[hid]
        if etiqueta:
            etiqueta = "versión delgada" if etiqueta == "delgada" else etiqueta
        desc = h["titulo"] + (f" *({etiqueta})*" if etiqueta else "")
        moscow = h["moscow"] + (" · depende de " + ", ".join(deps[hid]) if deps[hid] else "")
        filas.append(f"| **{hid}** | {desc} | {h['epica']} | {moscow} | {h['valor']} | {pts} | {equipo} |")
    filas.append(f"| | **{len(sprint['historias'])} historias** | | | | **{total(sprint)}** | |")
    return "\n".join(filas)


def seccion(sprint, historias):
    estado = " · ✅ Terminado" if sprint.get("estado") else ""
    texto = f"### Sprint {sprint['n']} · {sprint['titulo']} ({sprint['fechas']}) · {total(sprint)} SP{estado}\n\n"
    texto += tabla(sprint, historias) + "\n\n"
    if sprint.get("nota"):
        texto += sprint["nota"] + "\n\n"
    return texto + f"**Demo:** {sprint['demo']}\n"


def actualizar_plan_md(sprints, historias):
    ruta = PLANNING / "PlanMVP.md"
    texto = ruta.read_text(encoding="utf-8")
    if INICIO not in texto or FIN not in texto:
        raise SystemExit(f"PlanMVP.md no tiene los marcadores {INICIO} y {FIN}")
    bloque = "\n".join(seccion(sp, historias) for sp in sprints)
    antes, resto = texto.split(INICIO, 1)
    despues = resto.split(FIN, 1)[1]
    ruta.write_text(f"{antes}{INICIO}\n{bloque}{FIN}{despues}", encoding="utf-8")

    # La línea de tiempo se escribe a mano: solo se avisa si sus SP no coinciden.
    avisos = 0
    for sp in sprints:
        m = re.search(rf"^\| \*{{0,2}}{sp['n']}\*{{0,2}}[^|]*\|[^|]*\|[^|]*\| (\d+) \|", antes, re.M)
        if not m:
            print(f"Aviso: no se encontró la fila del Sprint {sp['n']} en la línea de tiempo de PlanMVP.md")
            avisos += 1
        elif int(m[1]) != total(sp):
            print(f"Aviso: la línea de tiempo dice {m[1]} SP para el Sprint {sp['n']}, pero sprints.json suma {total(sp)}")
            avisos += 1
    return avisos


def a_pdf(html, pdf):
    if not shutil.which("swift"):
        print(f"Sin swift: abre {html} en el navegador e imprímelo a PDF.")
        return
    subprocess.run(["swift", str(AQUI / "html_a_pdf.swift"), str(html), str(pdf)], check=True)


def main():
    sprints, historias, _ = cargar()
    avisos = actualizar_plan_md(sprints, historias)
    print("PlanMVP.md actualizado" + (f" ({avisos} avisos)" if avisos else ""))

    import pdf_plan
    import pdf_trim

    BUILD.mkdir(exist_ok=True)
    salidas = {"plan.html": (pdf_plan.HTML, "KilometroCero-Plan.pdf"), "trim.html": (pdf_trim.HTML, "TrimBreakDown.pdf")}
    for nombre, (html, pdf) in salidas.items():
        (BUILD / nombre).write_text(html, encoding="utf-8")
        if "--sin-pdf" not in sys.argv:
            a_pdf(BUILD / nombre, PLANNING / pdf)
    print("Listo")


if __name__ == "__main__":
    main()
