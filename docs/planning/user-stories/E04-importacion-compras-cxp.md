# Épica 4. Importación, compras y cuentas por pagar

Prioridad de la épica: 4 · MoSCoW: **Must**
Objetivo: determinar el costo real de cada unidad importada y controlar lo que se debe a proveedores.
Criterio de éxito de la épica: cada unidad tiene un costo desglosado (compra, importación y reparación) al darse de alta en la flota, y los saldos por pagar cuadran en ambas monedas.

---

### HU-4.01 Registrar proveedores locales y del exterior

**Como** auxiliar contable, **quiero** registrar proveedores locales y del exterior, **para** asociarles compras, pagos y retenciones.

Prioridad: Must · Depende de: HU-1.01

**Criterios de aceptación**
1. Cada proveedor tiene tipo (local o del exterior), nombre, identificación (NIT para locales; identificación fiscal y país para extranjeros), moneda habitual, condiciones de pago y datos bancarios.
2. Para proveedores locales registro su régimen (general, pequeño contribuyente) y si se le aplica retención de IVA o ISR.
3. Puedo clasificar al proveedor por rubro: subasta, dealer, naviera, agente aduanal, repuestos, seguros, servicios y otros.
4. El NIT de un proveedor local se valida con su dígito verificador y no puede repetirse.

---

### HU-4.02 Registrar la compra de una unidad en EE. UU.

**Como** auxiliar contable, **quiero** registrar la compra de un vehículo en subasta o dealer de EE. UU. con su VIN, **para** iniciar su hoja de costo y la cuenta por pagar.

Prioridad: Must · Depende de: HU-4.01, HU-1.05, HU-1.07

**Criterios de aceptación**
1. La compra tiene proveedor, fecha, VIN, datos del vehículo, precio en USD, cargos de la subasta (comisión, documentación, arrastre interno) y número de lote o factura.
2. Al confirmar, el sistema crea la unidad en estado "en tránsito", si no existía, y abre su hoja de costo.
3. La compra genera una cuenta por pagar en USD al proveedor y carga el costo a "unidades en proceso", ligado al VIN.
4. Puedo adjuntar la factura, el título (title) y el bill of sale.

**Pendiente:** tratamiento de compras de vehículos usados a particulares en Guatemala (factura especial, retenciones y traspaso).

---

### HU-4.03 Agrupar unidades en un expediente de importación

**Como** auxiliar contable, **quiero** agrupar en un expediente las unidades que viajan en el mismo embarque o contenedor, **para** asignarles los gastos compartidos.

Prioridad: Must · Depende de: HU-4.02

**Criterios de aceptación**
1. El expediente tiene número, naviera, número de BL o contenedor, puerto de origen y destino, y fechas estimadas y reales de salida y llegada.
2. Puedo agregar o quitar unidades del expediente mientras no tenga gastos prorrateados contabilizados.
3. Desde el expediente veo todas sus unidades, gastos y estado.

---

### HU-4.04 Registrar los gastos de importación

**Como** auxiliar contable, **quiero** registrar los gastos de importación ligados a una unidad o a un expediente, **para** sumarlos al costo de cada vehículo.

Prioridad: Must · Depende de: HU-4.03

**Criterios de aceptación**
1. Existe un catálogo de conceptos: flete, seguro de transporte, agente aduanal, almacenaje, DAI, IVA de importación, IPRIMA, placas y otros, cada uno con su cuenta y su tratamiento.
2. Un gasto se puede ligar a una unidad (VIN) o al expediente para prorratearlo después.
3. El IVA de importación se registra como crédito fiscal y no se suma al costo de la unidad.
4. Cada gasto puede estar en Q o USD y genera la cuenta por pagar al proveedor que corresponda (naviera, agente aduanal, SAT).
5. El IVA de los servicios locales (agente aduanal, almacenaje) se registra como crédito fiscal cuando el documento FEL lo permita.

---

### HU-4.05 Prorratear los gastos compartidos

**Como** contador, **quiero** prorratear los gastos de un expediente entre sus unidades, **para que** cada VIN cargue la parte que le corresponde.

Prioridad: Must · Depende de: HU-4.04

