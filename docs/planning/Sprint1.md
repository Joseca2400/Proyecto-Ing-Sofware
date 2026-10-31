# Sprint 1 · Corte transversal: de la compra al alta en flota

Versión 3 · 30 de octubre de 2026 · Sustituye a la versión 2. Se parte de cero: **no existe código**, solo esta planeación.

Integra a nuestro plan las mejoras de dos propuestas de compañeros: el `Planning.md` original (corte transversal, puntos de historia, valor de negocio) y su `Sprint1.md` ajustado (criterios de aceptación por historia, definición de terminado más estricta, contrato entre frentes). Complementa el [Plan de sprints](PlanSprints.md).

Todas las estimaciones y asignaciones A/B/C son iniciales y se ratifican en la planeación del equipo.

## 1. Qué cambia respecto a la versión 2 y a la propuesta del compañero

| Aspecto | Nuestra v2 | Propuesta del compañero | **v3 (adoptada)** |
|---|---|---|---|
| Alcance | Compromiso hasta el alta en flota, más un objetivo extendido (alquiler, factura, cobro, reportes) | Solo hasta el alta en flota | **Solo hasta el alta en flota.** El objetivo extendido se retira |
| Estimación | Días por tarea, con un factor SP a días para comparar escenarios | Días por tarea, sin factor SP a días | **Días por tarea, sin factor.** El esfuerzo real se mide en este sprint |
| Carga | 42 días (74 %), desde cero | 47 días (82 %), suponiendo reutilizar un backend | **48 días (84 %), desde cero**, con sus tareas de verificación añadidas |
| Backend | Desde cero | Reutilizar un backend existente | **Desde cero.** No hay código que reutilizar |
| Stack | Por definirse | Python, FastAPI y SQLAlchemy como candidato; motor e interfaz por ratificar | **Por definirse**; el candidato queda registrado (sección 4) |
| Avance | Porcentaje por historia | Criterios aceptados entre criterios acordados, con evidencia | **Criterios aceptados entre acordados**, con hoja de seguimiento |
| Acuerdos del día 1 | 6 | 7 | **8** (suma transacción atómica, secretos fuera de la bitácora, precisión monetaria en la API) |
| Definición de terminado | 6 puntos | 10 puntos | **10 puntos** |
| Sesiones con el contador | 3 | 4 | **4** (suma la aceptación del 25/11) |
| Administración visual de usuarios | En el sprint | Diferida | **Diferida** (cuentas iniciales sembradas) |
| Rol de gerencia | Consulta | Solo se verifica que no registre; sin tablero | **Solo se verifica que no registre** |
| Partidas automáticas | Sin precisar | Las contabiliza el servicio, sin aprobación humana por documento | **Igual**, validado con el contador |

**Qué se adopta del compañero:** retirar el objetivo extendido, medir por criterios aceptados, la definición de terminado de 10 puntos, los acuerdos adicionales del día 1, la sesión de aceptación del 25/11, la prueba automatizada del ciclo desde la interfaz, la vista de auditoría y los números de la demo.

**Qué no se adopta:**
- La reutilización del backend existente y las 41 pruebas, porque no hay código.
- Los 47 días tal cual: suponen reutilizar código. Desde cero salen 48 al sumar sus tareas de verificación.
- Las referencias a defectos de código (cobros en USD, tipo de cambio negativo). Se conservan como **criterios de aceptación**: el tipo de cambio debe ser positivo y los montos deben redondear sin error.

## 2. Objetivo y alcance transversal

**Objetivo:** un usuario autenticado registra una unidad comprada en Estados Unidos, incorpora sus costos de importación y reacondicionamiento, verifica su hoja de costo contra el mayor y la da de alta en flota, desde una interfaz web mínima.

```text
E4 Compra USD → E4 Importación → E5 Reacondicionamiento → E4 Hoja de costo → E3 Alta en flota
       │                │                  │                    │                 │
       └────────────────┴──────────────────┴────────────────────┴─────────────────┘
              E1: sesión, permisos, catálogo, VIN, tipo de cambio y auditoría
              E2: partidas por documento, aprobación manual, balance y mayor

En cada paso: pantalla → API → reglas de negocio → persistencia → verificación
```

El VIN es el hilo conductor. Las operaciones económicas generan partidas; los cambios de estado quedan auditados, sin crear asientos cuando no hay movimiento económico.

