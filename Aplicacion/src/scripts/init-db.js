// Crea el esquema y siembra los datos iniciales:  npm run db:init
// Con --demo agrega unidades y órdenes de ejemplo para las maquetas:  npm run db:demo
// Es idempotente: se puede ejecutar varias veces.
const fs = require('node:fs');
const path = require('node:path');
const config = require('../config');
const { pool, conTransaccion } = require('../config/db');
const { hashPassword } = require('../services/seguridad');

// Catálogo mínimo del corte (HU-1.02); el definitivo se valida con el contador.
// [código, nombre, tipo, naturaleza, es_detalle, monetaria_usd, exige_vin, línea por defecto]
const CATALOGO = [
  ['1', 'ACTIVO', 'ACTIVO', 'DEUDORA', false, false, 'NO_APLICA', null],
  ['1.1', 'Activo corriente', 'ACTIVO', 'DEUDORA', false, false, 'NO_APLICA', null],
  ['1.1.01', 'Bancos – quetzales', 'ACTIVO', 'DEUDORA', true, false, 'NO_APLICA', 'ADMINISTRACION'],
  ['1.1.02', 'Bancos – dólares', 'ACTIVO', 'DEUDORA', true, true, 'NO_APLICA', 'ADMINISTRACION'],
  ['1.1.03', 'Clientes – quetzales', 'ACTIVO', 'DEUDORA', true, false, 'OPCIONAL', null],
  ['1.1.04', 'Clientes – dólares', 'ACTIVO', 'DEUDORA', true, true, 'OPCIONAL', null],
  ['1.1.05', 'IVA crédito fiscal', 'ACTIVO', 'DEUDORA', true, false, 'OPCIONAL', 'ADMINISTRACION'],
  ['1.1.06', 'Unidades en proceso (importación y reacondicionamiento)', 'ACTIVO', 'DEUDORA', true, false, 'OBLIGATORIO', 'ALQUILER'],
  ['1.2', 'Activo no corriente', 'ACTIVO', 'DEUDORA', false, false, 'NO_APLICA', null],
  ['1.2.01', 'Activo fijo – flota', 'ACTIVO', 'DEUDORA', true, false, 'OBLIGATORIO', 'ALQUILER'],
  ['2', 'PASIVO', 'PASIVO', 'ACREEDORA', false, false, 'NO_APLICA', null],
  ['2.1', 'Pasivo corriente', 'PASIVO', 'ACREEDORA', false, false, 'NO_APLICA', null],
  ['2.1.01', 'Proveedores locales', 'PASIVO', 'ACREEDORA', true, false, 'OPCIONAL', null],
  ['2.1.02', 'Proveedores del exterior', 'PASIVO', 'ACREEDORA', true, true, 'OPCIONAL', null],
  ['2.1.03', 'IVA débito fiscal', 'PASIVO', 'ACREEDORA', true, false, 'OPCIONAL', 'ADMINISTRACION'],
  ['3', 'PATRIMONIO', 'PATRIMONIO', 'ACREEDORA', false, false, 'NO_APLICA', null],
  ['3.1.01', 'Capital social', 'PATRIMONIO', 'ACREEDORA', true, false, 'NO_APLICA', 'ADMINISTRACION'],
  ['4', 'INGRESOS', 'INGRESO', 'ACREEDORA', false, false, 'NO_APLICA', null],
  ['4.1.01', 'Ingresos por alquiler', 'INGRESO', 'ACREEDORA', true, false, 'OBLIGATORIO', 'ALQUILER'],
  ['5', 'COSTOS', 'COSTO', 'DEUDORA', false, false, 'NO_APLICA', null],
  ['5.1.01', 'Mano de obra aplicada – taller', 'COSTO', 'ACREEDORA', true, false, 'NO_APLICA', 'TALLER'],
  ['6', 'GASTOS', 'GASTO', 'DEUDORA', false, false, 'NO_APLICA', null],
  ['6.1.01', 'Mantenimiento de flota', 'GASTO', 'DEUDORA', true, false, 'OBLIGATORIO', 'ALQUILER'],
  ['6.1.02', 'Gastos de administración', 'GASTO', 'DEUDORA', true, false, 'NO_APLICA', 'ADMINISTRACION'],
  ['7', 'OTROS INGRESOS Y GASTOS', 'GASTO', 'DEUDORA', false, false, 'NO_APLICA', null],
  ['7.1.01', 'Diferencial cambiario realizado', 'GASTO', 'DEUDORA', true, false, 'NO_APLICA', 'ADMINISTRACION'],
];

