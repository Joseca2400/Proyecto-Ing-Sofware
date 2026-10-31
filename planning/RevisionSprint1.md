# Revisión del prototipo contra el Sprint 1

Versión 1 · 30 de octubre de 2026 · Compara el código de [`../Segunda%20entrega/proyecto-vehiculos/backend`](../Segunda%20entrega/proyecto-vehiculos/backend/README.md) con [Sprint1.md](Sprint1.md) (versión 3): alcance por historia (sección 5), definición de terminado (sección 9) y guion de la demo (sección 10).

## 1. Conclusión

- **El backend cubre el recorrido completo del Sprint 1**, de la compra al alta en flota, con sesión real, permisos en el servidor, partidas atómicas y auditoría automática. Lo que falta es sobre todo **la interfaz web** (frente de Dev B y las pantallas de A6 y C1 a C7), **las migraciones con PostgreSQL** (A1) y **la validación del contador**.
- **Se propone presentarlo como prototipo técnico (Sprint 0)**: es la evidencia de "primeras iteraciones de desarrollo" de la entrega del 30/10. Respeta la regla del Sprint1.md de no contarlo como avance aceptado; el Sprint 1 lo toma como base y lo completa.
- **Se hicieron 8 ajustes al código** para alinearlo con el Sprint1.md (sección 4). Pasan **47 pruebas**, y la demo sigue el guion de 9 pasos de la sección 10.

## 2. Estado por historia

✅ cumple lo que el Sprint1.md incluye para esta historia · 🟡 cumple en el servidor; falta la pantalla u otra parte · ❌ no está

| Historia | Lo que pide el Sprint 1 | Estado | Qué falta | Dueño |
|---|---|---|---|---|
| HT-01 Infraestructura | Repositorio, ambiente reproducible, migraciones, CI, ambiente de pruebas | 🟡 | Migraciones (Alembic) y PostgreSQL. Ya hay Docker y el flujo de CI (`.github/workflows/pruebas.yml`), que falta activar en GitHub | A |
| HU-1.09 Usuarios y roles | Login con hash, sesión, cierre, 4 roles, permisos en servidor, cuentas iniciales | ✅ | La pantalla de login (B1) | A, B |
| HU-1.10 Separación de funciones | Quien registra no contabiliza; rechazo con motivo | ✅ | — | A |
| HU-1.11 Bitácora | Automática, sin edición ni borrado, valores anteriores y nuevos, filtros | ✅ | La vista de auditoría (B8) | A, B |
| HU-2.01 Partida manual | Captura desde pantalla, Q y USD, dimensiones, cuadre al enviar | 🟡 | La pantalla de captura (A6) | A |
| HU-2.02 Revisión de partidas | Borrador, revisión, contabilizada o devuelta; corrección y reenvío; correlativo | 🟡 | La bandeja de aprobación (A6) | A |
| HU-1.02 Catálogo | Semilla, consulta jerárquica, alta mínima | 🟡 | La pantalla con árbol (B2) | B |
| HU-1.04 Dimensiones | Línea de negocio y exigencia de VIN por cuenta | ✅ | — | B |
| HU-4.01 Proveedores | Alta y consulta, local o exterior, NIT validado | 🟡 | El formulario (B3) | B |
| HU-4.02 Compra en EE. UU. | Pantalla de compra USD con unidad, CxP y partida | 🟡 | La pantalla (B4) | B |
| HU-4.04 Gastos de importación | Gastos por VIN; IVA separado del costo | 🟡 | La pantalla (B5) | B |
| HU-2.16 Balance y mayor | Consultas desde la interfaz con filtros | 🟡 | La pantalla (B6) | B |
| HU-1.05 Unidades por VIN | Validación, unicidad, ficha mínima, estados e historial | 🟡 | La pantalla de ficha (C1) | C |
| HU-1.06 Tipo de cambio | Carga manual positiva; bloqueo si falta o ya se usó | 🟡 | La pantalla (C2) | C |
| HU-1.07 Transacciones en USD | Monto original, TC y quetzales; TC personalizado positivo con justificación | ✅ | Verificar los criterios originales antes de marcarla completa | C |
| HU-2.03 Partidas automáticas | Compra, gastos, cierre de orden y alta; origen; transacción atómica | ✅ | Pruebas de reversa ampliadas (C3) | C |
| HU-4.07 Etapas de importación | Tránsito, aduana, taller y lista, con validación y auditoría | ✅ | — | C |
| HU-4.08 Hoja de costo | Pantalla por VIN; conciliación con el mayor | 🟡 | La pantalla (C4) | C |
| HU-5.01 Orden de taller | Reacondicionamiento ligado al VIN y coherente con el estado | 🟡 | La pantalla (C5) | C |
| HU-5.02 Tarifa de mano de obra | Tarifa horaria única parametrizada | ✅ | Documentarla con el contador (11/11) | C |
| HU-5.03 Mano de obra | Horas, tarifa aplicada y costo por orden | 🟡 | La pantalla (C5) | C |
| HU-5.07 Cierre de orden | Capitaliza, bloquea la edición posterior, justificación de costo cero | ✅ | — | C |
| HU-3.01 Alta en flota | Sólo unidad lista y sin órdenes abiertas, costo conciliado, vida útil y residual | 🟡 | La pantalla (C7) | C |

## 3. Definición de terminado del sprint (sección 9)

