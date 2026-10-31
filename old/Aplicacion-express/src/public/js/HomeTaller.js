// ===== Órdenes de trabajo: vienen de GET /api/v1/ordenes (HU-5.01, HU-5.03) =====
// Estado visual a partir de la orden:
//   CERRADA                      -> "listo"
//   ABIERTA con horas registradas -> "reparando"
//   ABIERTA sin horas             -> "comenzado"
let ordenes = [];

// ===== Maqueta: repuestos (aún sin base de datos; HU-5.04 a 5.06) =====
// Se ligan al vehículo por placa. prioridad: "alta" | "media" | "baja"
let faltantes = [
  { id: 1, repuesto: 'Pastillas de freno delanteras', placa: 'P-118XQL', cantidad: 1, prioridad: 'alta',  costo: 350 },
  { id: 2, repuesto: 'Kit de transmisión automática', placa: 'P-263VBH', cantidad: 1, prioridad: 'alta',  costo: 4800 },
  { id: 3, repuesto: 'Alternador',                    placa: 'P-914LCA', cantidad: 1, prioridad: 'media', costo: 1250 },
  { id: 4, repuesto: 'Espejo lateral derecho',        placa: 'P-690TRE', cantidad: 1, prioridad: 'baja',  costo: 420 },
  { id: 5, repuesto: 'Filtro de aceite y aire',       placa: 'P-402MNB', cantidad: 2, prioridad: 'baja',  costo: 160 }
];

// estado: "camino" | "recibido"
let compras = [
  { id: 101, repuesto: 'Amortiguadores delanteros', placa: 'P-118XQL', cantidad: 2, proveedor: 'Importado (USA)',   costo: 1900, estado: 'camino',   fecha: '2026-11-04' },
  { id: 102, repuesto: 'Disco de embrague',         placa: 'P-337FGW', cantidad: 1, proveedor: 'Repuestos Centro',  costo: 980,  estado: 'recibido', fecha: '2026-10-23' },
  { id: 103, repuesto: 'Bujías (juego)',            placa: 'P-775DKS', cantidad: 1, proveedor: 'Repuestos Centro',  costo: 240,  estado: 'recibido', fecha: '2026-10-26' },
  { id: 104, repuesto: 'Bomba de combustible',      placa: 'P-263VBH', cantidad: 1, proveedor: 'Importado (USA)',   costo: 1100, estado: 'camino',   fecha: '2026-11-06' },
  { id: 105, repuesto: 'Regulador de voltaje',      placa: 'P-914LCA', cantidad: 1, proveedor: 'Autopartes Zona 4', costo: 310,  estado: 'recibido', fecha: '2026-10-28' }
];

const ETIQUETAS_ESTADO = { comenzado: 'COMENZADO', reparando: 'REPARANDO', listo: 'LISTO PARA ENTREGAR' };
const ETIQUETAS_COMPRA = { camino: 'EN CAMINO', recibido: 'RECIBIDO' };
const ETIQUETAS_PRIORIDAD = { alta: 'ALTA', media: 'MEDIA', baja: 'BAJA' };
const ORDEN_PRIORIDAD = { alta: 0, media: 1, baja: 2 };
const ORIGEN_POR_TIPO = { REACONDICIONAMIENTO: 'Importación', MANTENIMIENTO: 'Flota propia' };

let filtroVehiculos = 'todos';
let filtroCompras = 'todos';

// ===== Utilidades =====
function estadoVisual(o) {
  if (o.estado === 'CERRADA') return 'listo';
  return Number(o.horas) > 0 ? 'reparando' : 'comenzado';
}

function nombreVehiculo(placa) {
  const o = ordenes.find((x) => x.placa === placa);
  return o ? `${o.marca} ${o.linea} · ${o.placa}` : placa;
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
  document.getElementById('statTotal').textContent = ordenes.length;
  document.getElementById('statReparando').textContent = ordenes.filter((o) => estadoVisual(o) === 'reparando').length;
  document.getElementById('statListos').textContent = ordenes.filter((o) => estadoVisual(o) === 'listo').length;
  document.getElementById('statFaltantes').textContent = faltantes.length;
  document.getElementById('pillFaltantes').textContent = faltantes.length;
}

