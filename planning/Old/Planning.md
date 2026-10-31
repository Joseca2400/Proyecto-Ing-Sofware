# Planning

Plan de implementación del sistema administrativo y financiero para la empresa de alquiler, venta y taller de vehículos. Se basa en las 10 épicas de [epicas.md](../contexto/epicas.md), las 130 historias de [user-stories/](../user-stories/README.md) y los releases del [UserStoryMapping.md](../UserStoryMapping.md).

Versión 2 · 30 de octubre de 2026 · **Sustituido** por [Sprint1.md](../Sprint1.md), [PlanSprints.md](../PlanSprints.md) y [AjustePlaneacion.md](../AjustePlaneacion.md). Se conserva como historial de la planeación (ver la sección 6 de AjustePlaneacion.md).

## Contenido

1. [Estrategia de implementación](#1-estrategia-de-implementación)
2. [Supuestos de planificación](#2-supuestos-de-planificación)
3. [Product Backlog priorizado por valor](#3-product-backlog-priorizado-por-valor)
4. [Plan de sprints](#4-plan-de-sprints)
5. [Sprint Backlog del Sprint 1: las 3 tareas prioritarias](#5-sprint-backlog-del-sprint-1-las-3-tareas-prioritarias)
6. [Resultado de la primera iteración](#6-resultado-de-la-primera-iteración)
7. [Definiciones de listo y terminado](#7-definiciones-de-listo-y-terminado)
8. [Riesgos y pendientes que afectan el plan](#8-riesgos-y-pendientes-que-afectan-el-plan)

---

## 1. Estrategia de implementación

### Corte transversal

El orden de construcción sugerido en [user-stories/README.md](../user-stories/README.md) va épica por épica: primero la base contable, luego el costo de la unidad, el ingreso, el cierre, los reportes, la venta y el arranque. Seguido al pie de la letra, el sistema no podría mostrar una unidad de principio a fin hasta varios meses después, y las integraciones entre épicas (que la compra genere su partida, que el taller cargue costo a la unidad, que la factura alimente la cuenta por cobrar) se probarían al final, que es donde más riesgo hay.

Por eso el plan arranca con un **corte transversal**. El Sprint 1 toma una **versión delgada de las historias que forman el ciclo de vida de la unidad** en las épicas 1 a 7 y las hace funcionar juntas. A partir del Sprint 2 se completa cada historia siguiendo el orden de construcción del equipo.

```
 Ciclo de la unidad (eje del sistema, por VIN)
 ─────────────────────────────────────────────────────────────────────────────────────────────
  E1 Base       E4 Comprar      E5 Taller        E3 Flota       E3 Alquilar   E6 Facturar   E7 Reportar
  roles, TC  →  en EE. UU.   →  reacondiciona →  alta como   →  contrato   →  FEL y cobro → rentabilidad
  catálogo,     (USD) y         y capitaliza     activo fijo    y cierre      con diferen-   por unidad
  VIN           gastos                                                        cial (E2)      y por etapa
  ─────────────────────────────────────────────────────────────────────────────────────────────
  E2 Contabilidad: cada paso genera su partida automática, ligada al VIN y a la línea de negocio
```

```
             E1     E2     E3     E4     E5     E6     E7     E8     E9     E10
           ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
 Sprint 1  │██████│██████│██████│██████│██████│██████│██████│      │      │      │  corte transversal
           ├──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┤
 S2 – S12  │▓▓▓▓▓▓│▓▓▓▓▓▓│▓▓▓▓▓▓│▓▓▓▓▓▓│▓▓▓▓▓▓│▓▓▓▓▓▓│▓▓▓▓▓▓│      │      │▓▓▓▓▓▓│  Release 1 · MVP
           ├──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┤
 S13 – S19 │░░░░░░│░░░░░░│░░░░░░│░░░░░░│░░░░░░│░░░░░░│░░░░░░│░░░░░░│░░░░░░│░░░░░░│  Releases 2 y 3
           └──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘
```

**Por qué este enfoque:**

- **Se implementa un poco de todo desde el primer sprint**, de modo que se puede demostrar el ciclo completo de una unidad y no un módulo aislado.
- **Se validan primero las reglas que sostienen todo el sistema**: que cada partida cuadre en quetzales, que una transacción en USD guarde monto original y tipo de cambio, que toda cuenta que lo exija lleve VIN y que quien registra no apruebe.
- **Las épicas 8, 9 y 10 quedan fuera del corte** a propósito: dependen de que la unidad ya exista en flota con su valor en libros (E8 y E9 son Release 2) y la migración depende de que todo lo demás esté definido.
- **El cliente puede validar el modelo contable** (cuentas, líneas de negocio, destino del costo de taller) con datos reales antes de que se construya el detalle.

### Criterio de priorización por valor

Cada historia tiene un **valor de negocio de 1 a 10**, calculado con una regla explícita para que el equipo y el cliente puedan discutirla:

| Componente | Puntos |
|---|---|
| Prioridad MoSCoW de la historia | Must 7 · Should 4 · Could 2 |
| Posición de la épica en el ciclo | E1 a E3 +2 · E4 a E6 +1 · E7 y E10 0 · E8 y E9 −1 |
| Forma parte del corte transversal | +1 |

El backlog se ordena por **release** (R1, R2, R3 del story map), luego por la **fase del orden de construcción** del equipo y, dentro de cada fase, por **valor** de mayor a menor. Cuando una dependencia lo exige, una historia se mueve después de la historia de la que depende (sección 3.4).

### Arquitectura de la primera iteración

| Capa | Decisión | Motivo |
|---|---|---|
| Backend | Python 3.11+ · FastAPI | Documentación interactiva (Swagger) para validar cada historia con el cliente |
| Persistencia | SQLAlchemy 2 · SQLite en desarrollo, PostgreSQL en producción | Cero configuración para empezar |
| Montos | Decimales exactos (nunca punto flotante) | Las partidas deben cuadrar al centavo |
| Contabilidad | Partida doble con validación de cuadre en quetzales; partidas automáticas por documento | Criterio de éxito de las épicas 1 y 2 |
| Frontend | Maqueta HTML y JavaScript (equipo) | Consume la API; CORS habilitado |
| Pruebas | pytest, un archivo por tarea del sprint | Cada criterio de aceptación del corte tiene prueba automatizada |
| Despliegue | Docker (`docker compose up`) | El mismo entorno en todas las computadoras |

---

## 2. Supuestos de planificación

| Supuesto | Valor | Nota |
|---|---|---|
| Duración del sprint | 2 semanas (lunes a viernes) | |
| Velocidad para planificar desde el S2 | 30 story points por sprint | Se recalibra al cierre de S2 y S3 |
| Estimación | Story points en escala Fibonacci | Estimación inicial del equipo; se revisa en cada refinamiento |
| Total del backlog | 546 SP en 130 historias | R1: 369 · R2: 150 · R3: 27 |
| Receso de fin de año | 14/12/2026 – 01/01/2027 | Por confirmar |
| Créditos vigentes al arrancar | No | Si los hay, la Épica 9 y HU-10.06 suben a Release 1 (nota de la Épica 9) |

> **Sobre la velocidad del Sprint 1.** El corte entregó 82 SP (79 de historias parciales y 3 de configuración técnica). No se usa para planificar porque las historias del corte son versiones delgadas y el sprint partió de una base técnica preparada. El plan usa 30 SP y se ajustará con la velocidad real de los sprints 2 y 3.

---

## 3. Product Backlog priorizado por valor

Las 130 historias ordenadas por prioridad. La columna **Hecho en S1** indica los puntos que ya entregó el corte transversal; esas historias se completan en el sprint indicado.

### 3.1 Release 1 · MVP (82 historias)

| # | Historia | Épica | MoSCoW | Valor | SP | Hecho en S1 | Sprint |
|---|---|---|---|---|---|---|---|
| 1 | **HU-1.07** Registrar transacciones en dólares | E1 | Must | 10 | 3 | 3 SP | S1 ✅ |
| 2 | **HU-1.02** Mantener el catálogo de cuentas | E1 | Must | 10 | 5 | 3 SP | S1 → S2 |
| 3 | **HU-1.04** Configurar las dimensiones analíticas | E1 | Must | 10 | 3 | 2 SP | S1 → S2 |
| 4 | **HU-1.05** Registrar y validar unidades por VIN | E1 | Must | 10 | 5 | 3 SP | S1 → S2 |
| 5 | **HU-1.06** Cargar el tipo de cambio de referencia del Banguat | E1 | Must | 10 | 5 | 2 SP | S1 → S2 |
| 6 | **HU-1.09** Administrar usuarios y roles | E1 | Must | 10 | 5 | 2 SP | S1 → S2 |
| 7 | **HU-1.10** Separar funciones de registro y aprobación | E1 | Must | 10 | 5 | 3 SP | S1 → S2 |
| 8 | **HU-1.11** Consultar la bitácora de cambios | E1 | Must | 10 | 3 | 2 SP | S1 → S2 |
| 9 | **HU-2.01** Registrar una partida manual | E2 | Must | 10 | 5 | 3 SP | S1 → S2 |
| 10 | **HU-2.02** Revisar y contabilizar partidas | E2 | Must | 10 | 5 | 3 SP | S1 → S2 |
| 11 | **HU-2.03** Generar partidas automáticas desde los módulos | E2 | Must | 10 | 8 | 5 SP | S1 → S2 |
| 12 | **HU-1.01** Registrar el perfil fiscal de la empresa | E1 | Must | 9 | 3 | — | S2 |
| 13 | **HU-1.08** Configurar cuentas bancarias en quetzales y dólares | E1 | Must | 9 | 3 | — | S2 |
| 14 | **HU-1.12** Respaldar y restaurar la información | E1 | Must | 9 | 5 | — | S3 |
| 15 | **HU-2.05** Revertir una partida contabilizada | E2 | Must | 9 | 3 | — | S3 |
| 16 | **HU-2.09** Calcular el diferencial cambiario realizado | E2 | Must | 10 | 5 | 3 SP | S1 → S3 |
| 17 | **HU-4.01** Registrar proveedores locales y del exterior | E4 | Must | 9 | 2 | 1 SP | S1 → S3 |
| 18 | **HU-4.02** Registrar la compra de una unidad en EE. UU. | E4 | Must | 9 | 5 | 4 SP | S1 → S3 |
| 19 | **HU-4.04** Registrar los gastos de importación | E4 | Must | 9 | 5 | 3 SP | S1 → S3 |
| 20 | **HU-4.07** Seguir el estado de la unidad durante la importación | E4 | Must | 9 | 3 | 2 SP | S1 → S3 |
| 21 | **HU-4.08** Consultar la hoja de costo de una unidad | E4 | Must | 9 | 3 | 2 SP | S1 → S3 |
| 22 | **HU-5.01** Abrir una orden de trabajo ligada a un VIN | E5 | Must | 9 | 3 | 2 SP | S1 → S3 |
| 23 | **HU-5.02** Configurar las tarifas de mano de obra | E5 | Must | 9 | 2 | 1 SP | S1 → S3 |
| 24 | **HU-5.03** Registrar mano de obra en la orden | E5 | Must | 9 | 3 | 2 SP | S1 → S3 |
| 25 | **HU-5.07** Cerrar la orden y generar su destino contable | E5 | Must | 9 | 5 | 3 SP | S1 → S3 |
| 26 | **HU-4.03** Agrupar unidades en un expediente de importación | E4 | Must | 8 | 3 | — | S3 |
| 27 | **HU-4.05** Prorratear los gastos compartidos | E4 | Must | 8 | 5 | — | S3 |
| 28 | **HU-4.06** Registrar la DUCA y vincularla a las unidades | E4 | Must | 8 | 3 | — | S4 |
| 29 | **HU-4.09** Registrar facturas de compras y gastos locales | E4 | Must | 8 | 5 | — | S4 |
| 30 | **HU-4.11** Retener IVA e ISR a proveedores locales | E4 | Must | 8 | 5 | — | S4 |
| 31 | **HU-4.13** Programar y aprobar pagos a proveedores | E4 | Must | 8 | 5 | — | S4 |
| 32 | **HU-4.14** Registrar el pago a un proveedor | E4 | Must | 8 | 5 | — | S4 |
| 33 | **HU-4.16** Consultar antigüedad de saldos y estado de cuenta de proveedores | E4 | Must | 8 | 5 | — | S4 |
| 34 | **HU-5.04** Mantener el catálogo e inventario de repuestos | E5 | Must | 8 | 5 | — | S5 |
| 35 | **HU-5.05** Consumir repuestos en una orden | E5 | Must | 8 | 3 | — | S5 |
| 36 | **HU-5.06** Registrar trabajos subcontratados | E5 | Must | 8 | 3 | — | S5 |
| 37 | **HU-5.09** Facturar la postventa no cubierta por garantía | E5 | Must | 8 | 3 | — | S5 |
| 38 | **HU-6.01** Registrar clientes | E6 | Must | 9 | 3 | 2 SP | S1 → S5 |
| 39 | **HU-6.02** Emitir una factura FEL | E6 | Must | 9 | 13 | 5 SP | S1 → S5 |
| 40 | **HU-3.01** Dar de alta una unidad como activo fijo de la flota | E3 | Must | 10 | 5 | 3 SP | S1 → S5 |
| 41 | **HU-3.06** Registrar un contrato de alquiler | E3 | Must | 10 | 5 | 3 SP | S1 → S5 |
| 42 | **HU-3.08** Cerrar un contrato al devolver la unidad | E3 | Must | 10 | 3 | 2 SP | S1 → S5 |
| 43 | **HU-3.02** Definir los parámetros de depreciación de cada unidad | E3 | Must | 9 | 5 | — | S6 |
| 44 | **HU-3.04** Controlar seguros, marchamo y documentos de cada unidad | E3 | Must | 9 | 5 | — | S6 |
| 45 | **HU-3.05** Mantener el tarifario de alquiler | E3 | Must | 9 | 3 | — | S6 |
| 46 | **HU-3.07** Recibir, aplicar y devolver depósitos en garantía | E3 | Must | 9 | 5 | — | S6 |
| 47 | **HU-3.09** Registrar cargos adicionales del contrato | E3 | Must | 9 | 5 | — | S6 |
| 48 | **HU-3.10** Facturar contratos de forma recurrente | E3 | Must | 9 | 8 | — | S7 |
| 49 | **HU-3.12** Consultar la ocupación de la flota | E3 | Must | 9 | 5 | — | S7 |
| 50 | **HU-3.15** Dar de baja una unidad de la flota y pasarla a venta | E3 | Must | 9 | 5 | — | S7 |
| 51 | **HU-2.07** Calcular la depreciación mensual | E2 | Must | 9 | 8 | — | S7 |
| 52 | **HU-3.13** Consultar la rentabilidad por contrato y por unidad | E3 | Must | 9 | 5 | — | S8 |
| 53 | **HU-6.07** Registrar cobros y aplicarlos a facturas | E6 | Must | 9 | 5 | 3 SP | S1 → S8 |
| 54 | **HU-6.03** Emitir notas de crédito | E6 | Must | 8 | 5 | — | S8 |
| 55 | **HU-6.05** Anular un documento FEL | E6 | Must | 8 | 5 | — | S8 |
| 56 | **HU-6.08** Registrar retenciones que nos hacen los clientes | E6 | Must | 8 | 3 | — | S8 |
| 57 | **HU-6.09** Registrar y aplicar anticipos de clientes | E6 | Must | 8 | 5 | — | S8 |
| 58 | **HU-6.11** Consultar el estado de cuenta de un cliente | E6 | Must | 8 | 3 | — | S8 |
| 59 | **HU-6.12** Consultar la antigüedad de saldos de clientes | E6 | Must | 8 | 5 | — | S9 |
| 60 | **HU-2.16** Consultar el balance de comprobación y el mayor | E2 | Must | 10 | 5 | 3 SP | S1 → S9 |
| 61 | **HU-2.08** Revaluar saldos en dólares al cierre | E2 | Must | 9 | 5 | — | S9 |
| 62 | **HU-2.10** Conciliar las cuentas bancarias | E2 | Must | 9 | 8 | — | S9 |
| 63 | **HU-2.12** Cerrar un período mensual | E2 | Must | 9 | 5 | — | S9 |
| 64 | **HU-2.13** Reabrir un período cerrado | E2 | Must | 9 | 3 | — | S9 |
| 65 | **HU-2.14** Ejecutar el cierre anual | E2 | Must | 9 | 5 | — | S10 |
| 66 | **HU-2.15** Emitir los libros legales | E2 | Must | 9 | 8 | — | S10 |
| 67 | **HU-7.02** Consultar la rentabilidad de cada unidad en todo su ciclo | E7 | Must | 8 | 5 | 2 SP | S1 → S10 |
| 68 | **HU-7.04** Consultar las unidades por etapa del ciclo | E7 | Must | 8 | 3 | 2 SP | S1 → S10 |
| 69 | **HU-7.01** Consultar estados financieros por línea de negocio | E7 | Must | 7 | 8 | — | S10 |
| 70 | **HU-7.03** Consultar la ocupación y rentabilidad de la flota | E7 | Must | 7 | 5 | — | S10 |
| 71 | **HU-7.07** Consultar la antigüedad de saldos de clientes y proveedores | E7 | Must | 7 | 3 | — | S11 |
| 72 | **HU-7.09** Exportar reportes a PDF y Excel | E7 | Must | 7 | 5 | — | S11 |
| 73 | **HU-10.01** Descargar plantillas de carga y validar archivos | E10 | Must | 7 | 5 | — | S11 |
| 74 | **HU-10.02** Cargar los saldos contables iniciales | E10 | Must | 7 | 3 | — | S11 |
| 75 | **HU-10.03** Cargar la flota con su valor en libros | E10 | Must | 7 | 5 | — | S11 |
| 76 | **HU-10.04** Cargar unidades en importación, en taller y en venta | E10 | Must | 7 | 3 | — | S11 |
| 77 | **HU-10.05** Cargar clientes, proveedores y sus saldos abiertos | E10 | Must | 7 | 5 | — | S11 |
| 78 | **HU-10.07** Cargar el inventario de repuestos | E10 | Must | 7 | 2 | — | S12 |
| 79 | **HU-10.08** Cargar los contratos de alquiler activos | E10 | Must | 7 | 3 | — | S12 |
| 80 | **HU-10.09** Conciliar el arranque y aceptar los saldos | E10 | Must | 7 | 5 | — | S12 |
| 81 | **HU-10.11** Capacitar a los usuarios por rol (habilitación) | E10 | Must | 7 | 2 | — | S12 |
| 82 | **HU-10.12** Dar soporte inicial tras el arranque (habilitación) | E10 | Must | 7 | 2 | — | S12 |
| | **Total (82 historias)** | | | | **369** | **79 SP** | |

### 3.2 Release 2 (40 historias)

| # | Historia | Épica | MoSCoW | Valor | SP | Hecho en S1 | Sprint |
|---|---|---|---|---|---|---|---|
| 83 | **HU-1.03** Importar el catálogo de cuentas existente | E1 | Should | 6 | 5 | — | S13 |
| 84 | **HU-2.04** Programar partidas recurrentes | E2 | Should | 6 | 3 | — | S13 |
| 85 | **HU-4.12** Retener ISR en pagos al exterior | E4 | Should | 5 | 3 | — | S13 |
| 86 | **HU-4.15** Registrar notas de crédito y devoluciones de proveedores | E4 | Should | 5 | 3 | — | S13 |
| 87 | **HU-5.10** Realizar el conteo físico de repuestos | E5 | Should | 5 | 3 | — | S13 |
| 88 | **HU-3.03** Capitalizar una mejora a una unidad de la flota | E3 | Should | 6 | 3 | — | S13 |
| 89 | **HU-3.11** Extender un contrato vigente | E3 | Should | 6 | 3 | — | S13 |
| 90 | **HU-3.14** Alertar sobre el fin de la vida útil en flota | E3 | Should | 6 | 3 | — | S13 |
| 91 | **HU-6.04** Emitir notas de débito | E6 | Should | 5 | 3 | — | S13 |
| 92 | **HU-6.06** Registrar documentos FEL emitidos fuera del sistema | E6 | Should | 5 | 3 | — | S14 |
| 93 | **HU-6.10** Identificar depósitos no aplicados | E6 | Should | 5 | 3 | — | S14 |
| 94 | **HU-2.06** Registrar provisiones con reversión automática | E2 | Should | 6 | 3 | — | S14 |
| 95 | **HU-2.11** Seguir una lista de verificación de cierre | E2 | Should | 6 | 5 | — | S14 |
| 96 | **HU-8.01** Consultar el inventario de unidades en venta | E8 | Must | 6 | 2 | — | S14 |
| 97 | **HU-8.02** Fijar el precio de lista y el precio mínimo | E8 | Must | 6 | 2 | — | S14 |
| 98 | **HU-8.04** Registrar una venta de contado | E8 | Must | 6 | 5 | — | S14 |
| 99 | **HU-8.07** Configurar el tratamiento fiscal de la venta de unidades | E8 | Must | 6 | 3 | — | S14 |
| 100 | **HU-8.08** Registrar vendedores y reglas de comisión | E8 | Must | 6 | 3 | — | S14 |
| 101 | **HU-8.09** Calcular la comisión de cada venta | E8 | Must | 6 | 5 | — | S15 |
| 102 | **HU-8.10** Liquidar comisiones por período | E8 | Must | 6 | 5 | — | S15 |
| 103 | **HU-8.12** Ver el margen de la unidad vendida | E8 | Must | 6 | 3 | — | S15 |
| 104 | **HU-8.05** Registrar una venta financiada | E8 | Must | 6 | 5 | — | S15 |
| 105 | **HU-9.01** Definir planes de crédito | E9 | Must | 6 | 3 | — | S15 |
| 106 | **HU-9.02** Registrar y aprobar un crédito | E9 | Must | 6 | 5 | — | S15 |
| 107 | **HU-9.03** Generar la tabla de amortización | E9 | Must | 6 | 5 | — | S16 |
| 108 | **HU-9.04** Devengar los intereses mensuales | E9 | Must | 6 | 5 | — | S16 |
| 109 | **HU-9.05** Facturar los intereses | E9 | Must | 6 | 5 | — | S16 |
| 110 | **HU-9.06** Registrar el cobro de una cuota | E9 | Must | 6 | 5 | — | S16 |
| 111 | **HU-9.07** Registrar abonos extraordinarios a capital | E9 | Must | 6 | 3 | — | S16 |
| 112 | **HU-9.08** Cancelar un crédito de forma anticipada | E9 | Must | 6 | 3 | — | S16 |
| 113 | **HU-9.09** Calcular la mora y el interés moratorio | E9 | Must | 6 | 5 | — | S17 |
| 114 | **HU-9.10** Calcular la antigüedad de la cartera y la provisión por incobrables | E9 | Must | 6 | 5 | — | S17 |
| 115 | **HU-9.13** Emitir el estado de cuenta del crédito | E9 | Must | 6 | 3 | — | S17 |
| 116 | **HU-9.14** Conciliar la cartera con la contabilidad | E9 | Must | 6 | 3 | — | S17 |
| 117 | **HU-7.05** Consultar la cartera financiada y la mora | E7 | Must | 7 | 5 | — | S17 |
| 118 | **HU-7.06** Consultar las comisiones por vendedor | E7 | Must | 7 | 3 | — | S17 |
| 119 | **HU-7.08** Consultar el inventario de unidades y repuestos | E7 | Should | 4 | 3 | — | S17 |
| 120 | **HU-7.10** Consultar un tablero gerencial | E7 | Should | 4 | 5 | — | S18 |
| 121 | **HU-10.06** Cargar la cartera financiada vigente | E10 | Must | 7 | 5 | — | S18 |
| 122 | **HU-10.10** Operar en paralelo antes del arranque definitivo | E10 | Should | 4 | 3 | — | S18 |
| | **Total (40 historias)** | | | | **150** | **0 SP** | |

### 3.3 Release 3 (8 historias)

| # | Historia | Épica | MoSCoW | Valor | SP | Hecho en S1 | Sprint |
|---|---|---|---|---|---|---|---|
| 123 | **HU-5.08** Validar la garantía de una unidad vendida | E5 | Should | 5 | 3 | — | S19 |
| 124 | **HU-4.10** Registrar compras a particulares con factura especial | E4 | Could | 3 | 3 | — | S19 |
| 125 | **HU-8.03** Reservar una unidad con anticipo | E8 | Should | 3 | 3 | — | S19 |
| 126 | **HU-8.06** Controlar el traspaso de propiedad | E8 | Should | 3 | 3 | — | S19 |
| 127 | **HU-8.11** Registrar la garantía ofrecida al comprador | E8 | Should | 3 | 3 | — | S19 |
| 128 | **HU-9.11** Registrar y liberar la garantía prendaria | E9 | Should | 3 | 2 | — | S19 |
| 129 | **HU-9.12** Recuperar una unidad por impago | E9 | Should | 3 | 5 | — | S19 |
| 130 | **HU-9.15** Reestructurar un crédito | E9 | Could | 1 | 5 | — | S19 |
| | **Total (8 historias)** | | | | **27** | **0 SP** | |
### 3.4 Ajustes por dependencias

El orden por valor se corrigió en estos casos para respetar las dependencias de las historias:

| Historia | Se movió | Motivo |
|---|---|---|
| HU-2.09 Diferencial cambiario realizado | Al S3, con la importación | HU-4.14 (pago a proveedores) lo necesita completo |
| HU-2.07 Depreciación mensual | Al S7, justo después del alta en flota | HU-3.13 (rentabilidad por contrato) la necesita |
| HU-8.05 Venta financiada, HU-9.01 y HU-9.02 | Al mismo sprint (S15) | **HU-8.05 y HU-9.02 dependen una de la otra** en las historias actuales; se construyen juntas. Conviene revisar esa dependencia circular con el equipo. |
| HU-7.05, HU-7.06, HU-7.08, HU-7.10 | Después de E8 y E9 | Dependen de la cartera (HU-9.10), las comisiones (HU-8.09) y el inventario en venta (HU-8.01) |

---

## 4. Plan de sprints

| Sprint | Fechas | Objetivo | Historias | SP |
|---|---|---|---|---|
| **S1** | 19/10 – 30/10/2026 | **Corte transversal: una unidad recorre su ciclo y cada paso genera su partida** | 30 historias en versión del corte + HT-01 | 82 ✅ |
| S2 | 02/11 – 13/11/2026 | Base completa: perfil fiscal, cuentas bancarias, inicio de sesión y partidas | 1.02, 1.04, 1.05, 1.06, 1.09, 1.10, 1.11, 2.01, 2.02, 2.03, 1.01, 1.08 | 27 |
| S3 | 16/11 – 27/11/2026 | Respaldos, reversión, diferencial cambiario e importación con expediente y prorrateo | 1.12, 2.05, 2.09, 4.01, 4.02, 4.04, 4.07, 4.08, 5.01, 5.02, 5.03, 5.07, 4.03, 4.05 | 29 |
| S4 | 30/11 – 11/12/2026 | DUCA, compras locales, retenciones y pagos a proveedores | 4.06, 4.09, 4.11, 4.13, 4.14, 4.16 | 28 |
| *Receso* | 14/12/2026 – 01/01/2027 | | | |
| S5 | 04/01 – 15/01/2027 | Repuestos y subcontratos en taller, FEL con certificador real y contratos completos | 5.04, 5.05, 5.06, 5.09, 6.01, 6.02, 3.01, 3.06, 3.08 | 28 |
| S6 | 18/01 – 29/01/2027 | Parámetros de depreciación, seguros, tarifario, depósitos y cargos (+ margen) | 3.02, 3.04, 3.05, 3.07, 3.09 | 23 |
| S7 | 01/02 – 12/02/2027 | Facturación recurrente, ocupación, baja de flota y depreciación mensual | 3.10, 3.12, 3.15, 2.07 | 26 |
| S8 | 15/02 – 26/02/2027 | Rentabilidad por contrato, cobros, notas de crédito, anulaciones y anticipos | 3.13, 6.07, 6.03, 6.05, 6.08, 6.09, 6.11 | 28 |
| S9 | 01/03 – 12/03/2027 | Antigüedad de saldos, revaluación, conciliación bancaria y cierre mensual | 6.12, 2.16, 2.08, 2.10, 2.12, 2.13 | 28 |
| S10 | 15/03 – 26/03/2027 | Cierre anual, libros legales y primeros reportes gerenciales | 2.14, 2.15, 7.02, 7.04, 7.01, 7.03 | 30 |
| S11 | 29/03 – 09/04/2027 | Reportes restantes del MVP y cargas iniciales | 7.07, 7.09, 10.01, 10.02, 10.03, 10.04, 10.05 | 29 |
| S12 | 12/04 – 23/04/2027 | Conciliación del arranque, capacitación y soporte (+ estabilización) | 10.07, 10.08, 10.09, 10.11, 10.12 | 14 |
| 🚀 | **23/04/2027** | **Release 1 · MVP: arranque con la línea de alquiler** | | |
| S13 | 26/04 – 07/05/2027 | Controles adicionales (Should de E1 a E6) | 1.03, 2.04, 4.12, 4.15, 5.10, 3.03, 3.11, 3.14, 6.04 | 29 |
| S14 | 10/05 – 21/05/2027 | Controles restantes e inicio de la venta de unidades | 6.06, 6.10, 2.06, 2.11, 8.01, 8.02, 8.04, 8.07, 8.08 | 29 |
| S15 | 24/05 – 04/06/2027 | Comisiones, margen y venta financiada con su crédito | 8.09, 8.10, 8.12, 8.05, 9.01, 9.02 | 26 |
| S16 | 07/06 – 18/06/2027 | Amortización, intereses y cobro de cuotas | 9.03, 9.04, 9.05, 9.06, 9.07, 9.08 | 26 |
| S17 | 21/06 – 02/07/2027 | Mora, cartera y reportes de cartera y comisiones | 9.09, 9.10, 9.13, 9.14, 7.05, 7.06, 7.08 | 27 |
| S18 | 05/07 – 16/07/2027 | Tablero, carga de cartera vigente y operación en paralelo (+ estabilización) | 7.10, 10.06, 10.10 | 13 |
| 🚀 | **16/07/2027** | **Release 2 · venta, financiamiento y controles** | | |
| S19 | 19/07 – 30/07/2027 | Funciones deseables | 5.08, 4.10, 8.03, 8.06, 8.11, 9.11, 9.12, 9.15 | 27 |
| 🚀 | **30/07/2027** | **Release 3 · funciones deseables** | | |
> Los sprints 6, 12 y 18 quedan por debajo de la velocidad a propósito. El 12 y el 18 cierran un release y dejan margen para estabilizar y atender lo que surja en la operación en paralelo. El 6 queda corto porque la historia siguiente (HU-3.10, 8 SP) no cabía; ese margen absorbe la integración con el certificador FEL del S5.

### Ceremonias

| Ceremonia | Cuándo | Duración |
|---|---|---|
| Sprint Planning | Primer lunes del sprint | 2 h |
| Daily Scrum | Diario | 15 min |
| Refinamiento con el contador (reglas de contabilización y pendientes) | Miércoles de la semana 1 | 1 h |
| Sprint Review con el cliente | Último viernes del sprint | 1 h |
| Retrospectiva | Último viernes, después de la review | 45 min |

---

## 5. Sprint Backlog del Sprint 1: las 3 tareas prioritarias

**Sprint:** S1 · 19/10 – 30/10/2026
**Objetivo:** una unidad recorre su ciclo, de la compra en EE. UU. al reporte de rentabilidad, y cada paso genera su partida contable ligada al VIN.

El corte se organizó en **3 tareas prioritarias**. Cada una se puede demostrar por sí sola y, juntas, recorren el ciclo completo:

```
 TAREA 1                          TAREA 2                            TAREA 3
 Base contable, multimoneda   →   Costo de la unidad:            →   Ingreso: alquiler, factura,
 y seguridad                      de la compra a la flota            cobro y reportes
 ──────────────────────────       ───────────────────────────        ──────────────────────────
 roles · catálogo · VIN ·         compra USD · gastos ·              contrato · factura FEL ·
 tipo de cambio · partidas ·      aduana · taller · hoja de          cobro con diferencial ·
 separación de funciones ·        costo · alta en flota ·            rentabilidad por unidad ·
 bitácora · balance               partidas automáticas               unidades por etapa
```

### Tarea 1 · Base contable, multimoneda y seguridad — 32 SP

**Historias (versión del corte):** HT-01, HU-1.02, HU-1.04, HU-1.05, HU-1.06, HU-1.07, HU-1.09, HU-1.10, HU-1.11, HU-2.01, HU-2.02, HU-2.16
**Por qué es la primera:** sin catálogo, tipo de cambio, roles y partidas que cuadren no se puede registrar nada. Es la base de las épicas 2 a 10.

| # | Tarea técnica | Horas | Estado |
|---|---|---|---|
| T1.1 | Estructura del proyecto, base de datos con decimal exacto, pruebas y Docker (HT-01) | 6 h | ✅ |
| T1.2 | Usuarios con los cuatro roles y permisos por operación (HU-1.09) | 4 h | ✅ |
| T1.3 | Catálogo inicial con cuentas de agrupación y de detalle, y reglas de línea y VIN por cuenta (HU-1.02, HU-1.04) | 5 h | ✅ |
| T1.4 | Unidades por VIN con dígito verificador, estados e historial (HU-1.05) | 4 h | ✅ |
| T1.5 | Tipo de cambio por fecha; bloqueo si falta o si ya se usó; líneas en USD con monto original (HU-1.06, HU-1.07) | 5 h | ✅ |
| T1.6 | Motor de partidas: cuadre en quetzales, borrador → revisión → contabilizada o devuelta, correlativo (HU-2.01, HU-2.02) | 7 h | ✅ |
| T1.7 | Separación de funciones: quien registra no contabiliza (HU-1.10) | 2 h | ✅ |
| T1.8 | Bitácora inmutable con filtros por usuario, VIN y entidad (HU-1.11) | 3 h | ✅ |
| T1.9 | Balance de comprobación y mayor con filtros por línea de negocio y VIN (HU-2.16) | 4 h | ✅ |
| T1.10 | Pruebas automatizadas de la tarea (18 pruebas) | 5 h | ✅ |

### Tarea 2 · Costo de la unidad: de la compra en EE. UU. a la flota — 28 SP

**Historias (versión del corte):** HU-4.01, HU-4.02, HU-4.04, HU-4.07, HU-4.08, HU-5.01, HU-5.02, HU-5.03, HU-5.07, HU-3.01, HU-2.03
**Por qué es la segunda:** el criterio de éxito de la Épica 4 (cada unidad con su costo desglosado al darse de alta) es el que hace posible la rentabilidad por vehículo, que es lo que la gerencia quiere ver.

| # | Tarea técnica | Horas | Estado |
|---|---|---|---|
| T2.1 | Proveedores locales (NIT validado) y del exterior (HU-4.01) | 2 h | ✅ |
| T2.2 | Compra en USD: crea la unidad en tránsito, la cuenta por pagar y la partida a unidades en proceso (HU-4.02) | 5 h | ✅ |
| T2.3 | Gastos de importación por VIN; el IVA de importación va a crédito fiscal y no al costo (HU-4.04) | 4 h | ✅ |
| T2.4 | Etapas de importación: tránsito → aduana → taller → lista (HU-4.07) | 2 h | ✅ |
| T2.5 | Órdenes de taller coherentes con el estado de la unidad, mano de obra con tarifa interna (HU-5.01 a HU-5.03) | 5 h | ✅ |
| T2.6 | Cierre de orden con destino contable: reacondicionamiento capitaliza, mantenimiento es gasto (HU-5.07) | 3 h | ✅ |
| T2.7 | Partidas automáticas por documento, ligadas a su origen (HU-2.03) | 4 h | ✅ |
| T2.8 | Hoja de costo por grupo, que cuadra con el mayor (HU-4.08) | 3 h | ✅ |
| T2.9 | Alta en flota al costo de la hoja, con vida útil y valor residual (HU-3.01) | 3 h | ✅ |
| T2.10 | Pruebas automatizadas de la tarea (12 pruebas) | 4 h | ✅ |

### Tarea 3 · Ingreso: alquiler, factura, cobro y reportes — 22 SP

**Historias (versión del corte):** HU-6.01, HU-3.06, HU-3.08, HU-6.02, HU-6.07, HU-2.09, HU-7.02, HU-7.04
**Por qué es la tercera:** el alquiler es la línea principal de ingresos y cierra el ciclo con lo que ve la gerencia.

| # | Tarea técnica | Horas | Estado |
|---|---|---|---|
| T3.1 | Clientes con NIT validado, CUI o pasaporte y sin duplicados (HU-6.01) | 2 h | ✅ |
| T3.2 | Contrato de alquiler con validación de disponibilidad; cierre con días y kilometraje (HU-3.06, HU-3.08) | 4 h | ✅ |
| T3.3 | Factura con IVA incluido separado, en Q o USD, regla de Consumidor Final y certificación FEL simulada (HU-6.02) | 5 h | ✅ |
| T3.4 | Cobro total o parcial con diferencial cambiario realizado (HU-6.07, HU-2.09) | 4 h | ✅ |
| T3.5 | Reportes de rentabilidad por unidad y unidades por etapa, desde el mayor (HU-7.02, HU-7.04) | 4 h | ✅ |
| T3.6 | Prueba del ciclo completo y script de demostración | 3 h | ✅ |
| T3.7 | Pruebas automatizadas de la tarea (10 pruebas) | 3 h | ✅ |

**Total:** 82 SP · 105 h · **Completado: 82 de 82 SP** (versiones del corte)

### Lo que el corte implementa y lo que falta de cada historia

| Historia | Épica | Hecho en el corte | Falta (sprint) |
|---|---|---|---|
| **HU-1.02** Mantener el catálogo de cuentas | E1 | Catálogo inicial sembrado y alta de cuentas; falta máscara de niveles e inactivación | 2 SP (S2) |
| **HU-1.04** Configurar las dimensiones analíticas | E1 | Líneas de negocio y exigencia de VIN por cuenta; falta línea obligatoria configurable | 1 SP (S2) |
| **HU-1.05** Registrar y validar unidades por VIN | E1 | VIN validado, estados e historial; falta placa/motor y ficha con todos los documentos | 2 SP (S2) |
| **HU-1.06** Cargar el tipo de cambio de referencia del Banguat | E1 | Carga manual y bloqueo si falta o ya se usó; falta servicio del Banguat | 3 SP (S2) |
| **HU-1.07** Registrar transacciones en dólares | E1 | Monto original, TC y quetzales; TC distinto con justificación en bitácora | Completa ✅ |
| **HU-1.09** Administrar usuarios y roles | E1 | Cuatro roles con permisos; falta contraseña, bloqueo e inactividad | 3 SP (S2) |
| **HU-1.10** Separar funciones de registro y aprobación | E1 | Quien registra no contabiliza; faltan montos de aprobación configurables | 2 SP (S2) |
| **HU-1.11** Consultar la bitácora de cambios | E1 | Bitácora inmutable con filtros; falta valores anteriores/nuevos y exportar a Excel | 1 SP (S2) |
| **HU-2.01** Registrar una partida manual | E2 | Partida manual con cuadre y USD; falta adjuntar soporte | 2 SP (S2) |
| **HU-2.02** Revisar y contabilizar partidas | E2 | Borrador → revisión → contabilizada o devuelta; falta contabilizar en lote | 2 SP (S2) |
| **HU-2.03** Generar partidas automáticas desde los módulos | E2 | Compra, gastos, taller, alta, factura y cobro generan su partida; reglas aún fijas en código | 3 SP (S2) |
| **HU-2.09** Calcular el diferencial cambiario realizado | E2 | Diferencial realizado en cobros; falta en pagos y parciales con revaluación | 2 SP (S3) |
| **HU-2.16** Consultar el balance de comprobación y el mayor | E2 | Balance y mayor con filtros por línea y VIN; falta navegar al documento | 2 SP (S9) |
| **HU-3.01** Dar de alta una unidad como activo fijo de la flota | E3 | Alta desde la hoja de costo con partida; falta aprobación cuando registra el auxiliar | 2 SP (S5) |
| **HU-3.06** Registrar un contrato de alquiler | E3 | Contrato con validación de disponibilidad; falta depósito, combustible e impresión | 2 SP (S5) |
| **HU-3.08** Cerrar un contrato al devolver la unidad | E3 | Días y kilometraje; faltan combustible, daños y paso a taller | 1 SP (S5) |
| **HU-4.01** Registrar proveedores locales y del exterior | E4 | Proveedor local/exterior con NIT validado; falta régimen y retenciones | 1 SP (S3) |
| **HU-4.02** Registrar la compra de una unidad en EE. UU. | E4 | Compra USD crea unidad, CxP y partida; faltan adjuntos | 1 SP (S3) |
| **HU-4.04** Registrar los gastos de importación | E4 | Gastos por VIN; IVA de importación como crédito fiscal; falta expediente | 2 SP (S3) |
| **HU-4.07** Seguir el estado de la unidad durante la importación | E4 | Tránsito → aduana → taller → lista; falta exigir DUCA y días por etapa | 1 SP (S3) |
| **HU-4.08** Consultar la hoja de costo de una unidad | E4 | Hoja de costo por grupo y cuadre con el mayor; falta exportar PDF/Excel | 1 SP (S3) |
| **HU-5.01** Abrir una orden de trabajo ligada a un VIN | E5 | Orden por VIN coherente con el estado; falta ligar a contrato y postventa | 1 SP (S3) |
| **HU-5.02** Configurar las tarifas de mano de obra | E5 | Tarifa horaria única configurable; falta tarifa por mecánico y de venta | 1 SP (S3) |
| **HU-5.03** Registrar mano de obra en la orden | E5 | Horas costeadas; falta comparar mano de obra aplicada vs. real | 1 SP (S3) |
| **HU-5.07** Cerrar la orden y generar su destino contable | E5 | Reacondicionamiento capitaliza, mantenimiento es gasto; faltan mejora, garantía y facturable | 2 SP (S3) |
| **HU-6.01** Registrar clientes | E6 | Cliente con NIT validado, CUI o pasaporte y sin duplicados; falta consulta a SAT | 1 SP (S5) |
| **HU-6.02** Emitir una factura FEL | E6 | Factura con IVA, USD y regla de Consumidor Final; certificación FEL simulada | 8 SP (S5) |
| **HU-6.07** Registrar cobros y aplicarlos a facturas | E6 | Cobro total o parcial con diferencial; falta aplicar a varias facturas y comisión de tarjeta | 2 SP (S8) |
| **HU-7.02** Consultar la rentabilidad de cada unidad en todo su ciclo | E7 | Costo, ingresos y mantenimiento por VIN desde el mayor; falta depreciación y venta | 3 SP (S10) |
| **HU-7.04** Consultar las unidades por etapa del ciclo | E7 | Cantidad y valor por etapa; falta días promedio y alertas | 1 SP (S10) |
---

## 6. Resultado de la primera iteración

### Qué se entregó

Una API funcional en [`../backend`](../backend/README.md) donde una unidad recorre su ciclo y la contabilidad cuadra al final. La maqueta HTML/JS puede consumirla directamente.

| Épica | Qué ya funciona |
|---|---|
| E1 Configuración, multimoneda y seguridad | Cuatro roles con permisos; catálogo con reglas de línea y VIN; VIN con dígito verificador; tipo de cambio por fecha; USD con monto original; bitácora |
| E2 Contabilidad | Partidas manuales con flujo de aprobación y separación de funciones; partidas automáticas; diferencial cambiario en cobros; balance y mayor por VIN |
| E4 Importación | Compra en USD; gastos de importación con IVA a crédito fiscal; etapas; hoja de costo |
| E5 Taller | Orden de trabajo por VIN; mano de obra costeada; cierre con destino contable |
| E3 Flota y alquileres | Alta en flota al costo de la hoja; contrato con disponibilidad; cierre con días y kilometraje |
| E6 Facturación y CxC | Clientes; factura con IVA en Q o USD (FEL simulada); cobros |
| E7 Reportes | Rentabilidad por unidad y capital invertido por etapa, visibles para el rol gerencia |

### Verificación

**41 pruebas automatizadas, todas aprobadas.**

| Archivo | Tarea | Pruebas |
|---|---|---|
| `test_e1_e2_base.py` | Tarea 1 | 18 |
| `test_e4_e5_e3_costo.py` | Tarea 2 | 12 |
| `test_e3_e6_e7_ingreso.py` | Tarea 3 | 10 |
| `test_ciclo_completo.py` | Ciclo completo de una unidad | 1 |

### Guion de la demostración

`python scripts/demo_ciclo.py` recorre el ciclo de un Honda Accord 2019 contra la API:

| Paso | Épica | Qué se ve |
|---|---|---|
| 1 | E1 | El contador carga los tipos de cambio del 01/10 al 27/10 |
| 2 | E4 | Compra en Copart por USD 8,500 → unidad en tránsito, cuenta por pagar y partida por Q65,450 |
| 3 | E4 | Flete USD 900 y DAI Q3,000 al costo; IVA de importación Q8,200 a crédito fiscal |
| 4 | E5 | Reacondicionamiento: 16 h × Q75 = Q1,200 capitalizado |
| 5 | E4 | Hoja de costo: compra Q65,450 + importación Q9,948 + taller Q1,200 = **Q76,598**, cuadra con el mayor |
| 6 | E3 | Alta en flota al costo de la hoja |
| 7 | E3 | Contrato de 6 días a USD 56 con Turismo Maya, S.A. |
| 8 | E6, E2 | Factura USD 336 (Q2,597.28 a TC 7.73); cobro a TC 7.75 → **ganancia cambiaria Q6.72** |
| 9 | E1, E2 | El contador no puede contabilizar su propia partida; la gerente financiera sí |
| 10 | E2 | Balance de comprobación: debe = haber |
| 11 | E7 | La gerencia ve la rentabilidad de la unidad y no puede registrar operaciones |

### Simplificaciones deliberadas del corte

| Simplificación | Se resuelve en |
|---|---|
| El usuario se identifica con el encabezado `X-Usuario`, sin contraseña | S2 (HU-1.09) |
| La certificación FEL es simulada (serie `SIM-A`, autorización generada) | S5 (HU-6.02, tras elegir certificador) |
| El tipo de cambio se carga a mano | S2 (HU-1.06, servicio del Banguat) |
| Las reglas de contabilización están fijas en el código | S2 (HU-2.03, reglas configurables) |
| Los gastos se ligan directo al VIN, sin expediente ni prorrateo | S3 (HU-4.03, HU-4.05) |
| Sólo mano de obra en taller; sin repuestos ni subcontratos | S5 (HU-5.04 a HU-5.06) |
| Sin depósitos en garantía ni cargos adicionales en contratos | S6 (HU-3.07, HU-3.09) |
| La rentabilidad no incluye depreciación, seguro ni marchamo | S7 a S10 |
| Esquema de base de datos sin migraciones | S2 |

---

## 7. Definiciones de listo y terminado

Se mantienen las del [README de historias](../user-stories/README.md), con dos agregados por el enfoque transversal:

**Definición de listo:** las del equipo, más:
- Si la historia ya tiene versión del corte, el refinamiento identifica qué criterios faltan.

**Definición de terminado:** las del equipo, más:
- Cada criterio de aceptación tiene al menos una prueba automatizada, y la prueba del ciclo completo sigue pasando.

---

## 8. Riesgos y pendientes que afectan el plan

| # | Riesgo o pendiente | Impacto | Antes de | Mitigación |
|---|---|---|---|---|
| 1 | **¿Hay créditos vigentes hoy?** | Alto | S2 | Si los hay, la Épica 9 (Must) y HU-10.06 suben a Release 1 y el MVP se extiende unos 3 sprints |
| 2 | **Certificador FEL sin elegir** | Alto | S5 | La factura está simulada; elegir el certificador durante S2–S4 |
| 3 | **Reglas de contabilización por validar con el contador** | Alto | S2 | El catálogo del corte es una propuesta; revisarlo en el primer refinamiento |
| 4 | **Quién registra la operación** (contratos, taller, ventas) | Medio | S5 | Hoy lo hace el rol auxiliar; si hay usuarios operativos, se agrega un rol en S2 |
| 5 | Régimen de ISR y calidad de agente de retención | Medio | S4 | Bloquea HU-4.11 y HU-4.12 |
| 6 | Depreciación fiscal frente a financiera | Medio | S6 | Bloquea HU-3.02 y HU-2.07 |
| 7 | Dependencia circular entre HU-8.05 y HU-9.02 | Bajo | S15 | Se planificaron en el mismo sprint; revisar la redacción de las historias |
| 8 | Velocidad real del equipo | Medio | S3 | Recalibrar el plan al cierre de S2 y S3 |
| 9 | La maqueta HTML/JS y la API pueden divergir | Medio | Demo | La maqueta usa los endpoints documentados en Swagger |

La lista completa de pendientes con el cliente está en [user-stories/README.md](../user-stories/README.md#pendientes-con-el-cliente-que-afectan-historias).
