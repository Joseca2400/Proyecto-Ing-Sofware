const { consultar } = require('../config/db');

const COLUMNAS = `id, vin, marca, linea, modelo_anio, color, tipo_vehiculo, placa, estado,
                  kilometraje, fecha_alta_flota, costo_alta, vida_util_meses, valor_residual`;

async function listar({ estado } = {}) {
  const { rows } = await consultar(
    `SELECT ${COLUMNAS} FROM unidades WHERE ($1::text IS NULL OR estado = $1) ORDER BY id`,
    [estado || null],
  );
  return rows;
}

async function porId(id) {
  const { rows } = await consultar(`SELECT ${COLUMNAS} FROM unidades WHERE id = $1`, [id]);
  return rows[0] || null;
}

async function porVin(vin) {
  const { rows } = await consultar(`SELECT ${COLUMNAS} FROM unidades WHERE vin = $1`, [vin]);
  return rows[0] || null;
}

async function historial(unidadId) {
  const { rows } = await consultar(
    `SELECT estado_anterior, estado_nuevo, fecha, usuario, documento
       FROM historial_estados WHERE unidad_id = $1 ORDER BY id`,
    [unidadId],
  );
  return rows;
}

module.exports = { listar, porId, porVin, historial };
