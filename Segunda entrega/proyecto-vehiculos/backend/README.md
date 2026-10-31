# Backend · prototipo técnico del Sprint 1

API del corte transversal del Sprint 1 según [`Sprint1.md`](../../../planning/Sprint1.md): **de la compra al alta en flota**. Cada paso genera su partida contable ligada al VIN y queda en la bitácora:

```
Compra en EE. UU. (USD) → gastos de importación → taller → hoja de costo → alta en flota
```

Es un **prototipo técnico**: valida el stack candidato y las reglas del corte. No se cuenta como avance aceptado del Sprint 1 (ver la revisión en [`RevisionSprint1.md`](../../../planning/RevisionSprint1.md)).

## Cómo ejecutarlo

> Si ya tenía un `sistema.db` de una versión anterior, **bórrelo** antes de arrancar: todavía no hay migraciones (tarea A1 del Sprint 1).

### Con Python 3.11 o superior

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

En otra terminal, con el entorno activado y dentro de `backend`:

```bash
python scripts/demo_ciclo.py      # guion de 9 pasos de Sprint1.md, sección 10 (requiere base vacía)
pytest                            # 47 pruebas
```

### Con Docker

```bash
cd backend
docker compose up -d --build
docker compose exec api python scripts/demo_ciclo.py
docker compose exec api pytest
docker compose down -v            # borra la base para repetir la demo
```

### Integración continua

`.github/workflows/pruebas.yml` corre las pruebas en GitHub en cada `push` y `pull request`.

## Usuarios y roles

Al iniciar con una base vacía se siembran el catálogo de ejemplo y cuatro cuentas. **Contraseña inicial de todas: `Demo2026!`** (sólo ambiente de pruebas; se cambia con `SISTEMA_PASSWORD_INICIAL`).

| Usuario | Nombre | Rol | Puede |
|---|---|---|---|
| `aux` | Ana López | Auxiliar contable | Registrar compras, gastos, órdenes, horas y partidas |
| `contador` | Carlos Pérez | Contador | Además: contabilizar, cerrar órdenes, dar de alta en flota, tipo de cambio, bitácora |
| `gerente` | María Gómez | Gerente financiero | Además: crear usuarios |
| `gerencia` | Luis Ramírez | Gerencia | Sólo consulta; no puede registrar |

Quien registra una partida no puede contabilizarla, aunque su rol lo permita.

**En Swagger (`/docs`):** ejecute `POST /api/v1/auth/login` con usuario y contraseña, copie el `token`, presione **Authorize** (arriba a la derecha) y péguelo.

### Módulos fuera del alcance del Sprint 1

El código de alquiler, facturación, cobros y reportes existe como adelanto, pero el Sprint 1 no lo incluye. Está **apagado por defecto**; se enciende con `SISTEMA_MODULOS_INGRESO=true`. Las pruebas lo cubren igualmente.

## Conectar la maqueta HTML/JS

La API tiene CORS habilitado: la maqueta puede llamarla con `fetch` aunque se abra con doble clic.

```js
const API = "http://localhost:8000/api/v1";
let token = null;

async function login(usuario, password) {
  const r = await fetch(API + "/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, password }),
  });
  const datos = await r.json();
  if (!r.ok) throw new Error(datos.detail);
  token = datos.token;            // datos.usuario.rol sirve para armar el menú por rol
  return datos.usuario;
}

async function api(metodo, ruta, cuerpo) {
  const r = await fetch(API + ruta, {
    method: metodo,
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  const datos = await r.json().catch(() => null);
  if (!r.ok) throw new Error(datos?.detail ?? `Error ${r.status}`);  // mensajes en español
  return datos;
}

// Ejemplo: iniciar sesión y consultar la hoja de costo de una unidad
await login("contador", "Demo2026!");
const unidad = await api("GET", "/unidades/vin/1HGCM82633A004352");
const hoja = await api("GET", `/unidades/${unidad.id}/hoja-costo`);
```