**Criterios de aceptación**
1. Puedo elegir el método de prorrateo por gasto: partes iguales, en proporción al precio de compra (valor FOB), en proporción al valor CIF o manual.
2. Antes de confirmar, el sistema muestra cuánto recibe cada unidad y verifica que la suma sea igual al gasto.
3. Al confirmar, genera la partida que distribuye el gasto en "unidades en proceso" por VIN.
4. Si un gasto se modifica después del prorrateo, el sistema exige revertir y volver a prorratear.

**Pendiente:** cómo se prorratean hoy los gastos de importación compartidos (pregunta 10 de las épicas).

---

### HU-4.06 Registrar la DUCA y vincularla a las unidades

**Como** auxiliar contable, **quiero** registrar la DUCA de cada importación, **para** respaldar los impuestos pagados y ligarlos a cada unidad.

Prioridad: Must · Depende de: HU-4.03

**Criterios de aceptación**
1. Registro número de DUCA, fecha, aduana, valor en aduana, DAI, IVA y otros cargos, y adjunto el documento.
2. Una DUCA se liga a una o más unidades por VIN.
3. El IVA de la DUCA alimenta el libro de compras como importación y el crédito fiscal del período.
4. El sistema avisa si los montos de DAI e IVA de la DUCA no coinciden con los gastos registrados para esas unidades.

---

### HU-4.07 Seguir el estado de la unidad durante la importación

**Como** gerente financiero, **quiero** ver en qué etapa está cada unidad (en tránsito, en aduana, en taller o lista), **para** planificar su entrada a la flota.

Prioridad: Must · Depende de: HU-1.05, HU-4.02

**Criterios de aceptación**
1. Puedo cambiar el estado de una unidad en el orden: en tránsito → en aduana → en taller → lista.
2. El paso a "en taller" se hace al abrir la orden de reacondicionamiento (HU-5.01).
3. El paso a "lista" exige que la DUCA esté registrada y que no haya órdenes de reacondicionamiento abiertas.
4. Puedo ver un listado de unidades por estado con días en cada etapa y costo acumulado.

---

### HU-4.08 Consultar la hoja de costo de una unidad

**Como** contador, **quiero** ver el costo desglosado de cada unidad, **para** validar el valor de alta en la flota.

Prioridad: Must · Depende de: HU-4.02, HU-4.05

**Criterios de aceptación**
1. La hoja muestra el costo agrupado en compra, importación (por concepto) y reacondicionamiento (mano de obra, repuestos, subcontratos).
2. Los montos en USD muestran el valor original, el tipo de cambio y el equivalente en quetzales.
3. El total de la hoja cuadra con el saldo de "unidades en proceso" para ese VIN en el mayor.
4. La hoja se puede exportar a PDF y Excel.

---

### HU-4.09 Registrar facturas de compras y gastos locales

**Como** auxiliar contable, **quiero** registrar las facturas FEL recibidas de proveedores, **para** contabilizar compras, gastos y crédito fiscal.

Prioridad: Must · Depende de: HU-4.01

**Criterios de aceptación**
1. Registro serie, número y autorización del DTE, fecha, proveedor, líneas con cuenta, línea de negocio y VIN cuando aplique, base e IVA.
2. El sistema impide registrar dos veces el mismo DTE del mismo proveedor.
3. Puedo importar los DTE desde el XML o el archivo que entrega la SAT o el certificador, en lugar de capturarlos.
4. Una factura de pequeño contribuyente no genera crédito fiscal de IVA.
5. La factura genera la cuenta por pagar y alimenta el libro de compras.

---

### HU-4.10 Registrar compras a particulares con factura especial

**Como** contador, **quiero** emitir la factura especial cuando le compro a una persona que no factura, **para** respaldar el gasto y retener los impuestos que corresponden.

Prioridad: Could · Depende de: HU-4.09, HU-6.02

**Criterios de aceptación**
1. La factura especial se emite como DTE FEL con los datos del vendedor (CUI o NIT).
2. El sistema calcula las retenciones de IVA e ISR que corresponden y genera la cuenta por pagar neta.
3. La retención queda como pasivo a pagar a la SAT.

**Pendiente:** si existen compras a particulares y su tratamiento (pendientes de la descripción de la empresa).

---

### HU-4.11 Retener IVA e ISR a proveedores locales

