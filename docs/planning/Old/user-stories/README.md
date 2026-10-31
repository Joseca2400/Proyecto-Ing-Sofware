# Historias de usuario

Sistema administrativo y financiero para la empresa de alquiler, venta y taller de vehículos. Las historias desarrollan las 10 épicas de [epicas.md](../contexto/epicas.md) (versión 3, 23 de octubre de 2026).

Versión 1 · 23 de octubre de 2026 · Borrador para validar con el cliente.

## Convenciones

**Identificador.** `HU-<épica>.<número>`. Por ejemplo, HU-3.06 es la sexta historia de la Épica 3.

**Formato.** Cada historia sigue la plantilla:

> **Como** <rol>, **quiero** <acción>, **para** <beneficio>.
>
> Prioridad · Depende de
>
> Criterios de aceptación numerados, verificables en una prueba.
>
> Pendiente: preguntas abiertas con el cliente que pueden cambiar la historia.

**Roles.** Son los definidos en la Épica 1 (HU-1.09):

| Rol | Qué hace en el sistema |
|---|---|
| Auxiliar contable | Registra documentos y operaciones |
| Contador | Revisa, contabiliza, concilia y cierra |
| Gerente financiero | Aprueba pagos, ajustes, descuentos, créditos y reapertura de períodos |
| Gerencia | Solo consulta reportes y tableros |

Supuesto: mientras no se responda quién registra la operación (contratos, órdenes de taller y ventas), esas historias se asignan al auxiliar contable. Si se agregan usuarios operativos, basta con cambiar el rol de esas historias.

**Prioridad.** MoSCoW dentro de su épica: Must (indispensable para el arranque), Should (importante, puede ir en una segunda entrega), Could (deseable). Una historia Must de una épica Should (épicas 8 y 9) hereda la prioridad de la épica: es indispensable solo cuando esa épica entra al alcance.

**Dependencias.** "Depende de" indica las historias que deben estar construidas antes. Hay dependencias entre épicas (por ejemplo, el alta en flota, HU-3.01, necesita la hoja de costo de la importación, HU-4.08), por lo que el orden de construcción no sigue estrictamente el número de épica.

## Definición de listo (para entrar a un sprint)

- La historia tiene criterios de aceptación verificables.
- Sus pendientes con el cliente están resueltos, o se acordó un supuesto por escrito.
- Las historias de las que depende están terminadas o planificadas en el mismo sprint.
- Si genera partidas, la regla de contabilización (cuentas, línea y VIN) está definida con el contador.

## Definición de terminado

- Cumple todos sus criterios de aceptación en el ambiente de pruebas.
- Las partidas que genera cuadran en quetzales y llevan línea de negocio y, cuando aplique, VIN.
- Los registros que crea o modifica quedan en la bitácora.
- Respeta la separación entre quien registra y quien aprueba.
- El contador la validó con un caso real o de ejemplo.

## Resumen

| Épica | Historias | Must | Should | Could |
|---|---|---|---|---|
| 1. Configuración, multimoneda y seguridad | 12 | 11 | 1 | 0 |
| 2. Contabilidad general y cierre | 16 | 13 | 3 | 0 |
| 3. Flota, activos fijos y alquileres | 15 | 12 | 3 | 0 |
| 4. Importación, compras y cuentas por pagar | 16 | 13 | 2 | 1 |
| 5. Taller interno y postventa | 10 | 8 | 2 | 0 |
| 6. Facturación electrónica y cuentas por cobrar | 12 | 9 | 3 | 0 |
| 7. Reportes gerenciales | 10 | 8 | 2 | 0 |
| 8. Venta de unidades y comisiones | 12 | 9 | 3 | 0 |
| 9. Financiamiento propio y cartera | 15 | 12 | 2 | 1 |
| 10. Migración y arranque | 12 | 11 | 1 | 0 |
| **Total** | **130** | **106** | **22** | **2** |

## Orden de construcción sugerido

El orden sigue el ciclo de vida de la unidad y respeta las dependencias entre épicas:

