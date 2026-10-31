# Épica 7. Reportes gerenciales

Prioridad de la épica: 7 · MoSCoW: **Must**
Objetivo: dar a la gerencia visibilidad de rentabilidad y control.
Criterio de éxito de la épica: los 3 a 5 reportes clave salen del sistema sin trabajo manual.

Reglas comunes a todos los reportes de esta épica:
- Las cifras salen de partidas contabilizadas y de los auxiliares que cuadran con el mayor; no hay captura manual en los reportes.
- Cada reporte indica fecha de corte, filtros aplicados y si incluye períodos abiertos.
- El rol gerencia puede consultar todos los reportes de esta épica, pero no los registros de origen.

**Pendiente:** cuáles son los 3 a 5 reportes más usados, para priorizar el orden de construcción dentro de esta épica.

---

### HU-7.01 Consultar estados financieros por línea de negocio

**Como** gerencia, **quiero** ver el balance general y el estado de resultados por línea de negocio, **para** saber qué línea genera utilidad.

Prioridad: Must · Depende de: HU-2.16

**Criterios de aceptación**
1. El estado de resultados muestra columnas por línea (alquiler, venta, taller, financiamiento, administración) y total.
2. Puedo comparar contra el mes anterior, el mismo mes del año anterior y el acumulado del año.
3. Las cifras se presentan en quetzales; de forma opcional, en USD como referencia al tipo de cambio de cierre.
4. Puedo bajar desde cualquier cifra hasta las cuentas y las partidas que la forman.

**Pendiente:** si se requiere la presentación en USD y si los gastos de administración se distribuyen entre líneas.

---

### HU-7.02 Consultar la rentabilidad de cada unidad en todo su ciclo

**Como** gerencia, **quiero** ver el resultado de cada vehículo desde su importación hasta su venta, **para** decidir qué tipo de unidades conviene importar.

Prioridad: Must · Depende de: HU-4.08, HU-3.13, HU-8.12

**Criterios de aceptación**
1. Por VIN se muestran: costo de compra, importación y reacondicionamiento; ingresos de alquiler; mantenimiento, seguro y marchamo; depreciación; resultado de la venta (precio menos valor en libros, comisión y garantía); e intereses del financiamiento, por separado.
2. Se muestran días en flota, ocupación y resultado total acumulado.
3. Puedo filtrar por estado (en flota, vendida), marca, modelo, año de compra y proveedor de origen.
4. Puedo comparar unidades y ordenarlas por resultado o por rentabilidad sobre el costo.

---

### HU-7.03 Consultar la ocupación y rentabilidad de la flota

**Como** gerencia, **quiero** ver la ocupación y el resultado de la flota por período, **para** evaluar tarifas y tamaño de la flota.

Prioridad: Must · Depende de: HU-3.12, HU-3.13

**Criterios de aceptación**
1. Muestra unidades en flota, días disponibles, días alquilados, días en taller, porcentaje de ocupación e ingreso promedio por día alquilado.
2. Muestra el resultado por tipo de vehículo y el total.
3. Incluye una gráfica de la tendencia mensual de ocupación e ingreso.

---

### HU-7.04 Consultar las unidades por etapa del ciclo

**Como** gerencia, **quiero** ver cuántas unidades hay en importación, en taller, en flota y en venta, y cuánto valen, **para** conocer el capital invertido en cada etapa.

Prioridad: Must · Depende de: HU-4.07

**Criterios de aceptación**
1. Muestra la cantidad de unidades y el valor (costo acumulado o valor en libros) por estado.
2. Muestra los días promedio en cada etapa y destaca las unidades que superan un plazo configurable.
3. Puedo abrir el listado de unidades de cada estado.

---

### HU-7.05 Consultar la cartera financiada y la mora

**Como** gerencia, **quiero** ver la cartera de créditos y su mora, **para** controlar el riesgo del financiamiento.

Prioridad: Must · Depende de: HU-9.10

**Criterios de aceptación**
1. Muestra créditos vigentes, saldo de capital, intereses por cobrar, cartera al día y en mora por rangos de días de atraso.
2. Muestra el índice de mora (saldo en mora entre saldo total) y su tendencia mensual.
3. Muestra la provisión para incobrables registrada.
4. Puedo abrir el detalle por cliente.

---

### HU-7.06 Consultar las comisiones por vendedor

**Como** gerencia, **quiero** ver las comisiones devengadas y pagadas por vendedor, **para** controlar el costo comercial de la venta de unidades.

Prioridad: Must · Depende de: HU-8.09

**Criterios de aceptación**
1. Muestra por vendedor y período: unidades vendidas, monto vendido, comisión devengada, pagada y pendiente.
2. Puedo abrir el detalle por venta.

---

### HU-7.07 Consultar la antigüedad de saldos de clientes y proveedores

**Como** gerencia, **quiero** un resumen de cuentas por cobrar y por pagar por antigüedad, **para** anticipar necesidades de liquidez.

Prioridad: Must · Depende de: HU-6.12, HU-4.16

**Criterios de aceptación**
1. Muestra en una misma vista el resumen por rangos de días de clientes y de proveedores, por moneda y en quetzales.
2. Destaca los 10 saldos más altos vencidos de cada lado.
3. Las cifras coinciden con los reportes detallados de las épicas 4 y 6.

---

### HU-7.08 Consultar el inventario de unidades y repuestos

**Como** gerencia, **quiero** un reporte valorizado del inventario de unidades en venta y de repuestos, **para** conocer el capital inmovilizado.

Prioridad: Should · Depende de: HU-5.04, HU-8.01

**Criterios de aceptación**
1. Las unidades en venta se muestran con su valor en libros, precio de lista y días en inventario.
2. Los repuestos se muestran con existencia, costo promedio, valor total y fecha del último movimiento.
3. Los totales cuadran con las cuentas de inventario del mayor.

---

### HU-7.09 Exportar reportes a PDF y Excel

**Como** gerencia, **quiero** exportar cualquier reporte a PDF y Excel, **para** compartirlo y analizarlo fuera del sistema.

Prioridad: Must · Depende de: —

**Criterios de aceptación**
1. Todos los reportes de esta épica tienen exportación a PDF y a Excel.
2. El PDF incluye el nombre de la empresa, el título, la fecha de corte, los filtros y la fecha y el usuario de generación.
3. El Excel conserva los números como valores numéricos, no como texto.

---

### HU-7.10 Consultar un tablero gerencial

**Como** gerencia, **quiero** un tablero con los indicadores clave del negocio, **para** ver el estado general en una sola pantalla.

Prioridad: Should · Depende de: HU-7.01, HU-7.03, HU-7.05

**Criterios de aceptación**
1. El tablero muestra, al último cierre y al día: utilidad del mes por línea, ocupación de la flota, unidades por etapa, cartera en mora, saldos de bancos en Q y USD y cuentas por cobrar y por pagar vencidas.
2. Cada indicador permite abrir el reporte detallado que lo origina.
3. El tablero indica si el mes del indicador ya está cerrado.
