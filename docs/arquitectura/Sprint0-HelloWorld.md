# Sprint 0 · Hello world de la nueva arquitectura

Versión 1 · 30/10/2026 · Lo que quedó construido sobre `main` con la [arquitectura propuesta](Arquitectura-Propuesta.md), y lo que sigue según el [Sprint 1](../planning/Sprint1.md).

## 1. Resumen

Se empezó de cero con la arquitectura propuesta: **Angular → FastAPI → PostgreSQL**, en un monolito modular. El hello world recorre todas las capas: la pantalla de Inicio llama a `GET /api/v1/sistema/estado` y la API responde con su versión, la conexión a la base y la revisión del esquema aplicada por Alembic.

Las dos implementaciones anteriores (el backend Express y el prototipo FastAPI con SQLite) quedaron descartadas en [`old/`](../../old/README.md) para borrarse más adelante.

Es la base técnica de **HT-01 Infraestructura** (tarea A1 del Sprint 1) y cumple los criterios mínimos del acuerdo 1 de K1, salvo lo que se marca como pendiente en la sección 4.

## 2. Qué se implementó

### Backend (`backend/`)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Arranque de la API | `app/main.py` | Crea la aplicación, `/health` y registra los módulos bajo `/api/v1` |
| Configuración | `app/comun/config.py` | Nombre, versión y `DATABASE_URL` desde variables de entorno |
| Base de datos | `app/comun/db.py` | Motor de SQLAlchemy, `Base` para las tablas y `get_db()` (una sesión por petición) |
| Dinero | `app/comun/dinero.py` | Tipos `NUMERIC(18,6)` y `NUMERIC(18,8)`, redondeo mitad hacia arriba, conversión USD→GTQ; rechaza `float` |
| Errores | `app/comun/errores.py` | `ErrorNegocio` con el formato común `{"detail": ...}` |
| Módulo `sistema` | `app/modulos/sistema/` | Primer módulo con las capas `router` → `service` → `schemas`; expone el estado del sistema |
| Migraciones | `migrations/`, `alembic.ini` | Alembic toma la URL de `DATABASE_URL`; la revisión `0001` es la línea base |
| Pruebas | `tests/` | 7 pruebas: health, estado con la base migrada, formato de error, redondeo, conversión y rechazo de `float` |
| Contenedor | `Dockerfile` | Python 3.13; al arrancar aplica las migraciones y levanta Uvicorn |

### Frontend (`frontend/`)

| Pieza | Archivo | Qué hace |
|---|---|---|
| Proyecto | Angular 22 (CLI) | Componentes standalone, signals, control de flujo `@if/@for`, pruebas con Vitest |
| Configuración | `app.config.ts`, `app.routes.ts` | `HttpClient` y rutas; cada módulo se carga solo cuando se usa |
| `core/api` | `api.ts` | Prefijo `/api/v1` común |
| `core/layout` | `layout.*` | Barra superior con la marca Kilómetro Cero y menú de módulos (los no construidos aparecen deshabilitados); se adapta a móvil |
| `shared/pipes` | `monto.pipe.ts` | Da formato a montos GTQ/USD que llegan como texto, sin pasar por `float` |
| `features/inicio` | `inicio.*` | Pantalla del hello world: estado del front, de la API y de la base, con reintento si la API no responde |
| Proxy | `proxy.conf.json`, `nginx.conf` | `/api` se reenvía a la API en desarrollo (`ng serve`) y en producción (Nginx) |
| Pruebas | `*.spec.ts` | 6 pruebas: la pantalla con respuesta y sin respuesta de la API, y el formato de montos |
| Contenedor | `Dockerfile` | Compila con Node 24 y sirve con Nginx |

### Raíz del repositorio

| Pieza | Qué hace |
|---|---|
| `docker-compose.yml` | Levanta `db` (PostgreSQL 16), `api` y `web` con un solo comando; la API espera a que la base esté lista; puertos configurables |
| `.github/workflows/ci.yml` | En cada push: pruebas del backend **contra PostgreSQL** y pruebas y build del front |
| `.env.example`, `.gitignore`, `README.md` | Credenciales locales, archivos ignorados y cómo levantar todo |
| `old/` | Las dos implementaciones descartadas, con un README de qué se puede rescatar |

## 3. Cómo se verificó

