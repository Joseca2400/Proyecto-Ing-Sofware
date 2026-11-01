"""Construye el HTML del plan de trabajo (KilometroCero-Plan.pdf) en la variable HTML. Lo usa generar_plan.py.

El texto de las páginas fijas (portada, resumen, identidad, la aplicación, estrategia) vive aquí;
las historias, los SP y los equipos salen de docs/planning/sprints.json.
"""

import html
from datetime import date
from pathlib import Path

from plan_datos import cargar, dependencias_mismo_sprint, total

e = html.escape
CSS = (Path(__file__).parent / "estilos.css").read_text(encoding="utf-8")
SPRINTS, H, EQUIPOS = cargar()
POR_N = {sp["n"]: sp for sp in SPRINTS}
MVP_SP = sum(total(sp) for sp in SPRINTS if sp["release"] == "MVP")
EN_PLAN = {h[0] for sp in SPRINTS for h in sp["historias"]}
DESCARTADAS = [k for k in H if k.startswith("HU-") and k not in EN_PLAN]


LOGO = lambda w: f'''<svg width="{w}" viewBox="0 0 120 168" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<path d="M0 60 A60 60 0 0 1 120 60 L120 60 L0 60 Z" fill="#F2A900"/><rect x="0" y="58" width="120" height="110" fill="#0E4A5A"/>
<text x="60" y="48" text-anchor="middle" font-family="Inter" font-weight="800" font-size="30" fill="#0E4A5A">KM</text>
<text x="60" y="140" text-anchor="middle" font-family="Inter" font-weight="800" font-size="74" fill="#fff">0</text>
<rect x="26" y="150" width="68" height="6" rx="3" fill="#F2A900"/></svg>'''

def wordmark(size=56, sub=13):
    return f'''<div class="wm"><div class="wm-t" style="font-size:{size}px">Kilómetro Cero</div>
<div class="wm-s" style="font-size:{sub}px"><span class="dash"></span><span class="dash"></span><span class="dash"></span>EQUIPO DE DESARROLLO</div></div>'''



pages = []
def page(body, cls="page", footer=True):
    pages.append((cls, body, footer))

# 1 Portada
page(f'''<div class="logo">{LOGO(92)}{wordmark(46, 12)}</div>
<div style="margin-top:44px" class="kicker">Ingeniería de Software · Plan de trabajo</div>
<h1>Sistema administrativo y financiero para alquiler, venta y taller de vehículos</h1>
<p class="lead">Plan del equipo: la base que ya funciona y la hoja de ruta sprint por sprint hasta el MVP del 11 de diciembre de 2026, con sus historias de usuario.</p>
<div style="position:absolute;left:80px;right:80px;top:700px"><table><tr><th>Integrantes</th><th class="num">Carné</th></tr>
<tr><td>Jose Carlos Eli Hernandez Quezel</td><td class="num">24007031</td></tr>
<tr><td>Dilson Koka´ib´ Morales Tajiboy</td><td class="num">23000163</td></tr>
<tr><td>Carlos Alexander Madrid de Leon</td><td class="num">23010900</td></tr></table></div>
<div class="foot"><span>Equipo Kilómetro Cero</span><span>Guatemala, 31 de octubre de 2026</span></div>''', "page cover", False)

