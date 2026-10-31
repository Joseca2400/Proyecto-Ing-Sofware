# Épicas del sistema de contabilidad: alquiler, venta y taller de vehículos

Versión 3 (23 de octubre de 2026). Son 10 épicas, ordenadas por prioridad.

Planteamiento confirmado:
- Negocio principal: **alquiler**. La venta es la salida de las unidades al final de su vida útil en la flota.
- Las unidades se **importan de EE. UU.** (usadas), se reparan en el taller propio y luego entran a la flota.
- **Taller privado**: atiende la flota propia y, como extensión, los vehículos que la empresa vendió (postventa).
- **Una sola sede.**
- Moneda: **quetzales y dólares**.
- Fiscal: Guatemala (IVA, ISR, FEL).
- **No se reciben vehículos en parte de pago.** Hay **financiamiento propio** y **comisiones para vendedores**.
- Usuarios: contador, gerente financiero y auxiliar contable. La gerencia consume reportes.

Criterio de orden: primero la base contable (sin ella no se puede registrar nada), después el ciclo de la unidad en el orden en que genera costo e ingreso, y al final las líneas secundarias y el arranque. Las prioridades se confirman con MoSCoW en la entrevista.

## Ciclo de vida de una unidad (eje del sistema)

```
Compra en EE. UU. (USD) → Importación y nacionalización → Taller (reacondicionamiento)
→ Alta como activo fijo de la flota → Alquiler + depreciación + mantenimiento
→ Baja de la flota (traslado a inventario de venta a valor en libros)
→ Venta (contado o financiada) + comisión → Postventa en taller (garantía o servicio)
```

Toda transacción debe poder ligarse a la unidad por su VIN. Esto es lo que permite calcular la rentabilidad completa de cada vehículo, desde la importación hasta la venta.

## Resumen

| Prioridad | Épica | MoSCoW inicial | Origen en v2 |
|-----------|-------|----------------|--------------|
| 1 | Configuración, multimoneda y seguridad | Must | Épicas 1 y 11 unidas |
| 2 | Contabilidad general y cierre | Must | Épica 2 |
| 3 | Flota, activos fijos y alquileres | Must | Épica 4 |
| 4 | Importación, compras y cuentas por pagar | Must | Épicas 3 y 9 unidas |
| 5 | Taller interno y postventa | Must | Épica 5 |
| 6 | Facturación electrónica y cuentas por cobrar | Must | Épica 8 |
| 7 | Reportes gerenciales | Must | Épica 10 |
| 8 | Venta de unidades y comisiones | Should | Épica 6 |
| 9 | Financiamiento propio y cartera | Should | Épica 7 |
| 10 | Migración y arranque | Must (al final) | Épica 12 |

La migración va al final porque depende de que las demás estén definidas, no porque sea opcional: sin ella no hay arranque.

---

## 1. Configuración, multimoneda y seguridad

Objetivo: dejar la base para contabilizar por línea de negocio, por unidad y en dos monedas, con funciones separadas.
Alcance:
- Datos de la empresa, NIT, régimen de ISR y calidad de agente de retención.
- Catálogo de cuentas (conservar, depurar o rediseñar).
- Dimensiones analíticas: línea de negocio (alquiler, venta, taller, financiamiento) y unidad (VIN). Sin sucursal.
- Moneda funcional en quetzales; transacciones en USD con el tipo de cambio de referencia del Banguat por fecha.
- Cuentas bancarias en quetzales y en dólares.
- Roles:
  - Auxiliar contable: registra.
  - Contador: revisa, contabiliza y cierra.
  - Gerente financiero: aprueba pagos, ajustes, descuentos, créditos y reapertura de períodos.
  - Gerencia: solo consulta reportes.
- Bitácora de cambios y respaldos.
Criterio de éxito: toda transacción se clasifica por cuenta, línea y unidad; la que se hace en USD guarda el monto original y el tipo de cambio; quien registra no aprueba.

## 2. Contabilidad general y cierre

Objetivo: registrar partidas, controlarlas y cerrar períodos con orden.
Alcance:
- Partidas manuales, automáticas y recurrentes, con aprobación.
- Ajustes, provisiones y reversiones.
- Depreciación mensual de la flota y demás activos.
- Revaluación de saldos en USD y registro del diferencial cambiario, realizado y no realizado.
- Cierre mensual y anual; reglas de reapertura.
- Libros legales (diario, mayor, inventarios, compras y ventas).
Criterio de éxito: cierre mensual reproducible, con el diferencial cambiario calculado por el sistema.

