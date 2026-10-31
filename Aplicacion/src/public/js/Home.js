// ===== Datos de ejemplo (luego se reemplazan por datos reales) =====
// estado: "disponible" | "alquilado"
// devolucion: fecha ISO (solo si está alquilado)
const flota = [
  { id: 1,  marca: 'Toyota',    modelo: 'Corolla',   anio: 2019, placa: 'P-482KLM', transmision: 'Automático', combustible: 'Gasolina', pasajeros: 5, precioDia: 280, estado: 'disponible' },
  { id: 2,  marca: 'Hyundai',   modelo: 'Elantra',   anio: 2018, placa: 'P-731BTR', transmision: 'Automático', combustible: 'Gasolina', pasajeros: 5, precioDia: 260, estado: 'alquilado',  devolucion: '2026-11-03' },
  { id: 3,  marca: 'Kia',       modelo: 'Sportage',  anio: 2020, placa: 'P-219CDF', transmision: 'Automático', combustible: 'Gasolina', pasajeros: 5, precioDia: 380, estado: 'disponible' },
  { id: 4,  marca: 'Toyota',    modelo: 'Hilux',     anio: 2019, placa: 'P-905HNV', transmision: 'Manual',     combustible: 'Diésel',   pasajeros: 5, precioDia: 450, estado: 'alquilado',  devolucion: '2026-11-07' },
  { id: 5,  marca: 'Honda',     modelo: 'CR-V',      anio: 2018, placa: 'P-367WQZ', transmision: 'Automático', combustible: 'Gasolina', pasajeros: 5, precioDia: 400, estado: 'disponible' },
  { id: 6,  marca: 'Nissan',    modelo: 'Frontier',  anio: 2017, placa: 'P-654JXA', transmision: 'Manual',     combustible: 'Diésel',   pasajeros: 5, precioDia: 420, estado: 'alquilado',  devolucion: '2026-11-01' },
  { id: 7,  marca: 'Mazda',     modelo: 'Mazda 3',   anio: 2019, placa: 'P-128SPL', transmision: 'Automático', combustible: 'Gasolina', pasajeros: 5, precioDia: 290, estado: 'disponible' },
  { id: 8,  marca: 'Chevrolet', modelo: 'Spark',     anio: 2018, placa: 'P-843MDE', transmision: 'Manual',     combustible: 'Gasolina', pasajeros: 4, precioDia: 180, estado: 'disponible' },
  { id: 9,  marca: 'Toyota',    modelo: 'RAV4',      anio: 2020, placa: 'P-570GHY', transmision: 'Automático', combustible: 'Gasolina', pasajeros: 5, precioDia: 420, estado: 'alquilado',  devolucion: '2026-11-05' },
  { id: 10, marca: 'Hyundai',   modelo: 'Tucson',    anio: 2019, placa: 'P-312RUC', transmision: 'Automático', combustible: 'Gasolina', pasajeros: 5, precioDia: 370, estado: 'disponible' },
  { id: 11, marca: 'Kia',       modelo: 'Rio',       anio: 2018, placa: 'P-996ZNB', transmision: 'Manual',     combustible: 'Gasolina', pasajeros: 5, precioDia: 210, estado: 'disponible' },
  { id: 12, marca: 'Ford',      modelo: 'Escape',    anio: 2019, placa: 'P-245TVK', transmision: 'Automático', combustible: 'Gasolina', pasajeros: 5, precioDia: 390, estado: 'alquilado',  devolucion: '2026-11-10' }
];

// ===== Referencias al DOM =====
const grid = document.getElementById('gridFlota');
const sinResultados = document.getElementById('sinResultados');
const buscador = document.getElementById('buscador');
const tabs = document.querySelectorAll('.tab');

let filtroActual = 'todos';
let textoBusqueda = '';

// ===== Utilidades =====
const iconoCarro = `
  <svg viewBox="0 0 120 60" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
    <path d="M8 40v-8c0-3 2-5 5-6l14-3 12-12h40l14 13 10 3c3 1 5 3 5 6v7"/>
    <path d="M8 40h104"/>
    <path d="M38 14 28 23h64L80 14"/>
    <circle cx="32" cy="42" r="8" fill="#fff"/>
    <circle cx="88" cy="42" r="8" fill="#fff"/>
  </svg>`;

function formatoFecha(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('es-GT', { day: 'numeric', month: 'short' });
}

// ===== Resumen superior =====
function actualizarResumen() {
  const total = flota.length;
  const alquilados = flota.filter(v => v.estado === 'alquilado').length;
  const disponibles = total - alquilados;
  const ocupacion = total ? Math.round((alquilados / total) * 100) : 0;

  document.getElementById('statTotal').textContent = total;
  document.getElementById('statDisponibles').textContent = disponibles;
  document.getElementById('statAlquilados').textContent = alquilados;
  document.getElementById('statOcupacion').textContent = ocupacion + '%';
  document.getElementById('barOcupacion').style.width = ocupacion + '%';
}

// ===== Render de tarjetas =====
function crearTarjeta(v) {
  const alquilado = v.estado === 'alquilado';
  return `
    <article class="car">
      <div class="car-img">
        ${iconoCarro}
        <span class="badge ${v.estado}">${alquilado ? 'ALQUILADO' : 'DISPONIBLE'}</span>
      </div>
      <div class="car-body">
        <h3>${v.marca} ${v.modelo}</h3>
        <p class="car-meta">${v.anio} · Placa ${v.placa}</p>
        <div class="car-specs">
          <span class="spec">${v.transmision}</span>
          <span class="spec">${v.combustible}</span>
          <span class="spec">${v.pasajeros} pasajeros</span>
        </div>
        <div class="car-foot">
          <div class="price">Q${v.precioDia} <small>/ día</small></div>
          ${alquilado
            ? `<div class="return">Devuelve<br>${formatoFecha(v.devolucion)}</div>`
            : `<div class="free">Listo para<br>alquilar</div>`}
        </div>
      </div>
    </article>`;
}

function renderFlota() {
  const q = textoBusqueda.trim().toLowerCase();

  const lista = flota.filter(v => {
    const coincideEstado = filtroActual === 'todos' || v.estado === filtroActual;
    const coincideTexto = !q || `${v.marca} ${v.modelo} ${v.placa}`.toLowerCase().includes(q);
    return coincideEstado && coincideTexto;
  });

  grid.innerHTML = lista.map(crearTarjeta).join('');
  sinResultados.hidden = lista.length > 0;
}

// ===== Eventos =====
tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    filtroActual = tab.dataset.filtro;
    renderFlota();
  });
});

buscador.addEventListener('input', e => {
  textoBusqueda = e.target.value;
  renderFlota();
});

// ===== Inicio =====
document.getElementById('fechaHoy').textContent =
  new Date().toLocaleDateString('es-GT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

actualizarResumen();
renderFlota();