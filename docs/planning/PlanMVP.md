# Plan v5 · MVP en 3 sprints con 6 desarrolladores

Versión 5 · 31 de octubre de 2026 · Sustituye al plan v3 ([Old/PlanSprints.md](Old/PlanSprints.md)) y al ajuste v4 ([Old/AjustePlaneacion.md](Old/AjustePlaneacion.md)). El detalle del primer sprint está en [Sprint1.md](Sprint1.md).

Se apoya en dos hechos nuevos:
- **El Sprint 0 está terminado.** La arquitectura está construida y verificada (Angular, FastAPI y PostgreSQL 16, con Alembic, Docker y CI): ver [Sprint0-HelloWorld.md](../arquitectura/Sprint0-HelloWorld.md). No hay que montar el ambiente ni decidir el stack.
- **El equipo pasa de 3 a 6 desarrolladores.** Eso permite construir en paralelo el costo de la unidad, la contabilidad y la línea de ingreso, en lugar de hacerlo en secuencia.

## Contenido

1. [Resumen](#1-resumen)
2. [Supuestos de capacidad](#2-supuestos-de-capacidad)
3. [Equipo y módulos](#3-equipo-y-módulos)
4. [Línea de tiempo](#4-línea-de-tiempo)
5. [Alcance del MVP](#5-alcance-del-mvp)
6. [Detalle de los sprints del MVP](#6-detalle-de-los-sprints-del-mvp)
7. [Puesta en marcha y releases siguientes](#7-puesta-en-marcha-y-releases-siguientes)
8. [Recortes y orden de sacrificio](#8-recortes-y-orden-de-sacrificio)
9. [Riesgos](#9-riesgos)
10. [Ceremonias y definiciones](#10-ceremonias-y-definiciones)
11. [Cómo se fue ajustando la planeación](#11-cómo-se-fue-ajustando-la-planeación)

## 1. Resumen

| | Plan v4 | **Plan v5 (este)** |
|---|---|---|
| Equipo | 3 desarrolladores | **6 desarrolladores en 3 equipos de 2** |
| Sprint 1 | 4 semanas (02/11 – 27/11) | **2 semanas (02/11 – 13/11)**; el Sprint 0 ya resolvió la infraestructura |
| MVP | Al cierre del Sprint 5 · 12/02/2027 | **Al cierre del Sprint 3 · 11/12/2026**, antes del receso |
| Arranque en operación | 26/02/2027 | **15/01/2027** (Sprint 4) |
| Release 1.1 | 09/04/2027 | **12/02/2027** |
| Release 2 (venta y financiamiento) | 21/05/2027 | **12/03/2027** |
| Fin del plan | 04/06/2027 | **26/03/2027** |
| Alcance del MVP | 212 SP | **184 SP** comprometidos (4 historias, 26 SP, pasan a la puesta en marcha) |
| Historias descartadas | 6 (24 SP) | **Las mismas 6**; no se descarta nada más |

**El MVP no cambia de fondo:** sigue siendo el ciclo de la línea de alquiler de punta a punta y contabilizado (comprar e importar, reacondicionar, dar de alta, alquilar, facturar con FEL, cobrar, pagar, cerrar el mes y ver la rentabilidad por unidad). Lo que cambia es que se construye en 6 semanas con el doble de gente trabajando en paralelo.

## 2. Supuestos de capacidad

| Dato | Valor |
|---|---|
| Duración del sprint | 2 semanas (10 días hábiles) |
| Capacidad bruta | 6 × 10 = 60 días-persona por sprint |
| Ceremonias | 1 día por persona y sprint → **54 días-persona planificables** |
| Velocidad del plan v4 | 40 SP por sprint con 3 personas (hipótesis, nunca medida) |
| **Velocidad supuesta con 6 personas** | **60 SP en el Sprint 1** (incorporación de 3 personas nuevas) y **70 SP desde el Sprint 2** |
| Capacidad del MVP (S1–S3) | 60 + 70 + 70 = **200 SP** |
| Alcance comprometido del MVP | **184 SP** (92 %), margen de 16 SP |

**Por qué no se supone el doble (80 SP).** Duplicar el equipo no duplica la velocidad: hay que incorporar a 3 personas, coordinar 3 frentes y aumentan los puntos de integración. Se supone un 75 % a 88 % de rendimiento por persona nueva. Al cierre del Sprint 1 se mide la velocidad real y se recalcula el plan.

**Qué aporta el Sprint 0.** HT-01 queda casi hecha: ambiente reproducible, migraciones, CI y esqueleto modular. Solo falta el ambiente de pruebas desplegado (1 SP de los 3 originales). El Sprint 1 empieza construyendo historias desde el primer día.

## 3. Equipo y módulos

Cada equipo es dueño de sus módulos **de punta a punta** (pantalla en `frontend/src/app/features/`, API en `backend/app/modulos/`, migraciones y pruebas), como pide la [arquitectura](../arquitectura/Arquitectura-Propuesta.md). En cada equipo va una persona del equipo original y una nueva, para transferir el contexto.

| Equipo | Nombre | Módulos que posee | Épicas |
|---|---|---|---|
| **A** | Plataforma y contabilidad | `seguridad`, `comun` (auditoría), `contabilidad`, `configuracion` (catálogo, dimensiones, bancos) | E1, E2 |
| **B** | Ciclo de la unidad | `unidades`, `compras`, `taller`, `configuracion` (tipo de cambio), rentabilidad por unidad en `reportes` | E1, E3 (flota), E4, E5, E7 |
| **C** | Ingreso | Base del front (`core/`, `shared/`), `alquileres`, `facturacion` (clientes, FEL, cobros), `configuracion` (perfil fiscal: es el emisor de la FEL) | E1, E3 (alquiler), E6 |

**Reglas de convivencia entre equipos:**
- `contabilidad` es de A. B y C generan sus partidas llamando a su servicio; nunca escriben en sus tablas.
- `configuracion` se reparte: A tiene el catálogo, las dimensiones y los bancos; B, el tipo de cambio; C, el perfil fiscal.
- El contrato entre equipos es el OpenAPI de FastAPI. Un cambio que rompa un endpoint usado por otro equipo se acuerda antes de integrarlo.
- La base del front (login, menú por rol, componentes de tabla, formulario y árbol) es de C. Los otros equipos la usan, no la duplican.

## 4. Línea de tiempo

| Sprint | Fechas | Objetivo | SP | Release |
|---|---|---|---|---|
| **0** ✅ | 30/10/2026 | Arquitectura construida y verificada (hello world) | — | Base |
| **1** | 02/11 – 13/11/2026 | Base contable, compra en USD y preparación del ingreso | 51 | MVP |
| **2** | 16/11 – 27/11/2026 | Unidad de punta a punta hasta la flota, y contrato de alquiler | 64 | MVP |
| **3** | 30/11 – 11/12/2026 | Facturar, cobrar, pagar, cerrar el mes y ver la rentabilidad | 69 | MVP |
| 🚀 | **11/12/2026** | **MVP: la línea de alquiler opera de punta a punta en ambiente de pruebas** | | |
| *Receso* | 14/12/2026 – 01/01/2027 | | | |
| **4** | 04/01 – 15/01/2027 | Puesta en marcha: libros legales, carga inicial y lo que salió del MVP | 64 | Arranque |
| 🚀 | **15/01/2027** | **Arranque en operación** | | |
| 5–6 | 18/01 – 12/02/2027 | Lo diferido del MVP: corte completo, importación, retenciones, taller completo, cierres y reportes | 116 | Release 1.1 |
| 7–8 | 15/02 – 12/03/2027 | Venta de contado, comisiones, financiamiento y cartera | 117 | Release 2 |
| 9 | 15/03 – 26/03/2027 | Controles restantes, tablero y casos de borde | 42 | Release 3 |

El Sprint 1 queda más liviano (51 SP) porque el equipo C dedica buena parte a la base del front y a la prueba de punta a punta, y porque se incorporan las personas nuevas. Su holgura se usa como margen.

## 5. Alcance del MVP

| Bloque | Historias | SP |
|---|---|---|
| Corte del Sprint 1 v3 (versión delgada), menos lo que hizo el Sprint 0 | 22 historias, más el resto de HT-01 | 58 |
| Alquiler: tarifario, contrato, depósitos y cierre | HU-3.05, 3.06, 3.07, 3.08, 3.09, 6.01 | 24 |
| Base: perfil fiscal, depreciación, reversión, usuarios (resto) | HU-1.01, 3.02, 2.05, 1.09 (resto) | 14 |
| Facturación FEL | HU-6.02, 6.05, 2.03 (resto) | 21 |
| Cobrar y pagar | HU-1.08, 6.07, 2.09, 6.11, 6.12, 4.09, 4.13, 4.14 | 36 |
| Cerrar el mes y ver la rentabilidad | HU-2.07, 2.08, 2.12, 3.13, 7.02, 7.04 | 31 |
| **Total** | | **184** |

Las 6 historias descartadas en la v4 siguen descartadas, con las mismas condiciones para volver (ver [Old/AjustePlaneacion.md, sección 5.1](Old/AjustePlaneacion.md#51-historias-descartadas-6-historias-24-sp)).

## 6. Detalle de los sprints del MVP

Entre paréntesis, los SP de cada historia. Las del corte usan la versión delgada de [Old/Sprint1-v3.md](Old/Sprint1-v3.md#5-alcance-por-historia-versión-delgada); sus restos siguen en el Release 1.1.

### Sprint 1 · Base contable, compra en USD y preparación del ingreso (02/11 – 13/11) · 51 SP

| Equipo | Historias | SP |
|---|---|---|
| **A** | HT-01 resto: ambiente de pruebas desplegado (1) · HU-1.09 Usuarios y roles (2) · HU-1.11 Bitácora (2) · HU-1.10 Separación de funciones (3) · HU-2.01 Partida manual (3) · HU-2.02 Revisión de partidas (3) · HU-1.02 Catálogo de cuentas (3) · HU-1.04 Dimensiones (2) | 19 |
| **B** | HU-1.05 Unidades por VIN (3) · HU-1.06 Tipo de cambio (2) · HU-1.07 Transacciones en USD (3) · HU-4.01 Proveedores (1) · HU-4.02 Compra en EE. UU. (4) · HU-4.04 Gastos de importación (3) · HU-4.07 Etapas de importación (2) · HU-4.09 Facturas de compras y gastos locales (5) | 23 |
| **C** | Base del front (login, menú por rol, componentes) · prueba de punta a punta en CI · adaptador FEL con simulador · HU-1.01 Perfil fiscal (3) · HU-6.01 Clientes (3) · HU-3.05 Tarifario (3) | 9 |

**Demo (13/11):** inicio de sesión con roles; compra en USD de una unidad con su partida y sus gastos de importación, todo auditado; una factura local de proveedor con su cuenta por pagar; el contador no puede aprobar su propia partida manual; se registran el perfil fiscal, un cliente y una tarifa.

### Sprint 2 · Unidad de punta a punta hasta la flota, y contrato de alquiler (16/11 – 27/11) · 64 SP

| Equipo | Historias | SP |
|---|---|---|
| **A** | HU-2.03 Partidas automáticas, completa (5 + 3) · HU-2.16 Balance y mayor (3) · HU-2.05 Revertir una partida (3) · HU-1.08 Cuentas bancarias (3) · HU-2.09 Diferencial cambiario realizado (5) | 22 |
| **B** | HU-5.01 Orden de taller (2) · HU-5.02 Tarifa de mano de obra (1) · HU-5.03 Mano de obra (2) · HU-5.07 Cierre de orden (3) · HU-4.08 Hoja de costo (2) · HU-3.01 Alta en flota (3) · HU-3.02 Parámetros de depreciación (5) · HU-7.04 Unidades por etapa (3) | 21 |
| **C** | HU-3.06 Contrato de alquiler (5) · HU-3.07 Depósitos en garantía (5) · HU-3.08 Cierre de contrato (3) · HU-6.02 Factura FEL, parte 1: documento, correlativo y partida con el simulador (8) | 21 |

**Demo (27/11):** el recorrido completo del corte original (compra, importación, taller, hoja de costo conciliada con el mayor y alta en flota con sus parámetros de depreciación); la unidad se alquila con depósito y el contrato se cierra al devolverla; se emite una factura contra el simulador FEL.

### Sprint 3 · Facturar, cobrar, pagar, cerrar el mes y ver la rentabilidad (30/11 – 11/12) · 69 SP

| Equipo | Historias | SP |
|---|---|---|
| **A** | HU-2.07 Depreciación mensual (8) · HU-2.08 Revaluación de saldos en USD (5) · HU-2.12 Cierre mensual (5) · HU-1.09 Usuarios (resto) (3) | 21 |
| **B** | HU-4.13 Programar y aprobar pagos (5) · HU-4.14 Pago a proveedor (5) · HU-3.13 Rentabilidad por contrato y unidad (5) · HU-7.02 Rentabilidad en todo el ciclo (5) · HU-6.12 Antigüedad de saldos de clientes (5) | 25 |
| **C** | HU-6.02 Factura FEL, parte 2: certificador real en ambiente de pruebas (5) · HU-6.05 Anular FEL (5) · HU-6.07 Cobros (5) · HU-6.11 Estado de cuenta del cliente (3) · HU-3.09 Cargos adicionales (5) | 23 |

**Demo del MVP (11/12):** el contrato cerrado, con un cargo por combustible, se factura con el certificador en pruebas y se anula una factura; se cobra en USD con diferencial cambiario; se paga la compra al proveedor; el contador deprecia, revalúa y cierra noviembre; la gerencia ve la rentabilidad de la unidad.

### Dependencias revisadas

El reparto respeta el campo "Depende de" de cada historia en `user-stories/`, con estas precisiones:

| Historia | Depende de | Cómo se resuelve |
|---|---|---|
| HU-6.07 Cobros, HU-4.14 Pago | HU-2.09 Diferencial cambiario | El diferencial se adelanta al Sprint 2 (A), un sprint antes que cobros y pagos |
| HU-3.02 Parámetros de depreciación | HU-3.01 Alta en flota | Ambas en el Sprint 2 (B), en ese orden |
| HU-6.01 Clientes | HU-1.01 Perfil fiscal | Ambas en el Sprint 1 (C); el perfil fiscal pasa a C porque es el emisor de la FEL |
| HU-6.02 Factura FEL | HU-2.03 Partidas automáticas | Ambas en el Sprint 2: la parte 1 de la FEL usa el contrato del motor contable publicado en el Sprint 1 |
| HU-6.11, HU-6.12 | HU-6.07 Cobros | Mismo sprint: los cobros (C) se integran a más tardar el miércoles 02/12, primera semana del Sprint 3 |
| HU-4.14 Pago | HU-4.13 Programar pagos | Mismo sprint y mismo equipo (B), en ese orden |
| HU-3.13 Rentabilidad por contrato | HU-3.10 Facturación recurrente (sale del MVP) | **Se relaja:** los ingresos salen de las facturas individuales de HU-6.02; la dependencia con HU-3.10 es de comodidad, no de datos |
| HU-7.02 Rentabilidad en todo el ciclo | HU-8.12 Resultado de la venta (Release 2) | Igual que en la v4: en el MVP cubre el ciclo hasta la flota y se completa con la venta en el Release 2 |

## 7. Puesta en marcha y releases siguientes

**Sprint 4 · Puesta en marcha (04/01 – 15/01/2027) · 64 SP**

- Lo que la v4 tenía para arrancar: HU-2.15 Libros legales (8), HU-10.01 Plantillas de carga (5), HU-10.02 Saldos iniciales (3), HU-10.03 Flota con valor en libros (5), HU-10.05 Clientes y proveedores con saldos (5), HU-10.08 Contratos vigentes (3), HU-10.09 Conciliación del arranque (5), HU-10.11 Capacitación (2), HU-10.12 Soporte inicial (2).
- Las 4 historias que salieron del MVP (sección 8): HU-1.12 Respaldos (5), HU-6.03 Notas de crédito (5), HU-3.10 Facturación recurrente (8), HU-2.10 Conciliación bancaria (8).

Así el arranque del 15/01/2027 tiene todo lo que la v4 tenía para el 26/02/2027.

**Releases siguientes** (mismos grupos de historias que la v4, ahora a 70 SP por sprint):

| Release | Sprints | Fechas | Contenido (sprints de la v4) | SP |
|---|---|---|---|---|
| 1.1 | 5–6 | 18/01 – 12/02/2027 | Endurecer el corte e importación completa; retenciones, taller completo, seguros y anticipos; cierres avanzados, ocupación, baja de flota y reportes (v4 S7–S9) | 116 (holgura de 24) |
| 2 | 7–8 | 15/02 – 12/03/2027 | Venta de contado y comisiones; venta financiada; cuotas, mora y cartera (v4 S10–S12) | 117 |
| 3 | 9 | 15/03 – 26/03/2027 | Controles restantes, tablero y casos de borde (v4 S13) | 42 |

La lista de historias de cada grupo está en [Old/AjustePlaneacion.md, sección 4](Old/AjustePlaneacion.md#releases-siguientes). Se reparte por equipos en la planeación de cada sprint.

## 8. Recortes y orden de sacrificio

### Historias que salen del MVP (pasan al Sprint 4, antes del arranque)

| Historia | SP | Alternativa mientras tanto |
|---|---|---|
| **HU-1.12** Respaldar y restaurar la información | 5 | Respaldo automático de PostgreSQL desde la infraestructura (`pg_dump` programado) y procedimiento de restauración documentado; falta la función dentro del sistema |
| **HU-6.03** Emitir notas de crédito | 5 | Anular la factura (HU-6.05) y emitir una nueva |
| **HU-3.10** Facturar contratos de forma recurrente | 8 | Facturar contrato por contrato con HU-6.02 |
| **HU-2.10** Conciliar las cuentas bancarias | 8 | Conciliación fuera del sistema durante el primer cierre del ambiente de pruebas |

Ninguna es necesaria para demostrar el ciclo en pruebas, y todas vuelven antes de operar en serio.

### Si la velocidad real es menor que la supuesta

Se sacrifica en este orden, sin tocar el recorrido central (costo, alta, contrato, factura, cobro, cierre):

1. HU-6.12 Antigüedad de saldos de clientes (5)
2. HU-7.04 Unidades por etapa (3)
3. HU-3.09 Cargos adicionales (5)
4. HU-2.05 Revertir una partida (3)
5. HU-7.02 Rentabilidad en todo el ciclo (5); se mantiene HU-3.13

**No se recortan:** autenticación y permisos, auditoría, la hoja de costo conciliada, el alta en flota, el contrato, la factura FEL, el cobro, la depreciación y el cierre mensual. Si alguno peligra, se informa y se mueve la fecha del MVP; no se presenta incompleto.

## 9. Riesgos

| Riesgo | Efecto | Respuesta |
|---|---|---|
| **Incorporar a 3 personas al mismo tiempo** | El Sprint 1 rinde menos de lo supuesto | Parejas mixtas (una persona original y una nueva por equipo); `CLAUDE.md`/`AGENTS.md` y la arquitectura como guía; K1 incluye la puesta al día |
| **El certificador FEL no está elegido** | El Sprint 3 no puede facturar con el certificador real | Fecha límite: **20/11/2026**, con credenciales del ambiente de pruebas. El Sprint 2 construye la factura contra el simulador del adaptador, así que solo falta conectar el real. Plan B: demostrar el MVP con el simulador y conectar el certificador en el Sprint 4 |
| **Tres equipos tocando lo mismo** | Conflictos e integración tardía | Dueños de módulo claros (sección 3), contrato por OpenAPI, CI obligatoria en cada pull request e integración continua a `main`, no al final del sprint |
| **Dependencias dentro del Sprint 3** | Estado de cuenta, antigüedad de saldos, pagos o cierre no llegan | Cobros integrados el 02/12 y programación de pagos antes que el pago; el cierre mensual va después de la depreciación. Si los cobros se atrasan, HU-6.12 es lo primero que se sacrifica |
| **El contador no alcanza a validar a este ritmo** | Retrabajo en partidas, depreciación y cierre | Una sesión semanal fija (sección 10) con casos concretos preparados de antemano |
| **Velocidad sin medir** | El MVP no cabe en 3 sprints | Medir al cierre del Sprint 1 y aplicar el orden de sacrificio de la sección 8 en la planeación del Sprint 2 |
| **El receso empieza el 14/12** | No hay colchón después del MVP | El 11/12 es fecha fija; lo que no esté aceptado pasa al Sprint 4 y se informa en la demo |
| **La empresa es agente de retención** | Los pagos del MVP salen sin retención | Confirmar antes del 13/11; si lo es, HU-4.11 (5) entra al Sprint 3 y HU-6.12 sale |

## 10. Ceremonias y definiciones

| Ceremonia | Cuándo | Quiénes |
|---|---|---|
| Planeación | Lunes de inicio de sprint, 2 horas | Todo el equipo |
| Daily | Diario, 10 minutos por equipo, más 10 minutos de sincronización entre los 3 | Cada equipo; un representante por equipo en la sincronización |
| Integración | Miércoles de la segunda semana | Todo el equipo: el recorrido del sprint pasa en el ambiente de pruebas |
| Revisión (demo) | Viernes de cierre | Equipo, responsables y, cuando aplique, el contador |
| Retrospectiva | Viernes de cierre, 45 minutos | Todo el equipo |
| Sesión con el contador | Miércoles 04/11, 11/11, 18/11, 25/11, 02/12 y aceptación el 09/12 | Equipo dueño del tema y el contador |

**Definición de terminado por historia:** cumple sus criterios desde la pantalla; las pruebas de reglas, permisos y casos de rechazo pasan en CI contra PostgreSQL; los cambios quedan auditados; la migración se aplica desde una base vacía; los criterios diferidos quedan en el backlog con su sprint de destino.

**Terminado para el MVP (11/12):** el ciclo completo pasa desde el navegador, con sesión real, en el ambiente de pruebas; documento y partida se confirman juntos; las partidas cuadran en quetzales y la hoja de costo concilia con el mayor; los cuatro roles respetan sus permisos; el contador valida el caso de costo, la factura y el cierre, y queda evidencia.

**Avance:** criterios aceptados entre criterios acordados, igual que en la v3. No se promedia para ocultar un criterio obligatorio incumplido.

## 11. Cómo se fue ajustando la planeación

| Versión | Fecha | Qué cambió | Por qué |
|---|---|---|---|
| v1 | 23/10/2026 | 10 épicas, 130 historias, User Story Mapping en 3 releases | Primera planeación a partir de la entrevista con el cliente |
| v2 | 30/10/2026 | `Planning.md`: corte transversal, valor de negocio y puntos de historia | La consigna pide un corte transversal |
| v3 | 30/10/2026 | Sprint 1 de 4 semanas hasta el alta en flota, con 3 desarrolladores; 16 sprints | El corte de v2 era demasiado ancho y el equipo era de 3 personas |
| v4 | 30/10/2026 | MVP en 4 sprints después del Sprint 1 (12/02/2027); 6 historias descartadas | Llegar antes a algo usable |
| Sprint 0 | 30/10/2026 | Arquitectura definida y construida: Angular, FastAPI y PostgreSQL | Base técnica verificada antes de empezar las historias |
| **v5** | **31/10/2026** | **Este documento: 6 desarrolladores en 3 equipos por módulo, sprints de 2 semanas, MVP al cierre del Sprint 3 (11/12/2026) y arranque el 15/01/2027** | **Plazo mucho más corto con el doble de equipo** |