### Niveles de alcance

| Nivel | Contenido | Compromiso |
|---|---|---|
| Obligatorio | Base técnica, compra, importación, reacondicionamiento, hoja de costo y alta | Se entrega integrado y validado |
| Mejora dentro del mismo recorrido | Usabilidad, mensajes de error y pruebas adicionales de riesgos detectados | Se atiende después de cerrar los criterios obligatorios |
| Fases siguientes | Alquiler, facturación, cobros, rentabilidad, mantenimiento operativo, venta y financiamiento | No entra a la demo inicial |

La gerencia conserva su rol sin facultades de registro. No se construye un tablero para mostrarlo; se verifica que no pueda ejecutar acciones fuera de sus permisos.

## 3. Duración, fechas y capacidad

| Dato | Valor |
|---|---|
| Sprint | Lunes 02/11/2026 a viernes 27/11/2026 (4 semanas) |
| Demo parcial | Viernes 13/11 |
| Revisión de cierre de alcance | Lunes 23/11: se revisan criterios faltantes y defectos; no se abren frentes nuevos |
| Demo final y retrospectiva | Viernes 27/11 |
| Equipo | 3 desarrolladores con asistencia de IA, identificados provisionalmente como A, B y C |
| Capacidad bruta | 3 × 20 días = 60 días-persona |
| Reserva para ceremonias | 3 días-persona |
| Capacidad planificable | 57 días-persona |
| Trabajo estimado | **48 días-persona**, con K1, pruebas e integración |
| Margen | **9 días-persona (16 %)** |

El margen es justo para un proyecto sin código ni stack definido. Se destina a defectos, ajustes del contador e integración, nunca a abrir el ciclo de ingreso. Si el margen se agota, se recortan las mejoras opcionales y la presentación, no la hoja de costo, la conciliación, la autenticación ni el alta.

Las estimaciones no vienen de una velocidad medida. Los puntos de historia del alcance se estiman en K1 y no se suman a los días como una segunda carga. La asistencia de IA acelera la programación, pero no el tiempo de integración ni de validación.

## 4. Acuerdos del día 1 (K1) y supuestos

### K1 · Sesión técnica de arranque

1. **Stack: por definirse.** La decisión no es de una sola persona; el equipo y los responsables del proyecto la toman **antes del lunes 02/11** y K1 la ratifica.
   - **Candidato registrado:** backend en Python con FastAPI y SQLAlchemy, propuesto por un compañero. Es solo una opción, sin código que la respalde.
   - **Sin definir:** motor de base de datos relacional y tecnología de la interfaz web.
   - **Criterios mínimos para cualquier opción:** decimales exactos en la base de datos y migraciones versionadas; pruebas automáticas con integración continua; ambiente reproducible con un comando documentado; una interfaz web real con componentes de tabla, formulario y árbol; experiencia del equipo y soporte de las herramientas de IA que usarán.
2. **Precisión monetaria:** decimales exactos en código y persistencia, escala y redondeo explícitos. El contrato de la API conserva los valores sin que el navegador calcule montos con punto flotante.
3. **Migraciones e integración continua:** un comando crea el ambiente y aplica el esquema; las pruebas corren en cada cambio integrado.
4. **Identidad y permisos:** contrato de sesión y matriz rol por acción en un solo lugar, aplicada en el servidor. La interfaz la usa para su navegación; ocultar opciones no sustituye la autorización.
5. **Auditoría automática** en la capa de persistencia para las entidades del alcance: actor, fecha, entidad, VIN cuando corresponda y valores anteriores y nuevos. No guarda contraseñas, hashes ni secretos de sesión.
6. **Servicio único de contabilización:** las reglas de cuentas del ciclo viven en un módulo aislado; el documento y su partida se confirman en una misma transacción. Un fallo no deja registros parciales.
7. **Contrato entre frentes:** entradas, salidas y errores de sesión, compra, contabilización, taller y alta, acordados en K1. Se mantiene una versión integrada durante todo el sprint.
8. **Asignación:** A, B y C coordinan frentes, no son silos por épica. Se ratifican las asignaciones.

### Supuestos por validar

