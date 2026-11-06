import { Component, computed, ElementRef, inject, signal, viewChild } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { ViewportScroller } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { Icono } from './icono';
import { MockupService, UnidadDemo } from './mockup.service';

@Component({
  selector: 'app-mockup',
  imports: [FormsModule, RouterLink, MontoPipe, Icono],
  templateUrl: './mockup.html',
})
export class Mockup {
  protected readonly datos = inject(MockupService);
  private readonly router = inject(Router);
  private readonly desplazamiento = inject(ViewportScroller);
  private readonly parametros = toSignal(inject(ActivatedRoute).queryParamMap);
  protected readonly grupos = [
    {
      titulo: 'ESPACIO DE TRABAJO',
      entradas: [
        { id: 'resumen', nombre: 'Resumen general', icono: 'panel' },
        { id: 'flota', nombre: 'Unidades y flota', icono: 'auto' },
        { id: 'alquileres', nombre: 'Alquileres', icono: 'contrato' },
        { id: 'importaciones', nombre: 'Compras e importación', icono: 'barco' },
        { id: 'taller', nombre: 'Taller', icono: 'taller' },
      ],
    },
    {
      titulo: 'CONTROL FINANCIERO',
      entradas: [
        { id: 'facturacion', nombre: 'Facturación y cobros', icono: 'factura' },
        { id: 'contabilidad', nombre: 'Contabilidad', icono: 'libro' },
        { id: 'reportes', nombre: 'Reportes', icono: 'grafica' },
        { id: 'ventas', nombre: 'Ventas', icono: 'venta' },
        { id: 'financiamiento', nombre: 'Financiamiento', icono: 'cartera' },
      ],
    },
    {
      titulo: 'ADMINISTRACIÓN',
      entradas: [
        { id: 'configuracion', nombre: 'Configuración', icono: 'ajustes' },
        { id: 'arranque', nombre: 'Migración y arranque', icono: 'carga' },
      ],
    },
  ];
  protected readonly vista = computed(() => {
    const id = this.parametros()?.get('vista') ?? 'resumen';
    return this.grupos.flatMap((g) => g.entradas).some((e) => e.id === id) ? id : 'resumen';
  });
  protected readonly titulo = computed(
    () =>
      this.grupos.flatMap((g) => g.entradas).find((e) => e.id === this.vista())?.nombre ??
      'Resumen general',
  );
  protected readonly descripciones: Record<string, string> = {
    resumen: 'Cada unidad, cada movimiento. Tu operación en un solo lugar.',
    flota: 'Toda la historia de tus vehículos, conectada por su VIN.',
    alquileres: 'De la entrega a la devolución, cada contrato bajo control.',
    importaciones: 'Del origen a la flota. Sigue cada etapa y su costo.',
    taller: 'Trabajo interno, costos claros y un destino para cada orden.',
    facturacion: 'Documentos, vencimientos y cobros en su moneda original.',
    contabilidad: 'Cada operación conectada con su partida contable.',
    reportes: 'Conoce el resultado de cada unidad durante su vida en la flota.',
    ventas: 'La siguiente etapa para las unidades que completan su vida en flota.',
    financiamiento: 'Una visión de los créditos propios y su recuperación.',
    configuracion: 'Una base común para operar con orden y trazabilidad.',
    arranque: 'Prepara los datos y concilia los saldos antes de comenzar.',
  };
  protected readonly menuAbierto = signal(false);
  protected readonly busqueda = signal('');
  protected readonly filtro = signal('Todas');
  protected readonly estados = ['Todas', 'Disponible', 'Alquilada', 'En taller', 'En tránsito'];
  protected readonly unidadesFiltradas = computed(() => {
    const termino = this.busqueda().trim().toLocaleLowerCase('es');
    return this.datos.unidades.filter(
      (u) =>
        (this.filtro() === 'Todas' || u.estado === this.filtro()) &&
        `${u.modelo} ${u.vin} ${u.placa} ${u.codigo}`.toLocaleLowerCase('es').includes(termino),
    );
  });
  protected readonly disponibles = this.datos.unidades.filter((u) => u.estado === 'Disponible');
  protected readonly unidad = signal<UnidadDemo | null>(null);
  protected readonly detalle = viewChild.required<ElementRef<HTMLDialogElement>>('detalle');
  protected readonly formulario = viewChild.required<ElementRef<HTMLDialogElement>>('formulario');
  protected readonly documento = viewChild.required<ElementRef<HTMLDialogElement>>('documento');
  protected readonly documentoTitulo = signal('');
  protected readonly documentoTexto = signal('');
  protected readonly aviso = signal('');
  protected readonly errorFormulario = signal('');
  protected readonly periodo = signal('noviembre');
  // Alturas ilustrativas precalculadas sobre el eje de Q150,000.
  private readonly serie = [
    { nombre: 'May', alto: 57, ingreso: '85500.00' },
    { nombre: 'Jun', alto: 61.667, ingreso: '92500.00' },
    { nombre: 'Jul', alto: 72, ingreso: '108000.00' },
    { nombre: 'Ago', alto: 67.467, ingreso: '101200.00' },
    { nombre: 'Sep', alto: 86.4, ingreso: '129600.00' },
    { nombre: 'Oct', alto: 88.533, ingreso: '132800.00' },
    { nombre: 'Nov', alto: 99, ingreso: '148500.00' },
  ];
  protected readonly meses = computed(() =>
    this.periodo() === 'noviembre' ? this.serie.slice(1) : this.serie.slice(0, 6),
  );
  protected readonly descripcionGrafica = computed(
    () =>
      'Ingresos ilustrativos en GTQ: ' +
      this.meses()
        .map((mes) => `${mes.nombre}: ${mes.ingreso}`)
        .join('; '),
  );
  protected readonly etapas = [
    {
      titulo: 'En tránsito',
      total: '02',
      texto: 'Compra y transporte',
      icono: 'barco',
      id: 'KC-005',
      modelo: 'Honda CR-V 2023',
      referencia: 'Lote 824061 · Miami',
      costo: '107800.00',
      dias: '12 días en etapa',
    },
    {
      titulo: 'En aduana',
      total: '01',
      texto: 'Nacionalización',
      icono: 'factura',
      id: 'KC-007',
      modelo: 'Toyota Yaris 2022',
      referencia: 'Puerto Quetzal',
      costo: '82400.00',
      dias: '3 días en etapa',
    },
    {
      titulo: 'En taller',
      total: '01',
      texto: 'Reacondicionamiento',
      icono: 'taller',
      id: 'KC-008',
      modelo: 'Nissan Rogue 2021',
      referencia: 'OT-026 · Mano de obra',
      costo: '118600.00',
      dias: '5 días en etapa',
    },
    {
      titulo: 'Lista para alta',
      total: '01',
      texto: 'Revisión del contador',
      icono: 'check',
      id: 'KC-009',
      modelo: 'Hyundai Accent 2022',
      referencia: 'Hoja de costo conciliada',
      costo: '89100.00',
      dias: '1 día en etapa',
    },
  ];
  protected readonly ordenes = [
    {
      numero: 'OT-026',
      modelo: 'Nissan Rogue · KC-008',
      tipo: 'Reacondicionamiento',
      tarea: 'Alineación y revisión de suspensión',
      responsable: 'Carlos López',
      horas: '12 h',
      monto: '1800.00',
      destino: 'Capitalizar al costo de la unidad',
      estado: 'En proceso',
    },
    {
      numero: 'OT-027',
      modelo: 'Kia Sportage · KC-004',
      tipo: 'Mantenimiento de flota',
      tarea: 'Servicio preventivo de 60,000 km',
      responsable: 'Luis Pérez',
      horas: '4 h',
      monto: '600.00',
      destino: 'Gasto de la unidad · Alquiler',
      estado: 'En revisión',
    },
  ];
  protected readonly roles = [
    {
      nombre: 'Auxiliar contable',
      permiso: 'Registra documentos y prepara borradores.',
      iniciales: 'AC',
    },
    { nombre: 'Contador', permiso: 'Revisa, contabiliza y cierra períodos.', iniciales: 'CO' },
    {
      nombre: 'Gerente financiero',
      permiso: 'Aprueba pagos, ajustes y reaperturas.',
      iniciales: 'GF',
    },
    { nombre: 'Gerencia', permiso: 'Consulta reportes gerenciales.', iniciales: 'GE' },
  ];

