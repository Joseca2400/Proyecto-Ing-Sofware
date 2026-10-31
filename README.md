# Proyecto-Ing-Sofware

Sistema administrativo y financiero para una empresa guatemalteca de alquiler, venta y taller de vehículos importados de EE. UU.

La arquitectura objetivo es un monolito modular: front en Angular, API en FastAPI y PostgreSQL. Está descrita en [docs/arquitectura/Arquitectura-Propuesta.md](docs/arquitectura/Arquitectura-Propuesta.md).

## Estructura

| Carpeta | Contenido | Estado |
|---|---|---|
| [`backend/`](backend/README.md) | API FastAPI del Sprint 1, pruebas y script de demostración | En uso; pendiente reorganizar en módulos y pasar a PostgreSQL |
| [`frontend/`](frontend/README.md) | Front en Angular | Por crear |
| [`docs/planning/`](docs/planning/README.md) | Épicas, historias, User Story Mapping, plan de sprints y Sprint 1 | Vigente |
| [`docs/arquitectura/`](docs/arquitectura/) | Arquitectura propuesta, diagramas C4 y decisiones | Vigente |
| [`Aplicacion/`](Aplicacion/README.md) | Maqueta HTML y backend Express del Sprint 0 | Se retira; la maqueta es la referencia visual del front |
| `.github/workflows/` | CI: pruebas del backend en cada push | Activa |

## Levantar la API

```bash
cd backend
docker compose up -d --build
```

Documentación interactiva en http://localhost:8000/docs.