| Tema | Supuesto de trabajo | Fecha límite y responsable |
|---|---|---|
| Stack tecnológico | Se define con los responsables del proyecto; si no está, K1 y la semana 1 se desplazan | Antes del 02/11, equipo y responsables |
| Catálogo y reglas | Catálogo semilla suficiente para el recorrido; no se exige un número fijo de cuentas | 04/11, contador y equipo |
| Usuario operativo | El auxiliar contable registra compra, gastos y horas | 04/11, responsable del negocio |
| Revisión y alta | El contador o el gerente financiero cierran la orden y dan de alta; no hay solicitud de alta por el auxiliar en el Sprint 1 | 04/11, contador |
| Moneda | Quetzal como moneda funcional; compra en USD; tipo de cambio manual por fecha | 04/11, contador |
| Taller | Reacondicionamiento con una tarifa horaria interna | 11/11, contador y responsable de taller |
| Retenciones | No se calculan en este corte | Antes de la fase de compras completas, contador |
| Créditos vigentes | No hay cartera que migrar; si existe, se adelanta la Épica 9 en el plan general | 04/11, responsable del negocio |
| Certificador FEL | Fuera del Sprint 1; se elige antes de la integración de facturación real | Antes del 18/01/2027 |

## 5. Alcance por historia: versión delgada

Las filas indican criterios de este sprint, no la terminación de la historia original. **SP ref.** es la estimación inicial de un compañero para esta versión delgada; sirve de referencia al plan general y **no se cuenta como avance**. El valor usa la regla del plan general (Must 7, más 2 en E1 a E3 o 1 en E4 a E6, más 1 por participar en el corte) y se revisa con el cliente.

| Historia | Valor | SP ref. | Dueño | Incluye en el Sprint 1 | Queda pendiente |
|---|---|---|---|---|---|
| HT-01 Infraestructura | — | 3 | A | Repositorio, ambiente reproducible, migraciones, integración continua y ambiente de pruebas | Operación productiva y observabilidad ampliada |
| HU-1.09 Usuarios y roles | 10 | 2 | A | Login real con hash, sesión, cierre de sesión, cuatro roles, permisos en el servidor y cuentas iniciales | Administración visual de usuarios, bloqueo por intentos e inactividad |
| HU-1.10 Separación de funciones | 10 | 3 | A | Quien registra una partida manual no la contabiliza; rechazo con motivo | Límites monetarios de aprobación |
| HU-1.11 Bitácora | 10 | 2 | A | Automática para el alcance, sin edición ni borrado por la API; valores anteriores y nuevos; filtros por usuario, VIN y entidad | Exportación y extensión a entidades futuras |
| HU-2.01 Partida manual | 10 | 3 | A | Captura desde pantalla, quetzales y USD, dimensiones y validación de cuadre al enviar | Adjuntos |
| HU-2.02 Revisión de partidas | 10 | 3 | A | Borrador, revisión, contabilizada o devuelta; corrección y reenvío; correlativo | Lotes |
| HU-1.02 Catálogo de cuentas | 10 | 3 | B | Semilla, consulta jerárquica y alta mínima con tipo, naturaleza y cuenta monetaria | Máscara de niveles e inactivación |
| HU-1.04 Dimensiones | 10 | 2 | B | Línea de negocio y exigencia de VIN por cuenta | Configuración avanzada de obligatoriedad |
| HU-4.01 Proveedores | 9 | 1 | B | Alta y consulta, local o del exterior; NIT local validado | Régimen, retenciones y gestión completa |
| HU-4.02 Compra en EE. UU. | 9 | 4 | B | Pantalla de compra en USD que crea la unidad, la cuenta por pagar y la partida | Adjuntos |
| HU-4.04 Gastos de importación | 9 | 3 | B | Gastos por VIN; el IVA de importación se separa del costo | Expediente, prorrateo y documentos completos |
| HU-2.16 Balance y mayor | 10 | 3 | B | Consultas desde la interfaz, con filtros de fechas, línea y VIN | Navegación completa al documento y exportación |
| HU-1.05 Unidades por VIN | 10 | 3 | C | Validación, unicidad, ficha mínima, estados e historial | Placa, motor y expediente documental |
| HU-1.06 Tipo de cambio | 10 | 2 | C | Carga manual positiva por fecha; bloqueo si falta o ya se usó, según la regla validada | Servicio del Banguat y correcciones excepcionales aprobadas |
| HU-1.07 Transacciones en USD | 10 | 3 | C | Monto original, tipo de cambio y equivalente en quetzales; tipo de cambio personalizado positivo con justificación | Verificar todos los criterios originales antes de marcarla completa |
| HU-2.03 Partidas automáticas | 10 | 5 | C | Compra, gastos, cierre de orden y alta, con origen y transacción atómica | Reglas configurables y otros documentos |
| HU-4.07 Etapas de importación | 9 | 2 | C | Tránsito, aduana, taller y lista, con validación y auditoría | DUCA y métricas por etapa |
| HU-4.08 Hoja de costo | 9 | 2 | C | Pantalla por VIN con compra, importación y taller; conciliación con el mayor | PDF y Excel |
| HU-5.01 Orden de taller | 9 | 2 | C | Orden de reacondicionamiento ligada al VIN y coherente con su estado | Mantenimiento operativo, contrato y postventa |
| HU-5.02 Tarifa de mano de obra | 9 | 1 | C | Tarifa horaria única parametrizada y documentada | Tarifa por mecánico y de venta |
| HU-5.03 Mano de obra | 9 | 2 | C | Registro de horas, tarifa aplicada y costo por orden | Comparar aplicada con real |
| HU-5.07 Cierre de orden | 9 | 3 | C | Capitaliza el reacondicionamiento, bloquea la edición posterior y exige justificación de costo cero | Mantenimiento, mejoras, garantía y facturable |
| HU-3.01 Alta en flota | 10 | 3 | C | Solo unidad lista y sin órdenes abiertas, con costo conciliado, vida útil y valor residual | Solicitud y aprobación de alta por el auxiliar |
| | | **60** | | | |

