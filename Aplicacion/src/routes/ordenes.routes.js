const { Router } = require('express');
const ordenes = require('../controllers/ordenes.controller');
const { requiere } = require('../middlewares/auth');
const { TODOS } = require('../config/permisos');

const router = Router();

// HU-5.01: consulta de órdenes de taller ligadas a un VIN.
router.get('/ordenes', requiere(TODOS), ordenes.listar);
router.get('/ordenes/:id', requiere(TODOS), ordenes.obtener);

module.exports = router;