# 2 Resumen
page('''<div class="kicker">01 · Resumen del plan</div><h1>Lo que va a tener la empresa</h1>
<p style="font-size:14px">Construimos un <b>sistema administrativo y financiero</b> que lleva la contabilidad de todo el ciclo de cada vehículo, de la compra en Estados Unidos a la venta, y le dice a la gerencia <b>cuánto costó y cuánto deja cada unidad</b>, en quetzales y en dólares.</p>
<div class="cards">
<div class="card"><div class="big">Hoy</div><div class="small">la base técnica funciona de punta a punta: pantalla, API y base de datos</div></div>
<div class="card"><div class="big">27/11/2026</div><div class="small">cada unidad se costea hasta la flota y se alquila, desde el navegador</div></div>
<div class="card"><div class="big">11/12/2026</div><div class="small"><b style="color:#0E4A5A">MVP:</b> contrato, factura FEL, cobro, pago y cierre del mes</div></div>
<div class="card"><div class="big">26/03/2027</div><div class="small">sistema completo, con venta y financiamiento de unidades</div></div></div>
<div class="cols"><div>
<h3>Lo que ya construimos (Sprint 0)</h3>
<p>La base técnica sobre la que se construye todo: la aplicación web, la API y la base de datos, conectadas y verificadas. Todo el ambiente se levanta con un solo comando y cada cambio pasa por pruebas automáticas antes de integrarse. Las reglas más delicadas ya están en la base: montos exactos en dos monedas, permisos validados en el servidor y una sola puerta para generar partidas contables.</p>
<h3 style="margin-top:14px">Cómo trabajamos</h3>
<p>En entregas de dos semanas, con tres equipos en paralelo: <b>plataforma y contabilidad</b>, <b>ciclo de la unidad</b> e <b>ingreso</b>. Al final de cada entrega se muestra algo que funciona con un caso real de la empresa, para revisarlo antes de seguir.</p>
<h3 style="margin-top:14px">Arranque en operación</h3>
<p>El <b>15/01/2027</b>, después de cargar los saldos iniciales, la flota existente, clientes, proveedores y contratos vigentes.</p>
</div><div>
<h3>Lo que necesitamos de la empresa</h3>
<table><tr><th>Decisión o dato</th><th>Para cuándo</th></tr>
<tr><td>Sesión con su contador para validar las cuentas y el caso de compra</td><td>04/11/2026</td></tr>
<tr class="z"><td>Confirmar si hay créditos vigentes con compradores</td><td>04/11/2026</td></tr>
<tr><td>Régimen de ISR y si la empresa es agente de retención</td><td>13/11/2026</td></tr>
<tr class="z"><td>Tarifas de alquiler, depósitos y cargos adicionales</td><td>13/11/2026</td></tr>
<tr><td>Elegir el certificador de facturación electrónica (FEL)</td><td>20/11/2026</td></tr></table>
<p class="note">Si alguna de estas respuestas se retrasa, se mueve la fecha del sprint que la necesita; el resto del plan sigue.</p>
</div></div>''')

# 3 Identidad
sw = [("#0E4A5A","Azul petróleo","#0E4A5A · principal"),("#F2A900","Ámbar señal","#F2A900 · acento"),("#2F7F8F","Petróleo claro","#2F7F8F · apoyo"),("#1C2A30","Tinta","#1C2A30 · texto"),("#5B6B71","Gris asfalto","#5B6B71 · secundario"),("#EEF3F4","Niebla","#EEF3F4 · fondos")]
sws = "".join(f'<div class="sw"><div class="c" style="background:{c}"></div><div class="l"><b>{n}</b><br>{d}</div></div>' for c,n,d in sw)
page(f'''<div class="kicker">02 · Identidad del equipo</div><h1>Kilómetro Cero</h1>
<p style="font-size:13.5px">El <b>kilómetro cero</b> es el mojón desde el que se miden todas las carreteras. Lo elegimos porque el sistema hace lo mismo con cada vehículo: registra desde su punto de partida, la compra en Estados Unidos, todo lo que cuesta y todo lo que produce hasta su venta. El VIN es el hilo que lo recorre de punta a punta.</p>
<div class="panel" style="margin-top:12px"><h3>Logotipo</h3>
<div style="display:flex;align-items:center;gap:22px;margin:10px 0 12px">{LOGO(70)}{LOGO(70)}{wordmark(46,12)}</div>
<p class="note" style="margin:0">Símbolo: un mojón de carretera con la marca <b>KM 0</b>. Versión vertical para íconos y avatares; versión horizontal para documentos y la aplicación, donde ya se usa en la barra superior.</p></div>
<div class="cols" style="margin-top:16px"><div class="panel"><h3>Gama de colores</h3>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:8px">{sws}</div></div>
<div class="panel"><h3>Por qué estos colores</h3>
<p><b>Azul petróleo:</b> transmite confianza y seriedad, lo que se espera de un sistema contable que maneja dinero en dos monedas.</p>
<p><b>Ámbar señal:</b> es el color de los mojones y la señalización vial; se usa sólo como acento, para hitos, alertas y llamados a la acción.</p>
<p><b>Neutros:</b> tinta, gris asfalto y niebla para el texto y las tablas, que son la mayor parte de la aplicación.</p>
<h3 style="margin-top:12px">Tipografía</h3>
<p><b style="font-size:17px;color:#0E4A5A;font-weight:800">Inter</b> para títulos, texto y cifras, con números tabulares para que los montos se alineen en las tablas.</p></div></div>''')

