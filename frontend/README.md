# Frontend

Aquí va el proyecto Angular (paso 4 de la migración en [Arquitectura-Propuesta.md](../docs/arquitectura/Arquitectura-Propuesta.md#9-pasos-de-migración)).

Organización prevista:

```
src/app/
├── core/       sesión, interceptor del token, guard por rol, layout
├── shared/     componentes y pipes sin lógica de negocio
└── features/   un módulo por épica, igual que backend/app/modulos/
```

Las pantallas existentes de `../Aplicacion/src/public` (login, unidades, taller) son la referencia visual de los primeros componentes.
