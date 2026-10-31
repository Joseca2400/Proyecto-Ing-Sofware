// Esqueleto del Sprint 1: endpoints del contrato (proyecto-vehiculos/backend/README.md) que aún
// no tienen lógica. Ya aplican la matriz de permisos y responden 501 con la historia que los
// implementa. Al construir uno, se mueve a su router propio y se elimina de esta lista.
const { Router } = require('express');
const { requiere } = require('../middlewares/auth');
const { ErrorNegocio } = require('../middlewares/errores');
const { TODOS, REGISTRAN, REVISAN, APRUEBAN } = require('../config/permisos');

const PENDIENTES = [
  // [método, ruta, historia, roles]
  ['get', '/usuarios', 'HU-1.09', APRUEBAN],
  ['post', '/usuarios', 'HU-1.09', APRUEBAN],
  ['get', '/bitacora', 'HU-1.11', REVISAN],
  ['get', '/cuentas', 'HU-1.02', REGISTRAN],
  ['get', '/cuentas/arbol', 'HU-1.02', REGISTRAN],
  ['post', '/cuentas', 'HU-1.02', REVISAN],
  ['get', '/tipos-cambio', 'HU-1.06', TODOS],
  ['post', '/tipos-cambio', 'HU-1.06', REVISAN],
  ['get', '/proveedores', 'HU-4.01', REGISTRAN],
  ['post', '/proveedores', 'HU-4.01', REGISTRAN],
  ['post', '/compras', 'HU-4.02', REGISTRAN],
  ['post', '/gastos-importacion', 'HU-4.04', REGISTRAN],
  ['get', '/cuentas-por-pagar', 'HU-4.02', REGISTRAN],
  ['post', '/unidades/:id/estado', 'HU-4.07', REGISTRAN],
  ['get', '/unidades/:id/hoja-costo', 'HU-4.08', REGISTRAN],
  ['post', '/unidades/:id/alta-flota', 'HU-3.01', REVISAN],
  ['post', '/ordenes', 'HU-5.01', REGISTRAN],
  ['post', '/ordenes/:id/mano-obra', 'HU-5.03', REGISTRAN],
  ['post', '/ordenes/:id/cerrar', 'HU-5.07', REVISAN],
  ['get', '/partidas', 'HU-2.01', REGISTRAN],
  ['get', '/partidas/:id', 'HU-2.01', REGISTRAN],
  ['post', '/partidas', 'HU-2.01', REGISTRAN],
  ['put', '/partidas/:id', 'HU-2.01', REGISTRAN],
  ['post', '/partidas/:id/enviar', 'HU-2.02', REGISTRAN],
  ['post', '/partidas/:id/contabilizar', 'HU-2.02', REVISAN],
  ['post', '/partidas/:id/devolver', 'HU-2.02', REVISAN],
  ['get', '/contabilidad/balance', 'HU-2.16', REGISTRAN],
  ['get', '/contabilidad/mayor/:codigo', 'HU-2.16', REGISTRAN],
];

const router = Router();

for (const [metodo, ruta, historia, roles] of PENDIENTES) {
  router[metodo](ruta, requiere(roles), () => {
    throw new ErrorNegocio(`Pendiente de implementar: ${historia} (Sprint 1)`, 501);
  });
}

module.exports = router;
module.exports.PENDIENTES = PENDIENTES;