# 4 La aplicación
flow = [("E4","Comprar","En subasta o dealer de EE. UU., en dólares"),("E4","Importar","Flete, aduana, DAI, IVA, DUCA"),("E5","Reacondicionar","Taller propio; se capitaliza"),("E3","Alquilar","Activo fijo, contratos, depreciación"),("E8 · E9","Vender","Contado o financiado, con comisión"),("E5","Postventa","Garantía o servicio facturado")]
fl = '<span class="arrow">›</span>'.join(f'<div class="step"><div class="ep">{a}</div><div class="st">{b}</div><div class="sd">{c}</div></div>' for a,b,c in flow)
page(f'''<div class="kicker">03 · La aplicación</div><h1>Qué es y para quién</h1>
<p>La empresa opera en Guatemala desde una sola sede. Su negocio principal es el alquiler de vehículos: los importa usados desde Estados Unidos, los repara en su propio taller y los pone en renta. Al final de su vida útil los vende, normalmente con financiamiento propio, y el taller sigue atendiéndolos en la postventa.</p>
<p>La aplicación es un sistema administrativo y financiero que centraliza la contabilidad y el control económico de todo ese ciclo, para que la gerencia sepa con datos confiables cuánto cuesta y cuánto deja cada vehículo.</p>
<h3 style="margin-top:12px">El ciclo de vida de una unidad: el eje del sistema</h3>
<div class="flow">{fl}</div>
<p class="note">Todas las transacciones se ligan al VIN de la unidad. Eso permite calcular la rentabilidad completa de cada vehículo, de la importación a la venta. Facturación FEL (E6), contabilidad (E2) y reportes (E7) atraviesan todo el ciclo.</p>
<div class="cols" style="margin-top:14px"><div><h3>Usuarios y roles</h3>
<table><tr><th>Rol</th><th>Qué hace</th></tr>
<tr><td><b>Auxiliar contable</b></td><td>Registra documentos y operaciones</td></tr>
<tr class="z"><td><b>Contador</b></td><td>Revisa, contabiliza, concilia y cierra</td></tr>
<tr><td><b>Gerente financiero</b></td><td>Aprueba pagos, ajustes, créditos y reaperturas</td></tr>
<tr class="z"><td><b>Gerencia</b></td><td>Sólo consulta reportes y tableros</td></tr></table>
<div class="box">Regla de control interno: <b>quien registra una transacción no puede aprobarla.</b></div></div>
<div><h3>Contexto fiscal y financiero</h3>
<table class="kv">
<tr><td>Impuestos</td><td>Normativa guatemalteca de IVA e ISR; facturación electrónica FEL ante la SAT</td></tr>
<tr class="z"><td>Monedas</td><td>Quetzal como moneda funcional y dólar, con el tipo de cambio del Banguat por fecha</td></tr>
<tr><td>Importación</td><td>Los costos de importación y de taller se suman al costo de la unidad; el IVA de importación es crédito fiscal</td></tr>
<tr class="z"><td>Ventas</td><td>Financiamiento propio con intereses y comisiones a vendedores; no se reciben vehículos en parte de pago</td></tr></table></div></div>''')

