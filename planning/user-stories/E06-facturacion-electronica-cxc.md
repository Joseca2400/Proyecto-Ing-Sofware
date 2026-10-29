# Épica 6. Facturación electrónica y cuentas por cobrar

Prioridad de la épica: 6 · MoSCoW: **Must**
Objetivo: emitir y registrar documentos FEL y controlar los saldos de clientes.
Criterio de éxito de la épica: cada documento fiscal queda ligado a su asiento, su cliente y su unidad.

---

### HU-6.01 Registrar clientes

**Como** auxiliar contable, **quiero** registrar a los clientes de alquiler, venta y taller, **para** facturarles y controlar sus saldos.

Prioridad: Must · Depende de: HU-1.01

**Criterios de aceptación**
1. Cada cliente tiene tipo (individual o empresa), nombre, NIT o CUI, o pasaporte y país para extranjeros, dirección, teléfono y correo.
2. El NIT se valida con su dígito verificador y, cuando el certificador lo permita, se consulta el nombre registrado en la SAT.
3. Puedo indicar si el cliente es agente de retención de IVA o ISR, para registrar las retenciones que nos haga.
4. Un cliente puede tener a la vez contratos de alquiler, compras de unidades y créditos; su estado de cuenta los integra.
5. El sistema evita clientes duplicados por NIT, CUI o pasaporte.

---

### HU-6.02 Emitir una factura FEL

**Como** auxiliar contable, **quiero** emitir facturas electrónicas a través del certificador, **para** documentar los ingresos según la normativa de la SAT.

Prioridad: Must · Depende de: HU-6.01, HU-2.03

**Criterios de aceptación**
1. La factura tiene cliente, fecha, moneda (GTQ o USD), líneas con descripción, cantidad, precio, IVA, línea de negocio y VIN cuando aplique, y referencia al contrato, venta u orden de origen.
2. El sistema envía el documento al certificador y guarda la serie, el número, el número de autorización (UUID) y el XML y PDF certificados.
3. Si el certificador rechaza el documento, el sistema muestra el motivo y la factura queda sin efecto contable.
4. Una factura en USD incluye el tipo de cambio exigido por la SAT y se contabiliza en quetzales.
5. Al certificarse, se genera la partida automática y la cuenta por cobrar, ligadas a la factura.
6. Si el total supera el umbral vigente de la SAT, el sistema no permite facturar a "Consumidor Final" sin NIT o CUI.

**Pendiente:** certificador FEL a utilizar y si se factura en USD a algunos clientes (pregunta 8 de las épicas).

---

### HU-6.03 Emitir notas de crédito

**Como** auxiliar contable, **quiero** emitir notas de crédito FEL ligadas a una factura, **para** registrar descuentos, devoluciones o correcciones.

Prioridad: Must · Depende de: HU-6.02

**Criterios de aceptación**
1. La nota de crédito referencia la factura original y no puede superar su saldo.
2. Las notas por encima del monto configurado requieren aprobación del gerente financiero.
3. La nota reduce la cuenta por cobrar, el ingreso y el IVA de la línea de negocio y el VIN de la factura original.

---

### HU-6.04 Emitir notas de débito

**Como** auxiliar contable, **quiero** emitir notas de débito FEL, **para** cobrar cargos posteriores relacionados con una factura.

Prioridad: Should · Depende de: HU-6.02

**Criterios de aceptación**
1. La nota de débito referencia la factura original e indica el motivo.
2. Aumenta la cuenta por cobrar y el ingreso en la línea de negocio y el VIN de la factura original.

---

### HU-6.05 Anular un documento FEL

**Como** contador, **quiero** anular un documento FEL emitido por error, **para** dejarlo sin efecto fiscal ni contable.

Prioridad: Must · Depende de: HU-6.02

**Criterios de aceptación**
1. La anulación exige motivo y se envía al certificador; solo se aplica cuando el certificador la confirma.
2. Un documento con cobros aplicados no se puede anular hasta revertir esos cobros.
3. La anulación revierte la partida en la fecha de anulación; si el mes del documento está cerrado, la reversión va al mes abierto.
4. El sistema respeta el plazo de anulación vigente de la SAT y avisa si ya venció, para emitir una nota de crédito en su lugar.

---

### HU-6.06 Registrar documentos FEL emitidos fuera del sistema

**Como** auxiliar contable, **quiero** registrar facturas emitidas desde el portal del certificador o de la SAT, **para** contabilizarlas cuando el sistema no estuvo disponible o en una contingencia.

Prioridad: Should · Depende de: HU-6.02

