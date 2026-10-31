const { Pool, types } = require('pg');
const config = require('./index');

// Precisión monetaria (acuerdo 2 de K1): NUMERIC se entrega como texto ("76598.000000"),
// nunca como Number, para que ni el servidor ni el navegador usen punto flotante.
// Se deja el tipo por defecto de pg, que ya lo hace así (OID 1700).
// Las fechas DATE se mantienen como "AAAA-MM-DD" para evitar corrimientos de zona horaria.
types.setTypeParser(1082, (valor) => valor);

const pool = new Pool({ connectionString: config.databaseUrl });

function consultar(texto, parametros = []) {
  return pool.query(texto, parametros);
}

// Ejecuta `trabajo(cliente)` en una transacción e informa el actor a la auditoría automática:
// los triggers de database/schema.sql leen `app.usuario` al registrar la bitácora (HU-1.11).
// Un fallo revierte todo: no quedan registros parciales (acuerdo 6 de K1).
async function conTransaccion(usuario, trabajo) {
  const cliente = await pool.connect();
  try {
    await cliente.query('BEGIN');
    await cliente.query("SELECT set_config('app.usuario', $1, true)", [usuario]);
    const resultado = await trabajo(cliente);
    await cliente.query('COMMIT');
    return resultado;
  } catch (error) {
    await cliente.query('ROLLBACK');
    throw error;
  } finally {
    cliente.release();
  }
}

module.exports = { pool, consultar, conTransaccion };
