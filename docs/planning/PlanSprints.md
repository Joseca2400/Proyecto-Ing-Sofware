# Plan de sprints (corte transversal)

Planeación de desarrollo del sistema administrativo y financiero para la empresa de alquiler, venta y taller de vehículos. Organiza las 130 historias de [user-stories/](user-stories/README.md) en sprints que cierran un flujo de negocio demostrable.

Versión 3 · 30 de octubre de 2026 · Borrador para validar con el equipo y el cliente. **Se parte de cero: no existe código.**

Fuentes: [UserStoryMapping.md](UserStoryMapping.md) (releases), las dependencias de `user-stories/` y [Sprint1.md](Sprint1.md) (Sprint 1 detallado). Los puntos de historia y el valor de negocio se toman de la propuesta de un compañero (`Planning.md`) como estimación inicial, que se recalibra con el ritmo real.

## Contenido

1. [Qué cambió respecto a la versión 1](#1-qué-cambió-respecto-a-la-versión-1)
2. [Supuestos de planificación](#2-supuestos-de-planificación)
3. [Estrategia](#3-estrategia)
4. [Vista general](#4-vista-general)
5. [Escenarios de fechas](#5-escenarios-de-fechas)
6. [Detalle por sprint](#6-detalle-por-sprint)
7. [Correcciones de dependencias y de alcance](#7-correcciones-de-dependencias-y-de-alcance)
8. [Dependencias externas con fecha límite](#8-dependencias-externas-con-fecha-límite)
9. [Riesgos](#9-riesgos)
10. [Ceremonias y definiciones](#10-ceremonias-y-definiciones)
11. [Apéndice: backlog completo](#apéndice-backlog-completo)

---

## 1. Qué cambió respecto a la versión 1

| Aspecto | Versión 1 | Versión 2 |
|---|---|---|
| Equipo | 4 a 5 desarrolladores | **3 desarrolladores** con asistencia de IA |
| Sprint 1 | 6 historias completas de E1 | **Corte transversal de la compra al alta en flota** (ver [Sprint1.md](Sprint1.md), versión 3) |
| Estimación | Historias por sprint | **Puntos de historia (SP)** y valor de negocio por historia |
| Duración | 3 semanas | Sprint 1 de 4 semanas; **2 semanas desde el Sprint 2** |
| Fechas | Semanas relativas | **Fechas reales** y receso de fin de año |
| Arranque del MVP | Semana 40 con más desarrolladores | **Del 26/04 al 07/05/2027** en el escenario esperado, con operación en paralelo incluida |
| Créditos vigentes | Por confirmar | **No hay**; la Épica 9 queda en Release 2 |
| Stack | Por definir | **Por definirse** entre el equipo y los responsables; candidato registrado: Python, FastAPI y SQLAlchemy; el plan no depende de él |
| Dependencias mal ordenadas | Sin revisar | Corregidas (sección 7) |

---

## 2. Supuestos de planificación

| Supuesto | Valor | Nota |
|---|---|---|
| Equipo | 3 desarrolladores, 1 dueño de producto, acceso semanal al contador | |
| Sprint 1 | 02/11 a 27/11/2026 (4 semanas) | Incluye la fundación técnica; demo parcial el 13/11 |
| Sprints 2 en adelante | 2 semanas (lunes a viernes) | Si el ritmo del Sprint 1 no lo permite, se pasa a 3 semanas |
| Receso de fin de año | 14/12/2026 a 01/01/2027 | Por confirmar |
| Estimación | SP en escala Fibonacci | Estimación inicial de un compañero; se revisa en cada refinamiento |
| Total del backlog | 546 SP en 130 historias | R1: 369 · R2: 150 · R3: 27 |
| Referencia del Sprint 1 | 57 SP de las historias (22 historias en versión delgada) | Es la estimación inicial de ese alcance y **no se cuenta como avance**; se reemplaza por los criterios aceptados al cierre |
| Pendiente tras el Sprint 1 | **489 SP** | |
| Velocidad para planificar | **hasta 40 SP por sprint de 2 semanas** | Hipótesis, no medida; se reemplaza con el esfuerzo real del Sprint 1 y se recalibra al cierre de los sprints 2 y 3 |
| Conversión de SP a días | No se usa un factor fijo | El esfuerzo real por tarea se registra desde el Sprint 1 |
| Créditos vigentes al arrancar | No | Si los hay, la Épica 9 y HU-10.06 suben a Release 1 |
| Stack | Por definirse | Criterios mínimos en [Sprint1.md](Sprint1.md), sección 4 |

**Cómo se eligió 40 SP.** En 2 semanas, 3 personas tienen 27 días-persona. No hay datos medidos, así que se plantean tres hipótesis de ritmo (33, 40 y 55 SP por sprint) y se planifica con **40 SP como techo**, dejando margen para defectos, refinamientos y validaciones. Los sprints de estabilización (10, 11 y 16) llevan menos carga a propósito. Es una hipótesis de trabajo, no un factor de conversión.

---

## 3. Estrategia

**Corte transversal.** El Sprint 1 recorre el ciclo de la unidad con versiones delgadas, de la compra al alta en flota, con interfaz, seguridad y contabilidad reales. A partir del Sprint 2 cada sprint **completa** un flujo de negocio con sus historias, en el orden en que la unidad genera costo e ingreso, y termina con una demo.

**Orden de las historias.** Primero por release; dentro del release, por el flujo del ciclo de la unidad y las dependencias; dentro de cada sprint, por valor.

**Valor de negocio (1 a 10).**

| Componente | Puntos |
|---|---|
| Prioridad MoSCoW | Must 7 · Should 4 · Could 2 |
| Posición de la épica en el ciclo | E1 a E3 +2 · E4 a E6 +1 · E7 y E10 0 · E8 y E9 −1 |
| Forma parte del corte transversal del Sprint 1 | +1 |

**Una demo por sprint,** con el mismo dato que viaja (una unidad con VIN) de principio a fin.

---

## 4. Vista general

| Sprint | Fechas | Tema | Historias | SP | Release |
|---|---|---|---|---|---|
| **1** | 02/11 – 27/11/2026 | Corte transversal: de la compra al alta en flota (4 semanas) | 22 en versión delgada | 60 (referencia) | R1 |
| **2** | 30/11 – 11/12/2026 | Endurecer la base | 17 | 39 | R1 |
| *Receso* | 14/12/2026 – 01/01/2027 | | | | |
| **3** | 04/01 – 15/01/2027 | Costo real de la unidad | 13 | 38 | R1 |
| **4** | 18/01 – 29/01/2027 | Pagos, taller completo y flota lista | 10 | 38 | R1 |
| **5** | 01/02 – 12/02/2027 | Del contrato a la factura FEL | 6 | 37 | R1 |
| **6** | 15/02 – 26/02/2027 | Cobros y correcciones | 8 | 36 | R1 |
| **7** | 01/03 – 12/03/2027 | Cierre mensual | 7 | 39 | R1 |
| **8** | 15/03 – 26/03/2027 | Rentabilidad y reportes gerenciales | 8 | 39 | R1 |
| **9** | 29/03 – 09/04/2027 | Libros legales y migración | 9 | 37 | R1 |
| **10** | 12/04 – 23/04/2027 | Conciliación del arranque | 2 | 7 | R1 |
| **11** | 26/04 – 07/05/2027 | Operación en paralelo y soporte | 2 | 5 | R1 |
| 🚀 | **07/05/2027** | **Release 1 · MVP: arranque con la línea de alquiler** | | | |
| **12** | 10/05 – 21/05/2027 | Vender de contado | 11 | 37 | R2 |
| **13** | 24/05 – 04/06/2027 | Venta financiada | 9 | 39 | R2 |
| **14** | 07/06 – 18/06/2027 | Mora y cartera | 9 | 39 | R2 |
| **15** | 21/06 – 02/07/2027 | Controles y tablero | 10 | 32 | R2 |
| 🚀 | **02/07/2027** | **Release 2 · venta, financiamiento y controles** | | | |
| **16** | 05/07 – 16/07/2027 | Garantías y casos de borde | 8 | 27 | R3 |
| 🚀 | **16/07/2027** | **Release 3 · funciones deseables** | | | |

Total pendiente: 489 SP en 15 sprints (del 2 al 16), con un promedio de unos 33 SP por sprint porque los sprints 10, 11 y 16 son de baja carga.

---

## 5. Escenarios de fechas

Si el ritmo real difiere de la hipótesis, las fechas se mueven. El MVP necesita los sprints 2 a 9 (304 SP) más dos sprints de arranque; el Release 2 suma 147 SP, y el Release 3, 27.

| Escenario | SP por sprint | Sprints hasta el MVP | MVP (Release 1) | Release 2 | Release 3 |
|---|---|---|---|---|---|
| Conservador | 33 | 12 (S2–S13) | 04/06/2027 | 13/08/2027 | 27/08/2027 |
| **Esperado (plan)** | 40 | 10 (S2–S11) | 07/05/2027 | 02/07/2027 | 16/07/2027 |
| Optimista | 55 | 8 (S2–S9) | 09/04/2027 | 21/05/2027 | 04/06/2027 |

El escenario esperado coincide con el plan de la sección 4. La fecha del MVP depende más de las validaciones del cliente (certificador FEL, reglas con el contador, limpieza de datos y operación en paralelo) que de la velocidad de programación; por eso los sprints de arranque y estabilización no se comprimen aunque el ritmo sea optimista.

**Efecto del Sprint 1.** El Sprint 1 no adelanta el ciclo de ingreso (alquiler, factura y cobro), que queda para los sprints 5 y 6. Si el esfuerzo real medido en el Sprint 1 difiere de lo estimado, se recalcula toda la tabla.

---

## 6. Detalle por sprint

Los SP de cada sprint son los pendientes después del Sprint 1.

## Release 1 · MVP

### Sprint 2 · Endurecer la base (30/11 – 11/12/2026) · 39 SP

**Objetivo:** Endurecer la base: completar lo que el Sprint 1 dejó delgado en seguridad, contabilidad y bitácora, y habilitar los respaldos antes del receso.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-1.01 | Registrar el perfil fiscal de la empresa | Must | 3 |  |
| HU-1.02 | Mantener el catálogo de cuentas | Must | 2 | resto tras Sprint 1 |
| HU-1.04 | Configurar las dimensiones analíticas | Must | 1 | resto tras Sprint 1 |
| HU-1.05 | Registrar y validar unidades por VIN | Must | 2 | resto tras Sprint 1 |
| HU-1.06 | Cargar el tipo de cambio de referencia del Banguat | Must | 3 | resto tras Sprint 1 |
| HU-1.08 | Configurar cuentas bancarias en quetzales y dólares | Must | 3 |  |
| HU-1.09 | Administrar usuarios y roles | Must | 3 | resto tras Sprint 1 |
| HU-1.10 | Separar funciones de registro y aprobación | Must | 2 | resto tras Sprint 1 |
| HU-1.11 | Consultar la bitácora de cambios | Must | 1 | resto tras Sprint 1 |
| HU-1.12 | Respaldar y restaurar la información | Must | 5 |  |
| HU-2.01 | Registrar una partida manual | Must | 2 | resto tras Sprint 1 |
| HU-2.02 | Revisar y contabilizar partidas | Must | 2 | resto tras Sprint 1 |
| HU-2.03 | Generar partidas automáticas desde los módulos | Must | 3 | resto tras Sprint 1 |
| HU-2.05 | Revertir una partida contabilizada | Must | 3 |  |
| HU-2.16 | Consultar el balance de comprobación y el mayor | Must | 2 | resto tras Sprint 1 |
| HU-4.01 | Registrar proveedores locales y del exterior | Must | 1 | resto tras Sprint 1 |
| HU-4.02 | Registrar la compra de una unidad en EE. UU. | Must | 1 | resto tras Sprint 1 |

**Demo:** Se bloquea una cuenta tras intentos fallidos; el contador configura el perfil fiscal, las cuentas bancarias y el catálogo con máscara de niveles; el tipo de cambio llega del Banguat; una partida automática usa reglas configurables y se revierte; se restaura un respaldo.

**Antes del sprint:** Servicio del Banguat; régimen de ISR y agente de retención confirmados (HU-1.01).

### Sprint 3 · Costo real de la unidad (04/01 – 15/01/2027) · 38 SP

**Objetivo:** Costo real de la unidad: expediente de importación, prorrateo, DUCA, compras locales con retenciones y el diferencial cambiario.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-2.09 | Calcular el diferencial cambiario realizado | Must | 5 |  |
| HU-4.03 | Agrupar unidades en un expediente de importación | Must | 3 |  |
| HU-4.04 | Registrar los gastos de importación | Must | 2 | resto tras Sprint 1 |
| HU-4.05 | Prorratear los gastos compartidos | Must | 5 |  |
| HU-4.06 | Registrar la DUCA y vincularla a las unidades | Must | 3 |  |
| HU-4.07 | Seguir el estado de la unidad durante la importación | Must | 1 | resto tras Sprint 1 |
| HU-4.08 | Consultar la hoja de costo de una unidad | Must | 1 | resto tras Sprint 1 |
| HU-4.09 | Registrar facturas de compras y gastos locales | Must | 5 |  |
| HU-4.11 | Retener IVA e ISR a proveedores locales | Must | 5 |  |
| HU-4.16 | Consultar antigüedad de saldos y estado de cuenta de proveedores | Must | 5 |  |
| HU-5.01 | Abrir una orden de trabajo ligada a un VIN | Must | 1 | resto tras Sprint 1 |
| HU-5.02 | Configurar las tarifas de mano de obra | Must | 1 | resto tras Sprint 1 |
| HU-5.03 | Registrar mano de obra en la orden | Must | 1 | resto tras Sprint 1 |

**Demo:** Un contenedor con tres unidades: se prorratean sus gastos, se registra la DUCA y la hoja de costo de cada unidad muestra su costo desglosado. Se registra una factura local con retención y se consulta la antigüedad de saldos de proveedores.

**Antes del sprint:** Regla de prorrateo, régimen de ISR y retenciones confirmados antes del 04/01.

### Sprint 4 · Pagos, taller completo y flota lista (18/01 – 29/01/2027) · 38 SP

**Objetivo:** Pagar a proveedores, completar el taller y dejar la unidad lista en flota.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-3.01 | Dar de alta una unidad como activo fijo de la flota | Must | 2 | resto tras Sprint 1 |
| HU-3.02 | Definir los parámetros de depreciación de cada unidad | Must | 5 |  |
| HU-3.04 | Controlar seguros, marchamo y documentos de cada unidad | Must | 5 |  |
| HU-3.05 | Mantener el tarifario de alquiler | Must | 3 |  |
| HU-4.13 | Programar y aprobar pagos a proveedores | Must | 5 |  |
| HU-4.14 | Registrar el pago a un proveedor | Must | 5 |  |
| HU-5.04 | Mantener el catálogo e inventario de repuestos | Must | 5 |  |
| HU-5.05 | Consumir repuestos en una orden | Must | 3 |  |
| HU-5.06 | Registrar trabajos subcontratados | Must | 3 |  |
| HU-5.07 | Cerrar la orden y generar su destino contable | Must | 2 | resto tras Sprint 1 |

**Demo:** Se programa y aprueba un pago en USD con su diferencial cambiario; la orden de taller usa repuestos y un subcontrato; al cerrarla capitaliza su costo y la unidad entra a flota con su depreciación y su tarifa de alquiler definidas.

**Antes del sprint:** Método de costeo de repuestos; depreciación fiscal frente a financiera; tarifas de alquiler; certificador FEL elegido y credenciales de pruebas.

### Sprint 5 · Del contrato a la factura FEL (01/02 – 12/02/2027) · 37 SP

**Objetivo:** Del contrato a la factura FEL con certificador real.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-3.06 | Registrar un contrato de alquiler | Must | 5 |  |
| HU-3.07 | Recibir, aplicar y devolver depósitos en garantía | Must | 5 |  |
| HU-3.08 | Cerrar un contrato al devolver la unidad | Must | 3 |  |
| HU-3.10 | Facturar contratos de forma recurrente | Must | 8 |  |
| HU-6.01 | Registrar clientes | Must | 3 |  |
| HU-6.02 | Emitir una factura FEL | Must | 13 |  |

**Demo:** Cliente, contrato, depósito en garantía y factura certificada; corre la facturación recurrente y el ingreso queda ligado al VIN.

**Antes del sprint:** Credenciales de pruebas del certificador FEL; reglas de depósitos y cobros adicionales.

### Sprint 6 · Cobros y correcciones (15/02 – 26/02/2027) · 36 SP

**Objetivo:** Cobros y correcciones del contrato: cobros, retenciones del cliente, anticipos, notas de crédito, anulaciones y cargos adicionales.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-3.09 | Registrar cargos adicionales del contrato | Must | 5 |  |
| HU-6.03 | Emitir notas de crédito | Must | 5 |  |
| HU-6.05 | Anular un documento FEL | Must | 5 |  |
| HU-6.07 | Registrar cobros y aplicarlos a facturas | Must | 5 |  |
| HU-6.08 | Registrar retenciones que nos hacen los clientes | Must | 3 |  |
| HU-6.09 | Registrar y aplicar anticipos de clientes | Must | 5 |  |
| HU-6.11 | Consultar el estado de cuenta de un cliente | Must | 3 |  |
| HU-6.12 | Consultar la antigüedad de saldos de clientes | Must | 5 |  |

**Demo:** Un cobro con retención del cliente y anticipo aplicado; una nota de crédito y una anulación; estado de cuenta y antigüedad de saldos de clientes.

**Antes del sprint:** Reglas de cargos adicionales (combustible, daños, multas).

### Sprint 7 · Cierre mensual (01/03 – 12/03/2027) · 39 SP

**Objetivo:** Cierre mensual completo con depreciación, revaluación y conciliación.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-2.07 | Calcular la depreciación mensual | Must | 8 |  |
| HU-2.08 | Revaluar saldos en dólares al cierre | Must | 5 |  |
| HU-2.10 | Conciliar las cuentas bancarias | Must | 8 |  |
| HU-2.12 | Cerrar un período mensual | Must | 5 |  |
| HU-2.13 | Reabrir un período cerrado | Must | 3 |  |
| HU-2.14 | Ejecutar el cierre anual | Must | 5 |  |
| HU-3.12 | Consultar la ocupación de la flota | Must | 5 |  |

**Demo:** El contador calcula la depreciación, revalúa los saldos en dólares, concilia el banco, cierra el mes, lo reabre con aprobación y ejecuta el cierre anual en pruebas; la gerencia ve la ocupación de la flota.

**Antes del sprint:** Depreciación fiscal y financiera definidas; estados de cuenta bancarios para conciliar.

### Sprint 8 · Rentabilidad y reportes gerenciales (15/03 – 26/03/2027) · 39 SP

**Objetivo:** Rentabilidad y reportes gerenciales; baja de unidades de la flota.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-3.13 | Consultar la rentabilidad por contrato y por unidad | Must | 5 |  |
| HU-3.15 | Dar de baja una unidad de la flota y pasarla a venta | Must | 5 |  |
| HU-7.01 | Consultar estados financieros por línea de negocio | Must | 8 |  |
| HU-7.02 | Consultar la rentabilidad de cada unidad en todo su ciclo | Must | 5 |  |
| HU-7.03 | Consultar la ocupación y rentabilidad de la flota | Must | 5 |  |
| HU-7.04 | Consultar las unidades por etapa del ciclo | Must | 3 |  |
| HU-7.07 | Consultar la antigüedad de saldos de clientes y proveedores | Must | 3 |  |
| HU-7.09 | Exportar reportes a PDF y Excel | Must | 5 |  |

**Demo:** La gerencia consulta estados financieros por línea, rentabilidad por unidad y por contrato, ocupación y unidades por etapa, y exporta a PDF y Excel; se da de baja una unidad a inventario de venta.

**Antes del sprint:** Los 3 a 5 reportes más usados, confirmados por la gerencia antes del 15/03.

### Sprint 9 · Libros legales y migración (29/03 – 09/04/2027) · 37 SP

**Objetivo:** Libros legales y migración: plantillas y cargas.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-2.15 | Emitir los libros legales | Must | 8 |  |
| HU-5.09 | Facturar la postventa no cubierta por garantía | Must | 3 |  |
| HU-10.01 | Descargar plantillas de carga y validar archivos | Must | 5 |  |
| HU-10.02 | Cargar los saldos contables iniciales | Must | 3 |  |
| HU-10.03 | Cargar la flota con su valor en libros | Must | 5 |  |
| HU-10.04 | Cargar unidades en importación, en taller y en venta | Must | 3 |  |
| HU-10.05 | Cargar clientes, proveedores y sus saldos abiertos | Must | 5 |  |
| HU-10.07 | Cargar el inventario de repuestos | Must | 2 |  |
| HU-10.08 | Cargar los contratos de alquiler activos | Must | 3 |  |

**Demo:** Se sube un Excel con errores y el sistema los muestra por fila; se cargan saldos, flota, clientes, proveedores, repuestos y contratos reales; se emiten los libros legales.

**Antes del sprint:** Catálogo de cuentas actual y estados financieros validados a la fecha de corte; datos limpios desde el Sprint 6.

### Sprint 10 · Conciliación del arranque (12/04 – 23/04/2027) · 7 SP

**Objetivo:** Conciliación del arranque y capacitación.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-10.09 | Conciliar el arranque y aceptar los saldos | Must | 5 |  |
| HU-10.11 | Capacitar a los usuarios por rol (habilitación) | Must | 2 |  |

**Demo:** Reporte de conciliación en cero diferencias aceptado por el gerente financiero; capacitación por rol en ambiente de pruebas. Sprint de baja carga a propósito: pruebas de aceptación, corrección de defectos y despliegue a producción.

**Antes del sprint:** Fecha de corte y de arranque acordadas con el contador.

### Sprint 11 · Operación en paralelo y soporte (26/04 – 07/05/2027) · 5 SP

**Objetivo:** Operación en paralelo y soporte inicial.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-10.10 | Operar en paralelo antes del arranque definitivo | Should | 3 |  |
| HU-10.12 | Dar soporte inicial tras el arranque (habilitación) | Must | 2 |  |

**Demo:** Se opera un mes en paralelo con el sistema actual y se comparan balance de comprobación, estado de resultados y auxiliares; canal de soporte con tiempos de respuesta. **Release 1 · MVP en operación.**

**Antes del sprint:** Período de operación en paralelo definido.


## Release 2

### Sprint 12 · Vender de contado (10/05 – 21/05/2027) · 37 SP

**Objetivo:** Vender de contado, con comisión y margen.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-2.04 | Programar partidas recurrentes | Should | 3 |  |
| HU-2.06 | Registrar provisiones con reversión automática | Should | 3 |  |
| HU-7.06 | Consultar las comisiones por vendedor | Must | 3 |  |
| HU-8.01 | Consultar el inventario de unidades en venta | Must | 2 |  |
| HU-8.02 | Fijar el precio de lista y el precio mínimo | Must | 2 |  |
| HU-8.04 | Registrar una venta de contado | Must | 5 |  |
| HU-8.07 | Configurar el tratamiento fiscal de la venta de unidades | Must | 3 |  |
| HU-8.08 | Registrar vendedores y reglas de comisión | Must | 3 |  |
| HU-8.09 | Calcular la comisión de cada venta | Must | 5 |  |
| HU-8.10 | Liquidar comisiones por período | Must | 5 |  |
| HU-8.12 | Ver el margen de la unidad vendida | Must | 3 |  |

**Demo:** La unidad dada de baja se vende de contado, se factura, se calcula la comisión del vendedor y se ve el margen. La rentabilidad por unidad (HU-7.02) queda completa con el resultado de la venta.

**Antes del sprint:** Tratamiento fiscal de la venta de un activo de la flota y reglas de comisión.

### Sprint 13 · Venta financiada (24/05 – 04/06/2027) · 39 SP

**Objetivo:** Venta financiada: plan de crédito, amortización, devengo y cobro de cuotas.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-8.05 | Registrar una venta financiada | Must | 5 |  |
| HU-9.01 | Definir planes de crédito | Must | 3 |  |
| HU-9.02 | Registrar y aprobar un crédito | Must | 5 |  |
| HU-9.03 | Generar la tabla de amortización | Must | 5 |  |
| HU-9.04 | Devengar los intereses mensuales | Must | 5 |  |
| HU-9.05 | Facturar los intereses | Must | 5 |  |
| HU-9.06 | Registrar el cobro de una cuota | Must | 5 |  |
| HU-9.07 | Registrar abonos extraordinarios a capital | Must | 3 |  |
| HU-9.08 | Cancelar un crédito de forma anticipada | Must | 3 |  |

**Demo:** Se vende una unidad con enganche y financiamiento; el gerente financiero aprueba el crédito; pasan tres meses simulados con intereses devengados y facturados, cuotas cobradas, un abono extraordinario y una cancelación anticipada.

**Antes del sprint:** Condiciones de financiamiento e IVA sobre intereses.

### Sprint 14 · Mora y cartera (07/06 – 18/06/2027) · 39 SP

**Objetivo:** Mora, cartera y controles del Release 2.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-1.03 | Importar el catálogo de cuentas existente | Should | 5 |  |
| HU-2.11 | Seguir una lista de verificación de cierre | Should | 5 |  |
| HU-6.06 | Registrar documentos FEL emitidos fuera del sistema | Should | 3 |  |
| HU-7.05 | Consultar la cartera financiada y la mora | Must | 5 |  |
| HU-9.09 | Calcular la mora y el interés moratorio | Must | 5 |  |
| HU-9.10 | Calcular la antigüedad de la cartera y la provisión por incobrables | Must | 5 |  |
| HU-9.13 | Emitir el estado de cuenta del crédito | Must | 3 |  |
| HU-9.14 | Conciliar la cartera con la contabilidad | Must | 3 |  |
| HU-10.06 | Cargar la cartera financiada vigente | Must | 5 |  |

**Demo:** La cartera muestra mora al día, la provisión se calcula y se contabiliza, y el reporte de cartera cuadra con el mayor; catálogo de cuentas importable y cierre guiado por lista de verificación.

**Antes del sprint:** Política de mora y provisión por incobrables.

### Sprint 15 · Controles y tablero (21/06 – 02/07/2027) · 32 SP

**Objetivo:** Controles restantes, inventarios y tablero gerencial. **Release 2.**.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-3.03 | Capitalizar una mejora a una unidad de la flota | Should | 3 |  |
| HU-3.11 | Extender un contrato vigente | Should | 3 |  |
| HU-3.14 | Alertar sobre el fin de la vida útil en flota | Should | 3 |  |
| HU-4.12 | Retener ISR en pagos al exterior | Should | 3 |  |
| HU-4.15 | Registrar notas de crédito y devoluciones de proveedores | Should | 3 |  |
| HU-5.10 | Realizar el conteo físico de repuestos | Should | 3 |  |
| HU-6.04 | Emitir notas de débito | Should | 3 |  |
| HU-6.10 | Identificar depósitos no aplicados | Should | 3 |  |
| HU-7.08 | Consultar el inventario de unidades y repuestos | Should | 3 |  |
| HU-7.10 | Consultar un tablero gerencial | Should | 5 |  |

**Demo:** Tablero gerencial con ocupación, resultados y cartera; conteo físico de repuestos; notas de débito; retenciones a pagos al exterior; alerta de fin de vida útil.

**Antes del sprint:** —


## Release 3

### Sprint 16 · Garantías y casos de borde (05/07 – 16/07/2027) · 27 SP

**Objetivo:** Garantías, traspaso, recuperación y reestructura. **Release 3.**.

| Historia | Descripción | MoSCoW | SP | Nota |
|---|---|---|---|---|
| HU-4.10 | Registrar compras a particulares con factura especial | Could | 3 |  |
| HU-5.08 | Validar la garantía de una unidad vendida | Should | 3 |  |
| HU-8.03 | Reservar una unidad con anticipo | Should | 3 |  |
| HU-8.06 | Controlar el traspaso de propiedad | Should | 3 |  |
| HU-8.11 | Registrar la garantía ofrecida al comprador | Should | 3 |  |
| HU-9.11 | Registrar y liberar la garantía prendaria | Should | 2 |  |
| HU-9.12 | Recuperar una unidad por impago | Should | 5 |  |
| HU-9.15 | Reestructurar un crédito | Could | 5 |  |

**Demo:** Una unidad vendida con garantía regresa al taller sin cargo; se recupera una unidad por impago y reingresa al inventario; se reestructura un crédito.

**Antes del sprint:** Plazo y cobertura de la garantía de postventa.

---

## 7. Correcciones de dependencias y de alcance

Se revisaron las dependencias de las 130 historias contra la secuencia. Quedan solo dos excepciones aceptadas a propósito.

| Caso | Tratamiento |
|---|---|
| HU-3.06 (contrato) antes de HU-3.05 (tarifario) | **Corregido.** El tarifario va primero en el Sprint 4; en el Sprint 1 el contrato lleva la tarifa capturada a mano |
| HU-5.07 (cerrar orden) antes de HU-5.05 y HU-5.06 (repuestos y subcontratos) | **Corregido.** HU-5.07 se completa en el Sprint 4, junto con los repuestos y los subcontratos; en el Sprint 1 solo cierra con mano de obra |
| HU-2.09 (diferencial cambiario) | Va en el Sprint 3, antes de HU-4.14 (pago a proveedores) y HU-6.07 (cobros) |
| HU-1.07 antes de HU-1.06 | **Aceptada.** En el Sprint 1 el tipo de cambio se carga a mano y la historia queda completa; el servicio del Banguat llega en el Sprint 2 |
| HU-7.02 (rentabilidad por unidad) antes de HU-8.12 (margen de venta) | **Aceptada.** Sale en el Sprint 8 con el ciclo hasta flota y se completa en el Sprint 12 con el resultado de la venta |
| HU-8.05 y HU-9.02 dependen una de la otra | Se construyen en el mismo sprint (13). Conviene revisar la redacción de esas historias antes del Release 2 |
| HU-10.10 (operación en paralelo) | **Se propone moverla al Release 1** (Sprint 11): es una comprobación previa al arranque definitivo y el mapa la tenía en Release 2. Requiere validarlo con el cliente |
| HU-1.01 y HU-1.08 | Pasan al Sprint 2: no son necesarias para recorrer el ciclo del Sprint 1 |
| HU-1.11, criterio de exportar a Excel | Se construye con HU-7.09 (Sprint 8) |

---

## 8. Dependencias externas con fecha límite

| Qué se necesita | Quién | Fecha límite | Historias |
|---|---|---|---|
| Elección del stack tecnológico | Equipo y responsables del proyecto | **Antes del 02/11/2026** | Todas |
| Refinamiento de reglas de partida con el contador | Contador | 04/11/2026 | Sprint 1 completo |
| Régimen de ISR, agente de retención y número de sociedades | Contador | 30/11/2026 | HU-1.01, HU-4.11 |
| Acceso o contingencia del tipo de cambio del Banguat | Equipo técnico | 30/11/2026 | HU-1.06 |
| Regla de prorrateo de gastos compartidos | Contador | 04/01/2027 | HU-4.05 |
| Método de costeo de repuestos | Contador | 18/01/2027 | HU-5.04 |
| Depreciación fiscal frente a financiera y vida útil | Contador | 18/01/2027 | HU-3.02, HU-2.07 |
| Tarifas de alquiler, depósitos y cobros adicionales | Gerente financiero | 18/01/2027 | HU-3.05, HU-3.07, HU-3.09 |
| **Certificador FEL elegido y credenciales de pruebas** | Gerente financiero, contador | **18/01/2027** (contrato firmado durante los sprints 2 y 3) | HU-6.02 a HU-6.06 |
| Los 3 a 5 reportes más usados | Gerencia | 15/03/2027 | Épica 7 |
| Catálogo de cuentas actual y estados financieros validados a la fecha de corte | Contador | 01/03/2027 (limpieza de datos desde el Sprint 6) | Épica 10 |
| Tratamiento fiscal de la venta de unidades y reglas de comisión | Contador, gerente financiero | 26/04/2027 | HU-8.07 a HU-8.10 |
| Condiciones de financiamiento e IVA sobre intereses | Gerente financiero, contador | 10/05/2027 | Épica 9 |
| Plazo y cobertura de la garantía de postventa | Gerencia | 21/06/2027 | HU-8.11, HU-5.08 |

---

## 9. Riesgos

| Riesgo | Efecto | Mitigación |
|---|---|---|
| La velocidad de 40 SP es una hipótesis | Corre las fechas (sección 5) | Medir el esfuerzo real desde el Sprint 1; recalibrar al cierre de los sprints 2 y 3; comunicar siempre un rango de fechas |
| Estimación inicial de SP sin contrastar con este equipo | Mismo efecto | Revisar los SP en cada refinamiento; medir el factor real de días por SP en el Sprint 1 |
| Se acumula deuda técnica del corte delgado | Retrabajo en el Sprint 2 | La tabla de deuda deliberada de [Sprint1.md](Sprint1.md) tiene sprint de resolución para cada atajo |
| Certificador FEL con retraso | Bloquea los sprints 5 y 6 | Elegirlo antes del 18/01; plan B: registrar documentos emitidos fuera del sistema (HU-6.06, adelantable) |
| Reglas contables sin validar | Retrabajo de partidas en varios módulos | Refinamiento semanal con el contador; reglas aisladas en un módulo hasta el Sprint 2 |
| Datos de migración de mala calidad | Retrasa el Sprint 9 y el arranque | Limpiar y validar datos reales desde el Sprint 6; cargas de prueba desde el Sprint 7 |
| El Sprint 5 concentra 37 SP con la integración FEL real (13 SP) | Puede desbordar | Si el certificador no está listo, se mueve HU-3.10 al Sprint 6 y se adelantan reportes de menor riesgo |
| Receso de fin de año | Pérdida de ritmo y contexto | Cerrar el Sprint 2 con respaldos probados y demo; retomar con un refinamiento antes del Sprint 3 |
| Hay una segunda sociedad | Obliga a evaluar multiempresa, hoy fuera del alcance | Confirmar antes del 30/11 |
| Ausencias en un equipo de 3 | Se pierde un tercio de la capacidad | Los márgenes de los sprints 10, 11 y 16; reducir alcance desde las historias de menor valor |

---

## 10. Ceremonias y definiciones

| Ceremonia | Cuándo | Duración |
|---|---|---|
| Planeación del sprint | Primer lunes | 2 h |
| Daily | Diario | 15 min |
| Refinamiento con el contador | Miércoles de la semana 1 de cada sprint | 1 h |
| Revisión (demo) con el cliente | Último viernes | 1 h |
| Retrospectiva | Último viernes, después de la revisión | 45 min |

**Definición de listo.** La historia tiene criterios de aceptación verificables; sus pendientes con el cliente están resueltos o hay un supuesto por escrito; sus dependencias están terminadas o en el mismo sprint; si genera partidas, la regla de contabilización (cuentas, línea y VIN) está definida con el contador. Si la historia ya tiene una versión delgada, el refinamiento identifica los criterios que faltan.

**Definición de terminado.** Cumple todos sus criterios en el ambiente de pruebas; cada criterio tiene al menos una prueba automática y la prueba del ciclo completo sigue pasando; las partidas cuadran en quetzales y llevan línea y VIN cuando aplique; los cambios quedan en la bitácora; respeta la separación entre quien registra y quien aprueba; el contador la validó con un caso real o de ejemplo.

---

## Apéndice: backlog completo

Valor y SP son estimación inicial. "Hecho en S1" son los SP de referencia del alcance delgado del Sprint 1; no se cuentan como avance aceptado.

| Historia | Épica | MoSCoW | Valor | SP | Hecho en S1 | Pendiente | Sprint |
|---|---|---|---|---|---|---|---|
| **HU-1.07** Registrar transacciones en dólares | E1 | Must | 10 | 3 | 3 | 0 | S1 |
| **HU-1.01** Registrar el perfil fiscal de la empresa | E1 | Must | 9 | 3 | — | 3 | S2 |
| **HU-1.02** Mantener el catálogo de cuentas | E1 | Must | 10 | 5 | 3 | 2 | S1 → S2 |
| **HU-1.04** Configurar las dimensiones analíticas | E1 | Must | 10 | 3 | 2 | 1 | S1 → S2 |
| **HU-1.05** Registrar y validar unidades por VIN | E1 | Must | 10 | 5 | 3 | 2 | S1 → S2 |
| **HU-1.06** Cargar el tipo de cambio de referencia del Banguat | E1 | Must | 10 | 5 | 2 | 3 | S1 → S2 |
| **HU-1.08** Configurar cuentas bancarias en quetzales y dólares | E1 | Must | 9 | 3 | — | 3 | S2 |
| **HU-1.09** Administrar usuarios y roles | E1 | Must | 10 | 5 | 2 | 3 | S1 → S2 |
| **HU-1.10** Separar funciones de registro y aprobación | E1 | Must | 10 | 5 | 3 | 2 | S1 → S2 |
| **HU-1.11** Consultar la bitácora de cambios | E1 | Must | 10 | 3 | 2 | 1 | S1 → S2 |
| **HU-1.12** Respaldar y restaurar la información | E1 | Must | 9 | 5 | — | 5 | S2 |
| **HU-2.01** Registrar una partida manual | E2 | Must | 10 | 5 | 3 | 2 | S1 → S2 |
| **HU-2.02** Revisar y contabilizar partidas | E2 | Must | 10 | 5 | 3 | 2 | S1 → S2 |
| **HU-2.03** Generar partidas automáticas desde los módulos | E2 | Must | 10 | 8 | 5 | 3 | S1 → S2 |
| **HU-2.05** Revertir una partida contabilizada | E2 | Must | 9 | 3 | — | 3 | S2 |
| **HU-2.16** Consultar el balance de comprobación y el mayor | E2 | Must | 10 | 5 | 3 | 2 | S1 → S2 |
| **HU-4.01** Registrar proveedores locales y del exterior | E4 | Must | 9 | 2 | 1 | 1 | S1 → S2 |
| **HU-4.02** Registrar la compra de una unidad en EE. UU. | E4 | Must | 9 | 5 | 4 | 1 | S1 → S2 |
| **HU-2.09** Calcular el diferencial cambiario realizado | E2 | Must | 10 | 5 | — | 5 | S3 |
| **HU-4.03** Agrupar unidades en un expediente de importación | E4 | Must | 8 | 3 | — | 3 | S3 |
| **HU-4.04** Registrar los gastos de importación | E4 | Must | 9 | 5 | 3 | 2 | S1 → S3 |
| **HU-4.05** Prorratear los gastos compartidos | E4 | Must | 8 | 5 | — | 5 | S3 |
| **HU-4.06** Registrar la DUCA y vincularla a las unidades | E4 | Must | 8 | 3 | — | 3 | S3 |
| **HU-4.07** Seguir el estado de la unidad durante la importación | E4 | Must | 9 | 3 | 2 | 1 | S1 → S3 |
| **HU-4.08** Consultar la hoja de costo de una unidad | E4 | Must | 9 | 3 | 2 | 1 | S1 → S3 |
| **HU-4.09** Registrar facturas de compras y gastos locales | E4 | Must | 8 | 5 | — | 5 | S3 |
| **HU-4.11** Retener IVA e ISR a proveedores locales | E4 | Must | 8 | 5 | — | 5 | S3 |
| **HU-4.16** Consultar antigüedad de saldos y estado de cuenta de proveedores | E4 | Must | 8 | 5 | — | 5 | S3 |
| **HU-5.01** Abrir una orden de trabajo ligada a un VIN | E5 | Must | 9 | 3 | 2 | 1 | S1 → S3 |
| **HU-5.02** Configurar las tarifas de mano de obra | E5 | Must | 9 | 2 | 1 | 1 | S1 → S3 |
| **HU-5.03** Registrar mano de obra en la orden | E5 | Must | 9 | 3 | 2 | 1 | S1 → S3 |
| **HU-3.01** Dar de alta una unidad como activo fijo de la flota | E3 | Must | 10 | 5 | 3 | 2 | S1 → S4 |
| **HU-3.02** Definir los parámetros de depreciación de cada unidad | E3 | Must | 9 | 5 | — | 5 | S4 |
| **HU-3.04** Controlar seguros, marchamo y documentos de cada unidad | E3 | Must | 9 | 5 | — | 5 | S4 |
| **HU-3.05** Mantener el tarifario de alquiler | E3 | Must | 9 | 3 | — | 3 | S4 |
| **HU-4.13** Programar y aprobar pagos a proveedores | E4 | Must | 8 | 5 | — | 5 | S4 |
| **HU-4.14** Registrar el pago a un proveedor | E4 | Must | 8 | 5 | — | 5 | S4 |
| **HU-5.04** Mantener el catálogo e inventario de repuestos | E5 | Must | 8 | 5 | — | 5 | S4 |
| **HU-5.05** Consumir repuestos en una orden | E5 | Must | 8 | 3 | — | 3 | S4 |
| **HU-5.06** Registrar trabajos subcontratados | E5 | Must | 8 | 3 | — | 3 | S4 |
| **HU-5.07** Cerrar la orden y generar su destino contable | E5 | Must | 9 | 5 | 3 | 2 | S1 → S4 |
| **HU-3.06** Registrar un contrato de alquiler | E3 | Must | 10 | 5 | — | 5 | S5 |
| **HU-3.07** Recibir, aplicar y devolver depósitos en garantía | E3 | Must | 9 | 5 | — | 5 | S5 |
| **HU-3.08** Cerrar un contrato al devolver la unidad | E3 | Must | 10 | 3 | — | 3 | S5 |
| **HU-3.10** Facturar contratos de forma recurrente | E3 | Must | 9 | 8 | — | 8 | S5 |
| **HU-6.01** Registrar clientes | E6 | Must | 9 | 3 | — | 3 | S5 |
| **HU-6.02** Emitir una factura FEL | E6 | Must | 9 | 13 | — | 13 | S5 |
| **HU-3.09** Registrar cargos adicionales del contrato | E3 | Must | 9 | 5 | — | 5 | S6 |
| **HU-6.03** Emitir notas de crédito | E6 | Must | 8 | 5 | — | 5 | S6 |
| **HU-6.05** Anular un documento FEL | E6 | Must | 8 | 5 | — | 5 | S6 |
| **HU-6.07** Registrar cobros y aplicarlos a facturas | E6 | Must | 9 | 5 | — | 5 | S6 |
| **HU-6.08** Registrar retenciones que nos hacen los clientes | E6 | Must | 8 | 3 | — | 3 | S6 |
| **HU-6.09** Registrar y aplicar anticipos de clientes | E6 | Must | 8 | 5 | — | 5 | S6 |
| **HU-6.11** Consultar el estado de cuenta de un cliente | E6 | Must | 8 | 3 | — | 3 | S6 |
| **HU-6.12** Consultar la antigüedad de saldos de clientes | E6 | Must | 8 | 5 | — | 5 | S6 |
| **HU-2.07** Calcular la depreciación mensual | E2 | Must | 9 | 8 | — | 8 | S7 |
| **HU-2.08** Revaluar saldos en dólares al cierre | E2 | Must | 9 | 5 | — | 5 | S7 |
| **HU-2.10** Conciliar las cuentas bancarias | E2 | Must | 9 | 8 | — | 8 | S7 |
| **HU-2.12** Cerrar un período mensual | E2 | Must | 9 | 5 | — | 5 | S7 |
| **HU-2.13** Reabrir un período cerrado | E2 | Must | 9 | 3 | — | 3 | S7 |
| **HU-2.14** Ejecutar el cierre anual | E2 | Must | 9 | 5 | — | 5 | S7 |
| **HU-3.12** Consultar la ocupación de la flota | E3 | Must | 9 | 5 | — | 5 | S7 |
| **HU-3.13** Consultar la rentabilidad por contrato y por unidad | E3 | Must | 9 | 5 | — | 5 | S8 |
| **HU-3.15** Dar de baja una unidad de la flota y pasarla a venta | E3 | Must | 9 | 5 | — | 5 | S8 |
| **HU-7.01** Consultar estados financieros por línea de negocio | E7 | Must | 7 | 8 | — | 8 | S8 |
| **HU-7.02** Consultar la rentabilidad de cada unidad en todo su ciclo | E7 | Must | 8 | 5 | — | 5 | S8 |
| **HU-7.03** Consultar la ocupación y rentabilidad de la flota | E7 | Must | 7 | 5 | — | 5 | S8 |
| **HU-7.04** Consultar las unidades por etapa del ciclo | E7 | Must | 8 | 3 | — | 3 | S8 |
| **HU-7.07** Consultar la antigüedad de saldos de clientes y proveedores | E7 | Must | 7 | 3 | — | 3 | S8 |
| **HU-7.09** Exportar reportes a PDF y Excel | E7 | Must | 7 | 5 | — | 5 | S8 |
| **HU-2.15** Emitir los libros legales | E2 | Must | 9 | 8 | — | 8 | S9 |
| **HU-5.09** Facturar la postventa no cubierta por garantía | E5 | Must | 8 | 3 | — | 3 | S9 |
| **HU-10.01** Descargar plantillas de carga y validar archivos | E10 | Must | 7 | 5 | — | 5 | S9 |
| **HU-10.02** Cargar los saldos contables iniciales | E10 | Must | 7 | 3 | — | 3 | S9 |
| **HU-10.03** Cargar la flota con su valor en libros | E10 | Must | 7 | 5 | — | 5 | S9 |
| **HU-10.04** Cargar unidades en importación, en taller y en venta | E10 | Must | 7 | 3 | — | 3 | S9 |
| **HU-10.05** Cargar clientes, proveedores y sus saldos abiertos | E10 | Must | 7 | 5 | — | 5 | S9 |
| **HU-10.07** Cargar el inventario de repuestos | E10 | Must | 7 | 2 | — | 2 | S9 |
| **HU-10.08** Cargar los contratos de alquiler activos | E10 | Must | 7 | 3 | — | 3 | S9 |
| **HU-10.09** Conciliar el arranque y aceptar los saldos | E10 | Must | 7 | 5 | — | 5 | S10 |
| **HU-10.11** Capacitar a los usuarios por rol (habilitación) | E10 | Must | 7 | 2 | — | 2 | S10 |
| **HU-10.10** Operar en paralelo antes del arranque definitivo | E10 | Should | 4 | 3 | — | 3 | S11 |
| **HU-10.12** Dar soporte inicial tras el arranque (habilitación) | E10 | Must | 7 | 2 | — | 2 | S11 |
| **HU-2.04** Programar partidas recurrentes | E2 | Should | 6 | 3 | — | 3 | S12 |
| **HU-2.06** Registrar provisiones con reversión automática | E2 | Should | 6 | 3 | — | 3 | S12 |
| **HU-7.06** Consultar las comisiones por vendedor | E7 | Must | 7 | 3 | — | 3 | S12 |
| **HU-8.01** Consultar el inventario de unidades en venta | E8 | Must | 6 | 2 | — | 2 | S12 |
| **HU-8.02** Fijar el precio de lista y el precio mínimo | E8 | Must | 6 | 2 | — | 2 | S12 |
| **HU-8.04** Registrar una venta de contado | E8 | Must | 6 | 5 | — | 5 | S12 |
| **HU-8.07** Configurar el tratamiento fiscal de la venta de unidades | E8 | Must | 6 | 3 | — | 3 | S12 |
| **HU-8.08** Registrar vendedores y reglas de comisión | E8 | Must | 6 | 3 | — | 3 | S12 |
| **HU-8.09** Calcular la comisión de cada venta | E8 | Must | 6 | 5 | — | 5 | S12 |
| **HU-8.10** Liquidar comisiones por período | E8 | Must | 6 | 5 | — | 5 | S12 |
| **HU-8.12** Ver el margen de la unidad vendida | E8 | Must | 6 | 3 | — | 3 | S12 |
| **HU-8.05** Registrar una venta financiada | E8 | Must | 6 | 5 | — | 5 | S13 |
| **HU-9.01** Definir planes de crédito | E9 | Must | 6 | 3 | — | 3 | S13 |
| **HU-9.02** Registrar y aprobar un crédito | E9 | Must | 6 | 5 | — | 5 | S13 |
| **HU-9.03** Generar la tabla de amortización | E9 | Must | 6 | 5 | — | 5 | S13 |
| **HU-9.04** Devengar los intereses mensuales | E9 | Must | 6 | 5 | — | 5 | S13 |
| **HU-9.05** Facturar los intereses | E9 | Must | 6 | 5 | — | 5 | S13 |
| **HU-9.06** Registrar el cobro de una cuota | E9 | Must | 6 | 5 | — | 5 | S13 |
| **HU-9.07** Registrar abonos extraordinarios a capital | E9 | Must | 6 | 3 | — | 3 | S13 |
| **HU-9.08** Cancelar un crédito de forma anticipada | E9 | Must | 6 | 3 | — | 3 | S13 |
| **HU-1.03** Importar el catálogo de cuentas existente | E1 | Should | 6 | 5 | — | 5 | S14 |
| **HU-2.11** Seguir una lista de verificación de cierre | E2 | Should | 6 | 5 | — | 5 | S14 |
| **HU-6.06** Registrar documentos FEL emitidos fuera del sistema | E6 | Should | 5 | 3 | — | 3 | S14 |
| **HU-7.05** Consultar la cartera financiada y la mora | E7 | Must | 7 | 5 | — | 5 | S14 |
| **HU-9.09** Calcular la mora y el interés moratorio | E9 | Must | 6 | 5 | — | 5 | S14 |
| **HU-9.10** Calcular la antigüedad de la cartera y la provisión por incobrables | E9 | Must | 6 | 5 | — | 5 | S14 |
| **HU-9.13** Emitir el estado de cuenta del crédito | E9 | Must | 6 | 3 | — | 3 | S14 |
| **HU-9.14** Conciliar la cartera con la contabilidad | E9 | Must | 6 | 3 | — | 3 | S14 |
| **HU-10.06** Cargar la cartera financiada vigente | E10 | Must | 7 | 5 | — | 5 | S14 |
| **HU-3.03** Capitalizar una mejora a una unidad de la flota | E3 | Should | 6 | 3 | — | 3 | S15 |
| **HU-3.11** Extender un contrato vigente | E3 | Should | 6 | 3 | — | 3 | S15 |
| **HU-3.14** Alertar sobre el fin de la vida útil en flota | E3 | Should | 6 | 3 | — | 3 | S15 |
| **HU-4.12** Retener ISR en pagos al exterior | E4 | Should | 5 | 3 | — | 3 | S15 |
| **HU-4.15** Registrar notas de crédito y devoluciones de proveedores | E4 | Should | 5 | 3 | — | 3 | S15 |
| **HU-5.10** Realizar el conteo físico de repuestos | E5 | Should | 5 | 3 | — | 3 | S15 |
| **HU-6.04** Emitir notas de débito | E6 | Should | 5 | 3 | — | 3 | S15 |
| **HU-6.10** Identificar depósitos no aplicados | E6 | Should | 5 | 3 | — | 3 | S15 |
| **HU-7.08** Consultar el inventario de unidades y repuestos | E7 | Should | 4 | 3 | — | 3 | S15 |
| **HU-7.10** Consultar un tablero gerencial | E7 | Should | 4 | 5 | — | 5 | S15 |
| **HU-4.10** Registrar compras a particulares con factura especial | E4 | Could | 3 | 3 | — | 3 | S16 |
| **HU-5.08** Validar la garantía de una unidad vendida | E5 | Should | 5 | 3 | — | 3 | S16 |
| **HU-8.03** Reservar una unidad con anticipo | E8 | Should | 3 | 3 | — | 3 | S16 |
| **HU-8.06** Controlar el traspaso de propiedad | E8 | Should | 3 | 3 | — | 3 | S16 |
| **HU-8.11** Registrar la garantía ofrecida al comprador | E8 | Should | 3 | 3 | — | 3 | S16 |
| **HU-9.11** Registrar y liberar la garantía prendaria | E9 | Should | 3 | 2 | — | 2 | S16 |
| **HU-9.12** Recuperar una unidad por impago | E9 | Should | 3 | 5 | — | 5 | S16 |
| **HU-9.15** Reestructurar un crédito | E9 | Could | 1 | 5 | — | 5 | S16 |
| **Total (130 historias)** | | | | **546** | **57** | **489** | |