1. **Base:** Épica 1 completa y Épica 2 hasta HU-2.05 (partidas, aprobación, partidas automáticas y reversión).
2. **Costo de la unidad:** Épica 4 (proveedores, compra, importación, DUCA, prorrateo, hoja de costo, cuentas por pagar) y Épica 5 (órdenes de taller y repuestos).
3. **Ingreso principal:** HU-6.01 y HU-6.02 (clientes y FEL), luego Épica 3 (alta en flota, contratos, depósitos, facturación recurrente) y el resto de la Épica 6.
4. **Cierre:** resto de la Épica 2 (depreciación, revaluación, conciliación, cierre y libros legales).
5. **Reportes:** Épica 7, empezando por los 3 a 5 reportes que el cliente confirme como clave.
6. **Salida de la flota:** épicas 8 y 9. Si ya hay créditos vigentes, la Épica 9 se adelanta.
7. **Arranque:** Épica 10.

## Pendientes con el cliente que afectan historias

| Pendiente | Historias afectadas |
|---|---|
| Quién registra la operación (contratos, taller, ventas) | HU-1.09, HU-3.06, HU-5.01, HU-8.04 |
| Una o dos sociedades | HU-1.01 (si son dos, se revisa el alcance de multiempresa) |
| Régimen de ISR y calidad de agente de retención | HU-1.01, HU-4.11, HU-4.12 |
| Depreciación fiscal frente a financiera | HU-2.07, HU-3.02 |
| Regla de fin de vida útil en flota | HU-3.14 |
| Tarifas, depósitos y cobros adicionales de alquiler | HU-3.05, HU-3.07, HU-3.09 |
| Cálculo, devengo y pago de comisiones; si los vendedores son empleados | HU-8.08, HU-8.09, HU-8.10 |
| Condiciones de financiamiento, impago y créditos vigentes | Épica 9 completa, HU-10.06 |
| Facturación en USD | HU-6.02 |
| Garantía de postventa: plazo y cobertura | HU-5.08, HU-8.11 |
| Prorrateo de gastos de importación compartidos | HU-4.05 |
| Compras a particulares (factura especial) | HU-4.10 |
| Tratamiento fiscal de la venta de unidades de la flota | HU-8.07 |
| IVA sobre intereses del financiamiento | HU-9.05 |
| Certificador FEL | HU-6.02 a HU-6.06 |
| Método de costeo de repuestos | HU-5.04 |
| Los 3 a 5 reportes más usados | Épica 7 (orden de construcción) |

## Índice de historias

#### [Épica 1. Configuración, multimoneda y seguridad](E01-configuracion-multimoneda-seguridad.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-1.01 | Registrar el perfil fiscal de la empresa | Must |
| HU-1.02 | Mantener el catálogo de cuentas | Must |
| HU-1.03 | Importar el catálogo de cuentas existente | Should |
| HU-1.04 | Configurar las dimensiones analíticas | Must |
| HU-1.05 | Registrar y validar unidades por VIN | Must |
| HU-1.06 | Cargar el tipo de cambio de referencia del Banguat | Must |
| HU-1.07 | Registrar transacciones en dólares | Must |
| HU-1.08 | Configurar cuentas bancarias en quetzales y dólares | Must |
| HU-1.09 | Administrar usuarios y roles | Must |
| HU-1.10 | Separar funciones de registro y aprobación | Must |
| HU-1.11 | Consultar la bitácora de cambios | Must |
| HU-1.12 | Respaldar y restaurar la información | Must |

#### [Épica 2. Contabilidad general y cierre](E02-contabilidad-general-cierre.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-2.01 | Registrar una partida manual | Must |
| HU-2.02 | Revisar y contabilizar partidas | Must |
| HU-2.03 | Generar partidas automáticas desde los módulos | Must |
| HU-2.04 | Programar partidas recurrentes | Should |
| HU-2.05 | Revertir una partida contabilizada | Must |
| HU-2.06 | Registrar provisiones con reversión automática | Should |
| HU-2.07 | Calcular la depreciación mensual | Must |
| HU-2.08 | Revaluar saldos en dólares al cierre | Must |
| HU-2.09 | Calcular el diferencial cambiario realizado | Must |
| HU-2.10 | Conciliar las cuentas bancarias | Must |
| HU-2.11 | Seguir una lista de verificación de cierre | Should |
| HU-2.12 | Cerrar un período mensual | Must |
| HU-2.13 | Reabrir un período cerrado | Must |
| HU-2.14 | Ejecutar el cierre anual | Must |
| HU-2.15 | Emitir los libros legales | Must |
| HU-2.16 | Consultar el balance de comprobación y el mayor | Must |