**Partidas automáticas.** En el Sprint 1 las contabiliza el servicio, con registro del actor y del documento. La separación entre quien registra y quien aprueba se demuestra con partidas manuales. Esto se valida con el contador: no equivale a una aprobación humana de cada documento automático.

## 6. Tareas por desarrollador

Cada estimación incluye las pruebas de su tarea. Los frentes se coordinan mediante los contratos de K1. Total: **48 días-persona**.

### Dev A · Plataforma, seguridad y contabilidad — 15.5 días

| ID | Tarea | Historias | Días |
|---|---|---|---|
| K1 | Decisiones, contratos y definición del arranque | — | 1 |
| A1 | Ambiente reproducible, esquema migrado, integración continua y despliegue de pruebas | HT-01 | 3 |
| A2 | Login, sesión, cuentas iniciales y matriz de permisos en el servidor | HU-1.09 | 3 |
| A3 | Auditoría automática con valores anteriores y nuevos, y consulta filtrada | HU-1.11 | 2.5 |
| A4 | Motor contable: reglas centralizadas, transacción atómica, líneas en USD, correlativo, servicio único y pruebas de cuadre | HU-2.01, HU-2.02 | 3 |
| A5 | Flujo manual: edición de borrador y devuelta, revisión, rechazo y aprobación separada | HU-1.10 | 1.5 |
| A6 | Pantalla de captura de partida y bandeja de aprobación con los componentes compartidos | HU-2.01, HU-2.02 | 1.5 |

### Dev B · Interfaz, catálogo y compras — 16.5 días

| ID | Tarea | Historias | Días |
|---|---|---|---|
| K1 | Decisiones y contratos | — | 1 |
| B1 | Interfaz base: login conectado, navegación por rol, tablas, formularios y árbol | — | 3 |
| B2 | Catálogo y dimensiones: semilla, consulta y alta mínima con pantalla | HU-1.02, HU-1.04 | 2.5 |
| B3 | Proveedor: servicio y formulario mínimo | HU-4.01 | 0.5 |
| B4 | Compra en USD desde pantalla, vinculada a la cuenta por pagar y la partida | HU-4.02 | 2 |
| B5 | Gastos de importación desde pantalla y separación del IVA | HU-4.04 | 1.5 |
| B6 | Balance y mayor desde pantalla con filtros | HU-2.16 | 1.5 |
| B7 | Prueba automatizada del ciclo desde la interfaz, integrada en CI, y guion de demo | — | 3 |
| B8 | Vista de auditoría y revisión de errores y usabilidad del recorrido | HU-1.11 | 1.5 |

