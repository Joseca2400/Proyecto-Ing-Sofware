# Sprint 1 · Base contable, compra en USD y preparación del ingreso

Versión 4 · 31 de octubre de 2026 · Sustituye a la versión 3 ([Old/Sprint1-v3.md](Old/Sprint1-v3.md)). Forma parte del [plan v5](PlanMVP.md): MVP al cierre del Sprint 3 con 6 desarrolladores.

## 1. Qué cambia respecto a la versión 3

| Aspecto | v3 | **v4 (este)** |
|---|---|---|
| Duración | 4 semanas (02/11 – 27/11) | **2 semanas (02/11 – 13/11)** |
| Equipo | 3 desarrolladores (A, B, C) | **6 desarrolladores en 3 equipos de 2**, dueños de módulos |
| Punto de partida | Sin código ni stack | **Sprint 0 terminado**: arquitectura construida y verificada ([Sprint0-HelloWorld.md](../arquitectura/Sprint0-HelloWorld.md)) |
| Stack | Por definirse | **Decidido**: Angular 22, FastAPI, PostgreSQL 16, Alembic, Docker y GitHub Actions |
| Alcance | Corte completo hasta el alta en flota | **Primera mitad del corte** (hasta la compra y la importación) más la base contable y la preparación del ingreso. El taller, la hoja de costo y el alta pasan al Sprint 2 |
| HT-01 | 3 días | **1 día**: solo falta el ambiente de pruebas desplegado |

Se conservan de la v3 los criterios de cada historia en su versión delgada, la medición por criterios aceptados y las reglas del día 1.

## 2. Objetivo

**Un usuario autenticado registra la compra en USD de una unidad por VIN y sus gastos de importación; cada paso genera su partida y queda auditado; el contador revisa partidas sin poder aprobar las suyas; se registran las facturas locales de proveedores; y la línea de ingreso queda lista para contratar (perfil fiscal, clientes, tarifario y base del front).**

```text
Equipo A:  sesión y roles → catálogo y dimensiones → motor contable → partida manual y revisión → bitácora
Equipo B:  VIN → tipo de cambio → proveedor → compra USD → gastos de importación → etapas → facturas locales
Equipo C:  base del front (login, menú por rol, componentes) → perfil fiscal → clientes → tarifario → adaptador FEL → prueba de punta a punta
```

## 3. Fechas y capacidad

| Dato | Valor |
|---|---|
| Sprint | Lunes 02/11 a viernes 13/11/2026 |
| K1 y puesta al día del equipo | Lunes 02/11 |
| Integración | Miércoles 11/11: la compra pasa por todas las capas en el ambiente de pruebas |
| Demo y retrospectiva | Viernes 13/11 |
| Equipo | 6 desarrolladores: equipos A, B y C, cada uno con una persona del equipo original y una nueva |
| Capacidad bruta | 6 × 10 = 60 días-persona |
| Ceremonias | 6 días-persona |
| Capacidad planificable | 54 días-persona |
| Trabajo estimado | **46.5 días-persona**, con K1, puesta al día y pruebas |
| Margen | **7.5 días-persona (14 %)**, para la incorporación de las personas nuevas |

## 4. K1 · Sesión técnica de arranque (lunes 02/11)

**Ya decidido** (no se discute de nuevo):
1. Stack y arquitectura: monolito modular según [Arquitectura-Propuesta.md](../arquitectura/Arquitectura-Propuesta.md) y las reglas de `CLAUDE.md` / `AGENTS.md`.
2. Precisión monetaria: `Decimal` y `NUMERIC(18,6)`; los montos viajan como texto y el front no calcula.
3. Migraciones con Alembic y CI contra PostgreSQL en cada pull request.
4. Permisos en el servidor, desde un solo lugar (módulo `seguridad`).
5. Servicio único de contabilización en el módulo `contabilidad`: documento y partida en la misma transacción.
6. Contrato entre equipos: el OpenAPI de FastAPI.

**Se decide en K1:**

| Decisión | Opciones | Bloquea |
|---|---|---|
| Auditoría | Eventos de SQLAlchemy (como el prototipo descartado) o triggers de PostgreSQL (como `schema.sql`) | HU-1.11 (A) |
| Librería de componentes de Angular | Angular Material u otra con tabla, formulario y árbol | Base del front (C) |
| Ambiente de pruebas desplegado | Proveedor y forma de despliegue desde `main` | HT-01 (A) |
| Prueba de punta a punta | Playwright u otra, integrada en CI | Prueba del recorrido (C) |
| Tipos de TypeScript desde el OpenAPI | Herramienta y dónde se generan | Todos los equipos |
| Contrato del motor contable | Entradas, salidas y errores del servicio que B y C usarán para pedir partidas | B y C desde la primera semana |