| Verificación | Resultado |
|---|---|
| `pytest` del backend contra PostgreSQL 16 (base `sistema_pruebas`, vaciada y migrada en cada corrida) | 7 de 7 pasan |
| `alembic upgrade head` y `alembic check` | Aplica `0001`; modelos y migraciones sincronizados |
| `ng test` del front | 6 de 6 pasan |
| `ng build` de producción | Compila: 247 kB inicial (69 kB comprimido); el módulo de Inicio va en un chunk aparte |
| `docker compose up --build` | Levanta `db`, `api` y `web`; la API aplica la migración al arrancar |
| Prueba de punta a punta en el navegador (Nginx → API → PostgreSQL) | La pantalla de Inicio muestra "Hola, mundo: la API responde" y "Conectada (postgresql) · revisión 0001" |

**Solo PostgreSQL.** No hay respaldo con SQLite: la API se niega a arrancar si `DATABASE_URL` apunta a otro motor, y las pruebas usan una base PostgreSQL aparte (`TEST_DATABASE_URL`) para no tocar la de desarrollo.

## 4. Pendiente de verificar

- **CI en GitHub**: el flujo no se ha ejecutado todavía; corre en el primer push.
- **Aviso de dependencias**: Starlette avisa que su cliente de pruebas pasará de `httpx` a `httpx2`. No afecta hoy; se cambia cuando la versión de FastAPI lo exija.
- **Puertos ocupados**: si el 8000, 4200 o 5432 ya están en uso, se cambian con `API_PORT`, `WEB_PORT` o `DB_PORT` (por ejemplo `API_PORT=8001 docker compose up`).

## 5. Qué sigue (propuesta para el Sprint 1)

El hello world deja lista la base; **no implementa ninguna historia de negocio todavía**. Este es el orden sugerido, siguiendo las dependencias del [Sprint 1](../planning/Sprint1.md#5-alcance-por-historia-versión-delgada):

| Orden | Qué | Historias | Módulos | Por qué en este orden |
|---|---|---|---|---|
| 1 | Cerrar la infraestructura: ambiente de pruebas desplegado y tipos de TypeScript generados desde el OpenAPI | HT-01 | raíz, `frontend/core/api` | Termina A1 y evita que el contrato se desincronice desde el primer endpoint |
| 2 | **Login, sesión, roles y permisos** en el servidor; interceptor del token y guard por rol en Angular | HU-1.09 | `seguridad`, `core/auth` | Todo lo demás exige saber quién opera y con qué rol |
| 3 | **Bitácora automática** con valores anteriores y nuevos | HU-1.11 | `comun/auditoria` | Debe existir antes de la primera tabla de negocio para que todo quede auditado |
| 4 | Catálogo de cuentas, dimensiones, tipo de cambio y transacciones en USD | HU-1.02, HU-1.04, HU-1.06, HU-1.07 | `configuracion`, `contabilidad` | Son los datos maestros que usan las partidas |
| 5 | **Partida manual, revisión y separación de funciones**; servicio único de contabilización | HU-2.01, HU-2.02, HU-1.10, HU-2.03 | `contabilidad` | Es el núcleo: los demás módulos le piden sus partidas |
| 6 | Unidades por VIN, proveedores, compra en EE. UU., gastos y etapas de importación | HU-1.05, HU-4.01, HU-4.02, HU-4.04, HU-4.07 | `unidades`, `compras` | Primer tramo del corte: la unidad entra con su costo |
| 7 | Orden de taller, tarifa, mano de obra y cierre | HU-5.01, HU-5.02, HU-5.03, HU-5.07 | `taller` | Capitaliza el reacondicionamiento al VIN |
| 8 | Hoja de costo, balance y mayor, y alta en flota | HU-4.08, HU-2.16, HU-3.01 | `unidades`, `contabilidad` | Cierra el corte y permite la demo final |

Del código descartado en `old/` conviene **rescatar, no copiar**: las reglas y pruebas del prototipo FastAPI (pasos 4 a 8) y las restricciones y triggers de `schema.sql` (paso 3), adaptados a la estructura de módulos.

**Decisiones abiertas para K1**: el proveedor del ambiente de pruebas desplegado, si la auditoría usa eventos de SQLAlchemy (como el prototipo) o triggers de PostgreSQL (como `schema.sql`), y la librería de componentes de Angular para tablas, formularios y árboles (por ejemplo, Angular Material).
