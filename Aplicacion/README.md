# Aplicación · Kilómetro Cero (Sprint 0)

Maqueta HTML5/CSS integrada con el esqueleto del backend: **Node.js (Express) + PostgreSQL**.
El contrato de la API (rutas, roles y mensajes) sigue a `../backend/README.md`.

## Cómo ejecutarlo

```bash
cd Aplicacion
npm install
cp .env.example .env          # ajustar DATABASE_URL
createdb kilometro_cero       # una vez
npm run db:demo               # esquema + usuarios + catálogo + unidades y órdenes de ejemplo
npm run dev                   # http://localhost:3000
npm test                      # prueba de humo de la API (requiere db:demo)
```

`npm run db:init` crea el esquema y los usuarios sin datos de ejemplo. Ambos comandos se pueden repetir.

Usuarios sembrados: `aux`, `contador`, `gerente` y `gerencia`, con la contraseña `PASSWORD_INICIAL` del `.env` (por defecto, la documentada en el README del backend de referencia). Solo ambiente de pruebas.

## Estructura

```
Aplicacion/
├── database/schema.sql        Tablas, restricciones y auditoría automática (triggers)
├── src/
│   ├── server.js · app.js     Arranque y aplicación Express (API en /api/v1 + front estático)
│   ├── config/                Entorno, pool de PostgreSQL y matriz de permisos por rol
│   ├── middlewares/           Sesión (Bearer), permisos y errores { detail }
│   ├── routes/ controllers/ models/ services/
│   ├── scripts/init-db.js     Esquema + semilla
│   └── public/                Front: index (login), home (unidades), HomeTaller
└── test/humo.test.js
```

## Qué es real y qué es esqueleto

| Pieza | Estado |
|---|---|
| Login, sesión con token, cierre de sesión, permisos por rol | Real (HU-1.09) |
| `GET /unidades`, `/unidades/:id`, `/unidades/vin/:vin`, `GET /ordenes` | Real |
| Auditoría automática con valores anteriores y nuevos, bitácora inmutable | Real, en la base (HU-1.11); falta el endpoint de consulta |
| Resto de endpoints del Sprint 1 (compras, gastos, partidas, hoja de costo, alta en flota…) | Esqueleto: responden `501` con la historia pendiente |
| Repuestos del taller y botones "Marcar comprado/recibido" | Maqueta: no se guardan |
| Ventas | Deshabilitado (Release 2) |

Los montos viajan como texto (`"900.000000"`): el navegador solo les da formato, no calcula con ellos.
