# Arquitectura en modelo C4

Estado al 30/10/2026 (Sprint 1). Los diagramas usan la sintaxis C4 de Mermaid, que GitHub y VS Code (con la extensión de Mermaid) muestran directamente.

Hoy hay **dos implementaciones del backend** con el mismo contrato de API:

| Carpeta | Stack | Base de datos | Papel |
|---|---|---|---|
| `Aplicacion/` | Node.js, Express 5, `pg` | PostgreSQL | Maqueta HTML integrada con un backend con esqueleto (login, unidades y órdenes reales; el resto responde `501`) |
| `proyecto-vehiculos/backend/` | Python, FastAPI, SQLAlchemy | SQLite (archivo en un volumen Docker) | Prototipo técnico del corte del Sprint 1, completo, con pruebas y CI; es la **referencia del contrato** |

## Nivel 1 · Contexto del sistema

```mermaid
C4Context
    title Contexto · Sistema administrativo y financiero (Kilómetro Cero)

    Person(auxiliar, "Auxiliar", "Registra compras, gastos y unidades")
    Person(contador, "Contador", "Revisa, contabiliza y cierra períodos")
    Person(gerente, "Gerente financiero", "Aprueba operaciones")
    Person(gerencia, "Gerencia", "Solo consulta reportes y rentabilidad")

    System(sistema, "Sistema administrativo y financiero", "Contabilidad y control económico del ciclo del vehículo: importación, taller, alquiler y venta (GTQ y USD)")

    System_Ext(sat, "SAT / Certificador FEL", "Facturación electrónica en Guatemala (Release 1, aún no integrado)")
    System_Ext(banguat, "Banguat", "Tipo de cambio oficial GTQ/USD (diferido; hoy se captura a mano)")
    System_Ext(fuentes, "Google Fonts", "Tipografía Inter cargada por el navegador")

    Rel(auxiliar, sistema, "Registra", "HTTPS")
    Rel(contador, sistema, "Contabiliza y cierra", "HTTPS")
    Rel(gerente, sistema, "Aprueba", "HTTPS")
    Rel(gerencia, sistema, "Consulta reportes", "HTTPS")
    Rel(sistema, sat, "Emitiría facturas", "Pendiente")
    Rel(sistema, banguat, "Obtendría tipo de cambio", "Pendiente")
    Rel(sistema, fuentes, "Descarga fuentes", "HTTPS")
```

## Nivel 2 · Contenedores

```mermaid
C4Container
    title Contenedores · Estado actual del repositorio

    Person(usuario, "Usuario del sistema", "Auxiliar, contador, gerente financiero o gerencia")

    System_Boundary(app, "Aplicacion/ (Node.js + PostgreSQL)") {
        Container(front, "Front web", "HTML5, CSS, JavaScript", "Login, Home de unidades y Home de taller. Sirve api.js como cliente de la API")
        Container(apiNode, "API Express", "Node.js, Express 5", "Sirve el front estático y la API en /api/v1. Sesión con token Bearer y permisos por rol")
        ContainerDb(pg, "PostgreSQL", "Base kilometro_cero", "Esquema, restricciones y triggers de auditoría. Montos NUMERIC(18,6)")
    }

    System_Boundary(ref, "proyecto-vehiculos/backend/ (Python, referencia)") {
        Container(apiPy, "API FastAPI", "Python, FastAPI, SQLAlchemy", "Corte del Sprint 1: compra, importación, taller, hoja de costo y alta en flota. Documentación en /docs")
        ContainerDb(sqlite, "SQLite", "Archivo sistema.db en volumen Docker", "Mismo modelo de datos; se migrará a Alembic en el Sprint 2")
    }

    System_Ext(ci, "GitHub Actions", "pytest en cada push y pull request (hoy solo el backend Python)")

    Rel(usuario, front, "Usa", "HTTPS")
    Rel(front, apiNode, "Llama", "JSON/HTTP, Bearer token")
    Rel(apiNode, pg, "Lee y escribe", "SQL, pool de pg")
    Rel(usuario, apiPy, "Prueba vía Swagger", "HTTP :8000")
    Rel(apiPy, sqlite, "Lee y escribe", "SQLAlchemy")
    Rel(ci, apiPy, "Ejecuta pruebas")
    Rel(apiNode, apiPy, "Sigue el contrato de", "Documentación, no hay llamadas")
```

## Nivel 3 · Componentes de la API Express (`Aplicacion/`)