# 5 Módulos
eps = [("E1","Configuración, multimoneda y seguridad","Catálogo, dimensiones por línea y VIN, tipo de cambio del Banguat, roles, bitácora y respaldos","Must",12),
("E2","Contabilidad general y cierre","Partidas manuales y automáticas, depreciación, diferencial cambiario, conciliación, cierres y libros legales","Must",16),
("E3","Flota, activos fijos y alquileres","Alta como activo, depreciación, contratos, depósitos, cargos, facturación recurrente y ocupación","Must",15),
("E4","Importación, compras y cuentas por pagar","Compra en EE. UU. en USD, gastos de importación, DUCA, prorrateo, hoja de costo, retenciones y pagos","Must",16),
("E5","Taller interno y postventa","Órdenes de trabajo por VIN, mano de obra, repuestos y destino contable de cada orden","Must",10),
("E6","Facturación electrónica y cuentas por cobrar","Facturas FEL, notas, anulaciones, cobros, anticipos y antigüedad de saldos","Must",12),
("E7","Reportes gerenciales","Estados financieros por línea, rentabilidad por unidad, ocupación, cartera y tablero","Must",10),
("E8","Venta de unidades y comisiones","Inventario en venta, precios, venta de contado o financiada, comisiones y margen","Should",12),
("E9","Financiamiento propio y cartera","Planes de crédito, amortización, intereses, cobro de cuotas, mora y provisión","Should",15),
("E10","Migración y arranque","Carga inicial, conciliación del arranque, capacitación y soporte","Must",12)]
rows = "".join(f'<tr class="{"z" if i%2 else ""}"><td class="id">{a}</td><td><b>{b}</b><br><span style="color:#5B6B71">{c}</span></td><td class="c">{d}</td><td class="num">{n}</td></tr>' for i,(a,b,c,d,n) in enumerate(eps))
page(f'''<div class="kicker">03 · La aplicación</div><h1>Módulos: las 10 épicas</h1>
<table><tr><th>Épica</th><th>Módulo y alcance</th><th class="c">MoSCoW</th><th class="num">Historias</th></tr>{rows}
<tr class="tot"><td></td><td>130 historias de usuario · 546 puntos de historia</td><td></td><td class="num">130</td></tr></table>
<div class="cols" style="margin-top:16px"><div class="box" style="margin:0"><h3>Fuera del alcance</h3>Multiempresa y consolidación · nómina (las comisiones se calculan pero se pagan por nómina) · presupuestos · integraciones bancarias automáticas · portal de clientes · taller para clientes externos.</div>
<div class="box" style="margin:0"><h3>Stack tecnológico</h3><b>Angular</b> para la aplicación web, <b>FastAPI</b> (Python) para la API, <b>PostgreSQL 16</b> como base de datos con migraciones versionadas, <b>Docker</b> para levantar todo con un comando y <b>GitHub Actions</b> para probar cada cambio. Un módulo por área de negocio, igual en la aplicación web y en la API.</div></div>''')

