# Proyecto-Ing-Sofware

Sistema administrativo y financiero para una empresa guatemalteca de alquiler, venta y taller de vehículos importados de EE. UU.

Arquitectura: monolito modular con front en Angular, API en FastAPI y PostgreSQL ([docs/arquitectura/Arquitectura-Propuesta.md](docs/arquitectura/Arquitectura-Propuesta.md)).

## Levantar todo

```bash
docker compose up --build
```

| Servicio | URL |
|---|---|
| Front (Angular) | http://localhost:4200 |
| API (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 (usuario, clave y base: `sistema`) |

Para trabajar sin Docker, ver [backend/README.md](backend/README.md) y [frontend/README.md](frontend/README.md).

## Estructura

| Carpeta | Contenido |
|---|---|
| [`backend/`](backend/README.md) | API FastAPI: `comun/` + `modulos/`, migraciones Alembic y pruebas |
| [`frontend/`](frontend/README.md) | Angular: `core/`, `shared/` y `features/` |
| [`docs/planning/`](docs/planning/README.md) | Épicas, historias, User Story Mapping, plan de sprints y Sprint 1 |
| [`docs/arquitectura/`](docs/arquitectura/) | Arquitectura propuesta, diagramas C4 y reporte del Sprint 0 |
| `.github/workflows/ci.yml` | Pruebas del backend (contra PostgreSQL) y del front en cada push |
| [`old/`](old/README.md) | Implementaciones descartadas, solo como referencia; se borrarán |
