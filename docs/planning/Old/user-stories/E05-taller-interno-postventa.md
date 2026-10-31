# Épica 5. Taller interno y postventa

Prioridad de la épica: 5 · MoSCoW: **Must**
Objetivo: costear cada trabajo y cargarlo a la unidad correcta.
Criterio de éxito de la épica: ninguna orden queda sin destino contable (capitalizar, gasto de flota, garantía o factura).

El taller no atiende clientes externos. Tipos de trabajo y destino contable:

| Tipo de orden | Unidad en estado | Destino contable al cerrar |
|---|---|---|
| Reacondicionamiento | en taller (importación) | Se capitaliza al costo de la unidad |
| Mantenimiento o reparación de flota | en flota | Gasto de la unidad, línea alquiler |
| Mejora capitalizable | en flota | Aumenta el costo del activo |
| Postventa en garantía | vendida | Costo de garantía de la venta |
| Postventa facturable | vendida | Se factura al comprador (FEL) |

---

### HU-5.01 Abrir una orden de trabajo ligada a un VIN

**Como** auxiliar contable, **quiero** abrir una orden de trabajo para una unidad indicando su tipo, **para que** todo su costo quede ligado al VIN y a un destino contable.

Prioridad: Must · Depende de: HU-1.05

**Criterios de aceptación**
1. La orden tiene número correlativo, VIN, tipo de trabajo, fecha de apertura, kilometraje, descripción del trabajo y responsable.
2. El tipo de trabajo es obligatorio y debe ser coherente con el estado de la unidad, según la tabla de esta épica; el sistema impide combinaciones inválidas.
3. Abrir una orden de reacondicionamiento pasa la unidad a "en taller"; abrir una de mantenimiento la marca "en taller" para el cálculo de ocupación.
4. Una orden de postventa queda ligada al cliente comprador y a la venta original.
5. La orden puede ligarse a un contrato de alquiler cuando se origina por daños.

**Pendiente:** quién registra las órdenes de taller (pregunta 1 de las épicas).

---

### HU-5.02 Configurar las tarifas de mano de obra

**Como** contador, **quiero** definir la tarifa horaria interna de costo y la tarifa de venta para postventa, **para** costear y cobrar la mano de obra de forma uniforme.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. Puedo definir una tarifa horaria de costo general y, de forma opcional, por mecánico o por especialidad, con vigencia.
2. Puedo definir una tarifa horaria de venta para los trabajos de postventa facturables.
3. Un cambio de tarifa aplica solo a las horas registradas después de la fecha de vigencia.

**Pendiente:** cómo se determina la tarifa horaria interna (costo de planilla del taller entre horas disponibles u otro criterio).

---

### HU-5.03 Registrar mano de obra en la orden

**Como** auxiliar contable, **quiero** registrar las horas trabajadas en cada orden, **para** cargar la mano de obra a la unidad.

Prioridad: Must · Depende de: HU-5.01, HU-5.02

**Criterios de aceptación**
1. Registro mecánico, fecha, horas y descripción de la tarea.
2. El sistema calcula el costo con la tarifa vigente.
3. El costo de mano de obra absorbido por las órdenes se acredita a una cuenta de "mano de obra aplicada" que se compara al cierre con el costo real del taller.
4. No se pueden registrar horas en una orden cerrada.

---

### HU-5.04 Mantener el catálogo e inventario de repuestos

**Como** auxiliar contable, **quiero** llevar el catálogo y las existencias de repuestos, **para** conocer su costo y disponibilidad.

Prioridad: Must · Depende de: HU-4.09

**Criterios de aceptación**
1. Cada repuesto tiene código, descripción, unidad de medida, ubicación, existencia mínima y cuenta de inventario.
2. Las compras de repuestos registradas en cuentas por pagar aumentan la existencia y recalculan el costo promedio ponderado.
3. Puedo consultar el kárdex de cada repuesto con entradas, salidas, existencia y costo.
4. El sistema avisa cuando la existencia de un repuesto baja del mínimo.
5. El valor total del inventario de repuestos cuadra con su cuenta de mayor.

**Pendiente:** confirmar el método de costeo (promedio ponderado propuesto).