**Puesta al día de las 3 personas nuevas:** lectura de `CLAUDE.md`, de la arquitectura y del hello world; cada una levanta el ambiente con `docker compose up --build` y hace un primer pull request pequeño en su módulo.

### Supuestos por validar

| Tema | Supuesto de trabajo | Fecha y responsable |
|---|---|---|
| Catálogo y reglas | Catálogo semilla suficiente para la compra y la importación | 04/11, contador y equipo A |
| Usuario operativo | El auxiliar contable registra compra, gastos, clientes y tarifas | 04/11, responsable del negocio |
| Moneda | Quetzal como moneda funcional; compra en USD; tipo de cambio manual por fecha | 04/11, contador |
| Agente de retención | La empresa no retiene IVA ni ISR | **13/11**, contador (afecta el Sprint 3) |
| Certificador FEL | Se elige con credenciales de pruebas | **20/11**, responsables del proyecto |

## 5. Alcance por historia

Versión delgada de cada historia; los criterios completos están en `user-stories/`. **SP** según el [plan v5](PlanMVP.md).

| Historia | SP | Equipo | Incluye en el Sprint 1 | Queda pendiente |
|---|---|---|---|---|
| HT-01 Infraestructura (resto) | 1 | A | Ambiente de pruebas desplegado desde `main`; tipos de TypeScript generados desde el OpenAPI | Operación productiva y observabilidad |
| HU-1.09 Usuarios y roles | 2 | A | Login real con hash, sesión, cierre de sesión, cuatro roles, permisos en el servidor y cuentas iniciales | Administración visual, bloqueo por intentos e inactividad (Sprint 2) |
| HU-1.11 Bitácora | 2 | A | Automática para las entidades del alcance, sin edición ni borrado por la API; valores anteriores y nuevos; filtros por usuario, VIN y entidad | Exportación |
| HU-1.10 Separación de funciones | 3 | A | Quien registra una partida manual no la contabiliza; rechazo con motivo | Límites monetarios de aprobación |
| HU-2.01 Partida manual | 3 | A | Captura desde pantalla, en quetzales y USD, con dimensiones y validación de cuadre | Adjuntos |
| HU-2.02 Revisión de partidas | 3 | A | Borrador, revisión, contabilizada o devuelta; corrección y reenvío; correlativo | Lotes |
| HU-1.02 Catálogo de cuentas | 3 | A | Semilla, consulta jerárquica y alta mínima con tipo, naturaleza y cuenta monetaria | Máscara de niveles e inactivación |
| HU-1.04 Dimensiones | 2 | A | Línea de negocio y exigencia de VIN por cuenta | Configuración avanzada |
| HU-1.05 Unidades por VIN | 3 | B | Validación, unicidad, ficha mínima, estados e historial | Placa, motor y expediente |
| HU-1.06 Tipo de cambio | 2 | B | Carga manual positiva por fecha; bloqueo si falta | Servicio del Banguat |
| HU-1.07 Transacciones en USD | 3 | B | Monto original, tipo de cambio y equivalente en quetzales; tipo personalizado positivo con justificación | Resto de criterios originales |
| HU-4.01 Proveedores | 1 | B | Alta y consulta, local o del exterior; NIT local validado | Régimen y retenciones |
| HU-4.02 Compra en EE. UU. | 4 | B | Pantalla de compra en USD que crea la unidad, la cuenta por pagar y la partida | Adjuntos |
| HU-4.04 Gastos de importación | 3 | B | Gastos por VIN; el IVA de importación se separa del costo | Expediente, prorrateo y DUCA |
| HU-4.07 Etapas de importación | 2 | B | Tránsito, aduana, taller y lista, con validación y auditoría | DUCA y métricas |
| HU-4.09 Facturas de compras y gastos locales | 5 | B | Captura del DTE (serie, número, autorización, proveedor, líneas con cuenta, línea de negocio y VIN, base e IVA); sin duplicados por proveedor; pequeño contribuyente sin crédito fiscal; genera la cuenta por pagar y su partida | Importar el XML del DTE; libro de compras (con HU-2.15) |
| HU-1.01 Perfil fiscal | 3 | C | Razón social, nombre comercial, NIT validado, dirección y establecimiento; régimen de ISR y agente de retención; vigencia por cambio; solo contador y gerente financiero lo modifican | Lo que dependa de confirmar el régimen exacto con el contador |
| HU-6.01 Clientes | 3 | C | Individual o empresa, NIT o CUI (pasaporte y país para extranjeros), contacto, agente de retención; NIT validado con dígito verificador; sin duplicados | Consulta del nombre en la SAT mediante el certificador; estado de cuenta integrado (Sprint 3) |
| HU-3.05 Tarifario de alquiler | 3 | C | Modalidad (diaria, semanal, mensual o por kilometraje), moneda, monto, kilometraje incluido y adicional, vigencia; por tipo de vehículo y, como excepción, por unidad; un cambio no afecta contratos firmados | Aprobación de descuentos por encima del porcentaje configurado |
| | **51** | | | |