# 6 Estrategia y gantt
D0, D1 = date(2026,10,19), date(2027,3,31)
span = (D1-D0).days
def pos(d): return (d-D0).days/span*100
bars = [("Sprint 0","S0",date(2026,10,26),date(2026,10,30),"#1E7F4F"),
("Sprint 1","S1",date(2026,11,2),date(2026,11,13),"#0E4A5A"),("Sprint 2","S2",date(2026,11,16),date(2026,11,27),"#0E4A5A"),("Sprint 3","S3",date(2026,11,30),date(2026,12,11),"#0E4A5A"),
("Receso","receso",date(2026,12,14),date(2027,1,1),"#DCE4E6"),
("Sprint 4","S4",date(2027,1,4),date(2027,1,15),"#A77700"),("Sprint 5","S5",date(2027,1,18),date(2027,1,29),"#2F7F8F"),("Sprint 6","S6",date(2027,2,1),date(2027,2,12),"#2F7F8F"),
("Sprint 7","S7",date(2027,2,15),date(2027,2,26),"#7FA9B3"),("Sprint 8","S8",date(2027,3,1),date(2027,3,12),"#7FA9B3"),("Sprint 9","S9",date(2027,3,15),date(2027,3,26),"#B7CDD2")]
grows = "".join(f'<div class="g-row"><div class="g-lab">{l}</div><div class="g-track"><div class="g-bar" style="left:{pos(a):.2f}%;width:{max(pos(b)-pos(a),2.6):.2f}%;background:{c};{"color:#5B6B71" if l=="Receso" else ""}">{t}</div></div></div>' for l,t,a,b,c in bars)
months = [("OCT",date(2026,10,19),date(2026,11,1)),("NOV 26",date(2026,11,1),date(2026,12,1)),("DIC 26",date(2026,12,1),date(2027,1,1)),("ENE 27",date(2027,1,1),date(2027,2,1)),("FEB 27",date(2027,2,1),date(2027,3,1)),("MAR 27",date(2027,3,1),date(2027,3,31))]
mh = "".join(f'<div style="width:{(b-a).days/span*100:.2f}%">{n}</div>' for n,a,b in months)
miles = [("MVP",date(2026,12,11)),("Arranque",date(2027,1,15)),("R 1.1",date(2027,2,12)),("R2",date(2027,3,12)),("R3",date(2027,3,26))]
ml = "".join(f'<div class="g-line" style="left:calc(96px + (100% - 96px) * {pos(d)/100:.4f})"></div><div class="g-mlab" style="left:calc(96px + (100% - 96px) * {pos(d)/100:.4f})">{n}</div>' for n,d in miles)
page(f'''<div class="kicker">04 · Planeación</div><h1>Estrategia y línea de tiempo</h1>
<p><b>Corte transversal.</b> En lugar de terminar una épica antes de empezar la siguiente, cada sprint entrega un tramo del ciclo de la unidad con interfaz, seguridad y contabilidad reales. Los Sprints 1 y 2 llevan la unidad de la compra a la flota; en paralelo se prepara la línea de ingreso, que el Sprint 3 completa con la factura, el cobro, el pago y el cierre del mes.</p>
<p><b>Prioridad por valor.</b> Cada historia tiene un valor de 1 a 10: <b>Must 7 · Should 4 · Could 2</b>, más <b>+2</b> en E1 a E3, <b>+1</b> en E4 a E6 y <b>−1</b> en E8 y E9, más <b>+1</b> si forma parte del recorrido de la unidad.</p>
<div class="cards" style="margin:10px 0 12px">
<div class="card"><div class="big">3 sprints</div><div class="small">hasta el MVP, después de la base técnica</div></div>
<div class="card"><div class="big">11/12/2026</div><div class="small">MVP de la línea de alquiler</div></div>
<div class="card"><div class="big">{MVP_SP} SP</div><div class="small">en el MVP, en sprints de dos semanas</div></div>
<div class="card"><div class="big">6 descartes</div><div class="small">24 SP que no aplican a la empresa</div></div></div>
<div class="gantt"><div class="g-months">{mh}</div>{grows}<div style="height:18px"></div>{ml}</div>
<div class="legend"><span><i style="background:#1E7F4F"></i>Sprint 0 (terminado)</span><span><i style="background:#0E4A5A"></i>MVP</span><span><i style="background:#A77700"></i>Puesta en marcha</span><span><i style="background:#2F7F8F"></i>Release 1.1</span><span><i style="background:#7FA9B3"></i>Release 2</span><span><i style="background:#B7CDD2"></i>Release 3</span></div>
<h3>Equipos de trabajo</h3>
<div class="teams">
<div class="team"><div class="tl">EQUIPO A</div><div class="tn">Plataforma y contabilidad</div><div class="td">Seguridad, bitácora, catálogo, partidas, cierres y bancos</div></div>
<div class="team"><div class="tl">EQUIPO B</div><div class="tn">Ciclo de la unidad</div><div class="td">VIN, compras e importación, taller, flota, pagos, rentabilidad y venta de unidades</div></div>
<div class="team"><div class="tl">EQUIPO C</div><div class="tn">Ingreso</div><div class="td">Aplicación web base, perfil fiscal, clientes, alquiler, FEL, cobros y financiamiento</div></div></div>
<table class="kv"><tr><td>Sprints</td><td>De dos semanas, del 02/11/2026 al 26/03/2027. Receso del 14/12/2026 al 01/01/2027</td></tr>
<tr class="z"><td>Ritmo</td><td>60 SP en el Sprint 1 y 70 SP por sprint desde el Sprint 2, medido al cierre de cada sprint</td></tr>
<tr><td>Contador</td><td>Una sesión semanal para validar reglas y casos; aceptación del MVP el 09/12/2026</td></tr></table>''')

