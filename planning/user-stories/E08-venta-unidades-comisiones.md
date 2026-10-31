# Épica 8. Venta de unidades y comisiones

Prioridad de la épica: 8 · MoSCoW: **Should**
Objetivo: vender las unidades que salen de la flota y liquidar las comisiones.
Criterio de éxito de la épica: margen por unidad vendida, neto de comisión y garantía, visible al cerrar la venta.

No se reciben vehículos en parte de pago.

---

### HU-8.01 Consultar el inventario de unidades en venta

**Como** auxiliar contable, **quiero** ver las unidades disponibles para la venta con su costo en libros, **para** ofrecerlas y fijar precios.

Prioridad: Must · Depende de: HU-3.15

**Criterios de aceptación**
1. El listado muestra VIN, datos del vehículo, kilometraje, fecha de baja de la flota, valor en libros, precio de lista y estado (disponible, reservada, vendida).
2. Solo aparecen unidades que llegaron desde la baja de la flota (HU-3.15) o desde una recuperación (HU-9.12).
3. El valor total del listado cuadra con la cuenta "inventario de unidades para la venta".

---

### HU-8.02 Fijar el precio de lista y el precio mínimo

**Como** gerente financiero, **quiero** fijar el precio de lista y el precio mínimo de cada unidad, **para** controlar los descuentos de los vendedores.

Prioridad: Must · Depende de: HU-8.01

**Criterios de aceptación**
1. Cada unidad tiene precio de lista y precio mínimo, en Q o USD.
2. El sistema muestra el margen estimado de cada precio contra el valor en libros.
3. Una venta por debajo del precio mínimo requiere aprobación del gerente financiero.
4. Los cambios de precio quedan en bitácora.

---

### HU-8.03 Reservar una unidad con anticipo

**Como** auxiliar contable, **quiero** reservar una unidad para un cliente que entrega un anticipo, **para** retirarla de la oferta mientras se concreta la venta.

Prioridad: Should · Depende de: HU-8.01, HU-6.09

**Criterios de aceptación**
1. La reserva tiene cliente, unidad, vendedor, monto del anticipo y fecha de vencimiento.
2. El anticipo se registra como pasivo ligado al VIN y la unidad pasa a "reservada".
3. Al concretar la venta, el anticipo se aplica a la factura o al enganche.
4. Si la reserva vence o se cancela, la unidad vuelve a "disponible" y el anticipo se devuelve o se retiene según la política configurada, con aprobación del gerente financiero.

---

### HU-8.04 Registrar una venta de contado

**Como** auxiliar contable, **quiero** registrar la venta de contado de una unidad, **para** facturarla y reconocer su resultado.

Prioridad: Must · Depende de: HU-8.02, HU-6.02

**Criterios de aceptación**
1. La venta tiene cliente, unidad, vendedor, precio, descuento, anticipos aplicados y condiciones de garantía.
2. Al confirmar, se emite la factura FEL y se genera la partida de ingreso por venta y de costo de venta al valor en libros, ligadas al VIN en la línea de venta.
3. La unidad pasa a estado "vendida" y sale del inventario de venta.
4. El sistema calcula la comisión del vendedor (HU-8.09) y la provisión de garantía (HU-8.11).
5. Una venta no se puede confirmar si la unidad está reservada para otro cliente.

---

### HU-8.05 Registrar una venta financiada

**Como** auxiliar contable, **quiero** registrar una venta con financiamiento propio, **para** facturarla y crear el crédito del comprador.

Prioridad: Must · Depende de: HU-8.04, HU-9.02

**Criterios de aceptación**
1. Además de los datos de la venta de contado, registro el enganche y el plan de crédito propuesto.
2. La venta no se confirma hasta que el gerente financiero apruebe el crédito.
3. Al confirmar, la factura se emite por el precio total; el enganche se registra como cobro y el saldo pasa a la cartera de financiamiento (Épica 9).
4. El resultado de la venta se registra en la línea de venta y los intereses futuros en la línea de financiamiento.

---

### HU-8.06 Controlar el traspaso de propiedad

**Como** auxiliar contable, **quiero** registrar el trámite de traspaso de cada unidad vendida y su costo, **para** saber quién lo paga y cuándo se completa.

Prioridad: Should · Depende de: HU-8.04

**Criterios de aceptación**
1. El traspaso tiene estado (pendiente, en trámite, completado), fecha y costo.
2. Puedo indicar si el costo lo asume la empresa (gasto de la venta, ligado al VIN) o el comprador (cargo en la factura o cobro aparte).
3. En una venta financiada, el sistema registra si el traspaso queda condicionado a la cancelación del crédito.
4. Un listado muestra los traspasos pendientes con su antigüedad.

