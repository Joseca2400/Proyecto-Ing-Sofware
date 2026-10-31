# Épica 2. Contabilidad general y cierre

Prioridad de la épica: 2 · MoSCoW: **Must**
Objetivo: registrar partidas, controlarlas y cerrar períodos con orden.
Criterio de éxito de la épica: cierre mensual reproducible, con el diferencial cambiario calculado por el sistema.

---

### HU-2.01 Registrar una partida manual

**Como** auxiliar contable, **quiero** registrar partidas de diario manuales, **para** contabilizar operaciones que no nacen de otro módulo.

Prioridad: Must · Depende de: HU-1.02, HU-1.04, HU-1.07

**Criterios de aceptación**
1. La partida tiene fecha, concepto, documento de soporte y líneas con cuenta, debe o haber, línea de negocio y, cuando la cuenta lo exija, VIN.
2. Dado que los débitos y créditos en quetzales no cuadran, cuando intento enviar la partida a revisión, entonces el sistema lo impide y muestra la diferencia.
3. Las líneas en USD muestran el monto original, el tipo de cambio y el equivalente en quetzales.
4. La partida nace en estado borrador y recibe un número correlativo al contabilizarse.
5. Puedo adjuntar el soporte digital (PDF o imagen) a la partida.

---

### HU-2.02 Revisar y contabilizar partidas

**Como** contador, **quiero** revisar las partidas en borrador y contabilizarlas o devolverlas, **para** asegurar que solo entren al mayor las partidas correctas.

Prioridad: Must · Depende de: HU-2.01, HU-1.10

**Criterios de aceptación**
1. El flujo de estados es: borrador → en revisión → contabilizada, o devuelta con comentario.
2. Solo las partidas contabilizadas afectan el mayor y los reportes.
3. Las partidas de ajuste que superan el monto configurado requieren además la aprobación del gerente financiero.
4. Una partida contabilizada no se puede editar; solo se puede revertir (HU-2.05).
5. Puedo contabilizar varias partidas en lote desde una bandeja de pendientes.

---

### HU-2.03 Generar partidas automáticas desde los módulos

**Como** contador, **quiero** que facturas, pagos, cobros, órdenes de taller y demás documentos generen su partida de forma automática, **para** evitar doble captura y errores.

Prioridad: Must · Depende de: HU-2.01

**Criterios de aceptación**
1. Cada tipo de documento tiene una regla de contabilización configurable (cuentas de débito y crédito, línea de negocio y origen del VIN).
2. La partida automática queda ligada al documento que la originó y se puede navegar en ambos sentidos.
3. Dado que falta una cuenta en la regla, cuando se confirma el documento, entonces el sistema no genera una partida incompleta y avisa qué regla falta.
4. Una partida automática no se edita a mano; para corregirla se anula o corrige el documento de origen.

---

### HU-2.04 Programar partidas recurrentes

**Como** auxiliar contable, **quiero** programar partidas que se repiten cada mes, **para no** registrarlas manualmente cada período.

Prioridad: Should · Depende de: HU-2.01

**Criterios de aceptación**
1. Puedo definir una plantilla con líneas, frecuencia, fecha de inicio y fecha de fin.
2. El sistema genera las partidas en borrador en la fecha programada y las envía a la bandeja de revisión.
3. Puedo pausar o terminar una recurrencia sin afectar las partidas ya generadas.

---

### HU-2.05 Revertir una partida contabilizada

**Como** contador, **quiero** revertir una partida contabilizada, **para** corregir errores sin borrar historia.

Prioridad: Must · Depende de: HU-2.02

**Criterios de aceptación**
1. La reversión crea una partida nueva con los mismos valores invertidos, ligada a la original, con motivo obligatorio.
2. Puedo elegir la fecha de la reversión; si cae en un período cerrado, el sistema lo impide.
3. La partida original queda marcada como revertida y no se puede revertir dos veces.

---

### HU-2.06 Registrar provisiones con reversión automática

**Como** contador, **quiero** registrar provisiones que se reviertan al inicio del período siguiente, **para** reconocer gastos e ingresos devengados no documentados.

