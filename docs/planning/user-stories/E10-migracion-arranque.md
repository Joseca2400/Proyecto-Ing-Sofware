# Épica 10. Migración y arranque

Prioridad de la épica: 10 · MoSCoW: **Must** (al final)
Objetivo: iniciar operación con datos confiables.
Criterio de éxito de la épica: los saldos del sistema cuadran con los últimos estados financieros validados.

Las historias de carga comparten estas reglas:
- Cada carga usa una plantilla de Excel descargable desde el sistema (HU-10.01).
- Toda carga se valida completa antes de confirmarse; si hay errores, no se carga nada.
- Toda carga queda en bitácora con usuario, fecha, archivo y totales.
- Las cargas se hacen con fecha de corte igual a la fecha de arranque.

---

### HU-10.01 Descargar plantillas de carga y validar archivos

**Como** contador, **quiero** plantillas de carga con validación previa, **para** migrar datos sin errores de formato.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. Existe una plantilla por tipo de carga con columnas, formatos y ejemplos.
2. Al subir el archivo, el sistema muestra los errores por fila y columna.
3. Puedo ejecutar la validación tantas veces como necesite sin efecto en los datos.
4. El resumen previo muestra cantidades y totales por moneda para compararlos con la fuente.

---

### HU-10.02 Cargar los saldos contables iniciales

**Como** contador, **quiero** cargar los saldos de apertura de todas las cuentas en Q y USD, **para** iniciar la contabilidad desde la fecha de arranque.

Prioridad: Must · Depende de: HU-10.01, HU-1.02

**Criterios de aceptación**
1. La carga genera una partida de apertura con saldo por cuenta, línea de negocio y, cuando la cuenta lo exija, VIN.
2. Las cuentas en USD se cargan con su saldo en dólares y su equivalente en quetzales a la fecha de corte.
3. La partida de apertura debe cuadrar en quetzales para confirmarse.
4. La partida de apertura requiere aprobación del gerente financiero.

---

### HU-10.03 Cargar la flota con su valor en libros

**Como** contador, **quiero** cargar las unidades de la flota con su costo, depreciación acumulada y valor en libros, **para** continuar su depreciación sin recalcular la historia.

Prioridad: Must · Depende de: HU-10.01, HU-3.02

**Criterios de aceptación**
1. Por VIN cargo datos del vehículo, fecha de alta, costo (desglosado en compra, importación y reacondicionamiento cuando exista), vida útil, valor residual, depreciación acumulada financiera y fiscal, y kilometraje.
2. El sistema valida que la suma de costos y depreciaciones coincida con los saldos de las cuentas de flota de la partida de apertura.
3. Las unidades quedan en estado "en flota" y se deprecian a partir del mes siguiente al corte.

---

### HU-10.04 Cargar unidades en importación, en taller y en venta

**Como** contador, **quiero** cargar las unidades que están en importación, en taller o en venta, **para** que sigan su ciclo en el sistema con el costo acumulado.

Prioridad: Must · Depende de: HU-10.01

**Criterios de aceptación**
1. Por VIN cargo estado, costo acumulado por concepto y, si aplica, expediente de importación y DUCA.
2. Las unidades en venta se cargan con su valor en libros y su precio de lista.
3. Los totales cuadran con las cuentas de "unidades en proceso" e "inventario de unidades para la venta" de la apertura.
4. Las órdenes de taller abiertas se cargan con su costo acumulado y su tipo de trabajo.

---

### HU-10.05 Cargar clientes, proveedores y sus saldos abiertos

**Como** auxiliar contable, **quiero** cargar clientes y proveedores con sus documentos pendientes, **para** cobrar y pagar los saldos existentes desde el sistema.

Prioridad: Must · Depende de: HU-10.01

**Criterios de aceptación**
1. Cargo los maestros de clientes y proveedores con sus datos fiscales.
2. Cargo cada documento pendiente con número, fecha, vencimiento, moneda, monto original, saldo y tipo de cambio original.
3. Los saldos por moneda cuadran con las cuentas de clientes y proveedores de la apertura.
4. Los anticipos y depósitos en garantía vigentes se cargan como tales, ligados a su cliente y contrato.

---

### HU-10.06 Cargar la cartera financiada vigente

