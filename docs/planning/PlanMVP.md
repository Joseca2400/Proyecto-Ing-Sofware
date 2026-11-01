# Plan del MVP · Kilómetro Cero

31 de octubre de 2026 · Plan de trabajo del sistema administrativo y financiero hasta el MVP (11/12/2026), el arranque en operación (15/01/2027) y el sistema completo (26/03/2027). El detalle operativo del sprint en curso está en [Sprint1.md](Sprint1.md). Las versiones anteriores del plan se conservan en [Old/](Old/).

## Contenido

1. [Objetivo y fechas clave](#1-objetivo-y-fechas-clave)
2. [Organización del trabajo](#2-organización-del-trabajo)
3. [Línea de tiempo](#3-línea-de-tiempo)
4. [Alcance del MVP](#4-alcance-del-mvp)
5. [Sprints](#5-sprints)
6. [Dependencias](#6-dependencias)
7. [Releases siguientes](#7-releases-siguientes)
8. [Puesta en marcha y orden de sacrificio](#8-puesta-en-marcha-y-orden-de-sacrificio)
9. [Riesgos](#9-riesgos)
10. [Ceremonias y definiciones](#10-ceremonias-y-definiciones)

## 1. Objetivo y fechas clave

**El MVP es el ciclo de la línea de alquiler de punta a punta y contabilizado:** comprar e importar una unidad, reacondicionarla, darla de alta en la flota, alquilarla, facturarla con FEL, cobrarla, pagar a los proveedores, cerrar el mes y ver la rentabilidad de cada unidad.

| Hito | Fecha |
|---|---|
| Base técnica de la arquitectura (Sprint 0) | ✅ 30/10/2026 |
| Compra en USD contabilizada desde el navegador | 13/11/2026 |
| La unidad llega a la flota y se alquila | 27/11/2026 |
| **MVP: la línea de alquiler opera de punta a punta en ambiente de pruebas** | **11/12/2026** |
| **Arranque en operación** | **15/01/2027** |
| Release 1.1: lo diferido del MVP | 12/02/2027 |
| Release 2: venta y financiamiento | 12/03/2027 |
| Release 3: funciones deseables | 26/03/2027 |

**Supuestos de trabajo**

| Tema | Supuesto |
|---|---|
| Sprints | De 2 semanas; receso del 14/12/2026 al 01/01/2027 |
| Ritmo | 60 SP en el Sprint 1 y 70 SP por sprint desde el Sprint 2; se mide al cierre de cada sprint |
| MVP | 184 SP en los Sprints 1 a 3, frente a 200 SP de capacidad |
| Contador | Una sesión semanal para validar reglas y casos |
| Créditos vigentes | No hay; si aparecen, la Épica 9 sube al MVP |

## 2. Organización del trabajo

El trabajo se reparte en tres equipos, cada uno dueño de sus módulos **de punta a punta** (pantalla en `frontend/src/app/features/`, API en `backend/app/modulos/`, migraciones y pruebas), como pide la [arquitectura](../arquitectura/Arquitectura-Propuesta.md).

| Equipo | Nombre | Módulos que posee | Épicas |
|---|---|---|---|
| **A** | Plataforma y contabilidad | `seguridad`, `comun` (auditoría), `contabilidad`, `configuracion` (catálogo, dimensiones, bancos) | E1, E2 |
| **B** | Ciclo de la unidad | `unidades`, `compras`, `taller`, `configuracion` (tipo de cambio), rentabilidad por unidad en `reportes` | E1, E3 (flota), E4, E5, E7 |
| **C** | Ingreso | Base del front (`core/`, `shared/`), `alquileres`, `facturacion` (clientes, FEL, cobros), `configuracion` (perfil fiscal, emisor de la FEL) | E1, E3 (alquiler), E6 |

**Reglas de convivencia entre equipos:**
- `contabilidad` es de A. B y C generan sus partidas llamando a su servicio; nunca escriben en sus tablas.
- `configuracion` se reparte: A tiene el catálogo, las dimensiones y los bancos; B, el tipo de cambio; C, el perfil fiscal.
- El contrato entre equipos es el OpenAPI de FastAPI. Un cambio que rompa un endpoint usado por otro equipo se acuerda antes de integrarlo.
- La base del front (login, menú por rol, componentes de tabla, formulario y árbol) es de C. Los otros equipos la usan, no la duplican.

**Prioridad por valor.** Cada historia tiene un valor de 1 a 10 (Must 7, Should 4, Could 2; +2 en E1 a E3, +1 en E4 a E6, −1 en E8 y E9; +1 si forma parte del recorrido de la unidad). Cada sprint se ordena por el flujo del ciclo, las dependencias y el valor.

## 3. Línea de tiempo

| Sprint | Fechas | Objetivo | SP | Release |
|---|---|---|---|---|
| **0** ✅ | 26/10 – 30/10/2026 | Base técnica de la arquitectura | 2 | Base |
| **1** | 02/11 – 13/11/2026 | Base contable, compra en USD y preparación del ingreso | 51 | MVP |
| **2** | 16/11 – 27/11/2026 | La unidad hasta la flota y el contrato de alquiler | 64 | MVP |
| **3** | 30/11 – 11/12/2026 | Facturar, cobrar, pagar, cerrar el mes y ver la rentabilidad | 69 | MVP |
| 🚀 | **11/12/2026** | **MVP** | | |
| *Receso* | 14/12/2026 – 01/01/2027 | | | |
| **4** | 04/01 – 15/01/2027 | Puesta en marcha | 64 | Arranque |
| 🚀 | **15/01/2027** | **Arranque en operación** | | |
| 5–6 | 18/01 – 12/02/2027 | Corte completo, importación detallada, retenciones, taller completo, cierres avanzados y reportes | 116 | Release 1.1 |
| 7–8 | 15/02 – 12/03/2027 | Venta de contado, comisiones, financiamiento y cartera | 117 | Release 2 |
| 9 | 15/03 – 26/03/2027 | Controles restantes, tablero y casos de borde | 42 | Release 3 |

## 4. Alcance del MVP

| Bloque | Historias | SP |
|---|---|---|
| Recorrido de la unidad, de la compra al alta en flota (versión delgada) y resto de la infraestructura | 22 historias y HT-01 | 58 |
| Alquiler: tarifario, contrato, depósitos, cargos y clientes | HU-3.05, 3.06, 3.07, 3.08, 3.09, 6.01 | 24 |
| Base: perfil fiscal, depreciación, reversión y administración de usuarios | HU-1.01, 3.02, 2.05, 1.09 (resto) | 14 |
| Facturación FEL | HU-6.02, 6.05, 2.03 (resto) | 21 |
| Cobrar y pagar | HU-1.08, 6.07, 2.09, 6.11, 6.12, 4.09, 4.13, 4.14 | 36 |
| Cerrar el mes y ver la rentabilidad | HU-2.07, 2.08, 2.12, 3.13, 7.02, 7.04 | 31 |
| **Total** | | **184** |

**Historias descartadas (6, 24 SP):** HU-10.10 Operar en paralelo, HU-10.06 Cargar la cartera financiada, HU-1.03 Importar el catálogo existente, HU-10.04 Cargar unidades en proceso, HU-4.10 Compras a particulares y HU-9.15 Reestructurar un crédito. No aplican a una empresa sin sistema previo ni créditos vigentes; cada una tiene su condición para volver en [Old/AjustePlaneacion.md](Old/AjustePlaneacion.md#51-historias-descartadas-6-historias-24-sp).

## 5. Sprints

En la columna **MoSCoW** se indica cuándo una historia depende de otra **del mismo sprint**; las dependencias con sprints anteriores ya están cubiertas. Las historias marcadas como *versión delgada* entregan los criterios del recorrido de la unidad; el resto de sus criterios se completa en el Release 1.1.

### Sprint 0 · Base técnica de la arquitectura (26/10 – 30/10/2026) · 2 SP · ✅ Terminado

| Historia | Descripción | Épica | MoSCoW | Valor | SP | Equipo |
|---|---|---|---|---|---|---|
| **HT-01** | Infraestructura y ambientes *(base técnica)* | — | Must | — | 2 | A |
| | **1 historias** | | | | **2** | |

**Demo:** La pantalla de Inicio en Angular consulta la API, que confirma la conexión con PostgreSQL 16 y la migración aplicada. Todo se levanta con un solo comando y la integración continua corre las pruebas en cada cambio.

### Sprint 1 · Base contable, compra en USD y preparación del ingreso (02/11 – 13/11/2026) · 51 SP

| Historia | Descripción | Épica | MoSCoW | Valor | SP | Equipo |
|---|---|---|---|---|---|---|
| **HT-01** | Infraestructura y ambientes *(ambiente de pruebas)* | — | Must | — | 1 | A |
| **HU-1.09** | Administrar usuarios y roles *(versión delgada)* | E1 | Must | 10 | 2 | A |
| **HU-1.11** | Consultar la bitácora de cambios *(versión delgada)* | E1 | Must · depende de HU-1.09 | 10 | 2 | A |
| **HU-1.10** | Separar funciones de registro y aprobación *(versión delgada)* | E1 | Must · depende de HU-1.09 | 10 | 3 | A |
| **HU-2.01** | Registrar una partida manual *(versión delgada)* | E2 | Must · depende de HU-1.02, HU-1.04, HU-1.07 | 10 | 3 | A |
| **HU-2.02** | Revisar y contabilizar partidas *(versión delgada)* | E2 | Must · depende de HU-2.01, HU-1.10 | 10 | 3 | A |
| **HU-1.02** | Mantener el catálogo de cuentas *(versión delgada)* | E1 | Must · depende de HU-1.01 | 10 | 3 | A |
| **HU-1.04** | Configurar las dimensiones analíticas *(versión delgada)* | E1 | Must · depende de HU-1.02 | 10 | 2 | A |
| **HU-1.05** | Registrar y validar unidades por VIN *(versión delgada)* | E1 | Must · depende de HU-1.04 | 10 | 3 | B |
| **HU-1.06** | Cargar el tipo de cambio de referencia del Banguat *(versión delgada)* | E1 | Must | 10 | 2 | B |
| **HU-1.07** | Registrar transacciones en dólares | E1 | Must · depende de HU-1.06 | 10 | 3 | B |
| **HU-4.01** | Registrar proveedores locales y del exterior *(versión delgada)* | E4 | Must · depende de HU-1.01 | 9 | 1 | B |
| **HU-4.02** | Registrar la compra de una unidad en EE. UU. *(versión delgada)* | E4 | Must · depende de HU-4.01, HU-1.05, HU-1.07 | 9 | 4 | B |
| **HU-4.04** | Registrar los gastos de importación *(versión delgada)* | E4 | Must | 9 | 3 | B |
| **HU-4.07** | Seguir el estado de la unidad durante la importación *(versión delgada)* | E4 | Must · depende de HU-1.05, HU-4.02 | 9 | 2 | B |
| **HU-4.09** | Registrar facturas de compras y gastos locales | E4 | Must · depende de HU-4.01 | 8 | 5 | B |
| **HU-1.01** | Registrar el perfil fiscal de la empresa | E1 | Must | 9 | 3 | C |
| **HU-6.01** | Registrar clientes | E6 | Must · depende de HU-1.01 | 9 | 3 | C |
| **HU-3.05** | Mantener el tarifario de alquiler | E3 | Must | 9 | 3 | C |
| | **19 historias** | | | | **51** | |

El equipo C construye además la base del front (login, menú por rol, tablas y formularios), la prueba automatizada del recorrido y el adaptador de facturación FEL con su simulador.

**Demo:** Inicio de sesión con roles; compra en USD de una unidad con su partida y sus gastos de importación, todo auditado; una factura local de proveedor con su cuenta por pagar; el contador no puede aprobar su propia partida manual; se registran el perfil fiscal, un cliente y una tarifa.

### Sprint 2 · La unidad hasta la flota y el contrato de alquiler (16/11 – 27/11/2026) · 64 SP

| Historia | Descripción | Épica | MoSCoW | Valor | SP | Equipo |
|---|---|---|---|---|---|---|
| **HU-2.03** | Generar partidas automáticas desde los módulos | E2 | Must | 10 | 8 | A |
| **HU-2.16** | Consultar el balance de comprobación y el mayor *(versión delgada)* | E2 | Must | 10 | 3 | A |
| **HU-2.05** | Revertir una partida contabilizada | E2 | Must | 9 | 3 | A |
| **HU-1.08** | Configurar cuentas bancarias en quetzales y dólares | E1 | Must | 9 | 3 | A |
| **HU-2.09** | Calcular el diferencial cambiario realizado | E2 | Must | 10 | 5 | A |
| **HU-5.01** | Abrir una orden de trabajo ligada a un VIN *(versión delgada)* | E5 | Must | 9 | 2 | B |
| **HU-5.02** | Configurar las tarifas de mano de obra *(versión delgada)* | E5 | Must | 9 | 1 | B |
| **HU-5.03** | Registrar mano de obra en la orden *(versión delgada)* | E5 | Must · depende de HU-5.01, HU-5.02 | 9 | 2 | B |
| **HU-5.07** | Cerrar la orden y generar su destino contable *(versión delgada)* | E5 | Must · depende de HU-5.03 | 9 | 3 | B |
| **HU-4.08** | Consultar la hoja de costo de una unidad *(versión delgada)* | E4 | Must | 9 | 2 | B |
| **HU-3.01** | Dar de alta una unidad como activo fijo de la flota *(versión delgada)* | E3 | Must · depende de HU-4.08, HU-5.07 | 10 | 3 | B |
| **HU-3.02** | Definir los parámetros de depreciación de cada unidad | E3 | Must · depende de HU-3.01 | 9 | 5 | B |
| **HU-7.04** | Consultar las unidades por etapa del ciclo | E7 | Must | 8 | 3 | B |
| **HU-3.06** | Registrar un contrato de alquiler | E3 | Must | 10 | 5 | C |
| **HU-3.07** | Recibir, aplicar y devolver depósitos en garantía | E3 | Must · depende de HU-3.06 | 9 | 5 | C |
| **HU-3.08** | Cerrar un contrato al devolver la unidad | E3 | Must · depende de HU-3.06 | 10 | 3 | C |
| **HU-6.02** | Emitir una factura FEL *(parte 1 · simulador)* | E6 | Must · depende de HU-2.03 | 9 | 8 | C |
| | **17 historias** | | | | **64** | |

**Demo:** Recorrido completo de la unidad: compra, importación, taller, hoja de costo conciliada con el mayor y alta en flota con sus parámetros de depreciación. La unidad se alquila con depósito, el contrato se cierra al devolverla y se emite una factura contra el simulador FEL.

### Sprint 3 · Facturar, cobrar, pagar, cerrar el mes y ver la rentabilidad (30/11 – 11/12/2026) · 69 SP

| Historia | Descripción | Épica | MoSCoW | Valor | SP | Equipo |
|---|---|---|---|---|---|---|
| **HU-2.07** | Calcular la depreciación mensual | E2 | Must | 9 | 8 | A |
| **HU-2.08** | Revaluar saldos en dólares al cierre | E2 | Must | 9 | 5 | A |
| **HU-2.12** | Cerrar un período mensual | E2 | Must | 9 | 5 | A |
| **HU-1.09** | Administrar usuarios y roles *(resto)* | E1 | Must | 10 | 3 | A |
| **HU-4.13** | Programar y aprobar pagos a proveedores | E4 | Must | 8 | 5 | B |
| **HU-4.14** | Registrar el pago a un proveedor | E4 | Must · depende de HU-4.13 | 8 | 5 | B |
| **HU-3.13** | Consultar la rentabilidad por contrato y por unidad | E3 | Must · depende de HU-2.07 | 9 | 5 | B |
| **HU-7.02** | Consultar la rentabilidad de cada unidad en todo su ciclo *(hasta la flota)* | E7 | Must · depende de HU-3.13 | 8 | 5 | B |
| **HU-6.12** | Consultar la antigüedad de saldos de clientes | E6 | Must · depende de HU-6.07 | 8 | 5 | B |
| **HU-6.02** | Emitir una factura FEL *(parte 2 · certificador)* | E6 | Must | 9 | 5 | C |
| **HU-6.05** | Anular un documento FEL | E6 | Must · depende de HU-6.02 | 8 | 5 | C |
| **HU-6.07** | Registrar cobros y aplicarlos a facturas | E6 | Must · depende de HU-6.02 | 9 | 5 | C |
| **HU-6.11** | Consultar el estado de cuenta de un cliente | E6 | Must · depende de HU-6.07 | 8 | 3 | C |
| **HU-3.09** | Registrar cargos adicionales del contrato | E3 | Must | 9 | 5 | C |
| | **14 historias** | | | | **69** | |

**Demo:** El contrato cerrado, con un cargo por combustible, se factura con el certificador en ambiente de pruebas y se anula una factura; se cobra en USD con diferencial cambiario; se paga la compra al proveedor; el contador deprecia, revalúa y cierra noviembre; la gerencia ve la rentabilidad de la unidad.

### Sprint 4 · Puesta en marcha (04/01 – 15/01/2027) · 64 SP

| Historia | Descripción | Épica | MoSCoW | Valor | SP | Equipo |
|---|---|---|---|---|---|---|
| **HU-2.15** | Emitir los libros legales | E2 | Must | 9 | 8 | A |
| **HU-2.10** | Conciliar las cuentas bancarias | E2 | Must | 9 | 8 | A |
| **HU-1.12** | Respaldar y restaurar la información | E1 | Must | 9 | 5 | A |
| **HU-10.02** | Cargar los saldos contables iniciales | E10 | Must · depende de HU-10.01 | 7 | 3 | A |
| **HU-10.01** | Descargar plantillas de carga y validar archivos | E10 | Must | 7 | 5 | B |
| **HU-10.03** | Cargar la flota con su valor en libros | E10 | Must · depende de HU-10.01 | 7 | 5 | B |
| **HU-10.09** | Conciliar el arranque y aceptar los saldos | E10 | Must · depende de HU-10.02, HU-10.08 | 7 | 5 | B |
| **HU-10.11** | Capacitar a los usuarios por rol (habilitación) | E10 | Must | 7 | 2 | B |
| **HU-10.12** | Dar soporte inicial tras el arranque (habilitación) | E10 | Must · depende de HU-10.09 | 7 | 2 | B |
| **HU-6.03** | Emitir notas de crédito | E6 | Must | 8 | 5 | C |
| **HU-3.10** | Facturar contratos de forma recurrente | E3 | Must | 9 | 8 | C |
| **HU-10.05** | Cargar clientes, proveedores y sus saldos abiertos | E10 | Must · depende de HU-10.01 | 7 | 5 | C |
| **HU-10.08** | Cargar los contratos de alquiler activos | E10 | Must · depende de HU-10.01 | 7 | 3 | C |
| | **13 historias** | | | | **64** | |

**Demo:** Se cargan los saldos iniciales, la flota existente con su valor en libros, clientes, proveedores y contratos vigentes; la conciliación del arranque da cero diferencias; se emiten los libros legales, se concilia el banco y se capacita a cada rol.

## 6. Dependencias

El reparto respeta el campo "Depende de" de cada historia en `user-stories/`. Decisiones tomadas para que el MVP cierre en el Sprint 3:

| Historia | Depende de | Cómo se resuelve |
|---|---|---|
| HU-6.07 Cobros, HU-4.14 Pago | HU-2.09 Diferencial cambiario | El diferencial se construye en el Sprint 2, antes que cobros y pagos |
| HU-6.01 Clientes, HU-4.01 Proveedores, HU-1.02 Catálogo | HU-1.01 Perfil fiscal | El perfil fiscal es lo primero del equipo C en el Sprint 1 |
| HU-6.02 Factura FEL | HU-2.03 Partidas automáticas | La parte 1 de la FEL usa el contrato del motor contable publicado en el Sprint 1 |
| HU-5.07 Cierre de orden, HU-4.08 Hoja de costo | HU-5.05, HU-5.06, HU-4.05 (Release 1.1) | Versión delgada: el MVP capitaliza solo mano de obra y carga los gastos por VIN; repuestos, subcontratos y prorrateo llegan en el Release 1.1 |
| HU-3.13 Rentabilidad por contrato | HU-3.10 Facturación recurrente (Sprint 4) | Los ingresos salen de las facturas individuales de HU-6.02; la dependencia con HU-3.10 es de comodidad, no de datos |
| HU-7.02 Rentabilidad en todo el ciclo | HU-8.12 Resultado de la venta (Release 2) | En el MVP cubre el ciclo hasta la flota; se completa con la venta en el Release 2 |

**Fechas de integración dentro de cada sprint:** el miércoles de la segunda semana el recorrido del sprint pasa en el ambiente de pruebas. En el Sprint 3, los cobros (C) se integran a más tardar el miércoles 02/12 porque el estado de cuenta y la antigüedad de saldos dependen de ellos.

## 7. Releases siguientes

A 70 SP por sprint, repartidos por equipo en la planeación de cada sprint.

| Release | Sprints | Fechas | Historias | SP |
|---|---|---|---|---|
| 1.1 | 5–6 | 18/01 – 12/02/2027 | **Corte completo e importación:** 1.02, 1.04, 1.05, 1.06, 1.10, 1.11, 2.01, 2.02, 2.16, 4.01, 4.02, 4.04, 4.07, 4.08, 5.01, 5.02, 5.03, 4.03, 4.05, 4.06 · **Retenciones, taller completo, seguros y anticipos:** 10.07, 4.11, 4.16, 3.01, 3.04, 5.07, 5.04, 5.05, 5.06, 6.08, 6.09 · **Cierres avanzados, ocupación, baja de flota y reportes:** 2.13, 2.14, 3.12, 3.15, 7.01, 7.03, 7.07, 7.09 | 116 |
| 2 | 7–8 | 15/02 – 12/03/2027 | **Venta de contado y comisiones:** 5.09, 7.06, 2.04, 2.06, 8.01, 8.02, 8.04, 8.07, 8.08, 8.09, 8.10, 8.12 · **Venta financiada y crédito:** 8.05, 9.01–9.08 · **Cuotas, mora y cartera:** 7.05, 2.11, 9.09, 9.10, 9.13, 9.14, 6.06, 3.03, 3.11, 3.14 | 117 |
| 3 | 9 | 15/03 – 26/03/2027 | **Controles restantes, tablero y casos de borde:** 4.12, 4.15, 5.10, 6.04, 6.10, 7.08, 7.10, 8.03, 8.06, 8.11, 9.11, 9.12, 5.08 | 42 |

En el Release 1.1, las historias del recorrido de la unidad (1.02 a 5.03, 3.01 y 5.07) completan los criterios que su versión delgada dejó pendientes.

## 8. Puesta en marcha y orden de sacrificio

### Historias que se entregan en la puesta en marcha

Cuatro historias del Release 1 se entregan en el Sprint 4, antes del arranque, porque el ciclo se puede demostrar sin ellas en ambiente de pruebas:

| Historia | SP | Mientras tanto |
|---|---|---|
| **HU-1.12** Respaldar y restaurar la información | 5 | Respaldo automático de PostgreSQL desde la infraestructura y procedimiento de restauración documentado |
| **HU-6.03** Emitir notas de crédito | 5 | Anular la factura (HU-6.05) y emitir una nueva |
| **HU-3.10** Facturar contratos de forma recurrente | 8 | Facturar contrato por contrato con HU-6.02 |
| **HU-2.10** Conciliar las cuentas bancarias | 8 | Conciliación fuera del sistema durante el primer cierre en pruebas |

### Si el ritmo medido es menor

Se sacrifica en este orden, sin tocar el recorrido central (costo, alta, contrato, factura, cobro y cierre):

1. HU-6.12 Antigüedad de saldos de clientes (5)
2. HU-7.04 Unidades por etapa (3)
3. HU-3.09 Cargos adicionales (5)
4. HU-2.05 Revertir una partida (3)
5. HU-7.02 Rentabilidad en todo el ciclo (5); se mantiene HU-3.13

**No se recortan:** autenticación y permisos, auditoría, la hoja de costo conciliada, el alta en flota, el contrato, la factura FEL, el cobro, la depreciación y el cierre mensual. Si alguno peligra, se informa y se mueve la fecha del MVP; no se presenta incompleto.

## 9. Riesgos

| Riesgo | Efecto | Respuesta |
|---|---|---|
| **El certificador FEL no está elegido** | El Sprint 3 no puede facturar con el certificador real | Fecha límite: **20/11/2026**, con credenciales del ambiente de pruebas. El Sprint 2 construye la factura contra el simulador del adaptador. Plan B: demostrar el MVP con el simulador y conectar el certificador en el Sprint 4 |
| **Tres equipos tocando lo mismo** | Conflictos e integración tardía | Dueños de módulo claros (sección 2), contrato por OpenAPI, CI obligatoria en cada pull request e integración continua a `main` |
| **Dependencias dentro del Sprint 3** | Estado de cuenta, antigüedad de saldos, pagos o cierre no llegan | Cobros integrados el 02/12 y programación de pagos antes que el pago; el cierre mensual va después de la depreciación. Si los cobros se atrasan, HU-6.12 es lo primero que se sacrifica |
| **El contador no alcanza a validar a este ritmo** | Retrabajo en partidas, depreciación y cierre | Una sesión semanal fija (sección 10) con casos concretos preparados de antemano |
| **Ritmo menor al previsto** | El MVP no cabe en 3 sprints | Se mide al cierre del Sprint 1 y se aplica el orden de sacrificio de la sección 8 en la planeación del Sprint 2 |
| **El receso empieza el 14/12** | No hay colchón después del MVP | El 11/12 es fecha fija; lo que no esté aceptado pasa al Sprint 4 y se informa en la demo |
| **La empresa es agente de retención** | Los pagos del MVP salen sin retención | Confirmar antes del 13/11; si lo es, HU-4.11 (5) entra al Sprint 3 y HU-6.12 sale |

## 10. Ceremonias y definiciones

| Ceremonia | Cuándo | Quiénes |
|---|---|---|
| Planeación | Lunes de inicio de sprint, 2 horas | Todo el equipo |
| Daily | Diario, 10 minutos por equipo, más 10 minutos de sincronización entre A, B y C | Cada equipo; un representante por equipo en la sincronización |
| Integración | Miércoles de la segunda semana | Todo el equipo: el recorrido del sprint pasa en el ambiente de pruebas |
| Revisión (demo) | Viernes de cierre | Equipo, responsables y, cuando aplique, el contador |
| Retrospectiva | Viernes de cierre, 45 minutos | Todo el equipo |
| Sesión con el contador | Miércoles 04/11, 11/11, 18/11, 25/11, 02/12 y aceptación el 09/12 | Equipo dueño del tema y el contador |

**Definición de terminado por historia:** cumple sus criterios desde la pantalla; las pruebas de reglas, permisos y casos de rechazo pasan en CI contra PostgreSQL; los cambios quedan auditados; la migración se aplica desde una base vacía; los criterios diferidos quedan en el backlog con su sprint de destino.

**Terminado para el MVP (11/12):** el ciclo completo pasa desde el navegador, con sesión real, en el ambiente de pruebas; documento y partida se confirman juntos; las partidas cuadran en quetzales y la hoja de costo concilia con el mayor; los cuatro roles respetan sus permisos; el contador valida el caso de costo, la factura y el cierre, y queda evidencia.

**Avance:** criterios aceptados entre criterios acordados. No se promedia para ocultar un criterio obligatorio incumplido.
