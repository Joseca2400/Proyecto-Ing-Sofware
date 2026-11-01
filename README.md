# Proyecto-Ing-Sofware

Sistema administrativo y financiero para una empresa guatemalteca de alquiler, venta y taller de vehículos importados de EE. UU.

Arquitectura: monolito modular con front en Angular, API en FastAPI y PostgreSQL ([docs/arquitectura/Arquitectura.md](docs/arquitectura/Arquitectura.md)). Para contribuir, lee [CONTRIBUTING.md](CONTRIBUTING.md).

## Levantar todo

```bash
docker compose up --build
```

| Servicio | URL |
|---|---|
| Front (Angular) | http://localhost:4200 |
| API (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 (usuario, clave y base: `sistema`) |

Si algún puerto está ocupado, cópialo de `.env.example` a `.env` y cámbialo (`API_PORT`, `WEB_PORT`, `DB_PORT`). Para trabajar sin Docker, ver [backend/README.md](backend/README.md) y [frontend/README.md](frontend/README.md).

## Estructura

| Carpeta | Contenido |
|---|---|
| [`backend/`](backend/README.md) | API FastAPI: `comun/` + `modulos/`, migraciones Alembic y pruebas |
| [`frontend/`](frontend/README.md) | Angular: `core/`, `shared/` y `features/` |
| [`docs/arquitectura/`](docs/arquitectura/Arquitectura.md) | Arquitectura vigente, decisiones y lo construido en el Sprint 0 |
| [`docs/planning/`](docs/planning/README.md) | Épicas, historias, plan del MVP, sprints y PDF del plan |
| [`docs/herramientas/`](docs/herramientas/README.md) | Generador de las tablas del plan y de los PDF |
| `.github/` | CI (estilo, pruebas y build), CODEOWNERS y plantilla de pull request |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Flujo de trabajo del equipo |
| `CLAUDE.md` · `AGENTS.md` | Guía para agentes de código |