---

### HU-5.05 Consumir repuestos en una orden

**Como** auxiliar contable, **quiero** registrar los repuestos usados en cada orden, **para** cargar su costo a la unidad y rebajar el inventario.

Prioridad: Must · Depende de: HU-5.01, HU-5.04

**Criterios de aceptación**
1. La salida de repuestos se valora al costo promedio del momento de la salida.
2. El sistema impide sacar más existencia de la disponible.
3. Puedo devolver al inventario repuestos no utilizados mientras la orden siga abierta.
4. Un repuesto comprado de forma directa para una orden se puede cargar a la orden sin pasar por inventario.

---

### HU-5.06 Registrar trabajos subcontratados

**Como** auxiliar contable, **quiero** ligar a la orden las facturas de talleres o servicios externos, **para** incluir su costo en la unidad.

Prioridad: Must · Depende de: HU-5.01, HU-4.09

**Criterios de aceptación**
1. Al registrar una factura de proveedor puedo asignar una o varias líneas a una orden de trabajo abierta.
2. El costo del subcontrato se muestra en la orden separado de mano de obra y repuestos.
3. El IVA del subcontrato se trata como crédito fiscal y no forma parte del costo.

---

### HU-5.07 Cerrar la orden y generar su destino contable

**Como** contador, **quiero** cerrar la orden y que el sistema contabilice su costo según el tipo de trabajo, **para que** ninguna orden quede sin destino contable.

Prioridad: Must · Depende de: HU-5.03, HU-5.05, HU-5.06

**Criterios de aceptación**
1. Al cerrar, el sistema genera la partida según el tipo: reacondicionamiento a "unidades en proceso", mantenimiento a gasto de la unidad, mejora al activo fijo, garantía al costo de garantía de la venta y postventa facturable a costo de ventas de taller.
2. Todas las líneas de la partida llevan el VIN y la línea de negocio correspondiente.
3. Una orden no se puede cerrar con cero costo sin una justificación.
4. Cambiar el tipo de una orden cerrada exige reabrirla con aprobación del contador.
5. El sistema muestra al cierre de mes las órdenes abiertas con su antigüedad y su costo acumulado.

---

### HU-5.08 Validar la garantía de una unidad vendida

**Como** auxiliar contable, **quiero** que el sistema indique si una unidad vendida está dentro de garantía, **para** clasificar correctamente la orden de postventa.

Prioridad: Should · Depende de: HU-8.11

**Criterios de aceptación**
1. Al abrir una orden de postventa, el sistema muestra la garantía de la venta (plazo, kilometraje y coberturas) y si está vigente.
2. Si la garantía no está vigente, el sistema propone el tipo "postventa facturable".
3. Una orden puede tener líneas en garantía y líneas facturables cuando la reparación cubre ambas.

**Pendiente:** si la postventa tiene garantía con plazo definido y qué cubre (pregunta 9 de las épicas).

---

### HU-5.09 Facturar la postventa no cubierta por garantía

**Como** auxiliar contable, **quiero** facturar al comprador los trabajos de postventa que no cubre la garantía, **para** registrar el ingreso del taller.

Prioridad: Must · Depende de: HU-5.07, HU-6.02

**Criterios de aceptación**
1. Desde la orden cerrada genero la factura FEL con mano de obra (a la tarifa de venta) y repuestos (a precio de venta).
2. La factura queda ligada a la orden, al VIN y al cliente, y se registra en la línea de taller.
3. Una orden facturable no se puede facturar dos veces.
4. El sistema muestra el margen de la orden: ingreso facturado menos costo.

---

### HU-5.10 Realizar el conteo físico de repuestos

**Como** contador, **quiero** registrar el conteo físico y ajustar las diferencias, **para que** el inventario del sistema coincida con la bodega.

Prioridad: Should · Depende de: HU-5.04

**Criterios de aceptación**
1. Puedo generar una hoja de conteo por ubicación o total, sin mostrar la existencia teórica.
2. Al ingresar las cantidades contadas, el sistema calcula las diferencias valorizadas.
3. Los ajustes requieren aprobación del gerente financiero si superan el monto configurado y generan su partida.