// ===== Vehículos en taller =====
function renderVehiculos() {
  const lista = ordenes.filter((o) => filtroVehiculos === 'todos' || estadoVisual(o) === filtroVehiculos);

  document.getElementById('gridVehiculos').innerHTML = lista.map((o) => {
    const estado = estadoVisual(o);
    const horas = Number(o.horas).toLocaleString('es-GT', { maximumFractionDigits: 2 });
    return `
    <article class="rcar">
      <div class="rcar-top">
        <div>
          <h3>${esc(o.marca)} ${esc(o.linea)}</h3>
          <p class="meta" title="VIN ${esc(o.vin)}">${esc(o.modelo_anio)} · ${esc(o.placa ?? 'Sin placa')}</p>
        </div>
        <span class="chip ${estado}">${ETIQUETAS_ESTADO[estado]}</span>
      </div>
      <span class="tag-origen">${esc(ORIGEN_POR_TIPO[o.tipo] ?? o.tipo)}</span>
      <p class="trabajo">${esc(o.descripcion)}</p>
      <p class="horas"><strong>${horas} h</strong> de mano de obra · ${formatoQuetzales(o.costo_mano_obra)}</p>
      <div class="rcar-foot">
        <span>Responsable: <strong>${esc(o.responsable)}</strong></span>
        <span>Ingresó ${formatoFecha(o.fecha_apertura)}</span>
      </div>
    </article>`;
  }).join('');

  document.getElementById('sinVehiculos').hidden = lista.length > 0;
}

// ===== Lista pequeña de estados =====
function renderEstados() {
  const orden = { reparando: 0, comenzado: 1, listo: 2 };
  const lista = [...ordenes].sort((a, b) => orden[estadoVisual(a)] - orden[estadoVisual(b)]);

  document.getElementById('listaEstados').innerHTML = lista.map((o) => `
    <li>
      <span class="car-name">${esc(o.marca)} ${esc(o.linea)}<span class="car-plate">${esc(o.placa ?? '')}</span></span>
      <span class="chip ${estadoVisual(o)}">${ETIQUETAS_ESTADO[estadoVisual(o)]}</span>
    </li>
  `).join('');
}

// ===== Repuestos faltantes (maqueta) =====
function renderFaltantes() {
  const lista = [...faltantes].sort((a, b) => ORDEN_PRIORIDAD[a.prioridad] - ORDEN_PRIORIDAD[b.prioridad]);

  document.getElementById('listaFaltantes').innerHTML = lista.map((p) => `
    <li class="part">
      <div class="part-info">
        <strong>${esc(p.repuesto)} <small>x${p.cantidad}</small></strong>
        <span>${esc(nombreVehiculo(p.placa))} · Est. Q${p.costo.toLocaleString('es-GT')}</span>
      </div>
      <div class="part-side">
        <span class="chip ${p.prioridad}">${ETIQUETAS_PRIORIDAD[p.prioridad]}</span>
        <button class="btn-sm" data-comprar="${p.id}">Marcar comprado</button>
      </div>
    </li>
  `).join('');

  document.getElementById('sinFaltantes').hidden = faltantes.length > 0;
}

// ===== Repuestos comprados (maqueta) =====
function renderCompras() {
  const lista = compras.filter((c) => filtroCompras === 'todos' || c.estado === filtroCompras);

  document.getElementById('listaCompras').innerHTML = lista.map((c) => `
    <li class="part">
      <div class="part-info">
        <strong>${esc(c.repuesto)} <small>x${c.cantidad}</small></strong>
        <span>${esc(nombreVehiculo(c.placa))} · ${esc(c.proveedor)}</span>
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
document.querySelectorAll('.tab:not(.tab-compras)').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab:not(.tab-compras)').forEach((t) => t.classList.remove('active'));
    tab.classList.add('active');
    filtroVehiculos = tab.dataset.filtro;
    renderVehiculos();
  });
});

// Filtro de compras
document.querySelectorAll('.tab-compras').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab-compras').forEach((t) => t.classList.remove('active'));
    tab.classList.add('active');
    filtroCompras = tab.dataset.filtro;
    renderCompras();
  });
});

// Faltante -> comprado (en camino). Maqueta: solo cambia la pantalla.
document.getElementById('listaFaltantes').addEventListener('click', (e) => {
  const btn = e.target.closest('[data-comprar]');
  if (!btn) return;

  const id = Number(btn.dataset.comprar);
  const item = faltantes.find((p) => p.id === id);
  if (!item) return;

  faltantes = faltantes.filter((p) => p.id !== id);
  compras.unshift({
    id: Date.now(),
    repuesto: item.repuesto,
    placa: item.placa,
    cantidad: item.cantidad,
    proveedor: 'Por definir',
    costo: item.costo,
    estado: 'camino',
    fecha: sumarDias(5)
  });
  renderTodo();
});

// En camino -> recibido
document.getElementById('listaCompras').addEventListener('click', (e) => {
  const btn = e.target.closest('[data-recibir]');
  if (!btn) return;

  const item = compras.find((c) => c.id === Number(btn.dataset.recibir));
  if (!item) return;

  item.estado = 'recibido';
  item.fecha = sumarDias(0);
  renderTodo();
});

// ===== Inicio =====
async function arrancar() {
  document.getElementById('fechaHoy').textContent =
    new Date().toLocaleDateString('es-GT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  try {
    ordenes = await api('GET', '/ordenes');
  } catch (error) {
    const aviso = document.getElementById('sinVehiculos');
    aviso.textContent = error.message;
    aviso.hidden = false;
  }
  renderTodo();
}

if (iniciarPantalla()) arrancar();
