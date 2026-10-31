# Ajuste de la planeación: MVP en 4 sprints

Versión 4 · 30 de octubre de 2026 · Ajusta el [Plan de sprints](PlanSprints.md) (versión 3) para llegar a un MVP en 4 sprints después del Sprint 1. El Sprint 1 no cambia: sigue siendo el de [Sprint1.md](Sprint1.md).

Este documento registra **qué se recorta, qué se descarta y por qué**, y cómo se fue ajustando la planeación desde la primera versión.

## Contenido

1. [Resumen del ajuste](#1-resumen-del-ajuste)
2. [Qué es el MVP](#2-qué-es-el-mvp)
3. [Línea de tiempo](#3-línea-de-tiempo)
4. [Detalle de los sprints del MVP](#4-detalle-de-los-sprints-del-mvp)
5. [Reporte de descartes y recortes](#5-reporte-de-descartes-y-recortes)
6. [Cómo se fue ajustando la planeación](#6-cómo-se-fue-ajustando-la-planeación)
7. [Riesgos del MVP corto](#7-riesgos-del-mvp-corto)

---

## 1. Resumen del ajuste

| | Plan v3 | **Plan v4 (este)** |
|---|---|---|
| MVP | Release 1 completo: 10 sprints después del Sprint 1 (S2–S11) | **4 sprints después del Sprint 1 (S2–S5)** |
| Fecha del MVP | 07/05/2027 | **12/02/2027** |
| Arranque en operación | 07/05/2027 | **26/02/2027** (Sprint 6), o 23/04/2027 si el cliente prefiere arrancar con el Release 1.1 |
| Release 2 (venta y financiamiento) | 02/07/2027 | **21/05/2027** |
| Fin del plan | 16/07/2027 (S16) | **04/06/2027 (S13)** |
| Historias descartadas | 0 | **6 (24 SP)** |
| Historias del R1 v3 que salen del MVP | — | **40 historias (119 SP), diferidas al Release 1.1 o posterior** |
| Velocidad supuesta | 40 SP por sprint de 2 semanas | **Igual** (hipótesis; se recalibra con el Sprint 1) |

Las cuentas cuadran con el plan v3: de los 489 SP pendientes tras el Sprint 1, **152 SP** van al MVP, **38 SP** a la puesta en marcha, **275 SP** a los releases siguientes y **24 SP** se descartan.

## 2. Qué es el MVP

**El MVP es el ciclo de la línea de alquiler, de punta a punta y contabilizado:** comprar e importar una unidad, reacondicionarla, darla de alta, alquilarla, facturarla con FEL real, cobrarla, pagar a los proveedores, cerrar el mes y ver la rentabilidad de cada unidad.

Es el mismo recorrido de la demo del Sprint 1, extendido hasta el ingreso y el cierre. El alquiler es la línea principal del negocio y lo que justifica arrancar.

| La empresa **puede** con el MVP | La empresa **todavía no puede** (y cuándo) |
|---|---|
| Costear cada unidad por VIN, de la compra al alta (S1) | Expediente de importación, prorrateo de contenedores y DUCA (S7) |
| Contratos con tarifa, depósito y cargos adicionales (S2–S3) | Seguros, marchamo y alertas de vencimiento (S8) |
| Facturar con FEL real, anular y emitir notas de crédito (S3) | Retenciones de IVA e ISR (S8; **sube al MVP** si son agentes de retención) |
| Cobrar con diferencial cambiario y ver la antigüedad de saldos de clientes (S4) | Repuestos y subcontratos en el taller (S8) |
| Registrar facturas de proveedores, aprobar y pagar (S4) | Estados financieros por línea de negocio, ocupación y exportar a PDF/Excel (S9) |
| Depreciar, revaluar USD, conciliar el banco y cerrar el mes (S5) | Cierre anual (S9; se necesita hasta enero de 2028) |
| Ver la rentabilidad por unidad y por contrato (S5) | Vender unidades y financiarlas (S10–S12) |

**Variante de 3 sprints.** Si el MVP tiene que caber en 3 sprints, se saca el Sprint 5 (cierre mensual y rentabilidad) y el MVP termina en la factura, el cobro y el pago, el 29/01/2027. No lo recomendamos: un sistema contable que no cierra el mes no se puede usar en producción, y la rentabilidad por unidad es lo que más le interesa a la gerencia.

## 3. Línea de tiempo

| Sprint | Fechas | Objetivo | Historias | SP | Release |
|---|---|---|---|---|---|
| **1** | 02/11 – 27/11/2026 | Corte transversal: de la compra al alta en flota (4 semanas) | 22 en versión delgada | 60 (ref.) | MVP |
| **2** | 30/11 – 11/12/2026 | Alquilar: del tarifario al contrato cerrado | 10 | 38 | MVP |
| *Receso* | 14/12/2026 – 01/01/2027 | | | | |
| **3** | 04/01 – 15/01/2027 | Facturar con FEL real | 6 | 39 | MVP |
| **4** | 18/01 – 29/01/2027 | Cobrar y pagar | 8 | 36 | MVP |
| **5** | 01/02 – 12/02/2027 | Cerrar el mes y ver la rentabilidad | 7 | 39 | MVP |
| 🚀 | **12/02/2027** | **MVP: la línea de alquiler opera de punta a punta en pruebas** | | | |
| **6** | 15/02 – 26/02/2027 | Puesta en marcha: libros legales y carga inicial mínima | 9 | 38 | Arranque |
| 🚀 | **26/02/2027** | **Arranque en operación** | | | |
| 7 | 01/03 – 12/03/2027 | Endurecer el corte e importación completa | 20 | 37 | Release 1.1 |
| 8 | 15/03 – 26/03/2027 | Retenciones, taller completo, seguros y anticipos | 11 | 40 | Release 1.1 |
| 9 | 29/03 – 09/04/2027 | Cierres avanzados, ocupación, baja de flota y reportes gerenciales | 8 | 39 | Release 1.1 |
| 🚀 | **09/04/2027** | **Release 1.1 · lo diferido del MVP** | | | |
| 10 | 12/04 – 23/04/2027 | Venta de contado y comisiones | 12 | 40 | Release 2 |
| 11 | 26/04 – 07/05/2027 | Venta financiada y crédito | 9 | 39 | Release 2 |
| 12 | 10/05 – 21/05/2027 | Cuotas, mora y cartera | 10 | 38 | Release 2 |
| 🚀 | **21/05/2027** | **Release 2 · venta y financiamiento** | | | |
| 13 | 24/05 – 04/06/2027 | Controles restantes, tablero y casos de borde | 13 | 42 | Release 3 |
| 🚀 | **04/06/2027** | **Release 3 · funciones deseables** | | | |

**Por qué el Sprint 6 es de puesta en marcha y no una función más.** Para operar en serio hacen falta los libros legales (obligación ante la SAT) y la carga inicial de lo que la empresa ya tiene. Si el cliente prefiere arrancar con más funciones (retenciones, DUCA, taller completo), el Sprint 6 se mueve después del Sprint 9 y el arranque pasa al 23/04/2027, sin cambiar lo demás.

## 4. Detalle de los sprints del MVP

### Sprint 2 · Alquilar: del tarifario al contrato cerrado (30/11 – 11/12/2026) · 38 SP

| Historia | MoSCoW | Valor | SP | Nota |
|---|---|---|---|---|
| **HU-3.05** Mantener el tarifario de alquiler | Must | 9 | 3 |  |
| **HU-3.06** Registrar un contrato de alquiler | Must | 10 | 5 |  |
| **HU-3.08** Cerrar un contrato al devolver la unidad | Must | 10 | 3 |  |
| **HU-3.07** Recibir, aplicar y devolver depósitos en garantía | Must | 9 | 5 |  |
| **HU-6.01** Registrar clientes | Must | 9 | 3 |  |
| **HU-1.01** Registrar el perfil fiscal de la empresa | Must | 9 | 3 |  |
| **HU-3.02** Definir los parámetros de depreciación de cada unidad | Must | 9 | 5 |  |
| **HU-2.05** Revertir una partida contabilizada | Must | 9 | 3 |  |
| **HU-1.12** Respaldar y restaurar la información | Must | 9 | 5 |  |
| **HU-1.09** Administrar usuarios y roles | Must | 10 | 3 | resto tras el Sprint 1 |
| | | | **38** | |

**Demo:** Se define la tarifa de un sedán; se registra un cliente y un contrato con depósito en garantía; al devolver la unidad se calculan días y kilómetros. Se revierte una partida y se restaura un respaldo antes del receso.

### Sprint 3 · Facturar con FEL real (04/01 – 15/01/2027) · 39 SP

| Historia | MoSCoW | Valor | SP | Nota |
|---|---|---|---|---|
| **HU-6.02** Emitir una factura FEL | Must | 9 | 13 |  |
| **HU-3.09** Registrar cargos adicionales del contrato | Must | 9 | 5 |  |
| **HU-3.10** Facturar contratos de forma recurrente | Must | 9 | 8 |  |
| **HU-6.05** Anular un documento FEL | Must | 8 | 5 |  |
| **HU-6.03** Emitir notas de crédito | Must | 8 | 5 |  |
| **HU-2.03** Generar partidas automáticas desde los módulos | Must | 10 | 3 | resto tras el Sprint 1 |
| | | | **39** | |

**Demo:** El contrato cerrado, con un cargo por combustible, se factura con el certificador en ambiente de pruebas; la facturación recurrente prepara el lote del mes; se anula una factura y se emite una nota de crédito.

### Sprint 4 · Cobrar y pagar (18/01 – 29/01/2027) · 36 SP

| Historia | MoSCoW | Valor | SP | Nota |
|---|---|---|---|---|
| **HU-1.08** Configurar cuentas bancarias en quetzales y dólares | Must | 9 | 3 |  |
| **HU-6.07** Registrar cobros y aplicarlos a facturas | Must | 9 | 5 |  |
| **HU-2.09** Calcular el diferencial cambiario realizado | Must | 10 | 5 |  |
| **HU-6.11** Consultar el estado de cuenta de un cliente | Must | 8 | 3 |  |
| **HU-6.12** Consultar la antigüedad de saldos de clientes | Must | 8 | 5 |  |
| **HU-4.09** Registrar facturas de compras y gastos locales | Must | 8 | 5 |  |
| **HU-4.13** Programar y aprobar pagos a proveedores | Must | 8 | 5 |  |
| **HU-4.14** Registrar el pago a un proveedor | Must | 8 | 5 |  |
| | | | **36** | |

**Demo:** Se cobra una factura en USD con diferencial cambiario; se registra una factura de proveedor, se aprueba y se paga la compra a Copart; estado de cuenta y antigüedad de saldos del cliente.

### Sprint 5 · Cerrar el mes y ver la rentabilidad (01/02 – 12/02/2027) · 39 SP

| Historia | MoSCoW | Valor | SP | Nota |
|---|---|---|---|---|
| **HU-2.07** Calcular la depreciación mensual | Must | 9 | 8 |  |
| **HU-2.08** Revaluar saldos en dólares al cierre | Must | 9 | 5 |  |
| **HU-2.12** Cerrar un período mensual | Must | 9 | 5 |  |
| **HU-2.10** Conciliar las cuentas bancarias | Must | 9 | 8 |  |
| **HU-3.13** Consultar la rentabilidad por contrato y por unidad | Must | 9 | 5 |  |
| **HU-7.02** Consultar la rentabilidad de cada unidad en todo su ciclo | Must | 8 | 5 |  |
| **HU-7.04** Consultar las unidades por etapa del ciclo | Must | 8 | 3 |  |
| | | | **39** | |

**Demo:** El contador deprecia la flota, revalúa los saldos en USD, concilia el banco y cierra enero; la gerencia ve la rentabilidad del Honda (ingresos − depreciación − mantenimiento) y las unidades por etapa.

### Sprint 6 · Puesta en marcha: libros legales y carga inicial mínima (15/02 – 26/02/2027) · 38 SP

| Historia | MoSCoW | Valor | SP | Nota |
|---|---|---|---|---|
| **HU-2.15** Emitir los libros legales | Must | 9 | 8 |  |
| **HU-10.01** Descargar plantillas de carga y validar archivos | Must | 7 | 5 |  |
| **HU-10.02** Cargar los saldos contables iniciales | Must | 7 | 3 |  |
| **HU-10.03** Cargar la flota con su valor en libros | Must | 7 | 5 |  |
| **HU-10.05** Cargar clientes, proveedores y sus saldos abiertos | Must | 7 | 5 |  |
| **HU-10.08** Cargar los contratos de alquiler activos | Must | 7 | 3 |  |
| **HU-10.09** Conciliar el arranque y aceptar los saldos | Must | 7 | 5 |  |
| **HU-10.11** Capacitar a los usuarios por rol (habilitación) | Must | 7 | 2 |  |
| **HU-10.12** Dar soporte inicial tras el arranque (habilitación) | Must | 7 | 2 |  |
| | | | **38** | |

**Demo:** Se cargan los saldos iniciales, la flota que ya existe con su valor en libros, clientes, proveedores y los contratos vigentes; la conciliación da cero diferencias; se emiten los libros legales; capacitación por rol.

### Releases siguientes

**Sprint 7 · Endurecer el corte e importación completa (01/03 – 12/03/2027) · 37 SP:** 1.02, 1.04, 1.05, 1.06, 1.10, 1.11, 2.01, 2.02, 2.16, 4.01, 4.02, 4.04, 4.07, 4.08, 5.01, 5.02, 5.03, 4.03, 4.05, 4.06

**Sprint 8 · Retenciones, taller completo, seguros y anticipos (15/03 – 26/03/2027) · 40 SP:** 10.07, 4.11, 4.16, 3.01, 3.04, 5.07, 5.04, 5.05, 5.06, 6.08, 6.09

**Sprint 9 · Cierres avanzados, ocupación, baja de flota y reportes gerenciales (29/03 – 09/04/2027) · 39 SP:** 2.13, 2.14, 3.12, 3.15, 7.01, 7.03, 7.07, 7.09

**Sprint 10 · Venta de contado y comisiones (12/04 – 23/04/2027) · 40 SP:** 5.09, 7.06, 2.04, 2.06, 8.01, 8.02, 8.04, 8.07, 8.08, 8.09, 8.10, 8.12

**Sprint 11 · Venta financiada y crédito (26/04 – 07/05/2027) · 39 SP:** 8.05, 9.01, 9.02, 9.03, 9.04, 9.05, 9.06, 9.07, 9.08

**Sprint 12 · Cuotas, mora y cartera (10/05 – 21/05/2027) · 38 SP:** 7.05, 2.11, 9.09, 9.10, 9.13, 9.14, 6.06, 3.03, 3.11, 3.14

**Sprint 13 · Controles restantes, tablero y casos de borde (24/05 – 04/06/2027) · 42 SP:** 4.12, 4.15, 5.10, 6.04, 6.10, 7.08, 7.10, 8.03, 8.06, 8.11, 9.11, 9.12, 5.08

## 5. Reporte de descartes y recortes

### 5.1 Historias descartadas (6 historias, 24 SP)

No se construyen. Cada una tiene una condición para volver al backlog.

| Historia | SP | Por qué se descarta | Vuelve al backlog si… |
|---|---|---|---|
| **HU-10.10** Operar en paralelo antes del arranque definitivo | 3 | No hay un sistema anterior con el cual comparar | Aparece un sistema contable previo |
| **HU-10.06** Cargar la cartera financiada vigente | 5 | No hay créditos vigentes (supuesto ya acordado en el plan v3) | El cliente confirma créditos vigentes |
| **HU-1.03** Importar el catálogo de cuentas existente | 5 | Sin sistema anterior, el catálogo se diseña nuevo con el contador sobre la semilla del Sprint 1 | El contador tiene un catálogo en Excel que quiere conservar |
| **HU-10.04** Cargar unidades en importación, en taller y en venta | 3 | Las unidades que estén en camino al arrancar se registran con el flujo normal de compra del Sprint 1 | Hay muchas unidades en proceso al arrancar |
| **HU-4.10** Registrar compras a particulares con factura especial | 3 | Could; no confirmado por el cliente | El cliente confirma compras frecuentes a particulares |
| **HU-9.15** Reestructurar un crédito | 5 | Could; no es necesaria para operar el financiamiento | Hay créditos en mora que reestructurar |

### 5.2 Sobre descartar la migración (Épica 10)

La propuesta de descartar la migración porque no venimos de un sistema existente **es correcta sólo en parte**:

- **Sí se descarta** lo que existe para comparar contra un sistema anterior o migrar sus datos: la operación en paralelo (HU-10.10), la importación del catálogo (HU-1.03), la carga de la cartera (HU-10.06) y la de unidades en proceso (HU-10.04).
- **No se puede descartar la carga inicial.** Aunque no haya un sistema anterior, la empresa ya opera: tiene flota con su valor en libros, dinero en el banco, deudas con proveedores, clientes y contratos de alquiler vigentes. Si el sistema arranca en cero, el balance no corresponde con la realidad y la depreciación de la flota sale mal. Por eso se conserva una **carga inicial mínima** en el Sprint 6: saldos iniciales (HU-10.02), flota existente (HU-10.03), clientes y proveedores con sus saldos (HU-10.05), contratos vigentes (HU-10.08), su conciliación (HU-10.09) y las plantillas de carga (HU-10.01).
- **La carga de repuestos (HU-10.07)** se mueve al Sprint 8, junto con el inventario de repuestos (HU-5.04). No tiene sentido cargarlos antes de que el sistema los controle.
- **Capacitación y soporte** (HU-10.11 y HU-10.12) se quedan: son pocos puntos y sin ellos el arranque falla.

Resultado: la Épica 10 pasa de 12 historias a 9 (3 descartadas: HU-10.04, HU-10.06 y HU-10.10), y la carga que queda se ajusta a lo que la empresa tiene hoy.

### 5.3 Historias que salen del MVP (40 historias, 119 SP)

Estaban en el Release 1 del plan v3 y pasan a después del arranque. **No se descartan**: se reordenan porque la línea de alquiler puede operar sin ellas al inicio.

| Historia | Épica | SP | Antes (plan v3) | Ahora |
|---|---|---|---|---|
| **HU-1.02** Mantener el catálogo de cuentas | E1 | 2 | S2 (R1) | S7 |
| **HU-1.04** Configurar las dimensiones analíticas | E1 | 1 | S2 (R1) | S7 |
| **HU-1.05** Registrar y validar unidades por VIN | E1 | 2 | S2 (R1) | S7 |
| **HU-1.06** Cargar el tipo de cambio de referencia del Banguat | E1 | 3 | S2 (R1) | S7 |
| **HU-1.10** Separar funciones de registro y aprobación | E1 | 2 | S2 (R1) | S7 |
| **HU-1.11** Consultar la bitácora de cambios | E1 | 1 | S2 (R1) | S7 |
| **HU-2.01** Registrar una partida manual | E2 | 2 | S2 (R1) | S7 |
| **HU-2.02** Revisar y contabilizar partidas | E2 | 2 | S2 (R1) | S7 |
| **HU-2.16** Consultar el balance de comprobación y el mayor | E2 | 2 | S2 (R1) | S7 |
| **HU-4.01** Registrar proveedores locales y del exterior | E4 | 1 | S2 (R1) | S7 |
| **HU-4.02** Registrar la compra de una unidad en EE. UU. | E4 | 1 | S2 (R1) | S7 |
| **HU-4.04** Registrar los gastos de importación | E4 | 2 | S3 (R1) | S7 |
| **HU-4.07** Seguir el estado de la unidad durante la importación | E4 | 1 | S3 (R1) | S7 |
| **HU-4.08** Consultar la hoja de costo de una unidad | E4 | 1 | S3 (R1) | S7 |
| **HU-5.01** Abrir una orden de trabajo ligada a un VIN | E5 | 1 | S3 (R1) | S7 |
| **HU-5.02** Configurar las tarifas de mano de obra | E5 | 1 | S3 (R1) | S7 |
| **HU-5.03** Registrar mano de obra en la orden | E5 | 1 | S3 (R1) | S7 |
| **HU-4.03** Agrupar unidades en un expediente de importación | E4 | 3 | S3 (R1) | S7 |
| **HU-4.05** Prorratear los gastos compartidos | E4 | 5 | S3 (R1) | S7 |
| **HU-4.06** Registrar la DUCA y vincularla a las unidades | E4 | 3 | S3 (R1) | S7 |
| **HU-10.07** Cargar el inventario de repuestos | E10 | 2 | S9 (R1) | S8 |
| **HU-4.11** Retener IVA e ISR a proveedores locales | E4 | 5 | S3 (R1) | S8 |
| **HU-4.16** Consultar antigüedad de saldos y estado de cuenta de proveedores | E4 | 5 | S3 (R1) | S8 |
| **HU-3.01** Dar de alta una unidad como activo fijo de la flota | E3 | 2 | S4 (R1) | S8 |
| **HU-3.04** Controlar seguros, marchamo y documentos de cada unidad | E3 | 5 | S4 (R1) | S8 |
| **HU-5.07** Cerrar la orden y generar su destino contable | E5 | 2 | S4 (R1) | S8 |
| **HU-5.04** Mantener el catálogo e inventario de repuestos | E5 | 5 | S4 (R1) | S8 |
| **HU-5.05** Consumir repuestos en una orden | E5 | 3 | S4 (R1) | S8 |
| **HU-5.06** Registrar trabajos subcontratados | E5 | 3 | S4 (R1) | S8 |
| **HU-6.08** Registrar retenciones que nos hacen los clientes | E6 | 3 | S6 (R1) | S8 |
| **HU-6.09** Registrar y aplicar anticipos de clientes | E6 | 5 | S6 (R1) | S8 |
| **HU-2.13** Reabrir un período cerrado | E2 | 3 | S7 (R1) | S9 |
| **HU-2.14** Ejecutar el cierre anual | E2 | 5 | S7 (R1) | S9 |
| **HU-3.12** Consultar la ocupación de la flota | E3 | 5 | S7 (R1) | S9 |
| **HU-3.15** Dar de baja una unidad de la flota y pasarla a venta | E3 | 5 | S8 (R1) | S9 |
| **HU-7.01** Consultar estados financieros por línea de negocio | E7 | 8 | S8 (R1) | S9 |
| **HU-7.03** Consultar la ocupación y rentabilidad de la flota | E7 | 5 | S8 (R1) | S9 |
| **HU-7.07** Consultar la antigüedad de saldos de clientes y proveedores | E7 | 3 | S8 (R1) | S9 |
| **HU-7.09** Exportar reportes a PDF y Excel | E7 | 5 | S8 (R1) | S9 |
| **HU-5.09** Facturar la postventa no cubierta por garantía | E5 | 3 | S9 (R1) | S10 |

**Criterio del recorte:** se queda en el MVP lo que el ciclo de alquiler necesita para operar y cerrar el mes. Sale lo que mejora la exactitud o el control pero tiene una alternativa manual temporal:

- **Importación detallada:** expediente, prorrateo y DUCA. Mientras tanto, los gastos se cargan por VIN como en el Sprint 1.
- **Restos del corte:** el servicio del Banguat (el tipo de cambio se sigue cargando a mano), los límites de aprobación y las exportaciones.
- **Reportes completos:** el MVP sólo trae rentabilidad por unidad y unidades por etapa.

### 5.4 Movimientos entre sprints respecto al plan v3

| Historia | v3 | v4 | Motivo |
|---|---|---|---|
| HU-3.05, HU-3.06, HU-3.07, HU-3.08, HU-6.01 (contrato) | S4–S5 | **S2** | El alquiler es lo primero del MVP |
| HU-6.02 FEL, HU-3.10 facturación recurrente | S5 | **S3** | Hay que elegir el certificador antes del 04/01 (antes era el 18/01) |
| HU-2.07, HU-2.08, HU-2.10, HU-2.12 (cierre) | S7 | **S5** | Sin cierre mensual no hay MVP contable |
| HU-3.13, HU-7.02, HU-7.04 (rentabilidad) | S8 | **S5** | Es lo que más le interesa a la gerencia |
| HU-2.15 libros legales | S9 | **S6** | Obligatorio para operar |
| HU-2.09 diferencial cambiario | S3 | **S4** | Va junto con el primer cobro y el primer pago |
| HU-4.03, HU-4.05, HU-4.06 (expediente, prorrateo, DUCA) | S3 | **S7** | Hay alternativa manual temporal |
| Restos del Sprint 1 (bitácora, límites de aprobación, Banguat, etc.) | S2–S4 | **S7–S8** | No bloquean el ciclo |

## 6. Cómo se fue ajustando la planeación

| Versión | Fecha | Quién | Qué cambió | Por qué |
|---|---|---|---|---|
| v1 | 23/10/2026 | Equipo | 10 épicas, 130 historias, User Story Mapping en 3 releases; sprints de 3 semanas y MVP hacia la semana 40 con 4 a 5 desarrolladores | Primera planeación a partir de la entrevista con el cliente |
| v2 | 30/10/2026 | Dilson | `Planning.md`: corte transversal, valor de negocio con regla explícita, puntos de historia y 19 sprints; prototipo del corte con código | La consigna pide un corte transversal: implementar un poco de todo |
| v3 | 30/10/2026 | Alex | `Sprint1.md` y `PlanSprints.md`: Sprint 1 de 4 semanas sólo hasta el alta en flota, 3 desarrolladores, capacidad en días-persona, avance por criterios aceptados, definición de terminado de 10 puntos, 16 sprints | El corte de v2 era demasiado ancho para un primer sprint y el equipo real es de 3 personas |
| **v4** | **30/10/2026** | **Equipo** | **Este documento: MVP en 4 sprints (12/02/2027), puesta en marcha en el S6, descarte de 6 historias y carga inicial mínima** | **Llegar antes a algo usable y quitar lo que no aplica a una empresa sin sistema previo** |

Lo que se mantuvo en todas las versiones: el VIN como hilo conductor, la regla de valor de negocio, las 130 historias como fuente y la velocidad tratada como hipótesis que se recalibra con datos.

## 7. Riesgos del MVP corto

| Riesgo | Efecto | Respuesta |
|---|---|---|
| **El certificador FEL no está elegido antes del 04/01** | El Sprint 3 no puede facturar | Fecha límite nueva: **14/12/2026** (antes del receso). Plan B: registrar documentos emitidos fuera del sistema (HU-6.06, se adelanta) |
| La empresa es agente de retención | Los pagos del Sprint 4 salen sin retención | Confirmar antes del 30/11; si lo es, HU-4.11 (5 SP) entra al S4 y HU-6.11 (3 SP) pasa al S7 |
| Contenedores con varias unidades | Sin prorrateo, el costo por unidad es aproximado hasta el S7 | Prorratear a mano con el contador durante el primer mes, o adelantar HU-4.05 al S5 en lugar de HU-7.04 |
| Arrancar el 26/02 con funciones incompletas | El cliente opera con alternativas manuales | Acordarlo con el cliente en la demo del MVP (12/02); si no lo acepta, el arranque pasa al 23/04/2027 |
| Velocidad de 40 SP sin medir | Las fechas se corren | Recalcular al cierre del Sprint 1 con el esfuerzo real; mantener los escenarios de la sección 5 del plan v3 |
| Sprint 13 con 42 SP | Puede desbordar | Es el último sprint y todo es Should o Could; lo que no entre se descarta |