#### [Épica 3. Flota, activos fijos y alquileres](E03-flota-activos-fijos-alquileres.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-3.01 | Dar de alta una unidad como activo fijo de la flota | Must |
| HU-3.02 | Definir los parámetros de depreciación de cada unidad | Must |
| HU-3.03 | Capitalizar una mejora a una unidad de la flota | Should |
| HU-3.04 | Controlar seguros, marchamo y documentos de cada unidad | Must |
| HU-3.05 | Mantener el tarifario de alquiler | Must |
| HU-3.06 | Registrar un contrato de alquiler | Must |
| HU-3.07 | Recibir, aplicar y devolver depósitos en garantía | Must |
| HU-3.08 | Cerrar un contrato al devolver la unidad | Must |
| HU-3.09 | Registrar cargos adicionales del contrato | Must |
| HU-3.10 | Facturar contratos de forma recurrente | Must |
| HU-3.11 | Extender un contrato vigente | Should |
| HU-3.12 | Consultar la ocupación de la flota | Must |
| HU-3.13 | Consultar la rentabilidad por contrato y por unidad | Must |
| HU-3.14 | Alertar sobre el fin de la vida útil en flota | Should |
| HU-3.15 | Dar de baja una unidad de la flota y pasarla a venta | Must |

#### [Épica 4. Importación, compras y cuentas por pagar](E04-importacion-compras-cxp.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-4.01 | Registrar proveedores locales y del exterior | Must |
| HU-4.02 | Registrar la compra de una unidad en EE. UU. | Must |
| HU-4.03 | Agrupar unidades en un expediente de importación | Must |
| HU-4.04 | Registrar los gastos de importación | Must |
| HU-4.05 | Prorratear los gastos compartidos | Must |
| HU-4.06 | Registrar la DUCA y vincularla a las unidades | Must |
| HU-4.07 | Seguir el estado de la unidad durante la importación | Must |
| HU-4.08 | Consultar la hoja de costo de una unidad | Must |
| HU-4.09 | Registrar facturas de compras y gastos locales | Must |
| HU-4.10 | Registrar compras a particulares con factura especial | Could |
| HU-4.11 | Retener IVA e ISR a proveedores locales | Must |
| HU-4.12 | Retener ISR en pagos al exterior | Should |
| HU-4.13 | Programar y aprobar pagos a proveedores | Must |
| HU-4.14 | Registrar el pago a un proveedor | Must |
| HU-4.15 | Registrar notas de crédito y devoluciones de proveedores | Should |
| HU-4.16 | Consultar antigüedad de saldos y estado de cuenta de proveedores | Must |

#### [Épica 5. Taller interno y postventa](E05-taller-interno-postventa.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-5.01 | Abrir una orden de trabajo ligada a un VIN | Must |
| HU-5.02 | Configurar las tarifas de mano de obra | Must |
| HU-5.03 | Registrar mano de obra en la orden | Must |
| HU-5.04 | Mantener el catálogo e inventario de repuestos | Must |
| HU-5.05 | Consumir repuestos en una orden | Must |
| HU-5.06 | Registrar trabajos subcontratados | Must |
| HU-5.07 | Cerrar la orden y generar su destino contable | Must |
| HU-5.08 | Validar la garantía de una unidad vendida | Should |
| HU-5.09 | Facturar la postventa no cubierta por garantía | Must |
| HU-5.10 | Realizar el conteo físico de repuestos | Should |

#### [Épica 6. Facturación electrónica y cuentas por cobrar](E06-facturacion-electronica-cxc.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-6.01 | Registrar clientes | Must |
| HU-6.02 | Emitir una factura FEL | Must |
| HU-6.03 | Emitir notas de crédito | Must |
| HU-6.04 | Emitir notas de débito | Should |
| HU-6.05 | Anular un documento FEL | Must |
| HU-6.06 | Registrar documentos FEL emitidos fuera del sistema | Should |
| HU-6.07 | Registrar cobros y aplicarlos a facturas | Must |
| HU-6.08 | Registrar retenciones que nos hacen los clientes | Must |
| HU-6.09 | Registrar y aplicar anticipos de clientes | Must |
| HU-6.10 | Identificar depósitos no aplicados | Should |
| HU-6.11 | Consultar el estado de cuenta de un cliente | Must |
| HU-6.12 | Consultar la antigüedad de saldos de clientes | Must |