| # | Criterio | Estado | Evidencia o pendiente |
|---|---|---|---|
| 1 | El ciclo pasa desde el navegador con sesión real | ❌ | La API está lista; faltan las pantallas (B1 a B8, C1 a C7) |
| 2 | No se duplica el VIN ni se saltan estados | ✅ | `test_hu_1_05_vin_validado`, `test_hu_4_07_orden_de_las_etapas` |
| 3 | USD con monto original, TC positivo y quetzales | ✅ | `test_hu_1_07_*` |
| 4 | Documento y partida juntos; una falla revierte todo | ✅ | `test_hu_2_03_documento_y_partida_se_confirman_juntos` |
| 5 | Partidas cuadran; hoja de costo concilia; el alta traslada el costo; el filtro por VIN no se exige cuadrado | ✅ | `test_hu_4_08_*`, `test_hu_3_01_*`, `test_hu_2_16_*` |
| 6 | El contador no aprueba su propia partida; permisos de los 4 roles | ✅ | `test_hu_2_02_y_hu_1_10_*`, `test_hu_1_09_*` |
| 7 | Borradores y devueltas se corrigen; contabilizadas no | ✅ | `test_hu_2_02_el_auxiliar_no_contabiliza_y_se_puede_devolver` |
| 8 | Auditoría con actor, fecha y valores; sin edición ni secretos | ✅ | `test_hu_1_11_*` (3 pruebas) |
| 9 | Migraciones y arranque desde base vacía; pruebas en CI | 🟡 | El arranque desde base vacía funciona; faltan Alembic y activar el CI en GitHub |
| 10 | El contador valida el caso de costo y alta | ❌ | Sesiones del 04/11 y 18/11 |

**Resultado:** 7 de 10 cumplidos en el servidor. Los 3 pendientes son trabajo del Sprint 1 que ya está planificado: la interfaz, las migraciones y la validación con el contador.

## 4. Ajustes hechos al código en esta revisión

| # | Ajuste | Criterio del Sprint1.md que cubre |
|---|---|---|
| 1 | **Login real**: contraseña con hash (PBKDF2), token de sesión con expiración y cierre de sesión. Se eliminó el atajo del encabezado `X-Usuario` | HU-1.09; acuerdo 4; DoD 1 y 6 |
| 2 | **Auditoría automática** en la capa de persistencia, con valores anteriores y nuevos; no guarda contraseñas, hashes ni tokens | HU-1.11; acuerdo 5; DoD 8 |
| 3 | **Corrección de partidas** en borrador o devueltas, sólo por quien las registró | HU-2.02; DoD 7 |
| 4 | **Tipo de cambio personalizado positivo** (antes aceptaba negativos) | HU-1.07; DoD 3; observación del compañero |
| 5 | **Catálogo jerárquico** (`GET /cuentas/arbol`) para el componente de árbol | HU-1.02; B1 y B2 |
| 6 | **Balance filtrado sin exigir cuadre**: con filtro por VIN o línea devuelve `cuadra: null` | DoD 5 |
| 7 | **Alquiler, factura, cobros y reportes apagados por defecto** (`SISTEMA_MODULOS_INGRESO=true` los enciende) | Sección 2: se retira el objetivo extendido |
| 8 | **CI y demo**: flujo de GitHub Actions y demo con el guion de 9 pasos de la sección 10 | HT-01; sección 10 |

Pruebas nuevas: login y cierre de sesión, contraseñas débiles, auditoría con valores, bitácora sin secretos, atomicidad, TC no positivo y catálogo jerárquico. Total: **47 pruebas**.

## 5. Decisiones para la sesión técnica del día 1 (K1)

| Tema | Estado en el prototipo | Decidir en K1 |
|---|---|---|
| Stack | Python, FastAPI, SQLAlchemy y Docker; base SQLite | Ratificarlo. El cambio a PostgreSQL es pequeño porque los montos ya usan el tipo decimal |
| Precisión monetaria en la API (acuerdo 2) | Los montos se calculan con decimales exactos, pero **la API los envía como número JSON** | Recomendado: enviarlos como texto (`"76598.00"`) para que el navegador no use punto flotante. Es un cambio del contrato que afecta a B y C |
| Interfaz | No hay; la API tiene CORS y un ejemplo en el README | Tecnología de la web de una sola página |
| Usar el prototipo | Existe y pasa la demo | **Partir de él** (lo recomendado, ahorra parte de A1 a A5 y C3 a C7) **o reescribirlo**. Si se parte de él, el Sprint 1 se enfoca en interfaz, migraciones, validación y endurecimiento, y quedan días libres para el margen |

## 6. Observaciones sobre Sprint1.md y PlanSprints.md

| Dónde | Observación | Propuesta |
|---|---|---|
| Ambos documentos | Dicen "no existe código" | Cambiar a "existe un prototipo técnico que no se cuenta como avance" y enlazar esta revisión |
| PlanSprints, sección 1 | La tabla dice "Versión 1 / Versión 2", pero el documento es la versión 3 | Corregir los encabezados |
| PlanSprints, sección 7 | Dice que "en el Sprint 1 el contrato lleva la tarifa capturada a mano", pero HU-3.06 ya no está en el Sprint 1 | Quitar la frase |
| PlanSprints, apéndice | HU-1.07 aparece terminada en el S1 con pendiente 0, contra la regla de no declarar completa una historia con criterios originales sin verificar | Dejar 1 SP pendiente hasta verificarla |
| PlanSprints, supuestos | Dice 57 SP del Sprint 1; la vista general dice 60 | Aclarar que la diferencia son los 3 SP de HT-01 |
| PlanSprints | El MVP termina el 07/05/2027 | Ver la propuesta de MVP en 4 sprints en [AjustePlaneacion.md](AjustePlaneacion.md) |

## 7. Cómo verlo

```bash
cd backend
python -m uvicorn app.main:app --reload     # borrar antes sistema.db si existe
python scripts/demo_ciclo.py                # en otra terminal: guion de 9 pasos
pytest                                      # 47 pruebas
```

Usuarios `aux`, `contador`, `gerente` y `gerencia`, todos con la contraseña `Demo2026!`.
