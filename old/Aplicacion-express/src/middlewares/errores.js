// Los errores de regla de negocio responden { detail } con un mensaje en español listo para
// mostrar, igual que la API de referencia (backend).
class ErrorNegocio extends Error {
  constructor(mensaje, status = 400) {
    super(mensaje);
    this.status = status;
  }
}

function noEncontrada(_req, res) {
  res.status(404).json({ detail: 'Ruta no encontrada' });
}

// Express 5 envía aquí también los rechazos de funciones async.
// eslint-disable-next-line no-unused-vars
function manejarErrores(error, _req, res, _next) {
  if (error instanceof ErrorNegocio) {
    return res.status(error.status).json({ detail: error.message });
  }
  if (error.type === 'entity.parse.failed') {
    return res.status(400).json({ detail: 'El cuerpo de la petición no es un JSON válido' });
  }
  console.error(error);
  res.status(500).json({ detail: 'Error interno del servidor' });
}

module.exports = { ErrorNegocio, noEncontrada, manejarErrores };
