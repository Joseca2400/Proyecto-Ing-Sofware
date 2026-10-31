// Prueba de humo de la API. Requiere PostgreSQL con datos:  npm run db:demo && npm test
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const app = require('../src/app');
const { pool } = require('../src/config/db');

const PASSWORD = process.env.PASSWORD_INICIAL || 'Demo2026!';
let servidor;
let base;

before(async () => {
  servidor = app.listen(0);
  await new Promise((resolver) => servidor.once('listening', resolver));
  base = `http://127.0.0.1:${servidor.address().port}/api/v1`;
});

after(async () => {
  await new Promise((resolver) => servidor.close(resolver));
  await pool.end();
});

async function llamar(metodo, ruta, { token, cuerpo } = {}) {
  const respuesta = await fetch(base + ruta, {
    method: metodo,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  const texto = await respuesta.text();
  return { status: respuesta.status, datos: texto ? JSON.parse(texto) : null };
}

async function entrar(usuario) {
  const { status, datos } = await llamar('POST', '/auth/login', { cuerpo: { usuario, password: PASSWORD } });
  assert.equal(status, 200);
  return datos;
}

test('HU-1.09 · login incorrecto usa el mismo mensaje para usuario o contraseña', async () => {
  const mala = await llamar('POST', '/auth/login', { cuerpo: { usuario: 'aux', password: 'incorrecta' } });
  const inexistente = await llamar('POST', '/auth/login', { cuerpo: { usuario: 'nadie', password: 'x' } });
  assert.equal(mala.status, 401);
  assert.equal(inexistente.status, 401);
  assert.equal(mala.datos.detail, inexistente.datos.detail);
});

test('HU-1.09 · login devuelve token y usuario sin secretos; /yo y cierre de sesión', async () => {
  const { token, usuario } = await entrar('contador');
  assert.equal(usuario.rol, 'CONTADOR');
  assert.equal(usuario.password_hash, undefined);

  assert.equal((await llamar('GET', '/yo', { token })).datos.usuario, 'contador');
  assert.equal((await llamar('POST', '/auth/logout', { token })).status, 204);
  assert.equal((await llamar('GET', '/yo', { token })).status, 401);
});

test('Sin sesión no se accede a la API', async () => {
  assert.equal((await llamar('GET', '/unidades')).status, 401);
  assert.equal((await llamar('GET', '/unidades', { token: 'falso' })).status, 401);
});

test('Todos los roles consultan unidades y órdenes', async () => {
  for (const u of ['aux', 'contador', 'gerente', 'gerencia']) {
    const { token } = await entrar(u);
    const unidades = await llamar('GET', '/unidades', { token });
    const ordenes = await llamar('GET', '/ordenes', { token });
    assert.equal(unidades.status, 200, u);
    assert.equal(ordenes.status, 200, u);
    assert.ok(Array.isArray(unidades.datos));
  }
});

test('Permisos por rol en el servidor: gerencia no registra, auxiliar no revisa', async () => {
  const gerencia = (await entrar('gerencia')).token;
  const aux = (await entrar('aux')).token;
  const contador = (await entrar('contador')).token;

  assert.equal((await llamar('POST', '/compras', { token: gerencia, cuerpo: {} })).status, 403);
  assert.equal((await llamar('GET', '/bitacora', { token: aux })).status, 403);
  assert.equal((await llamar('POST', '/ordenes/1/cerrar', { token: aux, cuerpo: {} })).status, 403);

  // Con permiso, el esqueleto responde 501 e indica la historia que falta.
  const pendiente = await llamar('POST', '/compras', { token: aux, cuerpo: {} });
  assert.equal(pendiente.status, 501);
  assert.match(pendiente.datos.detail, /HU-4\.02/);
  assert.equal((await llamar('GET', '/bitacora', { token: contador })).status, 501);
});

test('Los montos viajan como texto, no como número (acuerdo 2 de K1)', async () => {
  const { token } = await entrar('aux');
  const ordenes = (await llamar('GET', '/ordenes', { token })).datos;
  assert.ok(ordenes.length > 0, 'ejecute npm run db:demo');
  for (const o of ordenes) {
    assert.equal(typeof o.costo_mano_obra, 'string');
    assert.equal(typeof o.horas, 'string');
  }
  assert.match(ordenes[0].fecha_apertura, /^\d{4}-\d{2}-\d{2}$/);
});

test('HU-1.05 · una unidad se consulta por VIN con su historial', async () => {
  const { token } = await entrar('aux');
  const [primera] = (await llamar('GET', '/unidades', { token })).datos;
  const porVin = await llamar('GET', `/unidades/vin/${primera.vin.toLowerCase()}`, { token });
  assert.equal(porVin.status, 200);
  assert.equal(porVin.datos.id, primera.id);
  assert.ok(Array.isArray(porVin.datos.historial));
  assert.equal((await llamar('GET', '/unidades/vin/NOEXISTE', { token })).status, 404);
});