## 3. Flota, activos fijos y alquileres

Objetivo: administrar la flota y facturar los contratos, que son la principal fuente de ingreso.
Alcance:
- Alta de la unidad como activo fijo al costo final de importación y reparación; vida útil, valor residual y depreciación (financiera y fiscal, si difieren).
- Seguros, marchamo, tarjeta de circulación y mantenimiento por unidad.
- Contratos de alquiler y tarifas (diaria, semanal, mensual, por kilometraje), en Q o USD.
- Facturación recurrente y cargos adicionales: combustible, multas, daños, extensiones, deducible.
- Depósitos en garantía: recepción, aplicación y devolución.
- Ocupación: días alquilada, disponible o en taller.
- Baja de la flota: traslado a inventario de venta al valor en libros, según una regla de vida útil (kilometraje o antigüedad).
Criterio de éxito: ingreso, costo y rentabilidad por unidad y por contrato calculables en cualquier momento.

## 4. Importación, compras y cuentas por pagar

Objetivo: determinar el costo real de cada unidad importada y controlar lo que se debe a proveedores.
Alcance:
- Compra en EE. UU. (subasta o dealer) en USD, por VIN.
- Gastos de importación: flete, seguro, agente aduanal, almacenaje, DAI, IVA de importación (crédito fiscal), IPRIMA y placas.
- Registro de la DUCA y vínculo con la unidad.
- Prorrateo de los gastos compartidos (por ejemplo, un contenedor con varias unidades).
- Estado de la unidad: en tránsito, en aduana, en taller, lista.
- Proveedores locales (repuestos, seguros, servicios) y del exterior (subastas, navieras), en Q o USD.
- Retenciones de IVA e ISR y constancias, incluidos los pagos al exterior.
- Programación de pagos, antigüedad de saldos y devoluciones.
Criterio de éxito: cada unidad tiene un costo desglosado (compra, importación y reparación) al darse de alta en la flota, y los saldos por pagar cuadran en ambas monedas.

## 5. Taller interno y postventa

Objetivo: costear cada trabajo y cargarlo a la unidad correcta.
El taller no atiende clientes externos. Atiende tres tipos de trabajo:
1. Reacondicionamiento de unidades importadas: se capitaliza al costo de la unidad (Épica 4).
2. Mantenimiento y reparación de la flota: gasto de la unidad, salvo las mejoras que se capitalicen.
3. Postventa de unidades vendidas: garantía (costo de la venta) o servicio facturado al comprador.
Alcance:
- Orden de trabajo ligada a un VIN, con tipo de trabajo, mano de obra, repuestos y trabajos subcontratados.
- Costeo de mano de obra (tarifa horaria interna) y de repuestos.
- Inventario de repuestos con método de costeo (promedio ponderado, por confirmar).
- Facturación FEL solo para la postventa no cubierta por garantía.
Criterio de éxito: ninguna orden queda sin destino contable (capitalizar, gasto de flota, garantía o factura).

## 6. Facturación electrónica y cuentas por cobrar

Objetivo: emitir y registrar documentos FEL y controlar los saldos de clientes.
Alcance:
- Emisión o registro de facturas, notas de crédito y débito, con el certificador FEL (por confirmar).
- Facturas en Q o USD.
- Anulaciones.
- Cobros, anticipos, depósitos y conciliación de pagos.
- Estados de cuenta y antigüedad de saldos de alquiler y de venta de contado.
Criterio de éxito: cada documento fiscal queda ligado a su asiento, su cliente y su unidad.

## 7. Reportes gerenciales

Objetivo: dar a la gerencia visibilidad de rentabilidad y control.
Alcance:
- Estados financieros por línea de negocio, en Q (y en USD como referencia, por confirmar).
- **Rentabilidad por unidad en todo su ciclo**: costo de importación y reparación, ingresos de alquiler, mantenimiento, depreciación y resultado de la venta.
- Ocupación y rentabilidad de la flota.
- Unidades en importación, en taller, en flota y en venta.
- Cartera financiada y mora.
- Comisiones por vendedor.
- Antigüedad de saldos de clientes y proveedores.
- Exportación a PDF y Excel.
Criterio de éxito: los 3 a 5 reportes clave salen del sistema sin trabajo manual.

