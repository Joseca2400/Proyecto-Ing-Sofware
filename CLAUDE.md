# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

`AGENTS.md` es una copia de este archivo para otros agentes: si cambias uno, actualiza el otro en el mismo commit.

Sistema administrativo y financiero para una empresa guatemalteca de alquiler, venta y taller de vehículos importados de EE. UU. (GTQ y USD). Código, nombres, documentación y mensajes de commit en **español**. El flujo de trabajo del equipo (ramas por historia, pull requests, dueños de módulo, definición de terminado) está en `CONTRIBUTING.md`.

## Comandos

Ambiente completo (PostgreSQL 16, API y front): desde la raíz, `docker compose up --build` → front en http://localhost:4200, Swagger en http://localhost:8000/docs. Si un puerto está ocupado: `API_PORT=8001 docker compose up` (también `WEB_PORT`, `DB_PORT`; ver `.env.example`).

Backend (`backend/`, Python ≥ 3.12; el Python del sistema en macOS es 3.9 y no sirve):

```bash
docker compose up -d db                              # desde la raíz: la base que usan desarrollo y pruebas
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
pytest -q                                            # todas
pytest tests/test_sistema.py::test_health_responde   # una sola
alembic revision --autogenerate -m "<cambio>"        # tras agregar o cambiar models
alembic check                                        # modelos y migraciones sincronizados
ruff check . && ruff format --check .                # estilo (config en pyproject.toml); ruff format . para corregir
```

Las pruebas usan `TEST_DATABASE_URL` (por defecto la base `sistema_pruebas` del compose): `tests/conftest.py` la crea si falta, la vacía (`DROP SCHEMA public CASCADE`) y la migra en cada corrida. Nunca apuntarla a la base de desarrollo.

Frontend (`frontend/`, Angular 22, pruebas con Vitest):

```bash
npm start                                                          # ng serve; proxy.conf.json reenvía /api a :8000
npx ng test --watch=false                                          # todas
npx ng test --watch=false --include src/app/shared/pipes/monto.pipe.spec.ts   # una sola
npm run build
npm run lint                                                       # angular-eslint
npm run format:check                                               # prettier; npm run format para corregir
```

CI (`.github/workflows/ci.yml`) en cada push y PR: estilo (ruff, prettier, eslint), `pytest` contra un servicio PostgreSQL y `ng test` + `ng build` del front.

Plan y PDF: después de cambiar `docs/planning/sprints.json` o `user-stories/`, ejecutar `python3 docs/herramientas/generar_plan.py` (ver `docs/herramientas/README.md`). Las tablas de sprints de `PlanMVP.md` se generan; no se editan a mano.

## Arquitectura

Monolito modular: **Angular → (Nginx, proxy `/api`) → FastAPI → PostgreSQL 16**. Diseño completo, diagramas C4 y decisiones (ADR, sección 8) en `docs/arquitectura/Arquitectura.md`; lo construido en el Sprint 0 en `docs/arquitectura/Sprint0-HelloWorld.md`.

El backend y el front se organizan por **los mismos módulos de negocio** (uno o más por épica: `seguridad`, `configuracion`, `contabilidad`, `unidades`, `compras`, `taller`, `facturacion`, `alquileres`, `ventas`, `financiamiento`, `arranque`, `reportes`), para que cada equipo trabaje sus módulos de punta a punta. Hoy solo existe el módulo `sistema` (hello world: `GET /api/v1/sistema/estado`).

### Backend (`backend/app/`)

- `main.py` crea la app, define `/health` y registra cada router bajo `/api/v1`.
- `comun/` no depende de ningún módulo: `config.py` (variables de entorno), `db.py` (`Base`, `get_db`), `dinero.py`, `errores.py` (`ErrorNegocio` → `{"detail": ...}`).
- `modulos/<modulo>/` con `router.py` → `service.py` → `models.py`, más `schemas.py` (Pydantic).

Reglas de dependencia:
1. Un router nunca toca la base directamente; delega en su `service`.
2. Un módulo solo importa el `service.py` de otro módulo, nunca sus `models`.
3. **Solo `contabilidad` crea partidas**; los demás módulos se las piden a su `service`. El documento y su partida se confirman en la misma transacción.
4. Solo `seguridad` decide permisos; la autorización se aplica en el servidor (ocultar opciones en el front no la sustituye).
5. `reportes` solo lee.

Para agregar un módulo: crear la carpeta, registrar el router en `main.py`, importar sus `models` en `app/modulos/__init__.py` (Alembic los descubre desde ahí) y generar la migración.

### Frontend (`frontend/src/app/`)

- `core/`: se carga una vez (`api/api.ts` con el prefijo `/api/v1`, `layout/` con barra y menú; luego `auth/` con interceptor y guard por rol).
- `shared/`: sin lógica de negocio (componentes, `pipes/monto.pipe.ts`).
- `features/<modulo>/`: una carpeta por módulo, cargada con `loadComponent` en `app.routes.ts` como hija del `Layout`; su entrada de menú va en `core/layout/layout.ts`.
- Convenciones de Angular 22: componentes standalone, `inject()`, signals, `@if`/`@for`; archivos sin sufijo `.component` (`inicio.ts`, `inicio.html`).
- Un componente usa el servicio de su módulo (`features/<modulo>/<modulo>.service.ts`), nunca `HttpClient` directo.

## Reglas del dominio

- **Solo PostgreSQL.** No hay respaldo con SQLite: `comun/config.py` rechaza cualquier otro motor. Las URLs usan el driver `postgresql+psycopg://`.
- **Dinero sin punto flotante:** `Decimal` en Python (`comun/dinero.py` rechaza `float`), columnas `MONTO` = `NUMERIC(18,6)` y `TIPO_CAMBIO` = `NUMERIC(18,8)`, redondeo explícito mitad hacia arriba. En JSON los montos viajan como **texto** y el front solo les da formato con `MontoPipe`; nunca suma ni convierte monedas.
- **El VIN es el hilo conductor:** compra, importación, taller, alta, alquiler y venta se ligan a la unidad.
- **Auditoría automática** en la capa de persistencia (actor, fecha, entidad, VIN, valores anteriores y nuevos), dentro de la misma transacción; nunca guarda contraseñas, hashes ni tokens. Debe existir antes de la primera tabla de negocio (HU-1.11).
- Integraciones externas (FEL/SAT, tipo de cambio del Banguat) van detrás de adaptadores en `comun/`.

## Planeación

`docs/planning/` es la fuente de requisitos: épicas en `contexto/epicas.md`, historias (`HU-x.yy`) con criterios de aceptación en `user-stories/E01…E10`, reparto de historias por sprint y equipo en `sprints.json` (fuente única), plan vigente en `PlanMVP.md` (3 equipos dueños de módulos, MVP al cierre del Sprint 3) y detalle de cada sprint en `sprints/` (el actual es `sprint-01.md`). `docs/planning/Old/` es historial. Al implementar una historia, citar su identificador, respetar lo que el sprint marca como incluido o diferido y no tocar módulos de otro equipo sin acordarlo (dueños en `PlanMVP.md`, sección 2).

## Prototipos anteriores

Los dos prototipos descartados (Express con PostgreSQL y FastAPI con SQLite) ya no están en el repositorio. Si hace falta consultarlos (reglas y pruebas del corte del Sprint 1, restricciones y triggers de `schema.sql`, diseño visual de la maqueta), están en la etiqueta de git `legacy-prototipos`: `git show legacy-prototipos:old/<ruta>`. Se rescatan ideas, no se copia código.