### Dev C · Unidad, costo, taller y flota — 16 días

| ID | Tarea | Historias | Días |
|---|---|---|---|
| K1 | Decisiones y contratos | — | 1 |
| C1 | VIN, ficha mínima e historial desde la interfaz | HU-1.05 | 2 |
| C2 | Pantalla de tipo de cambio manual y reglas multimoneda | HU-1.06, HU-1.07 | 1.5 |
| C3 | Integración de los documentos con el servicio contable y pruebas de reversa | HU-2.03 | 1.5 |
| C4 | Etapas y hoja de costo conciliada, con pantalla | HU-4.07, HU-4.08 | 2 |
| C5 | Pantallas de orden de reacondicionamiento, tarifa y registro de horas | HU-5.01, HU-5.02, HU-5.03 | 2.5 |
| C6 | Cierre de orden y capitalización | HU-5.07 | 1.5 |
| C7 | Alta en flota desde pantalla, con validaciones | HU-3.01 | 1.5 |
| C8 | Pruebas de estados, precisión monetaria y apoyo al ciclo integrado | — | 2.5 |

### Resumen de carga

| Dev | Trabajo | Capacidad | Margen |
|---|---|---|---|
| A | 15.5 | 19 | 3.5 |
| B | 16.5 | 19 | 2.5 |
| C | 16 | 19 | 3 |
| **Total** | **48** | **57** | **9** |

## 7. Calendario e incrementos demostrables

| Semana | Incremento transversal | Trabajo coordinado | Evidencia |
|---|---|---|---|
| **1** · 02 al 06/11 | Un usuario autenticado consulta el catálogo y prepara una compra | K1; A1 y A2 iniciales; B1 y B2; C1 y C2; contrato del motor contable (A4) | Ambiente y migraciones funcionando; login real y primer flujo conectado |
| **2** · 09 al 13/11 | La compra en USD desde pantalla crea la unidad, la cuenta por pagar y la partida, con registro auditable | Terminar seguridad; A3 y A4; B3 y B4; C3; inicio de C5; A5 y A6 | **Demo parcial del 13/11** y pruebas en CI |
| **3** · 16 al 20/11 | Gastos y taller acumulan costo conciliado; primera alta integrada | B5, B6 y B8; C4 a C7; cierre de A5 y A6; B7 y C8 en curso | Una unidad de prueba pasa de la compra a la flota |
| **4** · 23 al 27/11 | Recorrido completo, aceptable y reproducible | B7 y C8; defectos; revisión contable y ensayo | **Demo final**, aceptación por criterios y retrospectiva |

### Sincronización y dependencias

- K1 acuerda sesión y contabilización antes de desarrollar a sus consumidores. Las respuestas de ejemplo sirven temporalmente para integrar, pero no se aceptan como funcionamiento final.
- **Viernes 06/11:** se verifican ambiente, migraciones e integración continua. Si fallan, se usa el margen y se explicita el efecto en la demo parcial.
- **Viernes 13/11:** existe al menos un recorrido real de compra por todas las capas. No se presentan pantallas sin persistencia.
- **Cadena principal:** compra, gastos y orden, cierre de reacondicionamiento, hoja de costo y alta. Seguridad, auditoría y contabilidad entran en cada incremento.
- **Lunes 23/11:** se revisa la lista de criterios faltantes. La última semana no abre frentes nuevos.

## 8. Refinamiento con el contador

| Fecha | Validación | Resultado registrado |
|---|---|---|
| 04/11 · 1 hora | Catálogo, dimensiones, VIN, reglas por documento y tratamiento de las partidas automáticas | Caso de compra y cuentas aprobadas para el corte |
| 11/11 · 30 minutos | Importación, IVA y capitalización de mano de obra | Ejemplo de costo esperado y reglas de redondeo |
| 18/11 · 30 minutos | Cierre de orden, costo conciliado, alta, vida útil y valor residual | Caso esperado de traslado a flota |
| 25/11 · 30 minutos | Recorrido integrado y evidencia de saldos y bitácora | Aceptación o defectos concretos que bloquean el cierre |

Los cambios acordados se registran como criterios y casos de prueba. Un visto bueno general no reemplaza la validación de importes y estados del ejemplo.

## 9. Definición de listo y de terminado