## 8. Venta de unidades y comisiones

Objetivo: vender las unidades que salen de la flota y liquidar las comisiones.
Alcance:
- Inventario de unidades en venta (provenientes de la flota), con costo en libros.
- Venta de contado o con financiamiento propio (Épica 9). Sin vehículos en parte de pago.
- Anticipos y reservas.
- Traspaso de propiedad y su costo.
- Tratamiento fiscal de la venta de un activo que fue de la flota: IVA de la venta y efecto en ISR (por validar con el contador).
- Comisiones de vendedores: reglas (porcentaje sobre precio o margen, fijo por unidad), momento de devengo (al facturar o al cobrar), liquidación y retención de ISR si el vendedor no es empleado.
- Garantía ofrecida al comprador (vínculo con la Épica 5).
Criterio de éxito: margen por unidad vendida, neto de comisión y garantía, visible al cerrar la venta.

## 9. Financiamiento propio y cartera

Objetivo: administrar los créditos otorgados a compradores.
Alcance:
- Condiciones del crédito: enganche, plazo, tasa, moneda, cuota.
- Tabla de amortización y separación de capital, interés y cargos.
- Facturación de los intereses (IVA sobre intereses, por validar).
- Cobro de cuotas, abonos extraordinarios y cancelación anticipada.
- Mora: intereses moratorios, antigüedad y provisión por incobrables.
- Garantía prendaria sobre el vehículo, y su liberación al cancelar.
- Recuperación de la unidad por impago y su reingreso al inventario.
Criterio de éxito: el saldo de capital e intereses por cliente cuadra con la contabilidad y la mora se ve al día.

Nota: si al arrancar ya hay créditos vigentes, esta épica sube a Must.

## 10. Migración y arranque

Objetivo: iniciar operación con datos confiables.
Alcance:
- Saldos iniciales conciliados en Q y USD.
- Carga de la flota con su costo, depreciación acumulada y valor en libros por VIN.
- Unidades en importación, en taller y en venta.
- Cartera financiada vigente con sus saldos.
- Repuestos, clientes, proveedores y contratos activos.
- Capacitación, operación en paralelo y soporte inicial.
Criterio de éxito: los saldos del sistema cuadran con los últimos estados financieros validados.

---

## Fuera del alcance (a confirmar)

- Multiempresa y consolidación (una sola sede y, en principio, una sola sociedad).
- Nómina (las comisiones se calculan aquí, pero se pagan por la nómina o se facturan).
- Presupuestos y proyecciones.
- Integraciones bancarias automáticas.
- Reservas en línea y portal de clientes de alquiler.
- Taller para clientes externos.

## Preguntas nuevas que deja este planteamiento

1. ¿Quién registra la operación (contratos, órdenes de taller, ventas) si los usuarios son solo el equipo contable? ¿Se necesitan usuarios operativos o se carga desde otro sistema?
2. ¿Hay una sociedad o dos (por ejemplo, una para importar y otra para alquilar)?
3. ¿Qué régimen de ISR aplican (utilidades o simplificado)?
4. ¿La depreciación fiscal (20 % anual para vehículos) difiere de la financiera?
5. ¿Qué regla define el fin de la vida útil en flota (años, kilometraje o decisión de gerencia)?
6. ¿Cómo se calculan las comisiones y cuándo se pagan? ¿Los vendedores son empleados?
7. Financiamiento: ¿plazo, tasa y moneda típicos? ¿Qué pasa con la unidad en caso de impago? ¿Hay créditos vigentes hoy?
8. ¿Se factura en USD a algunos clientes (por ejemplo, turistas o empresas)?
9. ¿La postventa tiene garantía con plazo definido? ¿Qué cubre?
10. ¿Cómo se prorratean hoy los gastos de importación compartidos entre varias unidades?

## Siguiente paso sugerido

Validar este orden con el cliente y pasar a historias de usuario las épicas 1 a 5, que forman la base contable y el costo de cada unidad. De ese costo dependen los reportes y la venta.
