# Backend · FastAPI + PostgreSQL

## Desarrollo

Requiere Python 3.12 o superior.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://sistema:sistema@localhost:5432/sistema   # o docker compose up db
alembic upgrade head
uvicorn app.main:app --reload       # http://localhost:8000/docs
pytest -q                           # sin DATABASE_URL usa SQLite temporal
```

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
