# Épica 9. Financiamiento propio y cartera

Prioridad de la épica: 9 · MoSCoW: **Should** (sube a **Must** si al arrancar ya hay créditos vigentes)
Objetivo: administrar los créditos otorgados a compradores.
Criterio de éxito de la épica: el saldo de capital e intereses por cliente cuadra con la contabilidad y la mora se ve al día.

**Pendiente general:** plazo, tasa y moneda típicos; qué pasa con la unidad en caso de impago; si hay créditos vigentes hoy (pregunta 7 de las épicas).

---

### HU-9.01 Definir planes de crédito

**Como** gerente financiero, **quiero** definir planes de crédito con sus condiciones, **para** ofrecer financiamiento de forma estandarizada.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. Un plan tiene nombre, moneda, enganche mínimo (porcentaje), plazos permitidos, tasa de interés anual, tasa de interés moratorio, días de gracia y cargos (por ejemplo, gastos administrativos o seguro).
2. Puedo elegir el método de cálculo: cuota nivelada (sistema francés) o capital fijo con interés sobre saldo.
3. Los planes tienen vigencia; un cambio no afecta los créditos ya otorgados.

---

### HU-9.02 Registrar y aprobar un crédito

**Como** auxiliar contable, **quiero** registrar un crédito a partir de una venta financiada, **para** que el gerente financiero lo apruebe con sus condiciones.

Prioridad: Must · Depende de: HU-9.01, HU-8.05

**Criterios de aceptación**
1. El crédito tiene cliente, unidad (VIN), venta, plan, monto financiado, enganche, plazo, tasa, fecha de primera cuota y día de pago.
2. El sistema impide condiciones fuera del plan (enganche menor al mínimo, plazo no permitido) salvo que el gerente financiero las apruebe como excepción.
3. El crédito queda en estado "por aprobar" hasta que el gerente financiero lo apruebe; quien lo registró no puede aprobarlo.
4. Al aprobarse y confirmarse la venta, el saldo financiado se traslada de la cuenta por cobrar de la venta a la cartera de créditos.

---

### HU-9.03 Generar la tabla de amortización

**Como** auxiliar contable, **quiero** generar la tabla de amortización del crédito, **para** conocer cada cuota y entregársela al cliente.

Prioridad: Must · Depende de: HU-9.02

**Criterios de aceptación**
1. La tabla muestra, por cuota, fecha de vencimiento, capital, interés, IVA sobre interés si aplica, cargos, cuota total y saldo de capital.
2. La suma del capital de las cuotas es igual al monto financiado; el redondeo se ajusta en la última cuota.
3. Puedo imprimir la tabla y adjuntarla al contrato.
4. La tabla se recalcula de forma automática tras un abono extraordinario o una reestructuración, y conserva la versión anterior.

---

### HU-9.04 Devengar los intereses mensuales

**Como** contador, **quiero** que el sistema devengue los intereses de la cartera al cierre de mes, **para** reconocer el ingreso por financiamiento en el período que corresponde.

Prioridad: Must · Depende de: HU-9.03

**Criterios de aceptación**
1. El proceso calcula el interés devengado y no cobrado de cada crédito a la fecha de cierre y genera una partida en la línea de financiamiento, ligada al cliente y al VIN.
2. Puedo configurar que un crédito con más de cierto número de días de atraso deje de devengar intereses (cartera en no devengo).
3. El proceso no duplica intereses ya devengados.

---

### HU-9.05 Facturar los intereses

**Como** auxiliar contable, **quiero** facturar los intereses de cada cuota, **para** cumplir con las obligaciones de IVA sobre intereses.

Prioridad: Must · Depende de: HU-9.03, HU-6.02

**Criterios de aceptación**
1. Puedo configurar si la factura de intereses se emite al vencer la cuota o al cobrarla.
2. La factura FEL incluye interés y cargos de la cuota, con el IVA que corresponda según la configuración.
3. La factura queda ligada al crédito, a la cuota y al VIN.

**Pendiente:** si el interés lleva IVA y en qué momento se factura, por validar con el contador.

---

### HU-9.06 Registrar el cobro de una cuota

**Como** auxiliar contable, **quiero** registrar los pagos de cuotas, **para** reducir el saldo del crédito en el orden correcto.

Prioridad: Must · Depende de: HU-9.03, HU-6.07

**Criterios de aceptación**
1. El pago se aplica en el orden configurado, por defecto: cargos, interés moratorio, interés corriente y capital, de la cuota más antigua a la más reciente.
2. Un pago parcial deja la cuota con saldo pendiente y el sistema muestra lo que falta.
3. El cobro genera su partida, separando capital, intereses y cargos, y actualiza la tabla de amortización.
4. Puedo emitir el recibo con el detalle de aplicación y el nuevo saldo.

---

### HU-9.07 Registrar abonos extraordinarios a capital

**Como** auxiliar contable, **quiero** registrar abonos a capital fuera de la cuota, **para** reducir el plazo o la cuota del crédito según lo que elija el cliente.

Prioridad: Must · Depende de: HU-9.06

**Criterios de aceptación**
1. El abono solo se acepta si las cuotas vencidas están al día.
2. Puedo elegir si el abono reduce el plazo o el monto de la cuota.
3. El sistema genera una nueva tabla de amortización y conserva la anterior.