#### [Épica 7. Reportes gerenciales](E07-reportes-gerenciales.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-7.01 | Consultar estados financieros por línea de negocio | Must |
| HU-7.02 | Consultar la rentabilidad de cada unidad en todo su ciclo | Must |
| HU-7.03 | Consultar la ocupación y rentabilidad de la flota | Must |
| HU-7.04 | Consultar las unidades por etapa del ciclo | Must |
| HU-7.05 | Consultar la cartera financiada y la mora | Must |
| HU-7.06 | Consultar las comisiones por vendedor | Must |
| HU-7.07 | Consultar la antigüedad de saldos de clientes y proveedores | Must |
| HU-7.08 | Consultar el inventario de unidades y repuestos | Should |
| HU-7.09 | Exportar reportes a PDF y Excel | Must |
| HU-7.10 | Consultar un tablero gerencial | Should |

#### [Épica 8. Venta de unidades y comisiones](E08-venta-unidades-comisiones.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-8.01 | Consultar el inventario de unidades en venta | Must |
| HU-8.02 | Fijar el precio de lista y el precio mínimo | Must |
| HU-8.03 | Reservar una unidad con anticipo | Should |
| HU-8.04 | Registrar una venta de contado | Must |
| HU-8.05 | Registrar una venta financiada | Must |
| HU-8.06 | Controlar el traspaso de propiedad | Should |
| HU-8.07 | Configurar el tratamiento fiscal de la venta de unidades | Must |
| HU-8.08 | Registrar vendedores y reglas de comisión | Must |
| HU-8.09 | Calcular la comisión de cada venta | Must |
| HU-8.10 | Liquidar comisiones por período | Must |
| HU-8.11 | Registrar la garantía ofrecida al comprador | Should |
| HU-8.12 | Ver el margen de la unidad vendida | Must |

#### [Épica 9. Financiamiento propio y cartera](E09-financiamiento-cartera.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-9.01 | Definir planes de crédito | Must |
| HU-9.02 | Registrar y aprobar un crédito | Must |
| HU-9.03 | Generar la tabla de amortización | Must |
| HU-9.04 | Devengar los intereses mensuales | Must |
| HU-9.05 | Facturar los intereses | Must |
| HU-9.06 | Registrar el cobro de una cuota | Must |
| HU-9.07 | Registrar abonos extraordinarios a capital | Must |
| HU-9.08 | Cancelar un crédito de forma anticipada | Must |
| HU-9.09 | Calcular la mora y el interés moratorio | Must |
| HU-9.10 | Calcular la antigüedad de la cartera y la provisión por incobrables | Must |
| HU-9.11 | Registrar y liberar la garantía prendaria | Should |
| HU-9.12 | Recuperar una unidad por impago | Should |
| HU-9.13 | Emitir el estado de cuenta del crédito | Must |
| HU-9.14 | Conciliar la cartera con la contabilidad | Must |
| HU-9.15 | Reestructurar un crédito | Could |

#### [Épica 10. Migración y arranque](E10-migracion-arranque.md)

| ID | Historia | Prioridad |
|---|---|---|
| HU-10.01 | Descargar plantillas de carga y validar archivos | Must |
| HU-10.02 | Cargar los saldos contables iniciales | Must |
| HU-10.03 | Cargar la flota con su valor en libros | Must |
| HU-10.04 | Cargar unidades en importación, en taller y en venta | Must |
| HU-10.05 | Cargar clientes, proveedores y sus saldos abiertos | Must |
| HU-10.06 | Cargar la cartera financiada vigente | Must (si hay créditos vigentes) |
| HU-10.07 | Cargar el inventario de repuestos | Must |
| HU-10.08 | Cargar los contratos de alquiler activos | Must |
| HU-10.09 | Conciliar el arranque y aceptar los saldos | Must |
| HU-10.10 | Operar en paralelo antes del arranque definitivo | Should |
| HU-10.11 | Capacitar a los usuarios por rol (habilitación) | Must |
| HU-10.12 | Dar soporte inicial tras el arranque (habilitación) | Must |
