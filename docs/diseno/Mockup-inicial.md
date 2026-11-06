# Mockup inicial · Kilómetro Cero

Prototipo navegable en Angular para discutir arquitectura de información, jerarquía visual y recorridos antes de conectar cada módulo. Se basa en las [épicas](../planning/contexto/epicas.md), las [historias de usuario](../planning/user-stories/README.md) y el [Plan del MVP](../planning/PlanMVP.md).

## Abrir la propuesta

Desde `frontend/`, ejecutar `npm start` y visitar **http://localhost:4200/mockup**. Si el puerto está ocupado: `npm start -- --port 4201` y **http://localhost:4201/mockup**. El menú del sistema actual incluye «Mockup del proyecto».

Las secciones tienen enlaces directos, por ejemplo `/mockup?vista=flota` y `/mockup?vista=alquileres`. La navegación respeta los botones atrás y adelante del navegador.

## Dirección de diseño

- Conservar la identidad Kilómetro Cero: verde petróleo, acento ámbar, superficies claras y estados con texto y color.
- Organizar el menú en operación, control financiero y administración.
- Mantener el VIN como vínculo entre compra, taller, flota, alquiler y resultado.
- Priorizar alquileres como negocio principal; venta y financiamiento tienen su alcance posterior señalado.
- Mostrar importes GTQ y USD como texto mediante `MontoPipe`. No sumar dinero ni convertir monedas en el navegador.
- Adaptar tarjetas y formularios a móviles, con menú plegable y desplazamiento horizontal dentro de las tablas.

## Trazabilidad y alcance visual

| Vista | Historias de referencia | Alcance representado |
|---|---|---|
| Resumen general | HU-7.10, HU-7.03, HU-7.04 | Visión conceptual del sistema completo. El tablero está previsto para Release 3; no se incorpora al compromiso del MVP. |
| Unidades y flota | HU-1.05, HU-3.01, HU-4.07, HU-4.08 | Búsqueda por VIN, placa o modelo, filtro por estado, ficha y hoja de costo ilustrativa. |
| Alquileres | HU-3.06, HU-3.07 | Listado, detalle y formulario de borrador con cliente, unidad disponible, fechas, moneda, tarifa, depósito, kilometraje y combustible. |
| Compras e importación | HU-4.02, HU-4.04, HU-4.07, HU-4.08, HU-1.07 | Etapas, costo acumulado y moneda de origen. En el MVP los gastos se asignan por VIN; expediente, DUCA y prorrateo detallados corresponden a Release 1.1. |
| Taller | HU-5.01, HU-5.03, HU-5.07 | Órdenes ilustrativas y destino contable. El MVP cubre reacondicionamiento con mano de obra; mantenimiento y los demás destinos, repuestos y subcontratos se completan después. |
| Facturación y cobros | HU-6.02, HU-6.07, HU-6.12 | Documentos y saldos por cliente, vencimiento y moneda; no se certifican facturas ni se registran cobros. |
| Contabilidad | HU-2.01, HU-2.02, HU-2.03, HU-2.07, HU-2.08, HU-2.12 | Libro de partidas, revisión informativa y recorrido del cierre. |
| Reportes | HU-3.13, HU-7.02 | Resultado operativo por unidad hasta la flota. CSV de demostración; no implementa la exportación PDF/Excel de HU-7.09. |
| Configuración | HU-1.01, HU-1.06 a HU-1.11 | Perfil, monedas, roles informativos y ejemplo de bitácora. |
| Ventas | HU-8.01, HU-8.02, HU-8.04, HU-8.05, HU-8.09, HU-8.12 | Mapa del recorrido de Release 2, sin captura ni transacciones. |
| Financiamiento | HU-9.01, HU-9.02, HU-9.03, HU-9.06, HU-9.10, HU-9.14 | Mapa del recorrido de Release 2, sin otorgar créditos ni calcular cuotas. |
| Migración y arranque | HU-10.01, HU-10.02, HU-10.03, HU-10.05, HU-10.08, HU-10.09 | Preparación, carga y aceptación previstas para el arranque. Sin carga de archivos real. |

## Recorrido sugerido para revisar

1. Cambiar el período del resumen entre octubre y noviembre.
2. Buscar «Tucson» o un VIN; filtrar disponibles y abrir la ficha de una unidad.
3. Revisar su costo de compra, importación y reacondicionamiento.
4. Abrir «Nuevo contrato». Probar campos vacíos y una devolución anterior a la salida; corregir y guardar el borrador.
5. Ver el nuevo borrador en Alquileres y abrir su detalle.
6. Consultar importaciones, taller, cobranza y una partida pendiente.
7. Abrir Reportes y exportar su muestra CSV; el directorio exporta solamente las unidades filtradas.
8. Revisar los alcances futuros y probar el menú en una pantalla pequeña.

## Límites de la demostración

Todos los nombres, VIN, contratos, estados, fechas, tipos de cambio y montos son ficticios. Las cifras del resumen representan un escenario de 24 unidades; el directorio muestra una muestra de seis, no una conciliación del tablero. Las tarjetas de importación son ejemplos de cada etapa, no el listado completo del escenario.

Los borradores viven en memoria y se pierden al recargar la página. No reservan unidades, generan documentos, calculan montos ni llaman a la API. El perfil de contador es ilustrativo: no hay autenticación, autorización, auditoría persistente ni decisiones contables implementadas por este prototipo. Las funciones definitivas seguirán validándose en el servidor y dentro de las transacciones del dominio.

El tema visual está limitado al selector `app-mockup` en `frontend/src/styles/mockup.css`; el resto del frontend conserva su presentación. La ruta tiene su propio marco visual y carga diferida, para permitir revisar el diseño antes de adoptarlo en los módulos del equipo.

Esta entrega no marca historias como terminadas ni cambia `sprints.json` o `PlanMVP.md`.

## Validación realizada

- Compilación de producción, ESLint y formato Prettier.
- Suite existente del frontend: 31 pruebas en seis archivos, todas aprobadas.
- Navegación por las doce secciones sin errores de consola observados.
- Búsqueda, filtros, ficha de costo, cambio de período y descarga CSV de la muestra filtrada.
- Formulario: campos obligatorios, rechazo de fechas invertidas y guardado de un borrador válido.
- Revisión visual en escritorio (1440 px), panel intermedio y móvil (390 px), incluida la apertura y cierre del menú.
