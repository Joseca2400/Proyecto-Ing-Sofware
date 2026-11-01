"""Construye el HTML de TrimBreakDown.pdf (lo que queda fuera del MVP) en la variable HTML. Lo usa generar_plan.py."""

import html
from pathlib import Path

from plan_datos import cargar, dependencias_mismo_sprint, total

e = html.escape
CSS = (Path(__file__).parent / "estilos.css").read_text(encoding="utf-8")
SPRINTS, H, EQUIPOS = cargar()
EN_PLAN = {h[0] for sp in SPRINTS for h in sp["historias"]}
DESCARTADAS = [k for k in H if k.startswith("HU-") and k not in EN_PLAN]

COL = {"Release 1.1":"#2F7F8F","Release 2":"#7FA9B3","Release 3":"#B7CDD2"}
FUERA = [sp for sp in SPRINTS if sp["release"].startswith("Release")]
todas = [(sp, h) for sp in FUERA for h in sp["historias"]]
n_tot, sp_tot = len(todas), sum(h[1] for _, h in todas)
restos = [h for _, h in todas if h[3] == "resto"]
should = [h for _, h in todas if H[h[0]]["moscow"] == "Should"]
rel_sp = {r: sum(total(sp) for sp in FUERA if sp["release"] == r) for r in COL}
EPN = {1:"E1 Configuración",2:"E2 Contabilidad",3:"E3 Flota y alquiler",4:"E4 Importación y compras",5:"E5 Taller",6:"E6 Facturación FEL",7:"E7 Reportes",8:"E8 Venta",9:"E9 Financiamiento",10:"E10 Arranque"}
ep = {}
for sp, h in todas:
    k = int(H[h[0]]["epica"][1:]); ep.setdefault(k, {r:0 for r in COL}); ep[k][sp["release"]] += h[1]
orden = sorted(ep, key=lambda k: -sum(ep[k].values()))
mx = max(sum(v.values()) for v in ep.values())
bars = "".join(f'<div class="r"><div class="lab">{EPN[k]}</div><div class="trk">' + "".join(f'<div style="width:{ep[k][r]/mx*100:.1f}%;background:{COL[r]}"></div>' for r in COL if ep[k][r]) + f'</div><div class="v">{sum(ep[k].values())}</div></div>' for k in orden)

pages = []
p1 = f'''<div class="kicker">TrimBreakDown · Plan de trabajo</div><h1>Lo que queda fuera del MVP</h1>
<p>El MVP del 11/12/2026 y la puesta en marcha del 15/01/2027 cubren el ciclo de la línea de alquiler. Este documento desglosa lo que se construye después, en los Sprints 5 a 9, para que el equipo lo revise antes de cada planeación.</p>
<div class="cards">
<div class="card"><div class="big">{n_tot} historias</div><div class="small">{sp_tot} SP en los Sprints 5 a 9</div></div>
<div class="card"><div class="big">{n_tot-len(restos)} nuevas</div><div class="small">{sp_tot-sum(h[1] for h in restos)} SP de trabajo nuevo</div></div>
<div class="card"><div class="big">{len(restos)} restos</div><div class="small">{sum(h[1] for h in restos)} SP que completan las versiones delgadas del MVP</div></div>
<div class="card"><div class="big">{len(should)} Should</div><div class="small">{sum(h[1] for h in should)} SP, sobre todo en los Releases 2 y 3</div></div></div>
<h3>SP por release</h3>
<div class="relbar">''' + "".join(f'<div style="flex:{rel_sp[r]};background:{COL[r]};{"color:#0E4A5A" if r=="Release 3" else ""}">{r} · {rel_sp[r]} SP</div>' for r in COL) + f'''</div>
<div style="display:flex;justify-content:space-between;font-size:10.5px;color:#5B6B71;margin-bottom:14px"><span>18/01/2027 · S5</span><span>12/02 · fin R1.1</span><span>12/03 · fin R2</span><span>26/03/2027 · S9</span></div>
<h3>SP por épica</h3><div class="bars">{bars}</div>
<div class="legend" style="margin-top:6px">''' + "".join(f'<span><i style="background:{COL[r]}"></i>{r}</span>' for r in COL) + '''</div>
<div class="cols" style="margin-top:6px">
<div class="box" style="margin:0"><h3>Por qué queda fuera</h3><b>Release 1.1:</b> mejora la exactitud o el control, pero tiene una alternativa manual temporal (gastos por VIN en lugar de prorrateo, retenciones fuera del sistema).<br><b>Release 2:</b> la venta y el financiamiento empiezan cuando las unidades salen de la flota.<br><b>Release 3:</b> funciones deseables (Should).</div>
<div class="box" style="margin:0"><h3>Ajustes al plan</h3><b>HU-2.11</b> Lista de verificación del cierre: del Release 2 al <b>Sprint 4</b>.<br><b>HU-3.14</b> Alerta de fin de vida útil en flota: del Release 2 al <b>Sprint 2</b>.<br>En el Sprint 4 también se entregan HU-1.12, HU-6.03, HU-3.10 y HU-2.10 (26 SP), antes del arranque.<br><b>Descartadas:</b> {len(DESCARTADAS)} historias ({sum(H[k]['sp'] for k in DESCARTADAS)} SP).</div></div>'''
pages.append(p1)