# Sprint pages
def sprint_page(sp, kicker, intro=None, extra=""):
    deps = dependencias_mismo_sprint(sp, H)
    cls = "done" if sp.get("estado") else {"Arranque":"arr","Release 1.1":"r11","Release 2":"r2","Release 3":"r3"}.get(sp["release"], "")
    tag = f'<span class="tag {cls}">{"Terminado" if sp.get("estado") else sp["release"]}</span>'
    rows, z = [], 0
    for eq in "ABC":
        hs = [h for h in sp["historias"] if h[2]==eq]
        if not hs: continue
        rows.append(f'<tr class="grp"><td colspan="5">Equipo {eq} · {EQUIPOS[eq]}</td><td class="num">{sum(h[1] for h in hs)}</td></tr>')
        for hid, pts, _, t in hs:
            h = H[hid]; z ^= 1
            chip = f'<span class="chip">{e(t)}</span>' if t else ""
            dep = f' <span class="dep">· {", ".join(d.replace("HU-","") for d in deps[hid])}</span>' if deps[hid] else ""
            rows.append(f'<tr class="{"z" if z else ""}"><td class="id">{hid}</td><td>{e(h["titulo"])}{chip}</td><td class="c">{h["epica"]}</td><td>{h["moscow"]}{dep}</td><td class="num">{h["valor"]}</td><td class="num">{pts}</td></tr>')
    n = len(sp["historias"])
    rows.append(f'<tr class="tot"><td></td><td>{n} historia{"s" if n != 1 else ""}</td><td></td><td></td><td></td><td class="num">{total(sp)}</td></tr>')
    nota = f'<p class="note">{e(sp["nota"])}</p>' if sp.get("nota") else ""
    partes = []
    if any(deps.values()):
        ej = next(d for d in deps.values() if d)[0]
        partes.append(f'En <b>MoSCoW</b>, los números en ámbar son historias del mismo sprint de las que depende (por ejemplo, <span class="dep">· {ej.replace("HU-","")}</span> = {ej}).')
    if any(h[3] == "delgada" for h in sp["historias"]):
        partes.append('<span class="chip">delgada</span> entrega los criterios del recorrido de la unidad; el resto se completa en un sprint posterior.')
    if any(h[3] == "resto" for h in sp["historias"]):
        partes.append('<span class="chip">resto</span> completa los criterios que la versión delgada dejó pendientes en el MVP.')
    leyenda = f'<p class="legend2">{" ".join(partes)}</p>' if partes else ""
    page(f'''<div class="kicker">{kicker}</div>
<div class="sp-head" style="margin-top:10px"><div class="badge {cls}">S{sp["n"]}</div><div><div class="sp-t" style="font-size:24px">{e(sp["titulo"])}</div><div class="sp-m">{sp["fechas"]} · {total(sp)} SP · {tag}</div></div></div>
{f"<p>{intro}</p>" if intro else ""}{extra}
<table class="st{" compacta" if len(sp["historias"]) > 22 else ""}"><tr><th style="width:68px">Historia</th><th>Descripción</th><th class="c" style="width:44px">Épica</th><th style="width:132px">MoSCoW</th><th class="num" style="width:40px">Valor</th><th class="num" style="width:30px">SP</th></tr>{"".join(rows)}</table>
{leyenda}{nota}<div class="box"><b>Demo:</b> {e(sp["demo"])}</div>''')

s0_extra = '''<div class="stats">
<div class="card"><div class="big">1 comando</div><div class="small">levanta la aplicación web, la API y la base de datos</div></div>
<div class="card"><div class="big">13 pruebas</div><div class="small">automáticas, en la API y en la aplicación web</div></div>
<div class="card"><div class="big">3 capas</div><div class="small">conectadas: Angular, FastAPI y PostgreSQL 16</div></div>
<div class="card"><div class="big">Cada cambio</div><div class="small">se prueba solo antes de integrarse</div></div></div>
<div class="cols" style="gap:20px;margin-bottom:6px"><div><h3>Qué quedó funcionando</h3><ul>
<li>Aplicación web con la marca, el menú de módulos y la pantalla de inicio</li>
<li>API organizada por módulos de negocio, con su documentación interactiva</li>
<li>Base de datos PostgreSQL 16 con migraciones versionadas</li>
<li>Ambiente completo con Docker e integración continua en GitHub</li></ul></div>
<div><h3>Reglas que ya trae la base</h3><ul>
<li>Montos exactos en quetzales y dólares, sin errores de redondeo</li>
<li>Los permisos se validan en el servidor, no sólo en la pantalla</li>
<li>Una sola puerta para crear partidas contables</li>
<li>Todos los cambios quedan listos para auditarse</li></ul></div></div>'''
def kicker(sp):
    if sp.get("estado"):
        partes = [f"Terminado el {sp['fechas'].split('–')[-1].strip()}"]
    else:
        etiqueta = sp.get("hito") or {"Arranque": "Puesta en marcha"}.get(sp["release"]) or (sp["release"] if sp["release"].startswith("Release") else None)
        partes = ([etiqueta] if etiqueta else []) + [sp["fechas"]]
    return f"{5 + sp['n']:02d} · Sprint {sp['n']} · " + " · ".join(partes)

