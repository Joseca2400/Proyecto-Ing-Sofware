# Backend · FastAPI + PostgreSQL

## Desarrollo

Requiere Python 3.12 o superior y PostgreSQL. La forma más simple de tener la base es la del compose.

```bash
docker compose up -d db             # desde la raíz: PostgreSQL 16 en localhost:5432
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head                # usa DATABASE_URL; por defecto la base "sistema" del compose
uvicorn app.main:app --reload       # http://localhost:8000/docs
pytest -q                           # usa TEST_DATABASE_URL; por defecto crea "sistema_pruebas"
ruff check . && ruff format .      # estilo (config en pyproject.toml)
```

Solo se admite PostgreSQL: la API no arranca si `DATABASE_URL` apunta a otro motor.

## S1 · Equipo A: catálogo, dimensiones y auditoría

HU-1.02 y HU-1.04: el alta de cuentas valida código (1–30 caracteres) y nombre
(1–200), después de quitar espacios exteriores. Un código duplicado devuelve 409,
incluso con solicitudes concurrentes. Las dimensiones rechazan un VIN vacío o con
solo espacios cuando es obligatorio, y un VIN informado cuando la cuenta indica
`no_aplica`. La validación de existencia de la unidad corresponde a la integración
con el servicio de unidades del equipo B.

HU-1.11: aplicar `alembic upgrade head` **antes de cargar semillas o utilizar la API**.
La migración `d5f18a6e0c47` instala la bitácora y los triggers de `usuarios` y `cuentas`.
Registra altas, cambios y bajas dentro de la misma transacción, tanto mediante ORM
como mediante SQL. Un rollback revierte también sus registros de auditoría.
La migración no reconstruye el historial de datos que ya existían.

Seguridad fija el actor autenticado en la sesión de base de datos; el cliente no
puede enviarlo en el cuerpo de la operación. El contexto es local a la transacción
y se restablece al reutilizar conexiones. Las semillas y operaciones de sistema sin
usuario tienen `usuario_id = null`; un proceso con identidad conocida debe usar
`comun.db.fijar_actor` con la identidad verificada por seguridad.

Solo se copian columnas expresamente permitidas por cada trigger. `clave_hash` y
la tabla `sesiones` quedan excluidos: no se guardan contraseñas, hashes ni tokens.
No hay rutas para escribir la bitácora y PostgreSQL rechaza UPDATE, DELETE y TRUNCATE.

Consulta para contador y gerente financiero:

```text
GET /api/v1/seguridad/bitacora?usuario_id=1&entidad=cuentas&limite=100&desplazamiento=0
```

También admite `vin` y ordena del registro más reciente al más antiguo; `limite`
admite 1–200. La política `cuentas.vin` (`obligatorio`, `opcional`, `no_aplica`) no se
confunde con el VIN de un vehículo. Para nuevas entidades, su migración debe crear
un trigger INSERT/UPDATE/DELETE que invoque `public.registrar_cambio` con la lista
de columnas públicas, incluyendo `id` y, cuando corresponda, `vin`. Esto se debe
hacer antes de habilitar escrituras en esa entidad.
`tests/test_migraciones.py` falla si una tabla queda sin ese trigger o si dos ramas dejan
más de una cabeza de migración. Las migraciones de este equipo usan identificador aleatorio
(`alembic revision --autogenerate` ya lo genera) para no chocar con las de otros equipos;
quien se integre después apunta su `down_revision` a la última cabeza.

Esta corrección cubre las entidades implementadas por A. El motor contable, el flujo
de aprobación y las pantallas pendientes de S1 siguen siendo trabajo separado. La
vista de bitácora corresponde al equipo C; exportación queda diferida según el sprint.

## Organización

```
app/
├── main.py              crea la API y registra los routers bajo /api/v1
├── comun/               config, db (Base, get_db), dinero (Decimal), errores ({detail})
└── modulos/
    └── sistema/         hola mundo: GET /api/v1/sistema/estado
        ├── router.py    endpoints
        ├── schemas.py   contratos (Pydantic)
        ├── service.py   reglas; única puerta para otros módulos
        └── models.py    tablas (cuando el módulo las tenga)
migrations/              Alembic; 0001 es la línea base
tests/
```

Para agregar un módulo: crear `app/modulos/<modulo>/` con esos archivos, registrar su router en `main.py`, importar sus `models` en `app/modulos/__init__.py` y generar la migración con `alembic revision --autogenerate -m "<cambio>"`.
