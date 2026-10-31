// Matriz de permisos por rol, en un solo lugar y aplicada en el servidor (acuerdo 4 de K1).
// Ocultar opciones en la interfaz no sustituye esta autorización.
// Mismos grupos que proyecto-vehiculos/backend/app/deps.py.
const ROLES = {
  AUXILIAR: 'AUXILIAR', // registra
  CONTADOR: 'CONTADOR', // revisa, contabiliza y cierra
  GERENTE_FINANCIERO: 'GERENTE_FINANCIERO', // aprueba
  GERENCIA: 'GERENCIA', // solo consulta
};

const REGISTRAN = [ROLES.AUXILIAR, ROLES.CONTADOR, ROLES.GERENTE_FINANCIERO];
const REVISAN = [ROLES.CONTADOR, ROLES.GERENTE_FINANCIERO];
const APRUEBAN = [ROLES.GERENTE_FINANCIERO];
const TODOS = Object.values(ROLES);

module.exports = { ROLES, REGISTRAN, REVISAN, APRUEBAN, TODOS };