for sp in SPRINTS:
    sprint_page(sp, kicker(sp), sp.get("intro"), s0_extra if sp["n"] == 0 else "")

def sp_de(*rels):
    return sum(total(sp) for sp in SPRINTS if sp["release"] in rels)

rel_rows = [("Base","S0","26/10 – 30/10/2026",sp_de("Base"),"#1E7F4F","Base técnica de la arquitectura"),("MVP","S1–S3","02/11 – 11/12/2026",sp_de("MVP"),"#0E4A5A","Ciclo de la línea de alquiler, de punta a punta"),("Arranque","S4","04/01 – 15/01/2027",sp_de("Arranque"),"#A77700","Puesta en marcha y primer cierre real"),("Release 1.1","S5–S6","18/01 – 12/02/2027",sp_de("Release 1.1"),"#2F7F8F","Lo diferido del MVP"),("Release 2","S7–S8","15/02 – 12/03/2027",sp_de("Release 2"),"#7FA9B3","Venta y financiamiento"),("Release 3","S9","15/03 – 26/03/2027",sp_de("Release 3"),"#B7CDD2","Funciones deseables")]
rr = "".join(f'<tr class="{"z" if i%2 else ""}"><td><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:{c};margin-right:8px"></span><b>{n}</b></td><td>{s_}</td><td>{f}</td><td>{t}</td><td class="num">{sp}</td></tr>' for i,(n,s_,f,sp,c,t) in enumerate(rel_rows))
page(f'''<div class="kicker">{5 + len(SPRINTS):02d} · Resumen</div><h1>Releases y sprints</h1>
<p>El plan completo suma <b>{len(EN_PLAN) - 1} historias de usuario y la infraestructura</b> en {len(SPRINTS)} sprints, del Sprint 0 al Sprint {SPRINTS[-1]["n"]}. Cada release se reparte entre los equipos A, B y C con el mismo criterio: cada equipo construye sus módulos de punta a punta.</p>
<table><tr><th>Entrega</th><th>Sprints</th><th>Fechas</th><th>Contenido</th><th class="num">SP</th></tr>{rr}
<tr class="tot"><td>Total</td><td>S0–S{SPRINTS[-1]["n"]}</td><td>26/10/2026 – 26/03/2027</td><td></td><td class="num">{sum(total(sp) for sp in SPRINTS)}</td></tr></table>
<div class="cols" style="margin-top:18px">
<div class="box" style="margin:0"><h3>Movidas al plan principal</h3><b>HU-2.11</b> Lista de verificación del cierre pasa del Release 2 al <b>Sprint 4</b>, para que el primer cierre real sea completo y reproducible.<br><br><b>HU-3.14</b> Alerta de fin de vida útil en flota pasa del Release 2 al <b>Sprint 2</b>, junto al alta en flota.</div>
<div class="box" style="margin:0"><h3>Historias descartadas ({len(DESCARTADAS)} · {sum(H[k]["sp"] for k in DESCARTADAS)} SP)</h3>Operar en paralelo (HU-10.10), cargar la cartera financiada (HU-10.06), importar el catálogo existente (HU-1.03), cargar unidades en proceso (HU-10.04), compras a particulares (HU-4.10) y reestructurar créditos (HU-9.15). No aplican a una empresa sin sistema previo ni créditos vigentes; vuelven al backlog si eso cambia.</div></div>
<p class="note" style="margin-top:14px">El total de SP cuenta las versiones delgadas y sus restos por separado; el desglose de lo que queda fuera del MVP está en TrimBreakDown.pdf.</p>''')

N = len(pages)
out = []
for i,(cls,body,footer) in enumerate(pages, 1):
    f = f'<div class="foot"><span>Kilómetro Cero · Plan de trabajo · Ingeniería de Software</span><span>Página {i} de {N}</span></div>' if footer else ""
    out.append(f'<section class="{cls}">{body}{f}</section>')
doc = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Kilómetro Cero · Plan de trabajo</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>{"".join(out)}</body></html>'''
HTML = doc
