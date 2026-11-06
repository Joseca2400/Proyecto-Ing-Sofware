# Auditoría del motor contable — 6 de noviembre de 2026

Rama: `hu-2.01-motor-contable`. Commit auditado: `8276b43`; comparación con `main` local en `52c79f5`. Las correcciones de esta auditoría quedan en el árbol de trabajo, sin commit ni publicación.

**Resultado:** el backend corregido está listo para revisión técnica del equipo. No representa todavía la entrega completa desde pantalla de HU-2.01/HU-2.02 ni la integración de compras. El commit original tenía defectos de integridad pese a aprobar sus 210 pruebas existentes.

## Hallazgos corregidos

| Prioridad | Hallazgo y reproducción | Corrección |
|---|---|---|
| P1 | Un `UPDATE` podía trasladar una línea de un borrador a una partida contabilizada; el trigger solo consultaba la cabecera anterior. | Se comprueban y bloquean ambas cabeceras. Las escrituras de líneas también esperan las contabilizaciones concurrentes. |
| P1 | Un `INSERT` directo permitía una cabecera contabilizada, con número y sin líneas. El trigger solo vigilaba `UPDATE` y `DELETE`. | Se valida el cuadre también al insertar una cabecera contabilizada. |
| P1 | Una sesión que conservaba un borrador podía corregirlo después de que otra sesión lo enviara a revisión. Dos contabilizaciones de la misma partida podían validar un estado obsoleto. | Las mutaciones bloquean la cabecera y recargan su estado y líneas antes de validar. La segunda contabilización recibe un conflicto de negocio. |
| P2 | Un VIN corto o largo llegaba a PostgreSQL y provocaba un error 500. | Validación de 17 caracteres antes de persistir, conservando normalización y reglas de dimensiones. |
| P2 | Un monto USD válido podía producir un equivalente GTQ que excediera `NUMERIC(18,6)`, generando un error 500. | Se verifica el límite del equivalente antes y después del redondeo. |
| P2 | El rechazo de una diferencia de Q0.000001 decía «diferencia 0.00». | El mensaje conserva los seis decimales admitidos por el motor. |
| P2 | PostgreSQL aceptaba líneas USD sin monto original ni tipo de cambio: el `CHECK` evaluaba a `NULL`. | La restricción exige explícitamente ambos valores no nulos. |
| P2 | Cualquier `IntegrityError` al registrar una automática se anunciaba como documento duplicado, incluso una restricción distinta. | Solo la violación única `uq_partida_documento` se traduce a ese conflicto; se conserva la causa real de otros errores. |

Siete regresiones fallaron antes de las correcciones y pasaron después. El manejo demasiado amplio de `IntegrityError` se detectó por inspección y también quedó cubierto por una regresión.

Archivos de implementación: `backend/app/modulos/contabilidad/service.py`, `backend/app/modulos/contabilidad/models.py` y la nueva migración `backend/migrations/versions/0009_integridad_motor_contable.py`. La migración `0008` se conserva para permitir actualizar bases que ya la aplicaron.

## Pruebas y comprobaciones

| Comprobación | Resultado |
|---|---|
| Suite original del backend | 210 aprobadas |
| Suite final del backend | **222 aprobadas** en PostgreSQL 16 aislado |
| Nuevas regresiones | 12 casos en `backend/tests/test_contabilidad_auditoria.py` |
| Concurrencia real | Dos conexiones contabilizando la misma partida: una confirma y otra obtiene conflicto; partidas distintas: correlativos consecutivos; una escritura de líneas espera y se rechaza al quedar contabilizada |
| Auditoría | Actor y VIN conservados por la API; rollback de la automática elimina también sus registros de bitácora |
| Migraciones desde base vacía | Aplicadas por la preparación de pytest, incluida `0009` |
| Migración con datos existentes | `downgrade 0008` seguido de `upgrade head` aprobado sobre los datos de prueba |
| Modelos frente a migraciones | `alembic check` sin operaciones pendientes, antes y después del ciclo de migración |
| Backend: Ruff | Lint y formato aprobados |
| Frontend exacto de `HEAD` | **31 pruebas aprobadas**, ESLint, Prettier y build de producción aprobados |
| Planeación | `generar_plan.py --sin-pdf --estricto` aprobado y `PlanMVP.md` sin diferencias |
| Espacios y parches | `git diff --check` aprobado |

Entorno: Python 3.12.16, dependencias del backend en las versiones fijadas por el repositorio, Node 24.21.0 y PostgreSQL `16-alpine`. Se usó un contenedor temporal en el puerto 55439 y la base `sistema_audit_motor`; no se ejecutaron pruebas destructivas contra desarrollo. El frontend de `HEAD` se extrajo a un directorio temporal para verificarlo independientemente de los cambios locales de diseño detectados durante el trabajo. No se modificaron esos cambios.

El primer intento de conexión al puerto 5432 falló porque allí no existía el rol `sistema`; las pruebas se ejecutaron finalmente en el PostgreSQL temporal. Un build dentro del sandbox abortó; fuera de él finalizaron correctamente tanto el build del espacio de trabajo como el de la copia de `HEAD`.

## Pendientes que debe conocer el equipo revisor

- **HU-2.01/HU-2.02:** esta rama ofrece API y servicio; falta la pantalla de captura y revisión. La definición de terminado de `CONTRIBUTING.md` exige el recorrido desde pantalla.
- **HU-1.10:** el contador todavía puede registrar y contabilizar su propia partida. Está anotado como pendiente en el motor, pero sí pertenece al Sprint 1 como historia separada. Debe entregarse antes de considerar completo ese flujo.
- **Integración del equipo B:** `compras/service.py` todavía confirma facturas sin solicitar su partida; lo declara explícitamente como pendiente. Hay que conectar el contrato del motor y probar documento, cuenta por pagar y partida en una sola transacción antes de aceptar el recorrido de compras. No se alteraron módulos de ese equipo.
- **HU-2.03 completa:** el servicio mínimo no incluye reglas de contabilización configurables ni navegación visual en ambos sentidos; esas capacidades corresponden a su alcance posterior.
- Se mantienen los diferimientos documentados: adjuntos, lotes, límites de aprobación, reversión y períodos cerrados. No se evaluó un flujo de UI contable inexistente ni un despliegue productivo.

La nueva restricción USD rechaza datos inválidos que pudieran existir en una base ya modificada por SQL directo. La migración no inventa valores para corregirlos: deben revisarse si aparecen al actualizar.

## Reproducción

Con el entorno del backend instalado y un PostgreSQL 16 dedicado a pruebas, desde `backend/`:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://sistema:sistema@127.0.0.1:55439/sistema_audit_motor
pytest -q
ruff check .
ruff format --check .
DATABASE_URL="$TEST_DATABASE_URL" alembic check
```

`pytest` recrea el esquema de la base indicada: usar exclusivamente una base de pruebas. Para el frontend, desde `frontend/`, ejecutar los controles habituales del repositorio: `npm run lint`, `npm run format:check`, `npx ng test --watch=false` y `npm run build`.

Antes de publicar, incluir en el commit las correcciones, la migración `0009`, las pruebas y este informe. Solicitar revisión como backend del motor contable, dejando explícitos los pendientes anteriores. Esta auditoría no hizo commit, push ni envió solicitudes de revisión.