**Partidas de la compra y de los gastos:** en el Sprint 1 el equipo B las pide al servicio de `contabilidad` según el contrato de K1. Si el servicio completo (HU-2.03, Sprint 2) aún no está, se usa la versión mínima del motor contable de A; no se escriben partidas desde el módulo `compras`.

## 6. Tareas por equipo

Cada estimación incluye sus pruebas. Días-persona.

### Equipo A · Plataforma y contabilidad — 17 días (capacidad 18)

| ID | Tarea | Historias | Días |
|---|---|---|---|
| K1 | Decisiones, contratos y puesta al día | — | 2 |
| A1 | Ambiente de pruebas desplegado y tipos de TypeScript desde el OpenAPI | HT-01 | 1 |
| A2 | Login, sesión, cuentas iniciales y matriz de permisos en el servidor | HU-1.09 | 3 |
| A3 | Auditoría automática con valores anteriores y nuevos, y consulta filtrada | HU-1.11 | 2.5 |
| A4 | Motor contable: servicio único, transacción atómica, líneas en USD, correlativo y pruebas de cuadre | HU-2.01, HU-2.02 | 3 |
| A5 | Flujo manual: borrador, devuelta, revisión, rechazo y aprobación separada | HU-1.10 | 1.5 |
| A6 | Catálogo y dimensiones: semilla, consulta y alta mínima, con pantalla | HU-1.02, HU-1.04 | 2.5 |
| A7 | Pantalla de captura de partida y bandeja de aprobación | HU-2.01, HU-2.02 | 1.5 |

### Equipo B · Ciclo de la unidad — 14 días (capacidad 18)

| ID | Tarea | Historias | Días |
|---|---|---|---|
| K1 | Decisiones, contratos y puesta al día | — | 2 |
| B1 | VIN, ficha mínima, estados e historial, con pantalla | HU-1.05 | 2 |
| B2 | Tipo de cambio manual y reglas multimoneda, con pantalla | HU-1.06, HU-1.07 | 1.5 |
| B3 | Proveedores: servicio y formulario mínimo | HU-4.01 | 0.5 |
| B4 | Compra en USD: unidad, cuenta por pagar y partida desde pantalla | HU-4.02 | 2 |
| B5 | Gastos de importación con IVA separado | HU-4.04 | 1.5 |
| B6 | Etapas de importación con validación | HU-4.07 | 1 |
| B7 | Facturas de compras y gastos locales, con su cuenta por pagar y su partida | HU-4.09 | 2 |
| B8 | Pruebas de estados, precisión monetaria y reversa de la compra | — | 1.5 |

El margen de B (4 días) cubre la dependencia del motor contable de A: si A4 se atrasa, B adelanta la captura de B4, B5 y B7 y conecta las partidas al final.

### Equipo C · Ingreso — 15.5 días (capacidad 18)

| ID | Tarea | Historias | Días |
|---|---|---|---|
| K1 | Decisiones, contratos y puesta al día | — | 2 |
| C1 | Base del front: login conectado, interceptor del token, guard y menú por rol; componentes de tabla, formulario y árbol | HU-1.09 (pantalla) | 3 |
| C2 | Prueba automatizada del recorrido desde la interfaz, integrada en CI | — | 2 |
| C7 | Perfil fiscal de la empresa: servicio y pantalla (antes que los clientes) | HU-1.01 | 1.5 |
| C3 | Clientes: servicio y pantalla | HU-6.01 | 1.5 |
| C4 | Tarifario de alquiler: servicio y pantalla | HU-3.05 | 1.5 |
| C5 | Adaptador FEL: interfaz, simulador y evaluación de certificadores con credenciales de pruebas | HU-6.02 (preparación) | 3 |
| C6 | Vista de la bitácora | HU-1.11 (pantalla) | 1 |