**Como** contador, **quiero** que el sistema calcule las retenciones de IVA e ISR al pagar a proveedores locales, **para** cumplir como agente de retención.

Prioridad: Must · Depende de: HU-1.01, HU-4.09

**Criterios de aceptación**
1. Las tasas, mínimos y reglas de retención son configurables por tipo de retención, con vigencia.
2. Al registrar o pagar una factura, el sistema propone la retención según el perfil del proveedor y de la empresa.
3. La retención se registra como pasivo con la SAT y reduce el pago al proveedor.
4. Puedo registrar el número de constancia de retención emitida y adjuntarla.
5. Un reporte mensual lista las retenciones por tipo para su declaración y pago.

**Pendiente:** si la empresa es agente de retención de IVA o de ISR.

---

### HU-4.12 Retener ISR en pagos al exterior

**Como** contador, **quiero** calcular la retención de ISR sobre pagos a proveedores no domiciliados, **para** cumplir con la ley sobre rentas de no residentes.

Prioridad: Should · Depende de: HU-4.11

**Criterios de aceptación**
1. Puedo marcar qué conceptos pagados al exterior están sujetos a retención y a qué tasa.
2. El sistema calcula la retención en quetzales al tipo de cambio de la fecha de pago o acreditación.
3. La retención aparece en el reporte mensual de retenciones a pagar.

**Pendiente:** si los pagos a subastas y navieras en EE. UU. están sujetos a retención; validar con el contador.

---

### HU-4.13 Programar y aprobar pagos a proveedores

**Como** gerente financiero, **quiero** revisar y aprobar una programación de pagos, **para** controlar la salida de dinero.

Prioridad: Must · Depende de: HU-4.09, HU-1.10

**Criterios de aceptación**
1. El auxiliar propone pagos seleccionando documentos vencidos o por vencer, por moneda y cuenta bancaria.
2. La propuesta muestra totales en Q y USD y el saldo disponible por cuenta bancaria.
3. El gerente financiero aprueba, rechaza o modifica cada pago; solo los aprobados se pueden ejecutar.
4. Quien propone el pago no puede aprobarlo.

---

### HU-4.14 Registrar el pago a un proveedor

**Como** auxiliar contable, **quiero** registrar el pago aprobado por cheque o transferencia, **para** cancelar la cuenta por pagar y registrar la salida del banco.

Prioridad: Must · Depende de: HU-4.13, HU-2.09

**Criterios de aceptación**
1. El pago indica cuenta bancaria, forma de pago, número de cheque o referencia, fecha y documentos que cancela, total o parcial.
2. Un pago en una moneda puede cancelar documentos en otra; el sistema aplica el tipo de cambio y calcula el diferencial realizado.
3. Puedo imprimir el cheque y el comprobante de pago.
4. Anular un pago reabre los documentos y genera la reversión de su partida.

---

### HU-4.15 Registrar notas de crédito y devoluciones de proveedores

**Como** auxiliar contable, **quiero** registrar notas de crédito y devoluciones de proveedores, **para** reducir el saldo por pagar y el costo correspondiente.

Prioridad: Should · Depende de: HU-4.09

**Criterios de aceptación**
1. La nota de crédito se liga a la factura original y reduce su saldo, su IVA y, si aplica, el costo de la unidad o del repuesto.
2. Una devolución de repuestos reduce la existencia en inventario.
3. La nota aparece en el libro de compras del período en que se recibe.

---

### HU-4.16 Consultar antigüedad de saldos y estado de cuenta de proveedores

**Como** contador, **quiero** ver los saldos por pagar por antigüedad y por proveedor, **para** planificar pagos y conciliar con el mayor.

Prioridad: Must · Depende de: HU-4.09

**Criterios de aceptación**
1. La antigüedad muestra saldos por rango de días (por vencer, 1–30, 31–60, 61–90, más de 90), en la moneda original y en quetzales.
2. El estado de cuenta de un proveedor muestra documentos, pagos, notas y saldo a una fecha.
3. El total del auxiliar de proveedores cuadra con la cuenta de mayor por moneda; si no cuadra, el sistema muestra la diferencia.
4. Ambos reportes se exportan a PDF y Excel.
