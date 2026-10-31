# Frontend · Angular

## Desarrollo

```bash
npm install
npm start          # http://localhost:4200, reenvía /api al backend en :8000 (proxy.conf.json)
npm test -- --watch=false
npm run build
```

## Organización

```
src/app/
├── core/        se carga una vez: api/ (prefijo /api/v1), layout/ (barra y menú); luego auth/
├── shared/      sin lógica de negocio: pipes/monto.pipe.ts (formato GTQ/USD sin float)
└── features/    un módulo por épica, con carga diferida; hoy solo inicio/
```

Reglas: un componente usa el servicio de su módulo, nunca `HttpClient` directo; los montos llegan como texto y solo se formatean.

Para agregar un módulo: `npx ng generate component features/<modulo>/<pantalla>` y registrar su ruta en `app.routes.ts` y su entrada en `core/layout/layout.ts`.
