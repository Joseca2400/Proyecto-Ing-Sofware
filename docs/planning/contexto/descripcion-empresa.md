# Descripción de la empresa y de la aplicación

Oct 23, 2026 · @Joseca198

## 1. Perfil de la empresa

La empresa opera en Guatemala desde una única sede y su negocio principal es el alquiler de vehículos. Importa vehículos de medio uso desde Estados Unidos, los repara en su propio taller y los pone en renta. Al cumplir cierta vida útil, los vende, normalmente con financiamiento propio.

El negocio funciona como un ciclo completo del vehículo:

1. Importación de vehículos usados desde EE. UU.
2. Reacondicionamiento en el taller antes de alquilarlos.
3. Alquiler, que es la fuente principal de ingresos.
4. Mantenimiento en el taller durante la vida útil del vehículo.
5. Venta del vehículo al final de su vida útil.
6. Servicio de taller posventa para los vehículos vendidos.

### Líneas de negocio

| Línea | Rol en el negocio |
| --- | --- |
| Alquiler | Línea principal y fuente recurrente de ingresos |
| Venta de vehículos | Salida de la flota tras su vida útil; con financiamiento y comisiones a vendedores |
| Taller | Privado; atiende la flota propia y se extiende a los vehículos vendidos |

Pendiente: porcentaje de ingresos y de margen por línea, y cuál es la más rentable. Esa información no se obtuvo en las respuestas y conviene confirmarla.

## 2. Contexto fiscal y financiero

La empresa se rige por la normativa guatemalteca de IVA e ISR y trabaja en quetzales y dólares, por lo que el sistema debe manejar dos monedas y su tipo de cambio.

- Jurisdicción: Guatemala, con aplicación de las reglas de IVA e ISR.
- Importación: la compra de vehículos en EE. UU. implica costos de importación que deben sumarse al costo del vehículo, junto con el costo de reparación en taller.
- Monedas: quetzales (GTQ) y dólares (USD).
- Ventas: no se reciben vehículos como parte de pago. Se ofrece financiamiento, lo que genera cartera por cobrar con intereses.
- Vendedores: trabajan con comisiones.

Pendiente de confirmar: régimen tributario exacto, si son agentes de retención, ISO, impuestos sobre vehículos y el tratamiento de las compras a particulares.

## 3. Descripción de la aplicación

La aplicación es un sistema administrativo y financiero que centraliza la contabilidad y el control económico de todo el ciclo del vehículo: importación, taller, alquiler y venta. Su objetivo es darle a la gerencia información confiable para decidir.

### Usuarios

El sistema lo usan el contador, el gerente financiero y un auxiliar. La gerencia lo consulta mediante reportes. Son pocos usuarios con perfil financiero, así que se prioriza el control contable sobre la operación masiva.

### Módulos principales

| Módulo | Qué cubre |
| --- | --- |
| Contabilidad y finanzas | Libros contables, estados financieros, conciliaciones y manejo multimoneda (GTQ/USD) con tipo de cambio |
| Impuestos (Guatemala) | Control de IVA e ISR, y de retenciones si aplican |
| Inventario de vehículos | Ficha por unidad con costo de compra, importación, reparaciones y estado (en taller, en renta, en venta, vendido); permite calcular la rentabilidad por vehículo |
| Taller | Órdenes de trabajo, repuestos y mano de obra, para la flota propia y los vehículos vendidos |
| Alquileres | Contratos, tarifas, facturación y cobros adicionales (por definir) |
| Ventas y financiamiento | Registro de ventas, planes de crédito propio, cuentas por cobrar y antigüedad de saldos |
| Comisiones | Cálculo de comisiones de vendedores por venta |
| Reportería para gerencia | Tableros e informes de rentabilidad y estado del negocio |

### Reportes previstos

Estos reportes están por confirmar con el cliente:

- Rentabilidad por línea de negocio y por vehículo
- Antigüedad de saldos (cartera de financiamiento)
- Inventario de unidades y repuestos
- Estados financieros
- Comisiones de vendedores

## 4. Información pendiente

Seis puntos del cuestionario quedaron sin respuesta o con respuesta parcial y conviene aclararlos con el cliente:

- [ ] Porcentaje de ingresos y de margen por línea, y cuál es la más rentable.
- [ ] Régimen tributario, impuestos específicos (ISO, impuestos sobre vehículos) y si son agentes de retención.
- [ ] Compra de vehículos usados a particulares: factura especial, retenciones y traspaso.
- [ ] Facturación de alquileres: contratos, tarifas (diaria, mensual, por kilometraje), facturación recurrente, depósitos en garantía y cobros adicionales (combustible, multas, daños, extensiones).
- [ ] Los 3 a 5 reportes más usados.
- [ ] Cómo se concreta el financiamiento: plazos, intereses, enganche, anticipos y traspaso.
