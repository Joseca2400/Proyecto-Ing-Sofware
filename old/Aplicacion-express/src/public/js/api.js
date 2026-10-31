// Cliente de la API y utilidades compartidas por todas las pantallas.
// Se carga antes del script de cada página.
const API = '/api/v1';
const CLAVE_SESION = 'km_sesion';

const ETIQUETAS_ROL = {
  AUXILIAR: 'Auxiliar contable',
  CONTADOR: 'Contador',
  GERENTE_FINANCIERO: 'Gerente financiero',
  GERENCIA: 'Gerencia',
};

// ---------- Sesión (token en sessionStorage: se pierde al cerrar la pestaña) ----------
function leerSesion() {
  try {
    return JSON.parse(sessionStorage.getItem(CLAVE_SESION));
  } catch {
    return null;
  }
}

function guardarSesion({ token, usuario: datosUsuario }) {
  sessionStorage.setItem(CLAVE_SESION, JSON.stringify({ token, usuario: datosUsuario }));
}

function olvidarSesion() {
  sessionStorage.removeItem(CLAVE_SESION);
}

// ---------- Llamadas a la API ----------
// Los mensajes de error vienen de la API en `detail`, ya en español.
async function api(metodo, ruta, cuerpo) {
  const sesion = leerSesion();
  let respuesta;
  try {
    respuesta = await fetch(API + ruta, {
      method: metodo,
      headers: {
        'Content-Type': 'application/json',
        ...(sesion ? { Authorization: `Bearer ${sesion.token}` } : {}),
      },
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    throw new Error('No se pudo conectar con el servidor');
  }

  if (respuesta.status === 401 && sesion) {
    // La sesión expiró o se cerró en otro lugar.
    olvidarSesion();
    window.location.replace('index.html');
  }

  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new Error(datos?.detail ?? `Error ${respuesta.status}`);
  return datos;
}

async function salir() {
  try {
    await api('POST', '/auth/logout');
  } catch {
    /* si la sesión ya no existe, igual se sale */
  }
  olvidarSesion();
  window.location.href = 'index.html';
}

// Para las páginas internas: exige sesión, muestra el usuario y conecta "Cerrar sesión".
function iniciarPantalla() {
  const sesion = leerSesion();
  if (!sesion) {
    window.location.replace('index.html');
    return null;
  }
  const chip = document.getElementById('usuarioActual');
  if (chip) {
    chip.innerHTML = `<strong>${esc(sesion.usuario.nombre)}</strong>${esc(ETIQUETAS_ROL[sesion.usuario.rol] ?? sesion.usuario.rol)}`;
    chip.hidden = false;
  }
  document.getElementById('btnSalir')?.addEventListener('click', salir);
  return sesion;
}

// ---------- Presentación ----------
// Todo dato que viene de la API se escapa antes de entrar a innerHTML.
function esc(texto) {
  return String(texto ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function formatoFecha(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('es-GT', { day: 'numeric', month: 'short' });
}

// Los montos llegan como texto ("900.000000"). Solo se les da formato de texto: sin Number(),
// para no pasar por punto flotante (acuerdo 2 de K1). Muestra 2 decimales.
function formatoQuetzales(monto) {
  const [entero, decimales = ''] = String(monto).split('.');
  return 'Q' + entero.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '.' + (decimales + '00').slice(0, 2);
}