### Resumen de carga

| Equipo | Trabajo | Capacidad | Margen |
|---|---|---|---|
| A | 17 | 18 | 1 |
| B | 14 | 18 | 4 |
| C | 15.5 | 18 | 2.5 |
| **Total** | **46.5** | **54** | **7.5** |

El margen de A es el más corto y A está en el camino crítico (sesión y motor contable). Si se atrasa, B o C toman A6 (catálogo) o A7 (pantallas de partidas), que no requieren el contexto del motor.

## 7. Calendario

| Día | Qué |
|---|---|
| Lun 02/11 | K1 y puesta al día; ambiente levantado por las 6 personas |
| Mié 04/11 | Sesión con el contador: catálogo, dimensiones, VIN y reglas de la compra |
| Jue 05/11 | Login real y menú por rol funcionando en el ambiente de pruebas; contrato del motor contable publicado |
| Lun 09/11 | Partida manual y revisión funcionando; la compra empieza a pedir partidas |
| Mié 11/11 | **Integración**: la compra en USD con su partida y sus gastos pasa por todas las capas en el ambiente de pruebas. Sesión con el contador: importación e IVA |
| Vie 13/11 | **Demo**, aceptación por criterios y retrospectiva; se mide la velocidad real para recalcular el plan |

## 8. Definición de terminado del Sprint 1

1. Se inicia sesión con los cuatro roles y cada uno respeta sus permisos en el servidor.
2. La compra en USD y los gastos de importación se registran desde el navegador, en el ambiente de pruebas, y cada uno genera su partida en la misma transacción.
3. Una unidad no se duplica por VIN ni se salta las etapas de importación.
4. Las operaciones en USD guardan monto original, tipo de cambio positivo y equivalente en quetzales.
5. Un contador no puede aprobar su propia partida manual; otro usuario autorizado sí.
6. La bitácora registra actor, fecha y valores anteriores y nuevos de todas las entidades del sprint, sin exponer secretos.
7. Las migraciones se aplican desde una base vacía y todas las pruebas, incluida la del recorrido desde la interfaz, pasan en CI.
8. El contador valida el caso de la compra y de los gastos de importación.

## 9. Guion de la demo (13/11, 15 minutos)

1. **Sesión y permisos:** el auxiliar inicia sesión y ve sus restricciones; luego el contador.
2. **Preparación:** catálogo de cuentas y tipo de cambio de 7.70 del día de la compra.
3. **Compra:** vehículo con VIN válido por USD 8,500; se ven la unidad en tránsito, la cuenta por pagar y la partida (Q65,450).
4. **Importación:** flete de USD 900 a 7.72 y DAI de Q3,000; el IVA se registra aparte del costo; la unidad pasa a aduana.
5. **Separación de funciones:** el contador prepara una partida manual, no puede aprobarla, y la aprueba el gerente financiero.
6. **Control:** bitácora del VIN con valores anteriores y nuevos.
7. **Compra local:** se registra la factura FEL de un proveedor local de repuestos con su cuenta por pagar; el IVA va al crédito fiscal.
8. **Ingreso:** se registran el perfil fiscal de la empresa, un cliente y la tarifa de un sedán; se muestra una factura de prueba contra el simulador del adaptador FEL.

Los importes son datos de demostración sujetos a validación del contador.

## 10. Riesgos del sprint

| Riesgo | Respuesta |
|---|---|
| Las personas nuevas tardan en rendir | Parejas mixtas, primer pull request pequeño el lunes, margen del 14 % |
| El motor contable (A4) se atrasa y bloquea la compra (B4) | Contrato publicado el jueves 05/11; B avanza con B7 y B8 mientras tanto |
| Las decisiones de K1 se alargan | Se cierran el lunes 02/11; si no hay acuerdo, decide el dueño del módulo afectado |
| Integración tardía entre equipos | Integración obligatoria el miércoles 11/11 en el ambiente de pruebas; nada se demuestra sin persistencia |
| Ambiente de pruebas no desplegado a tiempo | La demo se hace con `docker compose` en una máquina y el despliegue pasa al lunes 16/11 |
