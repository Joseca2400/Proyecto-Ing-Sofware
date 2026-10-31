// ===== Datos de ejemplo (luego se reemplazan por datos reales) =====

// estado: "comenzado" | "reparando" | "listo"
const vehiculos = [
  { id: 1, marca: 'Mazda',   modelo: 'CX-5',      anio: 2018, placa: 'P-118XQL', origen: 'Flota propia',    trabajo: 'Cambio de frenos y suspensión delantera', mecanico: 'Carlos M.', ingreso: '2026-10-22', avance: 60,  estado: 'reparando' },
  { id: 2, marca: 'Toyota',  modelo: 'Yaris',     anio: 2019, placa: 'P-402MNB', origen: 'Flota propia',    trabajo: 'Revisión general de importación',         mecanico: 'Luis R.',   ingreso: '2026-10-29', avance: 10,  estado: 'comenzado' },
  { id: 3, marca: 'Honda',   modelo: 'Civic',     anio: 2017, placa: 'P-775DKS', origen: 'Vehículo vendido', trabajo: 'Servicio de 60,000 km',                  mecanico: 'Pedro A.',  ingreso: '2026-10-25', avance: 100, estado: 'listo' },
  { id: 4, marca: 'Ford',    modelo: 'Ranger',    anio: 2018, placa: 'P-263VBH', origen: 'Flota propia',    trabajo: 'Reparación de transmisión',               mecanico: 'Carlos M.', ingreso: '2026-10-18', avance: 45,  estado: 'reparando' },
  { id: 5, marca: 'Hyundai', modelo: 'Santa Fe',  anio: 2019, placa: 'P-690TRE', origen: 'Flota propia',    trabajo: 'Pintura y enderezado de puerta',          mecanico: 'Marvin J.', ingreso: '2026-10-27', avance: 20,  estado: 'comenzado' },
  { id: 6, marca: 'Nissan',  modelo: 'Sentra',    anio: 2018, placa: 'P-337FGW', origen: 'Vehículo vendido', trabajo: 'Cambio de embrague',                     mecanico: 'Luis R.',   ingreso: '2026-10-20', avance: 100, estado: 'listo' },
  { id: 7, marca: 'Suzuki',  modelo: 'Swift',     anio: 2018, placa: 'P-914LCA', origen: 'Flota propia',    trabajo: 'Sistema eléctrico y alternador',          mecanico: 'Pedro A.',  ingreso: '2026-10-24', avance: 75,  estado: 'reparando' }
];

// prioridad: "alta" | "media" | "baja"
let faltantes = [
  { id: 1, repuesto: 'Pastillas de freno delanteras', vehiculoId: 1, cantidad: 1, prioridad: 'alta',  costo: 350 },
  { id: 2, repuesto: 'Kit de transmisión automática', vehiculoId: 4, cantidad: 1, prioridad: 'alta',  costo: 4800 },
  { id: 3, repuesto: 'Alternador',                    vehiculoId: 7, cantidad: 1, prioridad: 'media', costo: 1250 },
  { id: 4, repuesto: 'Espejo lateral derecho',        vehiculoId: 5, cantidad: 1, prioridad: 'baja',  costo: 420 },
  { id: 5, repuesto: 'Filtro de aceite y aire',       vehiculoId: 2, cantidad: 2, prioridad: 'baja',  costo: 160 }
];

// estado: "camino" | "recibido"
let compras = [
  { id: 101, repuesto: 'Amortiguadores delanteros', vehiculoId: 1, cantidad: 2, proveedor: 'Importado (USA)', costo: 1900, estado: 'camino',   fecha: '2026-11-04' },
  { id: 102, repuesto: 'Disco de embrague',         vehiculoId: 6, cantidad: 1, proveedor: 'Repuestos Centro', costo: 980,  estado: 'recibido', fecha: '2026-10-23' },
  { id: 103, repuesto: 'Bujías (juego)',            vehiculoId: 3, cantidad: 1, proveedor: 'Repuestos Centro', costo: 240,  estado: 'recibido', fecha: '2026-10-26' },
  { id: 104, repuesto: 'Bomba de combustible',      vehiculoId: 4, cantidad: 1, proveedor: 'Importado (USA)', costo: 1100, estado: 'camino',   fecha: '2026-11-06' },
  { id: 105, repuesto: 'Regulador de voltaje',      vehiculoId: 7, cantidad: 1, proveedor: 'Autopartes Zona 4', costo: 310, estado: 'recibido', fecha: '2026-10-28' }
];

const ETIQUETAS_ESTADO = { comenzado: 'COMENZADO', reparando: 'REPARANDO', listo: 'LISTO PARA ENTREGAR' };
const ETIQUETAS_COMPRA = { camino: 'EN CAMINO', recibido: 'RECIBIDO' };
const ETIQUETAS_PRIORIDAD = { alta: 'ALTA', media: 'MEDIA', baja: 'BAJA' };
const ORDEN_PRIORIDAD = { alta: 0, media: 1, baja: 2 };

let filtroVehiculos = 'todos';
let filtroCompras = 'todos';

// ===== Utilidades =====
function nombreVehiculo(id) {
  const v = vehiculos.find(x => x.id === id);
  return v ? `${v.marca} ${v.modelo} · ${v.placa}` : 'Sin asignar';
}

function formatoFecha(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('es-GT', { day: 'numeric', month: 'short' });
}

function sumarDias(dias) {
  const f = new Date();
  f.setDate(f.getDate() + dias);
  const mm = String(f.getMonth() + 1).padStart(2, '0');
  const dd = String(f.getDate()).padStart(2, '0');
  return `${f.getFullYear()}-${mm}-${dd}`;
}

