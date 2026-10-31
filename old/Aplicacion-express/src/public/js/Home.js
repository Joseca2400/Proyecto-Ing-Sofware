// Las unidades vienen de GET /api/v1/unidades (HU-1.05). El estado es el del ciclo de la
// unidad; "alquilada/disponible" llegará con los contratos de alquiler (HU-3.06).
// estado de la API -> texto de la insignia y grupo del filtro
const ESTADOS = {
  EN_TRANSITO: { texto: 'EN TRÁNSITO', grupo: 'proceso' },
  EN_ADUANA: { texto: 'EN ADUANA', grupo: 'proceso' },
  EN_TALLER: { texto: 'EN TALLER', grupo: 'proceso' },
  LISTA: { texto: 'LISTA PARA ALTA', grupo: 'proceso' },
  EN_FLOTA: { texto: 'EN FLOTA', grupo: 'flota' },
};

let unidades = [];
let filtroActual = 'todos';
let textoBusqueda = '';

const grid = document.getElementById('gridFlota');
const sinResultados = document.getElementById('sinResultados');
const buscador = document.getElementById('buscador');
const tabs = document.querySelectorAll('.tab');

const iconoCarro = `
  <svg viewBox="0 0 120 60" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
    <path d="M8 40v-8c0-3 2-5 5-6l14-3 12-12h40l14 13 10 3c3 1 5 3 5 6v7"/>
    <path d="M8 40h104"/>
    <path d="M38 14 28 23h64L80 14"/>
    <circle cx="32" cy="42" r="8" fill="#fff"/>
    <circle cx="88" cy="42" r="8" fill="#fff"/>
  </svg>`;

const grupoDe = (u) => ESTADOS[u.estado]?.grupo ?? 'otro';

// ===== Resumen superior =====
function actualizarResumen() {
  const total = unidades.length;
  const enFlota = unidades.filter((u) => grupoDe(u) === 'flota').length;
  const enProceso = unidades.filter((u) => grupoDe(u) === 'proceso').length;
  const avance = total ? Math.round((enFlota / total) * 100) : 0;

  document.getElementById('statTotal').textContent = total;
  document.getElementById('statEnFlota').textContent = enFlota;
  document.getElementById('statEnProceso').textContent = enProceso;
  document.getElementById('statAvance').textContent = avance + '%';
  document.getElementById('barAvance').style.width = avance + '%';
}

// ===== Render de tarjetas =====
function crearTarjeta(u) {
  const estado = ESTADOS[u.estado] ?? { texto: u.estado.replace('_', ' '), grupo: 'otro' };
  const enFlota = estado.grupo === 'flota';
  const specs = [
    u.tipo_vehiculo,
    u.color,
    u.kilometraje > 0 ? `${u.kilometraje.toLocaleString('es-GT')} km` : null,
  ].filter(Boolean);

  return `
    <article class="car">
      <div class="car-img">
        ${iconoCarro}
        <span class="badge ${esc(u.estado.toLowerCase())}">${esc(estado.texto)}</span>
      </div>
      <div class="car-body">
        <h3>${esc(u.marca)} ${esc(u.linea)}</h3>
        <p class="car-meta">${esc(u.modelo_anio)} · ${u.placa ? 'Placa ' + esc(u.placa) : 'Sin placa'}</p>
        <div class="car-specs">
          ${specs.map((s) => `<span class="spec">${esc(s)}</span>`).join('')}
        </div>
        <div class="car-foot">
          <div class="car-vin">VIN<br>${esc(u.vin)}</div>
          ${enFlota
            ? `<div class="free">Listo para<br>alquilar</div>`
            : `<div class="return">Aún no está<br>en flota</div>`}
        </div>
      </div>
    </article>`;
}

function renderFlota() {
  const q = textoBusqueda.trim().toLowerCase();

  const lista = unidades.filter((u) => {
    const coincideEstado = filtroActual === 'todos' || grupoDe(u) === filtroActual;
    const coincideTexto = !q || `${u.marca} ${u.linea} ${u.placa ?? ''} ${u.vin}`.toLowerCase().includes(q);
    return coincideEstado && coincideTexto;
  });

  grid.innerHTML = lista.map(crearTarjeta).join('');
  sinResultados.textContent = 'No se encontraron vehículos con ese filtro.';
  sinResultados.hidden = lista.length > 0;
}

// ===== Eventos =====
tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((t) => t.classList.remove('active'));
    tab.classList.add('active');
    filtroActual = tab.dataset.filtro;
    renderFlota();
  });
});

buscador.addEventListener('input', (e) => {
  textoBusqueda = e.target.value;
  renderFlota();
});

// ===== Inicio =====
async function arrancar() {
  document.getElementById('fechaHoy').textContent =
    new Date().toLocaleDateString('es-GT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  try {
    unidades = await api('GET', '/unidades');
    actualizarResumen();
    renderFlota();
  } catch (error) {
    sinResultados.textContent = error.message;
    sinResultados.hidden = false;
  }
}

if (iniciarPantalla()) arrancar();