  protected navegar(vista: string): void {
    void this.router.navigate(['/mockup'], { queryParams: { vista } });
    this.prepararVista();
  }

  protected prepararVista(): void {
    this.menuAbierto.set(false);
    this.aviso.set('');
    this.desplazamiento.scrollToPosition([0, 0]);
  }

  protected buscar(valor: string): void {
    this.busqueda.set(valor);
    this.filtro.set('Todas');
    if (this.vista() !== 'flota') this.navegar('flota');
  }

  protected abrirUnidad(unidad: UnidadDemo): void {
    this.unidad.set(unidad);
    this.detalle().nativeElement.showModal();
  }

  protected nuevoContrato(): void {
    this.errorFormulario.set('');
    this.formulario().nativeElement.showModal();
  }

  protected guardarContrato(formulario: NgForm): void {
    this.errorFormulario.set('');
    if (formulario.invalid) {
      formulario.control.markAllAsTouched();
      this.errorFormulario.set('Completa los campos obligatorios para guardar el borrador.');
      return;
    }
    const datos = formulario.value;
    if (!String(datos.cliente).trim()) {
      this.errorFormulario.set('Escribe el nombre del cliente.');
      return;
    }
    if (datos.devolucion <= datos.salida) {
      this.errorFormulario.set('La devolución debe ser posterior a la salida.');
      return;
    }
    if (!this.disponibles.some((u) => u.codigo === datos.unidad)) {
      this.errorFormulario.set('Selecciona una unidad disponible.');
      return;
    }
    this.datos.guardarBorrador({ ...datos, cliente: String(datos.cliente).trim() });
    this.formulario().nativeElement.close();
    formulario.resetForm({ moneda: 'GTQ', combustible: 'Lleno' });
    this.navegar('alquileres');
    this.aviso.set(
      'Borrador de demostración guardado en esta sesión. No se reservó la unidad ni se generaron cargos.',
    );
  }

