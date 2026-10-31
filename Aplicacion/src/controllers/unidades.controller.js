const unidades = require('../models/unidad.model');
const { ErrorNegocio } = require('../middlewares/errores');

async function listar(req, res) {
  res.json(await unidades.listar({ estado: req.query.estado }));
}

async function obtener(req, res) {
  const id = Number(req.params.id);
  const unidad = Number.isInteger(id) ? await unidades.porId(id) : null;
  if (!unidad) throw new ErrorNegocio('La unidad no existe', 404);
  res.json({ ...unidad, historial: await unidades.historial(unidad.id) });
}

async function obtenerPorVin(req, res) {
  const unidad = await unidades.porVin(req.params.vin.toUpperCase());
  if (!unidad) throw new ErrorNegocio('No hay una unidad con ese VIN', 404);
  res.json({ ...unidad, historial: await unidades.historial(unidad.id) });
}

module.exports = { listar, obtener, obtenerPorVin };