Cuando se incumple una regla, la API responde 4xx con un mensaje en `detail` listo para mostrar (por ejemplo: *"No hay tipo de cambio registrado para el 01/10/2026"*). Los montos llegan como números y las fechas como `AAAA-MM-DD`.

### Endpoints por pantalla

Todos bajo `/api/v1`. Ejemplos de cuerpo y respuesta en `/docs`.

**Sesión y configuración (E1)**

| Acción | Ruta |
|---|---|
| Iniciar sesión | `POST /auth/login` `{usuario, password}` → `{token, usuario}` |
| Cerrar sesión | `POST /auth/logout` |
| Usuario actual | `GET /yo` |
| Usuarios | `GET /usuarios` · `POST /usuarios` (gerente) |
| Catálogo de cuentas | `GET /cuentas` · `GET /cuentas/arbol` (jerárquico) · `POST /cuentas` |
| Tipo de cambio | `GET /tipos-cambio` · `POST /tipos-cambio` `{fecha, valor}` |
| Bitácora (con valores anteriores y nuevos) | `GET /bitacora?usuario=&vin=&entidad=` |

**Unidades e importación (E1, E4)**

| Acción | Ruta |
|---|---|
| Unidades | `GET /unidades?estado=` · `GET /unidades/{id}` · `GET /unidades/vin/{vin}` |
| Proveedores | `GET /proveedores` · `POST /proveedores` |
| Compra en EE. UU. | `POST /compras` `{proveedor_id, fecha, numero_lote, vin, marca, linea, modelo_anio, precio_usd, cargos_usd}` |
| Gasto de importación | `POST /gastos-importacion` `{unidad_id, proveedor_id, concepto, fecha, moneda, monto}` |
| Avanzar etapa | `POST /unidades/{id}/estado` `{estado: "EN_ADUANA" \| "LISTA", documento}` |
| Hoja de costo | `GET /unidades/{id}/hoja-costo` |
| Cuentas por pagar | `GET /cuentas-por-pagar` |

**Taller y flota (E5, E3)**

| Acción | Ruta |
|---|---|
| Órdenes | `GET /ordenes` · `POST /ordenes` `{unidad_id, tipo, descripcion, responsable, fecha}` |
| Mano de obra | `POST /ordenes/{id}/mano-obra` `{mecanico, fecha, horas, descripcion}` |
| Cerrar orden | `POST /ordenes/{id}/cerrar` `{fecha, justificacion}` (contador) |
| Alta en flota | `POST /unidades/{id}/alta-flota` `{fecha, vida_util_meses, valor_residual}` (contador) |

**Alquiler y facturación (E3, E6) · apagado en el Sprint 1**

| Acción | Ruta |
|---|---|
| Clientes | `GET /clientes` · `POST /clientes` `{tipo, nombre, nit \| cui \| pasaporte}` |
| Contratos | `GET /contratos?estado=` · `POST /contratos` `{cliente_id, unidad_id, fecha_salida, fecha_prevista, tarifa_diaria, moneda}` |
| Cerrar contrato | `POST /contratos/{id}/cerrar` `{fecha_devolucion, km_entrada}` |
| Facturar contrato | `POST /contratos/{id}/facturar` `{fecha, consumidor_final}` |
| Facturas | `GET /facturas?con_saldo=true` |
| Cobros | `POST /facturas/{id}/cobros` `{fecha, forma, monto, referencia}` · `GET /facturas/{id}/cobros` |

**Contabilidad (E2)**

| Acción | Ruta |
|---|---|
| Partidas | `GET /partidas?estado=` · `GET /partidas/{id}` · `POST /partidas` · `PUT /partidas/{id}` (corregir borrador o devuelta) |
| Flujo de aprobación | `POST /partidas/{id}/enviar` · `/contabilizar` · `/devolver` `{comentario}` |
| Balance de comprobación | `GET /contabilidad/balance?desde=&hasta=&linea_negocio=&vin=` |
| Mayor de una cuenta | `GET /contabilidad/mayor/{codigo}?vin=` |

