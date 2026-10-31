const config = require('../config');
const usuarios = require('../models/usuario.model');
const { verificarPassword, nuevoToken, hashToken } = require('../services/seguridad');
const { ErrorNegocio } = require('../middlewares/errores');

const publico = ({ id, usuario, nombre, rol }) => ({ id, usuario, nombre, rol });

async function login(req, res) {
  const { usuario, password } = req.body || {};
  if (typeof usuario !== 'string' || typeof password !== 'string' || !usuario || !password) {
    throw new ErrorNegocio('Ingrese usuario y contraseña', 422);
  }

  const u = await usuarios.buscarPorUsuario(usuario.trim());
  // Mismo mensaje para usuario inexistente, inactivo o contraseña incorrecta.
  if (!u || !u.activo || !verificarPassword(password, u.password_hash)) {
    throw new ErrorNegocio('Usuario o contraseña incorrectos', 401);
  }

  const token = nuevoToken();
  const expira = await usuarios.crearSesion(u.id, hashToken(token), config.horasSesion);
  res.json({ token, expira_en: expira, usuario: publico(u) });
}

async function logout(req, res) {
  await usuarios.cerrarSesion(req.usuario.sesion_id);
  res.status(204).end();
}

function yo(req, res) {
  res.json(publico(req.usuario));
}

module.exports = { login, logout, yo };