---

### HU-9.08 Cancelar un crédito de forma anticipada

**Como** auxiliar contable, **quiero** calcular el monto para cancelar un crédito antes del plazo, **para** liquidarlo y liberar la garantía.

Prioridad: Must · Depende de: HU-9.06

**Criterios de aceptación**
1. El sistema calcula, a una fecha, capital pendiente, interés devengado no pagado, mora y cargos o penalización por cancelación anticipada según el plan.
2. Puedo emitir una constancia del monto de cancelación con fecha de vigencia.
3. Al registrar el pago total, el crédito pasa a "cancelado" y se habilita la liberación de la garantía prendaria (HU-9.11).

---

### HU-9.09 Calcular la mora y el interés moratorio

**Como** contador, **quiero** que el sistema calcule los días de atraso y el interés moratorio de cada crédito, **para** cobrar la mora y ver el estado de la cartera al día.

Prioridad: Must · Depende de: HU-9.03

**Criterios de aceptación**
1. Cada día el sistema actualiza los días de atraso de cada crédito según su cuota vencida más antigua.
2. Pasados los días de gracia, calcula el interés moratorio sobre el capital vencido a la tasa del plan.
3. El gerente financiero puede condonar intereses moratorios con motivo; la condonación queda en bitácora.
4. Puedo ver la lista de créditos en mora con días de atraso, monto vencido y datos de contacto.

---

### HU-9.10 Calcular la antigüedad de la cartera y la provisión por incobrables

**Como** contador, **quiero** clasificar la cartera por antigüedad y calcular la provisión por incobrables, **para** reflejar el riesgo en los estados financieros.

Prioridad: Must · Depende de: HU-9.09

**Criterios de aceptación**
1. La antigüedad clasifica el saldo por rangos de días de atraso (al día, 1–30, 31–60, 61–90, 91–180, más de 180).
2. Puedo configurar el porcentaje de provisión por rango.
3. Al cierre, el sistema calcula la provisión requerida y genera la partida de ajuste por la diferencia con la provisión registrada.
4. El sistema muestra por separado la provisión deducible para ISR según el límite fiscal configurado.
5. Puedo dar de baja un crédito incobrable contra la provisión con aprobación del gerente financiero.

---

### HU-9.11 Registrar y liberar la garantía prendaria

**Como** auxiliar contable, **quiero** registrar la garantía prendaria sobre el vehículo financiado, **para** controlar su vigencia y liberarla al cancelar el crédito.

Prioridad: Should · Depende de: HU-9.02

**Criterios de aceptación**
1. La garantía registra VIN, documento de prenda, número de inscripción, fecha y estado (vigente, liberada, ejecutada).
2. El sistema impide liberar la garantía de un crédito con saldo pendiente.
3. Al liberar la garantía, registro la fecha y el documento de liberación.

---

### HU-9.12 Recuperar una unidad por impago

**Como** contador, **quiero** registrar la recuperación de una unidad por falta de pago, **para** cancelar el crédito y reingresar el vehículo al inventario.

Prioridad: Should · Depende de: HU-9.10, HU-9.11

**Criterios de aceptación**
1. La recuperación requiere aprobación del gerente financiero y registra fecha, estado del vehículo y valor de reingreso.
2. El sistema cancela el saldo del crédito contra el valor de reingreso de la unidad y la provisión; la diferencia se registra como pérdida o ganancia.
3. La unidad pasa a estado "recuperada" y luego al inventario de venta, con el valor de reingreso como su nuevo costo.
4. Se puede abrir una orden de taller de reacondicionamiento para la unidad recuperada.

**Pendiente:** criterio de valuación de la unidad recuperada y procedimiento legal (pregunta 7 de las épicas).

---

### HU-9.13 Emitir el estado de cuenta del crédito

**Como** auxiliar contable, **quiero** emitir el estado de cuenta de un crédito, **para** informar al cliente su situación.

Prioridad: Must · Depende de: HU-9.06

**Criterios de aceptación**
1. Muestra condiciones del crédito, cuotas pagadas y pendientes, pagos recibidos con su aplicación, mora y saldo de capital e intereses a una fecha.
2. Se puede exportar a PDF y enviar por correo desde el sistema.

---

### HU-9.14 Conciliar la cartera con la contabilidad

**Como** contador, **quiero** comparar el auxiliar de cartera con las cuentas de mayor, **para** confirmar que los saldos cuadran.

Prioridad: Must · Depende de: HU-9.06

**Criterios de aceptación**
1. El reporte compara, por moneda, el saldo de capital, intereses por cobrar y provisión del auxiliar contra sus cuentas de mayor.
2. Muestra las diferencias y los créditos que las originan.
3. Esta conciliación forma parte de la lista de verificación del cierre (HU-2.11).

---

### HU-9.15 Reestructurar un crédito

**Como** gerente financiero, **quiero** reestructurar un crédito en mora con nuevas condiciones, **para** facilitar su recuperación.

Prioridad: Could · Depende de: HU-9.03

**Criterios de aceptación**
1. La reestructuración capitaliza o no el interés vencido, según se elija, y define un nuevo plazo y tasa.
2. Genera una nueva tabla de amortización y conserva el historial del crédito original.
3. El crédito queda marcado como reestructurado para los reportes de cartera.