**Como** contador, **quiero** cargar los créditos vigentes con sus saldos y cuotas pendientes, **para** continuar el cobro y el control de la mora desde el sistema.

Prioridad: Must, si existen créditos vigentes · Depende de: HU-10.01, HU-9.03

**Criterios de aceptación**
1. Por crédito cargo cliente, VIN, condiciones originales, saldo de capital, intereses por cobrar, mora y cuotas pendientes.
2. El sistema genera la tabla de amortización de las cuotas pendientes y la compara con el saldo cargado.
3. Los saldos cuadran con las cuentas de cartera y provisión de la apertura.

---

### HU-10.07 Cargar el inventario de repuestos

**Como** auxiliar contable, **quiero** cargar los repuestos con su existencia y costo, **para** iniciar el control de inventario del taller.

Prioridad: Must · Depende de: HU-10.01, HU-5.04

**Criterios de aceptación**
1. Por repuesto cargo código, descripción, unidad de medida, ubicación, existencia y costo unitario.
2. El valor total cuadra con la cuenta de inventario de repuestos de la apertura.
3. Se recomienda que la carga parta de un conteo físico a la fecha de corte.

---

### HU-10.08 Cargar los contratos de alquiler activos

**Como** auxiliar contable, **quiero** cargar los contratos de alquiler vigentes, **para** seguir facturándolos y controlar la ocupación desde el sistema.

Prioridad: Must · Depende de: HU-10.01, HU-3.06

**Criterios de aceptación**
1. Por contrato cargo cliente, VIN, fechas, tarifa, frecuencia de facturación, último período facturado y depósito en garantía.
2. Las unidades con contrato activo quedan en estado "alquilada".
3. El sistema no factura otra vez los períodos ya facturados antes del arranque.

---

### HU-10.09 Conciliar el arranque y aceptar los saldos

**Como** gerente financiero, **quiero** un reporte que compare los saldos del sistema con los estados financieros validados, **para** aceptar formalmente el arranque.

Prioridad: Must · Depende de: HU-10.02 a HU-10.08

**Criterios de aceptación**
1. El reporte compara cuenta por cuenta el balance del sistema con el balance validado a la fecha de corte.
2. Compara cada auxiliar (clientes, proveedores, cartera, flota, unidades en proceso, inventarios, depósitos) con su cuenta de mayor.
3. Muestra las diferencias; el arranque no se puede aceptar con diferencias distintas de cero.
4. La aceptación queda registrada con usuario y fecha, y bloquea nuevas cargas iniciales.

---

### HU-10.10 Operar en paralelo antes del arranque definitivo

**Como** contador, **quiero** operar en paralelo el sistema nuevo y el actual durante un período, **para** comprobar que producen los mismos resultados.

Prioridad: Should · Depende de: HU-10.09

**Criterios de aceptación**
1. Se define el período de operación en paralelo (por ejemplo, un mes) y los reportes a comparar.
2. Al final del período se comparan el balance de comprobación, el estado de resultados y los auxiliares de ambos sistemas.
3. Las diferencias se documentan con su causa y su corrección antes de dejar el sistema anterior.

---

### HU-10.11 Capacitar a los usuarios por rol (habilitación)

**Como** gerente financiero, **quiero** que cada usuario reciba capacitación según su rol, **para** que pueda operar el sistema desde el primer día.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. Existe una guía breve por rol: auxiliar contable, contador, gerente financiero y gerencia.
2. Cada usuario completa la capacitación en un ambiente de pruebas con datos de ejemplo antes del arranque.
3. Se registra la asistencia y los temas cubiertos.

**Nota:** es una historia de habilitación, no de funcionalidad del sistema.

---

### HU-10.12 Dar soporte inicial tras el arranque (habilitación)

**Como** contador, **quiero** un canal de soporte durante las primeras semanas, **para** resolver dudas e incidencias sin detener la operación.

Prioridad: Must · Depende de: HU-10.09

**Criterios de aceptación**
1. Se define el período de soporte intensivo, el canal y los tiempos de respuesta.
2. Cada incidencia se registra con su prioridad, su estado y su solución.
3. Al cerrar el período, se entrega un resumen de incidencias y mejoras pendientes.

**Nota:** es una historia de habilitación, no de funcionalidad del sistema.
