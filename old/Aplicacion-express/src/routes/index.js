const { Router } = require('express');
const { sesionActual } = require('../middlewares/auth');

const router = Router();

// Públicas: iniciar sesión. Cerrar sesión y /yo validan el token dentro de su router.
router.use(require('./auth.routes'));

// Todo lo demás exige sesión; cada ruta aplica además su permiso por rol.
router.use(sesionActual);
router.use(require('./unidades.routes'));
router.use(require('./ordenes.routes'));
router.use(require('./pendientes.routes')); // esqueleto: responde 501 con la historia pendiente

module.exports = router;
