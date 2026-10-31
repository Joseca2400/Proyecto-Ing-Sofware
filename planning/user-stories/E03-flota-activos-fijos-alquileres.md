# Épica 3. Flota, activos fijos y alquileres

Prioridad de la épica: 3 · MoSCoW: **Must**
Objetivo: administrar la flota y facturar los contratos, que son la principal fuente de ingreso.
Criterio de éxito de la épica: ingreso, costo y rentabilidad por unidad y por contrato calculables en cualquier momento.

---

### HU-3.01 Dar de alta una unidad como activo fijo de la flota

**Como** contador, **quiero** dar de alta como activo fijo una unidad que terminó su importación y reacondicionamiento, **para** iniciar su depreciación y ponerla disponible para alquiler.

Prioridad: Must · Depende de: HU-4.08, HU-5.07

**Criterios de aceptación**
1. Solo se puede dar de alta una unidad en estado "lista" y sin órdenes de reacondicionamiento abiertas.
2. El costo de alta es la suma de compra, gastos de importación y reacondicionamiento de su hoja de costo; el IVA acreditable no forma parte del costo.
3. Al confirmar, el sistema genera la partida que traslada el costo de "unidades en proceso" a "activo fijo – flota", ligada al VIN, y cambia el estado a "en flota".
4. La unidad queda disponible para contratos a partir de la fecha de alta.
5. La alta requiere aprobación del contador si la registró el auxiliar.

---

### HU-3.02 Definir los parámetros de depreciación de cada unidad

**Como** contador, **quiero** definir vida útil, valor residual y método de depreciación por unidad, **para que** la depreciación refleje la política de la empresa y la norma fiscal.

Prioridad: Must · Depende de: HU-3.01

**Criterios de aceptación**
1. Cada unidad tiene parámetros financieros (vida útil en meses, valor residual, método de línea recta) y fiscales (porcentaje anual, por defecto 20 % para vehículos).
2. Puedo definir valores por defecto por tipo de vehículo que se proponen al dar de alta la unidad.
3. Un cambio de vida útil o valor residual aplica de forma prospectiva y queda en bitácora.
4. La ficha muestra depreciación acumulada y valor en libros, financiero y fiscal, a cualquier fecha.

---

### HU-3.03 Capitalizar una mejora a una unidad de la flota

**Como** contador, **quiero** sumar al costo del activo las mejoras que se capitalizan, **para** depreciarlas en la vida restante de la unidad.

Prioridad: Should · Depende de: HU-3.01, HU-5.07

**Criterios de aceptación**
1. Una orden de taller cerrada con tipo "mejora capitalizable" aumenta el costo del activo de su VIN.
2. La depreciación se recalcula a partir del mes siguiente sobre el nuevo valor en libros y la vida útil restante.
3. La ficha del activo muestra cada mejora con su fecha, monto y orden de origen.

---

### HU-3.04 Controlar seguros, marchamo y documentos de cada unidad

**Como** auxiliar contable, **quiero** registrar el seguro, el marchamo y la tarjeta de circulación de cada unidad, **para** controlar su costo y sus vencimientos.

Prioridad: Must · Depende de: HU-1.05

**Criterios de aceptación**
1. Por unidad registro póliza de seguro (aseguradora, número, vigencia, prima, deducible), marchamo (año, monto, fecha de pago) y tarjeta de circulación.
2. Una prima pagada por adelantado se registra como gasto anticipado y se amortiza de forma mensual a la unidad.
3. El sistema muestra una alerta de vencimientos próximos, con un plazo configurable.
4. Una unidad sin seguro vigente aparece marcada al crear un contrato.

---

### HU-3.05 Mantener el tarifario de alquiler

**Como** gerente financiero, **quiero** definir tarifas de alquiler por tipo de vehículo, **para** cotizar y facturar los contratos de forma consistente.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. Cada tarifa tiene modalidad (diaria, semanal, mensual o por kilometraje), moneda (GTQ o USD), monto, kilometraje incluido, costo por kilómetro adicional y vigencia.
2. Puedo definir tarifas por tipo de vehículo y, como excepción, por unidad.
3. Un descuento sobre la tarifa por encima del porcentaje configurado requiere aprobación del gerente financiero.
4. Cambiar una tarifa no afecta los contratos ya firmados.

