# User Story Mapping

Mapa de historias del sistema administrativo y financiero para la empresa de alquiler, venta y taller de vehículos. Consolida las 10 épicas y sus 130 historias de usuario en un solo mapa, organizado por actividades y por releases.

Versión 1 · 23 de octubre de 2026 · Borrador para validar con el cliente.

Fuentes: [epicas.md](contexto/epicas.md) y las historias detalladas en [user-stories/](user-stories/README.md), donde están los criterios de aceptación de cada una.

## Cómo leer el mapa

- **Columna vertebral (backbone):** las épicas, ordenadas según el ciclo de vida de la unidad, de la importación a la venta.
- **Actividades:** dentro de cada épica, lo que el usuario hace, en el orden en que lo hace.
- **Historias:** debajo de cada actividad, repartidas en tres releases. Lo que está más arriba se construye primero.
- Los roles son auxiliar contable, contador, gerente financiero y gerencia (HU-1.09).

## Columna vertebral

El sistema sigue el ciclo de vida de cada unidad, identificada por su VIN. Las épicas 1, 2, 7 y 10 sostienen todo el ciclo.

```
Base         E1 Configuración, multimoneda y seguridad  +  E2 Contabilidad y cierre

Ciclo de     E4 Comprar e importar ──► E5 Reacondicionar ──► E3 Alquilar y mantener
la unidad       (USD, DUCA,               (taller,               (flota, contratos,
                 prorrateo)                repuestos)             depreciación)
                                                                        │
                                                                        ▼
             E5 Postventa ◄── E9 Financiar ◄── E8 Vender ◄── E3 Dar de baja de la flota
                (garantía)       (cartera)       (comisiones)

Transversal  E6 Facturar (FEL) y cobrar  +  E7 Reportar a la gerencia

Arranque     E10 Migrar saldos, capacitar y arrancar
```

| Paso del ciclo | Épica | Rol principal | Resultado del paso |
|---|---|---|---|
| 0. Preparar la base | E1, E2 | Contador | Catálogo, dimensiones (línea y VIN), tipo de cambio y roles listos |
| 1. Comprar e importar | E4 | Auxiliar contable | Unidad creada por VIN con costo de compra e importación |
| 2. Reacondicionar | E5 | Auxiliar contable | Costo de taller capitalizado a la unidad |
| 3. Incorporar y alquilar | E3 | Auxiliar contable | Activo fijo en flota, contratos facturados, depreciación |
| 4. Facturar y cobrar | E6 | Auxiliar contable | Documentos FEL ligados a asiento, cliente y unidad |
| 5. Cerrar el mes | E2 | Contador | Depreciación, revaluación, conciliaciones y cierre |
| 6. Dar de baja y vender | E3, E8 | Gerente financiero | Unidad vendida, con margen neto de comisión y garantía |
| 7. Financiar | E9 | Gerente financiero | Crédito aprobado, cobrado y con mora al día |
| 8. Atender postventa | E5 | Auxiliar contable | Garantía o servicio facturado al comprador |
| 9. Decidir | E7 | Gerencia | Rentabilidad por línea y por unidad |
| 10. Arrancar | E10 | Contador | Saldos iniciales que cuadran con los estados financieros validados |

## Releases

| Release | Objetivo | Qué incluye |
|---|---|---|
| **Release 1 · MVP** | Arrancar la operación con la línea principal (alquiler): costear cada unidad, facturar contratos, cerrar el mes y emitir los reportes base | Historias Must de las épicas 1 a 7 y 10 |
| **Release 2** | Habilitar la salida de la flota (venta y financiamiento) y completar los controles | Historias Must de las épicas 8 y 9; historias Should de las épicas 1 a 7 y 10; reportes de cartera y comisiones |
| **Release 3** | Completar funciones deseables | Historias Should de las épicas 8 y 9 e historias Could |

Reglas de asignación y excepciones:
- **HU-7.05 (cartera y mora) y HU-7.06 (comisiones)** pasan a Release 2, porque dependen de las épicas 9 y 8.
- **HU-7.02 (rentabilidad por unidad)** sale en Release 1 con el ciclo hasta la flota (importación, taller, alquiler, depreciación) y se completa en Release 2 con el resultado de la venta (HU-8.12).
- **HU-5.08 (validar garantía)** pasa a Release 3, junto con la garantía de la venta (HU-8.11).
- **HU-10.06 (carga de cartera vigente)** va en Release 2 con la Épica 9. **Si al arrancar ya hay créditos vigentes**, la Épica 9 (sus historias Must) y HU-10.06 suben a Release 1, como indica la nota de la Épica 9.

