const { consultar } = require('../config/db');

// Orden de trabajo con su unidad y el total de mano de obra (HU-5.01, HU-5.03).
const SELECT_ORDEN = `
  SELECT o.id, o.unidad_id, o.tipo, o.descripcion, o.responsable, o.kilometraje,
         o.fecha_apertura, o.fecha_cierre, o.estado,
         u.vin, u.marca, u.linea, u.modelo_anio, u.placa,
         COALESCE(SUM(m.horas), 0)  AS horas,
         COALESCE(SUM(m.costo), 0)  AS costo_mano_obra
    FROM ordenes_trabajo o
    JOIN unidades u ON u.id = o.unidad_id
    LEFT JOIN mano_obra m ON m.orden_id = o.id`;

async function listar({ estado } = {}) {
  const { rows } = await consultar(
    `${SELECT_ORDEN}
      WHERE ($1::text IS NULL OR o.estado = $1)
      GROUP BY o.id, u.id
      ORDER BY o.id`,
    [estado || null],
  );
  return rows;
}

async function porId(id) {
  const { rows } = await consultar(`${SELECT_ORDEN} WHERE o.id = $1 GROUP BY o.id, u.id`, [id]);
  return rows[0] || null;
}

module.exports = { listar, porId };