### Listo para desarrollar

- Criterios incluidos y excluidos identificados por historia.
- Regla contable, permisos y datos de entrada definidos, o con supuesto explícito.
- Dependencias cubiertas dentro del sprint y contrato de integración acordado.
- Ejemplo de aceptación con datos y resultados esperados.

### Terminado por historia

- Cumple los criterios de la sección 5 desde la interfaz correspondiente.
- Las pruebas de reglas, permisos y casos de rechazo pasan en CI.
- Los cambios de las entidades incluidas quedan auditados automáticamente.
- Los criterios diferidos se conservan en el backlog con su fase de destino.

### Terminado para todo el sprint

1. El ciclo compra, importación, taller, hoja de costo y alta pasa desde el navegador, con sesión real, en el ambiente de pruebas.
2. Una unidad no puede duplicarse por VIN ni saltarse las restricciones de estado del recorrido.
3. Las operaciones en USD conservan monto original, tipo de cambio positivo y equivalente en quetzales; no se acepta un tipo de cambio inválido.
4. Documento y partida se confirman juntos; una falla contable revierte la operación.
5. Las partidas completas cuadran en quetzales. La hoja de costo concilia con el mayor y el alta traslada ese costo. Un subconjunto filtrado por VIN no se exige cuadrado si sus contrapartidas legítimas no llevan VIN.
6. Un contador no puede aprobar su propia partida manual; otro usuario autorizado sí. Se prueban los permisos de los cuatro roles.
7. Los borradores y las partidas devueltas pueden corregirse; las contabilizadas no se editan por el flujo del corte.
8. La auditoría registra actor, fecha y valores anteriores y nuevos; no ofrece edición ni borrado desde la API y no expone secretos.
9. Las migraciones y el arranque se verifican desde una base vacía; la prueba del recorrido y las regresiones pasan en CI.
10. El contador valida el caso de costo y alta, y queda evidencia de la revisión.

La demo final es una entrega en ambiente de pruebas; no autoriza el uso productivo. El porcentaje por historia es **criterios incluidos aceptados entre criterios incluidos acordados**, definidos con la misma granularidad antes de empezar. No se usa un promedio para ocultar un criterio obligatorio incumplido ni se declara completa una historia con criterios originales pendientes.

## 10. Guion de la demo final (20 minutos)

1. **Sesión y permisos:** se inicia sesión como auxiliar; se muestran sus restricciones y el acceso del contador.
2. **Preparación:** se consulta el catálogo y se registran los tipos de cambio del ejemplo.
3. **Compra:** se registra un vehículo con VIN válido por USD 8,500; se ven la unidad en tránsito, la cuenta por pagar y la partida.
4. **Importación:** se agregan flete de USD 900 y DAI de Q3,000; el IVA de importación se registra separado del costo; la unidad avanza a aduana.
5. **Taller:** se abre el reacondicionamiento, se registran 16 horas a Q75 y se cierra la orden.
6. **Costo:** con tipo de cambio de 7.70 en la compra y 7.72 en el flete, se verifica Q65,450 + Q6,948 + Q3,000 + Q1,200 = **Q76,598**. Los importes son datos de demostración sujetos a validación del contador.
7. **Alta:** la unidad pasa a lista y se da de alta en flota con vida útil y valor residual válidos; se verifica el saldo trasladado desde unidades en proceso.
8. **Control:** se consultan el mayor, el balance y la bitácora por VIN, con valores anteriores y nuevos.
9. **Separación de funciones:** en una partida manual preparada por el contador, se rechaza su propia aprobación y se aprueba con el gerente financiero.

La demo no incluye alquiler, FEL, cobro ni rentabilidad gerencial. Lo que demuestra es conocer y respaldar contablemente el costo de una unidad lista para incorporarse a la operación de alquiler.

## 11. Alcance diferido y deuda deliberada