---

### HU-3.06 Registrar un contrato de alquiler

**Como** auxiliar contable, **quiero** registrar un contrato de alquiler con su cliente, unidad, tarifa y fechas, **para** controlar la operación y su facturación.

Prioridad: Must · Depende de: HU-3.05, HU-6.01

**Criterios de aceptación**
1. El contrato tiene cliente, unidad, fecha y hora de salida, fecha prevista de devolución, tarifa, moneda, kilometraje y nivel de combustible de salida, y depósito en garantía.
2. Dado que la unidad no está disponible en esas fechas (alquilada, en taller o fuera de flota), cuando intento registrar el contrato, entonces el sistema lo impide.
3. Al iniciar el contrato, la unidad pasa a estado "alquilada" para el cálculo de ocupación.
4. El contrato tiene un número correlativo y se puede imprimir.
5. El sistema calcula el monto estimado del contrato según tarifa y días.

**Pendiente:** quién registra los contratos si los usuarios son solo el equipo contable (pregunta 1 de las épicas).

---

### HU-3.07 Recibir, aplicar y devolver depósitos en garantía

**Como** auxiliar contable, **quiero** registrar el depósito en garantía de cada contrato, **para** aplicarlo a cargos o devolverlo al cliente al cerrar.

Prioridad: Must · Depende de: HU-3.06

**Criterios de aceptación**
1. El depósito se registra como pasivo (no como ingreso), en la moneda en que se recibió y ligado al contrato.
2. Si el depósito se recibe como autorización de tarjeta sin cobro, se registra solo como referencia, sin partida.
3. Al cerrar el contrato puedo aplicar el depósito, total o parcialmente, a los cargos pendientes y devolver el resto.
4. La devolución genera el pago al cliente y su partida; un depósito no se puede devolver dos veces.
5. Puedo consultar los depósitos vigentes y su saldo total, que cuadra con la cuenta contable.

---

### HU-3.08 Cerrar un contrato al devolver la unidad

**Como** auxiliar contable, **quiero** registrar la devolución de la unidad, **para** calcular el cobro final del contrato.

Prioridad: Must · Depende de: HU-3.06

**Criterios de aceptación**
1. Registro fecha y hora de devolución, kilometraje y combustible de entrada, y observaciones de daños.
2. El sistema calcula días efectivos, kilómetros recorridos, kilómetros excedentes y combustible faltante según la tarifa.
3. Desde el cierre puedo agregar cargos adicionales (HU-3.09) y aplicar el depósito (HU-3.07).
4. El kilometraje de entrada actualiza el kilometraje de la unidad.
5. Al cerrar, la unidad vuelve a estado "disponible", o "en taller" si se abre una orden por daños.

---

### HU-3.09 Registrar cargos adicionales del contrato

**Como** auxiliar contable, **quiero** registrar cargos adicionales al contrato, **para** cobrar combustible, multas, daños, extensiones y deducibles.

Prioridad: Must · Depende de: HU-3.06

**Criterios de aceptación**
1. Existe un catálogo de cargos (combustible, multa, daño, extensión, deducible, otros) con su cuenta de ingreso y su tratamiento de IVA.
2. Una multa de tránsito que la empresa paga y recupera del cliente se puede registrar como reembolso en lugar de ingreso, según se configure.
3. Un cargo por daños puede ligarse a la orden de taller que repara la unidad.
4. Los cargos se incluyen en la siguiente factura del contrato o en la factura de cierre.

**Pendiente:** definición de cobros adicionales y su tratamiento fiscal (pendientes de la descripción de la empresa).

---

### HU-3.10 Facturar contratos de forma recurrente

**Como** auxiliar contable, **quiero** que los contratos de largo plazo generen su facturación periódica, **para no** olvidar cobros y facturar a tiempo.

