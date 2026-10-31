const usuarios = require('../models/usuario.model');
const { hashToken } = require('../services/seguridad');
const { ErrorNegocio } = require('./errores');

// Exige `Authorization: Bearer <token>` y deja el usuario en req.usuario (HU-1.09).
async function sesionActual(req, _res, next) {
  const [esquema, token] = (req.headers.authorization || '').split(' ');
  if (esquema !== 'Bearer' || !token) {
    throw new ErrorNegocio('Inicie sesión: falta el encabezado Authorization: Bearer <token>', 401);
  }
  const usuario = await usuarios.usuarioDeToken(hashToken(token));
  if (!usuario) {
    throw new ErrorNegocio('La sesión no es válida o expiró; inicie sesión de nuevo', 401);
  }
  req.usuario = usuario;
  next();
}

// Permiso por rol, aplicado en el servidor. Uso: router.post('/x', requiere(REGISTRAN), ...)
function requiere(roles) {
  return (req, _res, next) => {
    if (!roles.includes(req.usuario.rol)) {
      throw new ErrorNegocio(
        `El rol ${req.usuario.rol} no tiene permiso para esta operación (permitido: ${roles.join(', ')})`,
        403,
      );
    }
    next();
  };
}

module.exports = { sesionActual, requiere };