| Elemento | Destino | Condición |
|---|---|---|
| Administración visual de usuarios, bloqueo e inactividad | Sprint 2 | Login, sesión y permisos reales sí quedan en el Sprint 1 |
| Servicio del Banguat y reglas contables configurables | Sprint 2 | El tipo de cambio manual y las reglas centralizadas bastan para el Sprint 1 |
| Perfil fiscal y cuentas bancarias | Sprint 2 | Antes de los procesos reales que los requieran |
| Expediente, DUCA, prorrateo, retenciones y pagos | Sprint 3 y 4 | Compra y gastos directos por VIN en el Sprint 1 |
| Repuestos, subcontratos y mantenimiento operativo | Sprint 4 | El corte capitaliza solo mano de obra de reacondicionamiento |
| Tarifario de alquiler | Sprint 4 | Debe ir antes de completar contratos |
| Alquiler, clientes, devolución, factura y cobros | Sprint 5 y 6 | Incluye corregir el redondeo y las fechas de cobro como criterios |
| Rentabilidad y reportes por etapa | Sprint 8 | Con depreciación y costos completos |
| Depreciación y cierres | Sprint 7 | Antes de aceptar rentabilidad financiera completa |
| Certificador FEL real | Sprint 5 | Elegirlo antes del 18/01/2027 |
| Venta, comisiones y financiamiento | Sprints 12 a 14 | Dependen de la flota, el valor en libros y las reglas de crédito |
| Migración, capacitación y arranque | Sprints 9 a 11 | Obligatoria antes del arranque |

## 12. Riesgos y respuesta

| Riesgo | Efecto | Respuesta |
|---|---|---|
| El stack no se define a tiempo | K1 y todo el sprint se desplazan | Fecha límite antes del 02/11; si hay desacuerdo, se elige por los criterios de la sección 4 |
| Retraso de seguridad, migraciones o CI | Bloquea la base del recorrido | Priorizar A1 y A2; usar el margen, sin reemplazar el login real por atajos |
| Las pantallas quedan desconectadas del servidor | La demo muestra componentes, pero no un corte transversal | Integrar la compra en la semana 2 y el ciclo completo en la semana 3 |
| Cadena crítica larga en la semana 3 | El alta en flota no llega al viernes 20/11 | Contratos desde K1; el alta puede pasar a la mañana del 23/11 sin perder el compromiso |
| Cambios tardíos del contador | Retrabajo en costo y partidas | Casos concretos y revisión semanal; reglas aisladas en un módulo |
| Auditoría incompleta | Se pierde trazabilidad del recorrido | Probar creación y modificación de cada entidad incluida |
| Diferencias del motor decimal | Filtros o cálculos incorrectos | Probar persistencia, comparación y redondeo en el motor que se ratifique |
| Margen de 9 días | Cualquier imprevisto lo agota | Recortar mejoras opcionales; replanificar explícitamente si peligra el núcleo |
| Estimaciones sin base en datos medidos | Desvío de carga y calendario | Registrar esfuerzo real por tarea y reestimar al cierre |
| Ausencia de un desarrollador | Se pierde un tercio de la capacidad | Reducir presentación y mejoras; replanificar desde las historias de menor valor |

No se recortan la hoja de costo, la conciliación, la autenticación ni el alta para sostener artificialmente la fecha. Si esos criterios no se cumplen, se informa el alcance pendiente y se replanifica.

## 13. Efecto sobre el plan general y seguimiento

1. Este documento es la referencia del Sprint 1. El [Plan de sprints](PlanSprints.md) lo toma como base y se recalcula al cierre con datos medidos.
2. Se mantiene una **hoja de seguimiento por criterio** con estado (pendiente, en desarrollo, en pruebas, aceptado); cada aceptación enlaza evidencia de CI y revisión funcional.
3. El equipo registra el **esfuerzo real por tarea** y los defectos encontrados. Al cierre se reestima el trabajo restante sin asumir una velocidad ni un factor universal de puntos a días.
4. Los puntos de historia del plan general son una referencia inicial; se reemplazan por la medición del Sprint 1.
5. La fase de ingreso (alquiler, factura y cobro) puede requerir más de un sprint; no se promete completarla en la primera ventana de dos semanas.
6. Se conserva la dependencia del tarifario antes de completar contratos y de repuestos y subcontratos antes de completar el cierre de taller; las versiones mínimas de este sprint no completan esas historias.
7. La retrospectiva produce: criterios aceptados, pendientes por fase, decisiones técnicas, validación del contador y calendario actualizado.

**Resultado esperado:** una primera entrega transversal, utilizable en pruebas, que demuestra el costo y el alta de una unidad de extremo a extremo y deja una base verificable para incorporar su operación e ingresos.