Prioridad: Must · Depende de: HU-3.06, HU-6.02

**Criterios de aceptación**
1. En cada contrato puedo indicar la frecuencia de facturación (al cierre, semanal, mensual) y el día de corte.
2. En cada fecha de corte el sistema prepara las facturas en borrador con el período, la tarifa y los cargos pendientes.
3. Reviso el lote y emito las facturas FEL en conjunto o de forma individual.
4. El ingreso se registra en la línea de alquiler, ligado al VIN y al contrato.
5. El sistema evita facturar dos veces el mismo período del mismo contrato.

---

### HU-3.11 Extender un contrato vigente

**Como** auxiliar contable, **quiero** extender la fecha de devolución de un contrato, **para** reflejar acuerdos con el cliente sin abrir un contrato nuevo.

Prioridad: Should · Depende de: HU-3.06

**Criterios de aceptación**
1. Dado que la unidad tiene otra reserva o contrato en las nuevas fechas, cuando intento extender, entonces el sistema me avisa del conflicto.
2. La extensión guarda la fecha anterior, la nueva fecha y la tarifa aplicada.
3. El monto estimado y la facturación recurrente se ajustan a la nueva fecha.

---

### HU-3.12 Consultar la ocupación de la flota

**Como** gerente financiero, **quiero** ver cuántos días estuvo cada unidad alquilada, disponible o en taller, **para** medir el uso de la flota.

Prioridad: Must · Depende de: HU-3.06, HU-5.01

**Criterios de aceptación**
1. El sistema calcula, por unidad y período, los días en cada estado a partir de contratos y órdenes de taller.
2. La ocupación es días alquilada entre días en flota del período.
3. Puedo ver la ocupación por unidad, por tipo de vehículo y total de la flota.
4. Puedo ver un calendario de la flota con el estado de cada unidad por día.

---

### HU-3.13 Consultar la rentabilidad por contrato y por unidad

**Como** gerente financiero, **quiero** ver el ingreso, el costo y el resultado de cada contrato y de cada unidad, **para** decidir tarifas y renovación de la flota.

Prioridad: Must · Depende de: HU-3.10, HU-2.07

**Criterios de aceptación**
1. Por contrato se muestran ingresos facturados, cargos adicionales y costos directos (taller por daños, combustible repuesto).
2. Por unidad se muestran, en el período elegido, ingresos de alquiler, depreciación, mantenimiento, seguro, marchamo y resultado.
3. Las cifras salen del mayor contable filtrado por VIN, por lo que cuadran con la contabilidad.
4. Puedo exportar la consulta a Excel.

---

### HU-3.14 Alertar sobre el fin de la vida útil en flota

**Como** gerente financiero, **quiero** que el sistema me avise cuándo una unidad alcanza el límite de vida en flota, **para** decidir su baja y venta a tiempo.

Prioridad: Should · Depende de: HU-3.08

**Criterios de aceptación**
1. Puedo configurar la regla de fin de vida por kilometraje, antigüedad en meses, o ambas.
2. El sistema lista las unidades que alcanzaron o están por alcanzar el límite, con su valor en libros.
3. La decisión final de baja la toma la gerencia; la alerta no da de baja la unidad.

**Pendiente:** qué regla define el fin de la vida útil en flota (pregunta 5 de las épicas).

---

### HU-3.15 Dar de baja una unidad de la flota y pasarla a venta

**Como** contador, **quiero** dar de baja una unidad de la flota y trasladarla al inventario de venta a su valor en libros, **para** iniciar su venta.

Prioridad: Must · Depende de: HU-3.02

**Criterios de aceptación**
1. Solo se puede dar de baja una unidad sin contrato vigente.
2. La baja calcula la depreciación hasta la fecha de baja y genera la partida que traslada el valor en libros de "activo fijo – flota" a "inventario de unidades para la venta", ligada al VIN.
3. La unidad cambia a estado "en venta" y deja de depreciarse.
4. La baja requiere aprobación del gerente financiero.
5. El valor fiscal pendiente de depreciar queda registrado para la conciliación del ISR en la venta.
