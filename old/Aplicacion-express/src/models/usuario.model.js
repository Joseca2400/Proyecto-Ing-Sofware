const { consultar } = require('../config/db');

async function buscarPorUsuario(usuario) {
  const { rows } = await consultar(
    'SELECT id, usuario, nombre, rol, activo, password_hash FROM usuarios WHERE usuario = $1',
    [usuario],
  );
  return rows[0] || null;
}

async function crearSesion(usuarioId, tokenHash, horas) {
  const { rows } = await consultar(
    `INSERT INTO sesiones (usuario_id, token_hash, expira_en)
     VALUES ($1, $2, now() + make_interval(hours => $3::int))
     RETURNING expira_en`,
    [usuarioId, tokenHash, horas],
  );
  return rows[0].expira_en;
}

// Devuelve el usuario dueño de una sesión vigente, o null.
async function usuarioDeToken(tokenHash) {
  const { rows } = await consultar(
    `SELECT u.id, u.usuario, u.nombre, u.rol, s.id AS sesion_id
       FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id
      WHERE s.token_hash = $1 AND NOT s.cerrada AND s.expira_en > now() AND u.activo`,
    [tokenHash],
  );
  return rows[0] || null;
}

async function cerrarSesion(sesionId) {
  await consultar('UPDATE sesiones SET cerrada = TRUE WHERE id = $1', [sesionId]);
}

module.exports = { buscarPorUsuario, crearSesion, usuarioDeToken, cerrarSesion };