def bloque(sp):
    deps = dependencias_mismo_sprint(sp, H); c = COL[sp["release"]]
    rows, z = [], 0
    for eq in "ABC":
        hs = [h for h in sp["historias"] if h[2] == eq]
        if not hs: continue
        rows.append(f'<tr class="grp"><td colspan="5">Equipo {eq} · {EQUIPOS[eq]}</td><td class="num">{sum(h[1] for h in hs)}</td></tr>')
        for hid, pts, _, t in hs:
            h = H[hid]; z ^= 1
            chip = f'<span class="chip">{e(t)}</span>' if t else ""
            dep = f' <span class="dep">· {", ".join(d.replace("HU-","") for d in deps[hid])}</span>' if deps[hid] else ""
            rows.append(f'<tr class="{"z" if z else ""}"><td class="id">{hid}</td><td>{e(h["titulo"])}{chip}</td><td class="c">{h["epica"]}</td><td>{h["moscow"]}{dep}</td><td class="num">{h["valor"]}</td><td class="num">{pts}</td></tr>')
    return f'''<div class="mini"><div class="b" style="background:{c};{"color:#0E4A5A" if sp["release"]=="Release 3" else ""}">S{sp["n"]}</div><div><div class="t">{e(sp["titulo"])}</div><div class="m">{sp["fechas"]} · {sp["release"]} · {len(sp["historias"])} historias · {total(sp)} SP</div></div></div>
<table class="st compacta"><tr><th style="width:68px">Historia</th><th>Descripción</th><th class="c" style="width:44px">Épica</th><th style="width:132px">MoSCoW</th><th class="num" style="width:40px">Valor</th><th class="num" style="width:30px">SP</th></tr>{"".join(rows)}</table>'''

def pagina(grupo):
    rels = " y ".join(dict.fromkeys(sp["release"] for sp in grupo))
    nums = " y ".join(str(sp["n"]) for sp in grupo)
    titulo = f"Sprint{'s' if len(grupo) > 1 else ''} {nums}"
    return f'<div class="kicker">{rels}</div><h1 style="font-size:24px">{titulo}</h1>' + "".join(bloque(sp) for sp in grupo) + LEY

LEY = '<p class="legend2">En <b>MoSCoW</b>, los números en ámbar son historias del mismo sprint de las que depende. <span class="chip">resto</span> completa los criterios que la versión delgada dejó pendientes en el MVP.</p>'
# Agrupa los sprints en páginas de hasta ~36 filas (historias + grupos por equipo).
grupo, filas = [], 0
for sp in FUERA:
    n = len(sp["historias"]) + 3
    if grupo and filas + n > 36:
        pages.append(pagina(grupo)); grupo, filas = [], 0
    grupo.append(sp); filas += n
if grupo:
    pages.append(pagina(grupo))

N = len(pages)
out = "".join(f'<section class="page">{b}<div class="foot"><span>Kilómetro Cero · TrimBreakDown · Ingeniería de Software</span><span>Página {i} de {N}</span></div></section>' for i, b in enumerate(pages, 1))
HTML = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>TrimBreakDown</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"><style>{CSS}</style></head><body>{out}</body></html>'''
