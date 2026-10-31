// HU-1.09: contraseñas con hash y tokens de sesión. Solo biblioteca estándar de Node (scrypt).
const crypto = require('node:crypto');

const COSTO = 16384; // N de scrypt

function hashPassword(password) {
  const sal = crypto.randomBytes(16).toString('hex');
  const derivada = crypto.scryptSync(password, sal, 32, { N: COSTO }).toString('hex');
  return `scrypt$${COSTO}$${sal}$${derivada}`;
}

function verificarPassword(password, almacenado) {
  const [esquema, costo, sal, esperado] = String(almacenado).split('$');
  if (esquema !== 'scrypt' || !costo || !sal || !esperado) return false;
  const calculada = crypto.scryptSync(password, sal, 32, { N: Number(costo) });
  const referencia = Buffer.from(esperado, 'hex');
  return referencia.length === calculada.length && crypto.timingSafeEqual(calculada, referencia);
}

function nuevoToken() {
  return crypto.randomBytes(32).toString('base64url');
}

// En la base solo se guarda este hash, nunca el token.
function hashToken(token) {
  return crypto.createHash('sha256').update(token).digest('hex');
}

module.exports = { hashPassword, verificarPassword, nuevoToken, hashToken };
