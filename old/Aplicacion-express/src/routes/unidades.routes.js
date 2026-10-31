const { Router } = require('express');
const unidades = require('../controllers/unidades.controller');
const { requiere } = require('../middlewares/auth');
const { TODOS } = require('../config/permisos');

const router = Router();

// HU-1.05: consulta de unidades por VIN. Todos los roles consultan; registrar es de otras rutas.
router.get('/unidades', requiere(TODOS), unidades.listar);
router.get('/unidades/vin/:vin', requiere(TODOS), unidades.obtenerPorVin);
router.get('/unidades/:id', requiere(TODOS), unidades.obtener);

module.exports = router;
