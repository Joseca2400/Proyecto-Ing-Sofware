# Cómo trabajamos

Guía del equipo para construir el sistema sobre `main` sin pisarnos. Las reglas técnicas de la arquitectura están en [docs/arquitectura/Arquitectura.md](docs/arquitectura/Arquitectura.md); los comandos, en el [README](README.md).

## Equipos y dueños de módulo

Cada equipo es dueño de sus módulos de punta a punta: pantalla en `frontend/src/app/features/`, API en `backend/app/modulos/`, migraciones y pruebas. El reparto completo está en la sección 2 de [PlanMVP.md](docs/planning/PlanMVP.md).

| Equipo | Módulos |
|---|---|
| A · Plataforma y contabilidad | `seguridad`, `comun` (auditoría), `contabilidad`, `configuracion` (catálogo, dimensiones, bancos) |
| B · Ciclo de la unidad | `unidades`, `compras`, `taller`, `ventas`, `configuracion` (tipo de cambio), `reportes` (rentabilidad) |
| C · Ingreso | `core/` y `shared/` del front, `alquileres`, `facturacion`, `financiamiento`, `configuracion` (perfil fiscal) |

Para cambiar un módulo de otro equipo, se acuerda con ese equipo antes de abrir el pull request. `.github/CODEOWNERS` le pide la revisión automáticamente.

## Flujo de trabajo

1. **Una rama por historia**, desde `main` actualizado: `hu-4.02-compra-usd`, `hu-1.09-login`. Para trabajo sin historia: `tec-…` (técnico) o `doc-…` (documentación).
2. **Commits pequeños en español**, en imperativo y con el identificador de la historia: `HU-4.02: registrar la compra en USD con su partida`.
3. **Pull request a `main`** con la plantilla completa. Nadie hace push directo a `main`.
4. **La CI debe pasar**: estilo (ruff, prettier, eslint), pruebas del backend contra PostgreSQL y pruebas y build del front.
5. **Una aprobación** del equipo dueño del módulo (y de otro equipo si el cambio cruza módulos). Se mezcla con *squash*.
6. Integrar seguido: una rama no debería vivir más de dos o tres días. La integración del miércoles de la segunda semana de cada sprint pasa en el ambiente de pruebas.

## Definición de terminado de una historia

- Cumple los criterios incluidos en el sprint, desde la pantalla.
- Pruebas de reglas, permisos y casos de rechazo, en verde en la CI.
- Los cambios de sus entidades quedan en la bitácora.
- La migración se aplica desde una base vacía (`alembic upgrade head`).
- Los criterios diferidos quedan anotados con su sprint de destino.

## Agregar un módulo

**Backend**

1. Crear `backend/app/modulos/<modulo>/` con `router.py`, `schemas.py`, `service.py` y `models.py`.
2. Registrar el router en `backend/app/main.py` bajo `/api/v1`.
3. Importar sus `models` en `backend/app/modulos/__init__.py` y generar la migración: `alembic revision --autogenerate -m "<cambio>"`.
4. Otros módulos solo llaman a su `service.py`. Las partidas se piden al servicio de `contabilidad`.

**Frontend**

1. `npx ng generate component features/<modulo>/<pantalla>` y un `features/<modulo>/<modulo>.service.ts` para las llamadas a la API.
2. Registrar la ruta en `app.routes.ts` (con `loadComponent`) y la entrada del menú en `core/layout/layout.ts`.

## Documentación

| Qué cambia | Dónde |
|---|---|
| Criterios, MoSCoW o dependencias de una historia | `docs/planning/user-stories/` |
| Sprint, equipo o SP de una historia | `docs/planning/sprints.json` y luego `python3 docs/herramientas/generar_plan.py` |
| Detalle del sprint en curso | `docs/planning/sprints/` (uno por sprint, desde `plantilla.md`) |
| Una decisión de arquitectura | Sección 8 de `docs/arquitectura/Arquitectura.md` |
| Reglas para agentes de código | `CLAUDE.md` y `AGENTS.md`, siempre iguales y en el mismo commit |

Lo que se reemplaza pasa a la carpeta `Old/` de su sección; no se borra el historial de planeación.
