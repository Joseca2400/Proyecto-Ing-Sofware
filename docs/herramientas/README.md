# Herramientas de documentación

Generan las tablas de sprints de `docs/planning/PlanMVP.md` y los PDF del plan a partir de una sola fuente.

| Archivo | Qué hace |
|---|---|
| `../planning/sprints.json` | **Fuente única** del reparto: historias por sprint, SP, equipo, etiqueta (delgada, resto…), demo y textos de cada sprint; catálogo con el valor de cada historia |
| `plan_datos.py` | Carga `sprints.json` y lee título, MoSCoW y dependencias desde `../planning/user-stories/` |
| `generar_plan.py` | Punto de entrada: actualiza `PlanMVP.md`, revisa la línea de tiempo y produce los PDF |
| `pdf_plan.py` · `pdf_trim.py` | Páginas de `KilometroCero-Plan.pdf` y `TrimBreakDown.pdf` (el texto fijo vive aquí) |
| `estilos.css` | Estilos compartidos de ambos PDF |
| `html_a_pdf.swift` | Convierte el HTML en PDF con WebKit (macOS) |

## Uso

```bash
python3 docs/herramientas/generar_plan.py            # PlanMVP.md + PDF (macOS)
python3 docs/herramientas/generar_plan.py --sin-pdf  # PlanMVP.md + HTML en docs/herramientas/build/
```

Solo usa la biblioteca estándar de Python 3.9 o superior. Sin macOS, abre `build/plan.html` y `build/trim.html` en el navegador e imprímelos a PDF (tamaño carta, sin márgenes, con gráficos de fondo).

## Cómo cambiar el plan

1. Para mover una historia de sprint o de equipo, o cambiar sus SP, edita `sprints.json`.
2. Para cambiar el título, el MoSCoW o las dependencias de una historia, edita su archivo en `user-stories/`.
3. Ejecuta `generar_plan.py` y commitea juntos `sprints.json`, `PlanMVP.md` y los dos PDF.
4. Si cambian los SP de un sprint, el generador avisa: ajusta a mano la línea de tiempo (sección 3) de `PlanMVP.md`.