### Historias por release

| Épica | Release 1 · MVP | Release 2 | Release 3 | Total |
|---|---|---|---|---|
| 1. Configuración, multimoneda y seguridad | 11 | 1 | 0 | 12 |
| 2. Contabilidad general y cierre | 13 | 3 | 0 | 16 |
| 3. Flota, activos fijos y alquileres | 12 | 3 | 0 | 15 |
| 4. Importación, compras y cuentas por pagar | 13 | 2 | 1 | 16 |
| 5. Taller interno y postventa | 8 | 1 | 1 | 10 |
| 6. Facturación electrónica y cuentas por cobrar | 9 | 3 | 0 | 12 |
| 7. Reportes gerenciales | 6 | 4 | 0 | 10 |
| 8. Venta de unidades y comisiones | 0 | 9 | 3 | 12 |
| 9. Financiamiento propio y cartera | 0 | 12 | 3 | 15 |
| 10. Migración y arranque | 10 | 2 | 0 | 12 |
| **Total** | **82** | **40** | **8** | **130** |

## Mapa de historias

Cada tabla es una épica. Las filas son las actividades en el orden en que el usuario las realiza; las columnas, los releases.

### Épica 1. Configuración, multimoneda y seguridad

Detalle: [E01-configuracion-multimoneda-seguridad.md](user-stories/E01-configuracion-multimoneda-seguridad.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Configurar la empresa** | **HU-1.01** Registrar el perfil fiscal de la empresa<br>**HU-1.02** Mantener el catálogo de cuentas<br>**HU-1.04** Configurar las dimensiones analíticas | **HU-1.03** Importar el catálogo de cuentas existente | — |
| **Identificar unidades** | **HU-1.05** Registrar y validar unidades por VIN | — | — |
| **Manejar dos monedas** | **HU-1.06** Cargar el tipo de cambio de referencia del Banguat<br>**HU-1.07** Registrar transacciones en dólares<br>**HU-1.08** Configurar cuentas bancarias en quetzales y dólares | — | — |
| **Controlar el acceso** | **HU-1.09** Administrar usuarios y roles<br>**HU-1.10** Separar funciones de registro y aprobación<br>**HU-1.11** Consultar la bitácora de cambios<br>**HU-1.12** Respaldar y restaurar la información | — | — |

### Épica 2. Contabilidad general y cierre

Detalle: [E02-contabilidad-general-cierre.md](user-stories/E02-contabilidad-general-cierre.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Registrar partidas** | **HU-2.01** Registrar una partida manual<br>**HU-2.02** Revisar y contabilizar partidas<br>**HU-2.03** Generar partidas automáticas desde los módulos<br>**HU-2.05** Revertir una partida contabilizada | **HU-2.04** Programar partidas recurrentes<br>**HU-2.06** Registrar provisiones con reversión automática | — |
| **Ajustar al cierre** | **HU-2.07** Calcular la depreciación mensual<br>**HU-2.08** Revaluar saldos en dólares al cierre<br>**HU-2.09** Calcular el diferencial cambiario realizado<br>**HU-2.10** Conciliar las cuentas bancarias | — | — |
| **Cerrar períodos** | **HU-2.12** Cerrar un período mensual<br>**HU-2.13** Reabrir un período cerrado<br>**HU-2.14** Ejecutar el cierre anual | **HU-2.11** Seguir una lista de verificación de cierre | — |
| **Emitir libros y consultar** | **HU-2.15** Emitir los libros legales<br>**HU-2.16** Consultar el balance de comprobación y el mayor | — | — |

### Épica 3. Flota, activos fijos y alquileres

Detalle: [E03-flota-activos-fijos-alquileres.md](user-stories/E03-flota-activos-fijos-alquileres.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Incorporar a la flota** | **HU-3.01** Dar de alta una unidad como activo fijo de la flota<br>**HU-3.02** Definir los parámetros de depreciación de cada unidad<br>**HU-3.04** Controlar seguros, marchamo y documentos de cada unidad | **HU-3.03** Capitalizar una mejora a una unidad de la flota | — |
| **Contratar alquileres** | **HU-3.05** Mantener el tarifario de alquiler<br>**HU-3.06** Registrar un contrato de alquiler<br>**HU-3.07** Recibir, aplicar y devolver depósitos en garantía | **HU-3.11** Extender un contrato vigente | — |
| **Cerrar y facturar contratos** | **HU-3.08** Cerrar un contrato al devolver la unidad<br>**HU-3.09** Registrar cargos adicionales del contrato<br>**HU-3.10** Facturar contratos de forma recurrente | — | — |
| **Medir la flota** | **HU-3.12** Consultar la ocupación de la flota<br>**HU-3.13** Consultar la rentabilidad por contrato y por unidad | — | — |
| **Retirar de la flota** | **HU-3.15** Dar de baja una unidad de la flota y pasarla a venta | **HU-3.14** Alertar sobre el fin de la vida útil en flota | — |

### Épica 4. Importación, compras y cuentas por pagar

Detalle: [E04-importacion-compras-cxp.md](user-stories/E04-importacion-compras-cxp.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Comprar en EE. UU.** | **HU-4.01** Registrar proveedores locales y del exterior<br>**HU-4.02** Registrar la compra de una unidad en EE. UU. | — | — |
| **Importar y nacionalizar** | **HU-4.03** Agrupar unidades en un expediente de importación<br>**HU-4.04** Registrar los gastos de importación<br>**HU-4.05** Prorratear los gastos compartidos<br>**HU-4.06** Registrar la DUCA y vincularla a las unidades<br>**HU-4.07** Seguir el estado de la unidad durante la importación | — | — |
| **Costear la unidad** | **HU-4.08** Consultar la hoja de costo de una unidad | — | — |
| **Registrar compras locales** | **HU-4.09** Registrar facturas de compras y gastos locales | **HU-4.15** Registrar notas de crédito y devoluciones de proveedores | **HU-4.10** Registrar compras a particulares con factura especial |
| **Retener impuestos** | **HU-4.11** Retener IVA e ISR a proveedores locales | **HU-4.12** Retener ISR en pagos al exterior | — |
| **Pagar a proveedores** | **HU-4.13** Programar y aprobar pagos a proveedores<br>**HU-4.14** Registrar el pago a un proveedor<br>**HU-4.16** Consultar antigüedad de saldos y estado de cuenta de proveedores | — | — |

### Épica 5. Taller interno y postventa

Detalle: [E05-taller-interno-postventa.md](user-stories/E05-taller-interno-postventa.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Abrir y costear órdenes** | **HU-5.01** Abrir una orden de trabajo ligada a un VIN<br>**HU-5.02** Configurar las tarifas de mano de obra<br>**HU-5.03** Registrar mano de obra en la orden<br>**HU-5.06** Registrar trabajos subcontratados | — | — |
| **Controlar repuestos** | **HU-5.04** Mantener el catálogo e inventario de repuestos<br>**HU-5.05** Consumir repuestos en una orden | **HU-5.10** Realizar el conteo físico de repuestos | — |
| **Cerrar órdenes** | **HU-5.07** Cerrar la orden y generar su destino contable | — | — |
| **Atender postventa** | **HU-5.09** Facturar la postventa no cubierta por garantía | — | **HU-5.08** Validar la garantía de una unidad vendida |

### Épica 6. Facturación electrónica y cuentas por cobrar

Detalle: [E06-facturacion-electronica-cxc.md](user-stories/E06-facturacion-electronica-cxc.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Registrar clientes** | **HU-6.01** Registrar clientes | — | — |
| **Emitir documentos FEL** | **HU-6.02** Emitir una factura FEL<br>**HU-6.03** Emitir notas de crédito<br>**HU-6.05** Anular un documento FEL | **HU-6.04** Emitir notas de débito<br>**HU-6.06** Registrar documentos FEL emitidos fuera del sistema | — |
| **Cobrar** | **HU-6.07** Registrar cobros y aplicarlos a facturas<br>**HU-6.08** Registrar retenciones que nos hacen los clientes<br>**HU-6.09** Registrar y aplicar anticipos de clientes | **HU-6.10** Identificar depósitos no aplicados | — |
| **Controlar saldos** | **HU-6.11** Consultar el estado de cuenta de un cliente<br>**HU-6.12** Consultar la antigüedad de saldos de clientes | — | — |

### Épica 7. Reportes gerenciales

Detalle: [E07-reportes-gerenciales.md](user-stories/E07-reportes-gerenciales.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Ver resultados** | **HU-7.01** Consultar estados financieros por línea de negocio<br>**HU-7.02** Consultar la rentabilidad de cada unidad en todo su ciclo<br>**HU-7.03** Consultar la ocupación y rentabilidad de la flota | — | — |
| **Ver la operación** | **HU-7.04** Consultar las unidades por etapa del ciclo | **HU-7.08** Consultar el inventario de unidades y repuestos | — |
| **Ver cartera y saldos** | **HU-7.07** Consultar la antigüedad de saldos de clientes y proveedores | **HU-7.05** Consultar la cartera financiada y la mora<br>**HU-7.06** Consultar las comisiones por vendedor | — |
| **Compartir y resumir** | **HU-7.09** Exportar reportes a PDF y Excel | **HU-7.10** Consultar un tablero gerencial | — |

### Épica 8. Venta de unidades y comisiones

Detalle: [E08-venta-unidades-comisiones.md](user-stories/E08-venta-unidades-comisiones.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Preparar la venta** | — | **HU-8.01** Consultar el inventario de unidades en venta<br>**HU-8.02** Fijar el precio de lista y el precio mínimo | **HU-8.03** Reservar una unidad con anticipo |
| **Vender** | — | **HU-8.04** Registrar una venta de contado<br>**HU-8.05** Registrar una venta financiada<br>**HU-8.07** Configurar el tratamiento fiscal de la venta de unidades | **HU-8.06** Controlar el traspaso de propiedad |
| **Pagar comisiones** | — | **HU-8.08** Registrar vendedores y reglas de comisión<br>**HU-8.09** Calcular la comisión de cada venta<br>**HU-8.10** Liquidar comisiones por período | — |
| **Cerrar el resultado** | — | **HU-8.12** Ver el margen de la unidad vendida | **HU-8.11** Registrar la garantía ofrecida al comprador |

### Épica 9. Financiamiento propio y cartera

Detalle: [E09-financiamiento-cartera.md](user-stories/E09-financiamiento-cartera.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Otorgar el crédito** | — | **HU-9.01** Definir planes de crédito<br>**HU-9.02** Registrar y aprobar un crédito<br>**HU-9.03** Generar la tabla de amortización | **HU-9.11** Registrar y liberar la garantía prendaria |
| **Cobrar y devengar** | — | **HU-9.04** Devengar los intereses mensuales<br>**HU-9.05** Facturar los intereses<br>**HU-9.06** Registrar el cobro de una cuota<br>**HU-9.07** Registrar abonos extraordinarios a capital<br>**HU-9.08** Cancelar un crédito de forma anticipada | — |
| **Gestionar la mora** | — | **HU-9.09** Calcular la mora y el interés moratorio<br>**HU-9.10** Calcular la antigüedad de la cartera y la provisión por incobrables | **HU-9.12** Recuperar una unidad por impago<br>**HU-9.15** Reestructurar un crédito |
| **Informar y conciliar** | — | **HU-9.13** Emitir el estado de cuenta del crédito<br>**HU-9.14** Conciliar la cartera con la contabilidad | — |

### Épica 10. Migración y arranque

Detalle: [E10-migracion-arranque.md](user-stories/E10-migracion-arranque.md)

| Actividad | Release 1 · MVP | Release 2 | Release 3 |
|---|---|---|---|
| **Preparar la carga** | **HU-10.01** Descargar plantillas de carga y validar archivos | — | — |
| **Cargar saldos y unidades** | **HU-10.02** Cargar los saldos contables iniciales<br>**HU-10.03** Cargar la flota con su valor en libros<br>**HU-10.04** Cargar unidades en importación, en taller y en venta | — | — |
| **Cargar terceros y operación** | **HU-10.05** Cargar clientes, proveedores y sus saldos abiertos<br>**HU-10.07** Cargar el inventario de repuestos<br>**HU-10.08** Cargar los contratos de alquiler activos | **HU-10.06** Cargar la cartera financiada vigente | — |
| **Validar y arrancar** | **HU-10.09** Conciliar el arranque y aceptar los saldos<br>**HU-10.11** Capacitar a los usuarios por rol (habilitación)<br>**HU-10.12** Dar soporte inicial tras el arranque (habilitación) | **HU-10.10** Operar en paralelo antes del arranque definitivo | — |

## Pendientes que pueden mover historias entre releases

| Pendiente con el cliente | Efecto en el mapa |
|---|---|
| ¿Hay créditos vigentes hoy? | Si los hay, la Épica 9 (Must) y HU-10.06 suben a Release 1 |
| ¿Cuáles son los 3 a 5 reportes más usados? | Define el orden de la Épica 7 dentro de Release 1 |
| ¿Quién registra la operación (contratos, taller, ventas)? | Puede agregar un rol operativo en HU-1.09 dentro de Release 1 |
| ¿Hay una o dos sociedades? | Si son dos, se evalúa multiempresa, hoy fuera del alcance |
| ¿Hay compras a particulares? | Si son frecuentes, HU-4.10 sube de Release 3 a Release 1 |
| ¿La postventa tiene garantía definida? | Si existe y es frecuente, HU-8.11 y HU-5.08 suben a Release 2 |

La lista completa de pendientes y las historias que afectan está en [user-stories/README.md](user-stories/README.md).