const USUARIOS = [
  ['aux', 'Ana López', 'AUXILIAR'],
  ['contador', 'Carlos Pérez', 'CONTADOR'],
  ['gerente', 'María Gómez', 'GERENTE_FINANCIERO'],
  ['gerencia', 'Luis Ramírez', 'GERENCIA'],
];

// ---- Datos de demostración (--demo) -------------------------------------------------------
// [marca, línea, año, color, tipo, placa, estado, km]
const UNIDADES_DEMO = [
  ['Mazda', 'CX-5', 2018, 'Gris', 'SUV', 'P-118XQL', 'EN_TALLER', 64200],
  ['Toyota', 'Yaris', 2019, 'Blanco', 'Sedán', 'P-402MNB', 'EN_TALLER', 41800],
  ['Honda', 'Civic', 2017, 'Negro', 'Sedán', 'P-775DKS', 'EN_FLOTA', 88300],
  ['Ford', 'Ranger', 2018, 'Rojo', 'Pickup', 'P-263VBH', 'EN_TALLER', 97100],
  ['Hyundai', 'Santa Fe', 2019, 'Azul', 'SUV', 'P-690TRE', 'EN_TALLER', 52600],
  ['Nissan', 'Sentra', 2018, 'Plata', 'Sedán', 'P-337FGW', 'EN_FLOTA', 73900],
  ['Suzuki', 'Swift', 2018, 'Blanco', 'Hatchback', 'P-914LCA', 'EN_TALLER', 58400],
  ['Toyota', 'Corolla', 2019, 'Blanco', 'Sedán', 'P-482KLM', 'EN_FLOTA', 45200],
  ['Kia', 'Sportage', 2020, 'Gris', 'SUV', 'P-219CDF', 'EN_FLOTA', 31900],
  ['Honda', 'CR-V', 2018, 'Azul', 'SUV', 'P-367WQZ', 'EN_FLOTA', 66700],
  ['Mazda', 'Mazda 3', 2019, 'Rojo', 'Sedán', 'P-128SPL', 'EN_FLOTA', 39800],
  ['Chevrolet', 'Spark', 2018, 'Amarillo', 'Hatchback', 'P-843MDE', 'EN_FLOTA', 54100],
  ['Hyundai', 'Tucson', 2019, 'Plata', 'SUV', 'P-312RUC', 'EN_FLOTA', 47300],
  ['Kia', 'Rio', 2018, 'Negro', 'Sedán', 'P-996ZNB', 'EN_FLOTA', 61000],
  ['Hyundai', 'Elantra', 2018, 'Gris', 'Sedán', null, 'EN_TRANSITO', 0],
  ['Toyota', 'Hilux', 2019, 'Blanco', 'Pickup', null, 'EN_ADUANA', 0],
  ['Nissan', 'Frontier', 2017, 'Negro', 'Pickup', null, 'LISTA', 0],
  ['Toyota', 'RAV4', 2020, 'Rojo', 'SUV', null, 'EN_TRANSITO', 0],
  ['Ford', 'Escape', 2019, 'Azul', 'SUV', null, 'EN_ADUANA', 0],
];