Prioridad: Should · Depende de: HU-2.05

**Criterios de aceptación**
1. Al registrar una partida puedo marcarla como "reversible" e indicar la fecha de reversión.
2. El sistema genera la reversión en borrador en esa fecha, ligada a la provisión original.
3. Puedo consultar un listado de provisiones vigentes y ya revertidas.

---

### HU-2.07 Calcular la depreciación mensual

**Como** contador, **quiero** que el sistema calcule y contabilice la depreciación mensual de la flota y de los demás activos fijos, **para** reflejar el gasto de cada unidad sin cálculos manuales.

Prioridad: Must · Depende de: HU-3.01, HU-3.02

**Criterios de aceptación**
1. El cálculo usa los parámetros de cada activo (costo, vida útil, valor residual y método) y genera una partida en borrador con una línea por unidad, ligada a su VIN y a la línea de alquiler.
2. Los activos que no son flota (mobiliario, equipo de taller, cómputo) se deprecian con su propia línea de negocio.
3. Si la depreciación fiscal difiere de la financiera, el sistema calcula ambas y guarda la diferencia para la conciliación fiscal del ISR.
4. El cálculo no deprecia activos dados de baja, ni más allá del valor residual.
5. Volver a ejecutar el cálculo del mismo mes reemplaza el borrador; si ya está contabilizado, el sistema lo impide.

**Pendiente:** si la depreciación fiscal (20 % anual para vehículos) difiere de la financiera (pregunta 4 de las épicas).

---

### HU-2.08 Revaluar saldos en dólares al cierre

**Como** contador, **quiero** revaluar al cierre de mes los saldos de las cuentas monetarias en USD, **para** registrar el diferencial cambiario no realizado.

Prioridad: Must · Depende de: HU-1.06, HU-1.07

**Criterios de aceptación**
1. El proceso toma el tipo de cambio del Banguat del último día del mes y lo aplica a bancos, cuentas por cobrar, cuentas por pagar y préstamos en USD.
2. Genera una partida con el diferencial no realizado (ganancia o pérdida) por cuenta y, cuando aplique, por cliente o proveedor.
3. La partida de revaluación se revierte de forma automática el primer día del mes siguiente, o el sistema mantiene el saldo revaluado, según la política configurada.
4. El reporte de revaluación muestra, por cuenta, saldo en USD, tipo de cambio anterior, tipo de cambio de cierre y diferencial.

---

### HU-2.09 Calcular el diferencial cambiario realizado

**Como** contador, **quiero** que al pagar o cobrar un documento en USD el sistema calcule el diferencial entre el tipo de cambio del documento y el del pago, **para** registrar la ganancia o pérdida cambiaria realizada.

Prioridad: Must · Depende de: HU-1.07

**Criterios de aceptación**
1. Dado que una factura en USD se registró con un tipo de cambio y se paga con otro, cuando confirmo el pago, entonces la partida incluye una línea de diferencial cambiario realizado.
2. El cálculo considera la revaluación ya registrada para no duplicar el efecto.
3. Los pagos parciales calculan el diferencial en proporción al monto aplicado.

---

### HU-2.10 Conciliar las cuentas bancarias

**Como** auxiliar contable, **quiero** conciliar los movimientos del banco con los registros contables, **para** detectar diferencias y partidas en tránsito.

Prioridad: Must · Depende de: HU-1.08

**Criterios de aceptación**
1. Puedo importar el estado de cuenta del banco en Excel o CSV, o capturarlo de forma manual.
2. El sistema sugiere coincidencias por monto, fecha y referencia; yo confirmo o corrijo cada una.
3. Los movimientos del banco sin registro contable (comisiones, intereses, cargos) se pueden contabilizar desde la misma pantalla.
4. La conciliación muestra saldo según banco, saldo según libros, cheques en circulación, depósitos en tránsito y diferencia, que debe ser cero para cerrarla.
5. Las cuentas en USD se concilian en dólares.

**Nota:** las integraciones bancarias automáticas están fuera del alcance.

---

