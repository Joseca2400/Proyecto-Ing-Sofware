const ordenes = require('../models/orden.model');
const { ErrorNegocio } = require('../middlewares/errores');

async function listar(req, res) {
  res.json(await ordenes.listar({ estado: req.query.estado }));
}

async function obtener(req, res) {
  const id = Number(req.params.id);
  const orden = Number.isInteger(id) ? await ordenes.porId(id) : null;
  if (!orden) throw new ErrorNegocio('La orden no existe', 404);
  res.json(orden);
}

module.exports = { listar, obtener };