  protected verDocumento(titulo: string, texto: string): void {
    this.documentoTitulo.set(titulo);
    this.documentoTexto.set(texto);
    this.documento().nativeElement.showModal();
  }

  protected exportar(): void {
    const reporte = this.vista() === 'reportes';
    const filas = reporte
      ? [
          ['DEMOSTRACIÓN — noviembre 2026 — período abierto — GTQ'],
          ['Unidad', 'VIN', 'Ingreso', 'Resultado operativo', 'Ocupación %'],
          ...this.datos.unidades
            .filter((u) => u.estado !== 'En tránsito')
            .map((u) => [u.modelo, u.vin, u.ingreso, u.resultado, u.ocupacion]),
        ]
      : [
          ['DEMOSTRACIÓN — corte 06/11/2026 — muestra filtrada'],
          ['Unidad', 'VIN', 'Placa', 'Estado', 'Costo acumulado GTQ'],
          ...this.unidadesFiltradas().map((u) => [u.modelo, u.vin, u.placa, u.estado, u.costo]),
        ];
    const csv = filas
      .map((fila) => fila.map((valor) => `"${valor.replaceAll('"', '""')}"`).join(','))
      .join('\r\n');
    const url = URL.createObjectURL(new Blob(['\uFEFF', csv], { type: 'text/csv;charset=utf-8;' }));
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = reporte ? 'demo-rentabilidad-noviembre.csv' : 'demo-unidades.csv';
    enlace.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    this.aviso.set('Se exportó la muestra de datos ficticios en formato CSV.');
  }
}