### HU-2.11 Seguir una lista de verificación de cierre

**Como** contador, **quiero** una lista de verificación de cierre mensual, **para** no omitir pasos y que el cierre sea reproducible.

Prioridad: Should · Depende de: HU-2.07, HU-2.08, HU-2.10

**Criterios de aceptación**
1. La lista incluye, como mínimo: partidas pendientes de contabilizar, depreciación, revaluación, conciliaciones bancarias, cuadre de auxiliares (cuentas por cobrar, cuentas por pagar, cartera e inventarios) con el mayor y órdenes de taller abiertas.
2. El sistema marca de forma automática los pasos que puede verificar y muestra la diferencia de cada uno.
3. Puedo agregar pasos manuales y marcarlos como hechos con comentario.

---

### HU-2.12 Cerrar un período mensual

**Como** contador, **quiero** cerrar el mes, **para** impedir registros que alteren cifras ya reportadas.

Prioridad: Must · Depende de: HU-2.02

**Criterios de aceptación**
1. Dado que hay partidas en borrador o en revisión en el mes, cuando intento cerrar, entonces el sistema me avisa y no cierra.
2. Un mes cerrado no acepta partidas nuevas, reversiones ni documentos con fecha en ese mes.
3. El cierre guarda usuario, fecha y una instantánea del balance de comprobación.
4. Los meses se cierran en orden; no puedo cerrar un mes si el anterior está abierto.

---

### HU-2.13 Reabrir un período cerrado

**Como** contador, **quiero** solicitar la reapertura de un mes cerrado, **para** corregir un error de importancia con autorización.

Prioridad: Must · Depende de: HU-2.12, HU-1.10

**Criterios de aceptación**
1. La solicitud exige motivo y queda pendiente hasta que el gerente financiero la apruebe.
2. Al reabrir un mes se reabren también los meses posteriores que estén cerrados.
3. La reapertura y el nuevo cierre quedan en bitácora con la diferencia entre la instantánea anterior y la nueva.
4. Un año con cierre anual contabilizado no se puede reabrir sin revertir antes el cierre anual.

---

### HU-2.14 Ejecutar el cierre anual

**Como** contador, **quiero** ejecutar el cierre del ejercicio, **para** trasladar el resultado del año y abrir el siguiente.

Prioridad: Must · Depende de: HU-2.12

**Criterios de aceptación**
1. El cierre anual exige que los doce meses estén cerrados.
2. Genera la partida de cierre de cuentas de resultados contra la cuenta de resultado del ejercicio y la partida de apertura del año siguiente.
3. El ejercicio fiscal es del 1 de enero al 31 de diciembre.
4. El cierre conserva el detalle por línea de negocio para los reportes comparativos.

---

### HU-2.15 Emitir los libros legales

**Como** contador, **quiero** generar los libros diario, mayor, de inventarios y de compras y ventas, **para** cumplir con las obligaciones ante la SAT.

Prioridad: Must · Depende de: HU-2.02

**Criterios de aceptación**
1. Cada libro se genera por rango de fechas con encabezado de empresa, NIT y período.
2. El libro de compras y ventas muestra, por documento, fecha, serie y número, NIT, nombre, base, IVA y total, y separa bienes, servicios, importaciones y exentos.
3. Los libros se pueden exportar a PDF con numeración de folios configurable para impresión en hojas habilitadas, y a Excel.
4. Un libro emitido para un período cerrado coincide siempre con el mismo contenido.

---

### HU-2.16 Consultar el balance de comprobación y el mayor

**Como** contador, **quiero** consultar el balance de comprobación y el mayor con filtros, **para** analizar saldos por cuenta, línea y unidad.

Prioridad: Must · Depende de: HU-2.02

**Criterios de aceptación**
1. Puedo filtrar por rango de fechas, cuenta, línea de negocio y VIN.
2. El mayor muestra saldo inicial, movimientos con su documento de origen y saldo final.
3. Para cuentas en USD puedo ver la columna en moneda original además de quetzales.
4. Desde cualquier movimiento puedo abrir la partida y el documento que la originó.