// [placa, tipo, descripción, responsable, apertura, cierre|null, horas]
const ORDENES_DEMO = [
  ['P-118XQL', 'MANTENIMIENTO', 'Cambio de frenos y suspensión delantera', 'Carlos M.', '2026-10-22', null, 12],
  ['P-402MNB', 'REACONDICIONAMIENTO', 'Revisión general de importación', 'Luis R.', '2026-10-29', null, 0],
  ['P-775DKS', 'MANTENIMIENTO', 'Servicio de 60,000 km', 'Pedro A.', '2026-10-25', '2026-10-27', 6],
  ['P-263VBH', 'MANTENIMIENTO', 'Reparación de transmisión', 'Carlos M.', '2026-10-18', null, 8],
  ['P-690TRE', 'MANTENIMIENTO', 'Pintura y enderezado de puerta', 'Marvin J.', '2026-10-27', null, 0],
  ['P-337FGW', 'MANTENIMIENTO', 'Cambio de embrague', 'Luis R.', '2026-10-20', '2026-10-24', 9],
  ['P-914LCA', 'MANTENIMIENTO', 'Sistema eléctrico y alternador', 'Pedro A.', '2026-10-24', null, 15],
];

const TARIFA_HORA = '75';

async function sembrarBase(cliente) {
  for (const fila of CATALOGO) {
    await cliente.query(
      `INSERT INTO cuentas (codigo, nombre, tipo, naturaleza, es_detalle, monetaria_usd, exige_vin, linea_defecto)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT (codigo) DO NOTHING`,
      fila,
    );
  }
  for (const [usuario, nombre, rol] of USUARIOS) {
    await cliente.query(
      `INSERT INTO usuarios (usuario, nombre, rol, password_hash)
       VALUES ($1,$2,$3,$4) ON CONFLICT (usuario) DO NOTHING`,
      [usuario, nombre, rol, hashPassword(config.passwordInicial)],
    );
  }
}

async function sembrarDemo(cliente) {
  const { rows } = await cliente.query('SELECT count(*)::int AS n FROM unidades');
  if (rows[0].n > 0) {
    console.log('Ya hay unidades: no se agregan datos de demostración.');
    return;
  }

  const idPorPlaca = {};
  for (const [i, [marca, linea, anio, color, tipo, placa, estado, km]] of UNIDADES_DEMO.entries()) {
    const vin = `KM0DEM${String(i + 1).padStart(11, '0')}`; // 17 caracteres, sin I, O ni Q
    const r = await cliente.query(
      `INSERT INTO unidades (vin, marca, linea, modelo_anio, color, tipo_vehiculo, placa, estado, kilometraje)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING id`,
      [vin, marca, linea, anio, color, tipo, placa, estado, km],
    );
    if (placa) idPorPlaca[placa] = r.rows[0].id;
    await cliente.query(
      `INSERT INTO historial_estados (unidad_id, estado_nuevo, usuario, documento)
       VALUES ($1,$2,'sistema','CARGA DE DEMOSTRACIÓN')`,
      [r.rows[0].id, estado],
    );
  }

  for (const [placa, tipo, descripcion, responsable, apertura, cierre, horas] of ORDENES_DEMO) {
    const orden = await cliente.query(
      `INSERT INTO ordenes_trabajo (unidad_id, tipo, descripcion, responsable, fecha_apertura, fecha_cierre, estado)
       VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id`,
      [idPorPlaca[placa], tipo, descripcion, responsable, apertura, cierre, cierre ? 'CERRADA' : 'ABIERTA'],
    );
    if (horas > 0) {
      await cliente.query(
        `INSERT INTO mano_obra (orden_id, mecanico, fecha, horas, tarifa, costo, descripcion)
         VALUES ($1,$2,$3,$4::numeric,$5::numeric,$4::numeric * $5::numeric,$6)`,
        [orden.rows[0].id, responsable, apertura, horas, TARIFA_HORA, descripcion],
      );
    }
  }
  console.log(`Datos de demostración: ${UNIDADES_DEMO.length} unidades y ${ORDENES_DEMO.length} órdenes.`);
}

async function main() {
  const esquema = fs.readFileSync(path.join(__dirname, '../../database/schema.sql'), 'utf8');
  await pool.query(esquema);
  console.log('Esquema aplicado.');

  await conTransaccion('sistema', sembrarBase);
  console.log('Catálogo y usuarios iniciales listos (aux, contador, gerente, gerencia).');

  if (process.argv.includes('--demo')) {
    await conTransaccion('sistema', sembrarDemo);
  }
}

main()
  .catch((error) => {
    console.error('No se pudo preparar la base de datos:', error.message);
    process.exitCode = 1;
  })
  .finally(() => pool.end());