---

### HU-8.07 Configurar el tratamiento fiscal de la venta de unidades

**Como** contador, **quiero** configurar cómo se gravan las ventas de unidades que fueron de la flota, **para** calcular bien el IVA y el efecto en ISR.

Prioridad: Must · Depende de: HU-1.01

**Criterios de aceptación**
1. Puedo definir si la venta lleva IVA y a qué tasa, con vigencia.
2. Al vender, el sistema calcula la diferencia entre el valor en libros financiero y el fiscal, para la conciliación del ISR.
3. Puedo configurar la cuenta y el tratamiento de la ganancia o pérdida en la venta de activos.

**Pendiente:** tratamiento fiscal de la venta de un activo que fue de la flota (IVA y efecto en ISR), por validar con el contador.

---

### HU-8.08 Registrar vendedores y reglas de comisión

**Como** gerente financiero, **quiero** registrar a los vendedores y sus reglas de comisión, **para** calcular las comisiones sin hojas de cálculo.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. Cada vendedor tiene nombre, identificación, tipo (empleado o independiente) y, si es independiente, su NIT y régimen.
2. Una regla de comisión puede ser porcentaje sobre el precio, porcentaje sobre el margen o monto fijo por unidad, con vigencia.
3. Puedo definir el momento de devengo: al facturar o al cobrar (en ventas financiadas, al cobrar el enganche o en proporción a lo cobrado).
4. Puedo asignar una regla por defecto y excepciones por vendedor.

**Pendiente:** cómo se calculan las comisiones, cuándo se pagan y si los vendedores son empleados (pregunta 6 de las épicas).

---

### HU-8.09 Calcular la comisión de cada venta

**Como** contador, **quiero** que el sistema calcule la comisión de cada venta según la regla vigente, **para** registrarla como costo de la venta en el momento correcto.

Prioridad: Must · Depende de: HU-8.08, HU-8.04

**Criterios de aceptación**
1. Al confirmar la venta, el sistema calcula la comisión con la regla vigente en la fecha de la venta.
2. Si el devengo es al facturar, registra el gasto y el pasivo al confirmar la venta; si es al cobrar, los registra al aplicar cada cobro.
3. La comisión queda ligada a la venta, al vendedor y al VIN.
4. Una nota de crédito o anulación de la venta revierte la comisión no pagada y deja pendiente de descuento la ya pagada.

---

### HU-8.10 Liquidar comisiones por período

**Como** contador, **quiero** liquidar las comisiones devengadas de un período, **para** pagarlas por nómina o contra factura del vendedor.

Prioridad: Must · Depende de: HU-8.09

**Criterios de aceptación**
1. La liquidación agrupa por vendedor las comisiones devengadas y no pagadas hasta una fecha.
2. Para vendedores empleados, el sistema genera un reporte para la nómina (que está fuera del alcance) y registra el pasivo.
3. Para vendedores independientes, registro su factura, el sistema calcula la retención de ISR que corresponda y genera la cuenta por pagar.
4. La liquidación requiere aprobación del gerente financiero.

---

### HU-8.11 Registrar la garantía ofrecida al comprador

**Como** contador, **quiero** registrar las condiciones de garantía de cada venta y provisionar su costo, **para** reflejar la obligación con el comprador.

Prioridad: Should · Depende de: HU-8.04

**Criterios de aceptación**
1. La garantía tiene plazo en meses, kilometraje máximo y coberturas, a partir de una plantilla configurable.
2. Al vender, puedo registrar una provisión de garantía como costo de la venta, según un porcentaje o monto configurado.
3. Las órdenes de postventa en garantía (Épica 5) consumen la provisión de su venta.
4. Al vencer la garantía, el saldo de provisión no usado se revierte.

**Pendiente:** si se provisiona la garantía o se registra solo el costo real (pregunta 9 de las épicas).

---

### HU-8.12 Ver el margen de la unidad vendida

**Como** gerente financiero, **quiero** ver el margen de cada venta neto de comisión y garantía al cerrarla, **para** evaluar el resultado de la salida de cada unidad.

Prioridad: Must · Depende de: HU-8.04, HU-8.09

**Criterios de aceptación**
1. El margen muestra precio de venta, menos valor en libros, comisión, costo de traspaso asumido y garantía (provisionada y real).
2. El margen se ve en la ficha de la venta al confirmarla y se actualiza con los costos de garantía posteriores.
3. Puedo listar las ventas de un período con su margen.