// ===== Resumen =====
function renderResumen() {
  document.getElementById('statTotal').textContent = vehiculos.length;
  document.getElementById('statReparando').textContent = vehiculos.filter(v => v.estado === 'reparando').length;
  document.getElementById('statListos').textContent = vehiculos.filter(v => v.estado === 'listo').length;
  document.getElementById('statFaltantes').textContent = faltantes.length;
  document.getElementById('pillFaltantes').textContent = faltantes.length;
}

// ===== Vehículos en taller =====
function renderVehiculos() {
  const lista = vehiculos.filter(v => filtroVehiculos === 'todos' || v.estado === filtroVehiculos);

  document.getElementById('gridVehiculos').innerHTML = lista.map(v => `
    <article class="rcar">
      <div class="rcar-top">
        <div>
          <h3>${v.marca} ${v.modelo}</h3>
          <p class="meta">${v.anio} · ${v.placa}</p>
        </div>
        <span class="chip ${v.estado}">${ETIQUETAS_ESTADO[v.estado]}</span>
      </div>
      <span class="tag-origen">${v.origen}</span>
      <p class="trabajo">${v.trabajo}</p>
      <div>
        <div class="progress"><div class="progress-fill ${v.estado}" style="width:${v.avance}%"></div></div>
      </div>
      <div class="rcar-foot">
        <span>Mecánico: <strong>${v.mecanico}</strong></span>
        <span>Ingresó ${formatoFecha(v.ingreso)}</span>
      </div>
    </article>
  `).join('');

  document.getElementById('sinVehiculos').hidden = lista.length > 0;
}

// ===== Lista pequeña de estados =====
function renderEstados() {
  const orden = { reparando: 0, comenzado: 1, listo: 2 };
  const lista = [...vehiculos].sort((a, b) => orden[a.estado] - orden[b.estado]);

  document.getElementById('listaEstados').innerHTML = lista.map(v => `
    <li>
      <span class="car-name">${v.marca} ${v.modelo}<span class="car-plate">${v.placa}</span></span>
      <span class="chip ${v.estado}">${ETIQUETAS_ESTADO[v.estado]}</span>
    </li>
  `).join('');
}

// ===== Repuestos faltantes =====
function renderFaltantes() {
  const lista = [...faltantes].sort((a, b) => ORDEN_PRIORIDAD[a.prioridad] - ORDEN_PRIORIDAD[b.prioridad]);

  document.getElementById('listaFaltantes').innerHTML = lista.map(p => `
    <li class="part">
      <div class="part-info">
        <strong>${p.repuesto} <small>x${p.cantidad}</small></strong>
        <span>${nombreVehiculo(p.vehiculoId)} · Est. Q${p.costo.toLocaleString('es-GT')}</span>
      </div>
      <div class="part-side">
        <span class="chip ${p.prioridad}">${ETIQUETAS_PRIORIDAD[p.prioridad]}</span>
        <button class="btn-sm" data-comprar="${p.id}">Marcar comprado</button>
      </div>
    </li>
  `).join('');

  document.getElementById('sinFaltantes').hidden = faltantes.length > 0;
}

// ===== Repuestos comprados =====
function renderCompras() {
  const lista = compras.filter(c => filtroCompras === 'todos' || c.estado === filtroCompras);

  document.getElementById('listaCompras').innerHTML = lista.map(c => `
    <li class="part">
      <div class="part-info">
        <strong>${c.repuesto} <small>x${c.cantidad}</small></strong>
        <span>${nombreVehiculo(c.vehiculoId)} · ${c.proveedor}</span>
        <span>${c.estado === 'camino' ? 'Llega aprox.' : 'Recibido'} ${formatoFecha(c.fecha)} · Q${c.costo.toLocaleString('es-GT')}</span>
      </div>
      <div class="part-side">
        <span class="chip ${c.estado}">${ETIQUETAS_COMPRA[c.estado]}</span>
        ${c.estado === 'camino' ? `<button class="btn-sm outline" data-recibir="${c.id}">Marcar recibido</button>` : ''}
      </div>
    </li>
  `).join('');

  document.getElementById('sinCompras').hidden = lista.length > 0;
}

function renderTodo() {
  renderResumen();
  renderVehiculos();
  renderEstados();
  renderFaltantes();
  renderCompras();
}

// ===== Eventos =====
// Filtro de vehículos
document.querySelectorAll('.tab:not(.tab-compras)').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab:not(.tab-compras)').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    filtroVehiculos = tab.dataset.filtro;
    renderVehiculos();
  });
});

// Filtro de compras
document.querySelectorAll('.tab-compras').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab-compras').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    filtroCompras = tab.dataset.filtro;
    renderCompras();
  });
});

// Faltante -> comprado (en camino)
document.getElementById('listaFaltantes').addEventListener('click', e => {
  const btn = e.target.closest('[data-comprar]');
  if (!btn) return;

  const id = Number(btn.dataset.comprar);
  const item = faltantes.find(p => p.id === id);
  if (!item) return;

  faltantes = faltantes.filter(p => p.id !== id);
  compras.unshift({
    id: Date.now(),
    repuesto: item.repuesto,
    vehiculoId: item.vehiculoId,
    cantidad: item.cantidad,
    proveedor: 'Por definir',
    costo: item.costo,
    estado: 'camino',
    fecha: sumarDias(5)
  });
  renderTodo();
});

// En camino -> recibido
document.getElementById('listaCompras').addEventListener('click', e => {
  const btn = e.target.closest('[data-recibir]');
  if (!btn) return;

  const item = compras.find(c => c.id === Number(btn.dataset.recibir));
  if (!item) return;

  item.estado = 'recibido';
  item.fecha = sumarDias(0);
  renderTodo();
});

// ===== Inicio =====
document.getElementById('fechaHoy').textContent =
  new Date().toLocaleDateString('es-GT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

renderTodo();