**Criterios de aceptación**
1. Puedo importar el XML del documento certificado o capturar sus datos y su número de autorización.
2. El sistema impide registrar dos veces el mismo número de autorización.
3. El documento registrado se completa con línea de negocio, VIN y referencia de origen antes de contabilizarse.

---

### HU-6.07 Registrar cobros y aplicarlos a facturas

**Como** auxiliar contable, **quiero** registrar los cobros recibidos y aplicarlos a una o varias facturas, **para** mantener al día los saldos de clientes.

Prioridad: Must · Depende de: HU-6.02, HU-2.09

**Criterios de aceptación**
1. El cobro tiene cliente, fecha, forma de pago (efectivo, cheque, transferencia, tarjeta), cuenta bancaria, moneda, monto y referencia.
2. Puedo aplicar el cobro a varias facturas, de forma total o parcial; el sistema propone las más antiguas primero.
3. Un cobro en una moneda puede aplicarse a facturas en otra; el sistema calcula el diferencial realizado.
4. La comisión de tarjeta se registra como gasto al recibir el cobro o al conciliar.
5. Puedo imprimir o enviar el recibo de caja.

---

### HU-6.08 Registrar retenciones que nos hacen los clientes

**Como** contador, **quiero** registrar las constancias de retención de IVA e ISR que nos entregan los clientes, **para** aplicarlas al saldo y acreditarlas en las declaraciones.

Prioridad: Must · Depende de: HU-6.07

**Criterios de aceptación**
1. Registro el tipo de retención, número de constancia, fecha, monto y factura a la que aplica.
2. La retención se aplica como parte del cobro de la factura y se registra en la cuenta de impuesto por acreditar.
3. Un reporte mensual muestra las retenciones recibidas para su aplicación en las declaraciones de IVA e ISR.

---

### HU-6.09 Registrar y aplicar anticipos de clientes

**Como** auxiliar contable, **quiero** registrar anticipos de clientes y aplicarlos después a sus facturas, **para** controlar los pagos recibidos antes de facturar.

Prioridad: Must · Depende de: HU-6.07

**Criterios de aceptación**
1. El anticipo se registra como pasivo, ligado al cliente y, cuando aplique, a un contrato, una reserva de unidad o un VIN.
2. Al emitir la factura, puedo aplicar el anticipo de forma total o parcial.
3. Puedo devolver un anticipo no aplicado; la devolución requiere aprobación del gerente financiero.
4. El saldo de anticipos por cliente cuadra con su cuenta de mayor.

**Pendiente:** confirmar con el contador si algún anticipo debe facturarse al recibirse.

---

### HU-6.10 Identificar depósitos no aplicados

**Como** auxiliar contable, **quiero** ver los depósitos en banco que no se han identificado como cobro de un cliente, **para** aplicarlos o investigarlos.

Prioridad: Should · Depende de: HU-2.10, HU-6.07

**Criterios de aceptación**
1. Durante la conciliación bancaria puedo marcar un depósito como "no identificado" y registrarlo en una cuenta transitoria.
2. Puedo aplicar luego el depósito no identificado a un cliente y a sus facturas.
3. Un listado muestra los depósitos no identificados con su antigüedad.

---

### HU-6.11 Consultar el estado de cuenta de un cliente

**Como** auxiliar contable, **quiero** generar el estado de cuenta de un cliente, **para** informarle su saldo y gestionar cobros.

Prioridad: Must · Depende de: HU-6.07

**Criterios de aceptación**
1. El estado de cuenta muestra, a una fecha, facturas, notas, cobros, anticipos, retenciones y saldo, por moneda.
2. Puedo filtrarlo por tipo de operación: alquiler, venta de contado o taller.
3. Se puede exportar a PDF y enviar por correo desde el sistema.

**Nota:** el estado de cuenta de los créditos financiados está en la Épica 9.

---

### HU-6.12 Consultar la antigüedad de saldos de clientes

**Como** contador, **quiero** ver los saldos por cobrar por antigüedad, **para** priorizar la cobranza y estimar riesgos.

Prioridad: Must · Depende de: HU-6.07

**Criterios de aceptación**
1. La antigüedad se calcula por fecha de vencimiento en rangos de días (por vencer, 1–30, 31–60, 61–90, más de 90).
2. Puedo verla por cliente, por línea de negocio (alquiler, venta de contado, taller) y por moneda.
3. El total del auxiliar cuadra con la cuenta de mayor de clientes; si no cuadra, el sistema muestra la diferencia.
4. Se exporta a PDF y Excel.