```mermaid
C4Component
    title Componentes · API Express

    Container(front, "Front web", "JavaScript", "api.js adjunta el token a cada llamada")
    ContainerDb(pg, "PostgreSQL", "kilometro_cero", "Tablas, triggers de bitácora")

    Container_Boundary(api, "API Express (src/)") {
        Component(app, "app.js / server.js", "Express", "Arranque, CORS, JSON, front estático, /health, prefijo /api/v1")
        Component(rutas, "routes/", "Express Router", "auth, unidades, ordenes y pendientes (501 con la historia pendiente)")
        Component(mw, "middlewares/", "Express", "auth.js (sesión Bearer, permisos) y errores.js (formato { detail })")
        Component(ctrl, "controllers/", "Express", "auth, unidades y ordenes: validan entrada y arman la respuesta")
        Component(models, "models/", "pg", "usuario, unidad y orden: consultas SQL")
        Component(svc, "services/seguridad.js", "crypto", "Hash de contraseñas y tokens de sesión")
        Component(cfg, "config/", "dotenv, pg", "index.js (entorno), db.js (pool y transacciones con app.usuario), permisos.js (matriz de roles)")
    }

    Rel(front, app, "HTTP /api/v1")
    Rel(app, rutas, "Delega")
    Rel(rutas, mw, "Aplica sesión y permisos")
    Rel(rutas, ctrl, "Invoca")
    Rel(ctrl, models, "Consulta")
    Rel(ctrl, svc, "Usa")
    Rel(mw, cfg, "Lee permisos")
    Rel(models, cfg, "Usa el pool")
    Rel(cfg, pg, "Conexión", "SQL")
```

## Nivel 3 · Componentes de la API FastAPI (`proyecto-vehiculos/backend/`)

```mermaid
C4Component
    title Componentes · API FastAPI

    ContainerDb(sqlite, "SQLite", "sistema.db", "Datos y bitácora")

    Container_Boundary(api, "API FastAPI (app/)") {
        Component(main, "main.py", "FastAPI", "Arranque, CORS, manejo de ErrorNegocio, /health; crea el esquema y siembra datos")
        Component(routers, "routers/", "APIRouter", "base (E1, E2), ciclo (unidades, importación, taller, alta en flota) e ingreso (E3, E6, E7; apagado en el Sprint 1)")
        Component(deps, "deps.py", "FastAPI Depends", "Usuario autenticado y matriz de permisos por rol")
        Component(services, "services/", "Python", "Reglas de negocio: base, contabilidad (partidas y multimoneda), ciclo e ingreso")
        Component(seg, "seguridad.py", "PBKDF2-SHA256", "Contraseñas con hash y sesiones con token")
        Component(aud, "auditoria.py", "SQLAlchemy events", "Bitácora automática en la misma transacción del cambio (HU-1.11)")
        Component(models, "models.py / schemas.py", "SQLAlchemy, Pydantic", "Entidades persistentes y contratos de entrada y salida")
        Component(db, "database.py / config.py", "SQLAlchemy", "Motor, sesión y SISTEMA_DB_URL")
    }

    Rel(main, routers, "Registra en /api/v1")
    Rel(routers, deps, "Exige sesión y rol")
    Rel(routers, services, "Delega")
    Rel(deps, seg, "Valida token")
    Rel(services, models, "Usa")
    Rel(services, db, "Sesión")
    Rel(aud, models, "Observa cambios")
    Rel(db, sqlite, "Conexión", "SQL")
```

## Decisiones de arquitectura visibles en el código

- **Dos monedas sin punto flotante**: los montos son `NUMERIC(18,6)` en PostgreSQL y `Decimal` en Python; viajan como texto y el navegador no calcula con ellos.
- **Autorización en el servidor**: la matriz de permisos vive en un solo lugar por backend (`config/permisos.js` y `deps.py`); ocultar opciones en el front no sustituye esa validación.
- **Auditoría automática** en la capa de persistencia (triggers en PostgreSQL, eventos de SQLAlchemy en Python), dentro de la misma transacción.
- **Contrato compartido**: ambas APIs exponen `/api/v1` y devuelven errores como `{ "detail": ... }`.

## Puntos abiertos

1. Hay dos backends con la misma responsabilidad y esquemas distintos (`database/schema.sql` frente a `models.py`). Conviene decidir cuál es el definitivo antes del Sprint 2.
2. La integración con FEL y con el tipo de cambio del Banguat no existe todavía.
3. La CI solo prueba el backend Python; el de Node tiene una prueba de humo sin pipeline.
4. El workflow vive en `proyecto-vehiculos/.github/`, así que GitHub no lo ejecuta (solo lee `.github/` en la raíz del repositorio).