**Reportes (E7) · apagado en el Sprint 1**

| Acción | Ruta |
|---|---|
| Unidades y capital por etapa | `GET /reportes/unidades-por-etapa` |
| Rentabilidad por unidad | `GET /reportes/rentabilidad-unidades?estado=` |

### Estados de una unidad

```
EN_TRANSITO ──► EN_ADUANA ──(abrir orden)──► EN_TALLER ──► LISTA ──(alta)──► EN_FLOTA ⇄ EN_TALLER
  (compra)                                                                  (mantenimiento)
```

## Catálogo de cuentas del corte

| Código | Cuenta | VIN |
|---|---|---|
| 1.1.01 / 1.1.02 | Bancos en quetzales / dólares | — |
| 1.1.03 / 1.1.04 | Clientes en quetzales / dólares | Opcional |
| 1.1.05 | IVA crédito fiscal | Opcional |
| 1.1.06 | Unidades en proceso (importación y reacondicionamiento) | Obligatorio |
| 1.2.01 | Activo fijo – flota | Obligatorio |
| 2.1.01 / 2.1.02 | Proveedores locales / del exterior | Opcional |
| 2.1.03 | IVA débito fiscal | Opcional |
| 3.1.01 | Capital social | — |
| 4.1.01 | Ingresos por alquiler | Obligatorio |
| 5.1.01 | Mano de obra aplicada – taller | — |
| 6.1.01 | Mantenimiento de flota | Obligatorio |
| 6.1.02 | Gastos de administración | — |
| 7.1.01 | Diferencial cambiario realizado | — |

Es una propuesta para el corte; el catálogo definitivo se valida con el contador (HU-1.02).

## Configuración

| Variable | Por defecto | Uso |
|---|---|---|
| `SISTEMA_DB_URL` | `sqlite:///./sistema.db` | Base de datos |
| `SISTEMA_TASA_IVA` | `0.12` | IVA (tarifas con IVA incluido) |
| `SISTEMA_UMBRAL_CF` | `2500` | Monto desde el que no se factura a Consumidor Final (verificar el umbral vigente de la SAT) |
| `SISTEMA_TARIFA_HORA_TALLER` | `75` | Tarifa horaria interna de mano de obra (Q) |
| `SISTEMA_PASSWORD_INICIAL` | `Demo2026!` | Contraseña de las cuentas sembradas |
| `SISTEMA_HORAS_SESION` | `8` | Duración de la sesión |
| `SISTEMA_MODULOS_INGRESO` | `false` | Enciende alquiler, facturación, cobros y reportes |

## Estructura

```
backend/
├── app/
│   ├── main.py              # App, CORS, errores y datos iniciales
│   ├── models.py            # Tablas de las épicas 1 a 7
│   ├── schemas.py           # Validación de entrada y salida
│   ├── deps.py              # Sesión actual y matriz de permisos por rol
│   ├── seguridad.py         # Hash de contraseñas y sesiones
│   ├── auditoria.py         # Bitácora automática con valores anteriores y nuevos
│   ├── routers/             # base (E1, E2) · ciclo (E4, E5, E3) · ingreso (E3, E6, E7)
│   └── services/            # Reglas de negocio, sin dependencias HTTP
│       ├── base.py          #   errores, bitácora, VIN, NIT, catálogo inicial
│       ├── contabilidad.py  #   tipo de cambio, partidas, balance y mayor
│       ├── ciclo.py         #   compra, importación, taller, hoja de costo, alta
│       └── ingreso.py       #   clientes, contratos, factura, cobro, reportes
├── tests/                   # Una prueba por criterio de aceptación del corte
├── scripts/demo_ciclo.py    # Demostración del ciclo completo
└── Dockerfile · docker-compose.yml
```
