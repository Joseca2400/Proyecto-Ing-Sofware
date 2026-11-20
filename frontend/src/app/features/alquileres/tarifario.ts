import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  AlquileresService,
  Concepto,
  ConceptoEntrada,
  MODALIDADES,
  Modalidad,
  Moneda,
  NATURALEZAS,
  Naturaleza,
  Tarifa,
  TarifaEntrada,
  Temporada,
  TIPOS_VEHICULO,
} from './alquileres.service';

const hoy = () => new Date().toLocaleDateString('en-CA');
const MONTO = /^\d+(\.\d{1,2})?$/;

type Alcance = 'tipo' | 'unidad';

// HU-3.05 (Sprint 1): tarifas por modalidad, moneda y vigencia, por tipo de vehículo o por unidad;
// temporadas (listas de precios con fechas) y conceptos con su tratamiento fiscal.
// Las tarifas no se editan: un cambio es una versión nueva, así los contratos no cambian.
// Diferido: aprobación de descuentos sobre el porcentaje configurado.
@Component({
  selector: 'app-tarifario',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './tarifario.html',
  styleUrl: './tarifario.css',
})
export class TarifarioPantalla {
  private readonly servicio = inject(AlquileresService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly tipos = TIPOS_VEHICULO;
  protected readonly modalidades = MODALIDADES;
  protected readonly naturalezas = NATURALEZAS;

  protected readonly tarifas = signal<Tarifa[]>([]);
  protected readonly temporadas = signal<Temporada[]>([]);
  protected readonly conceptos = signal<Concepto[]>([]);
  protected readonly temporadasActivas = computed(() => this.temporadas().filter((t) => t.activa));

  protected readonly mensajes = {
    tarifa: { error: signal<string | null>(null), aviso: signal<string | null>(null) },
    temporada: { error: signal<string | null>(null), aviso: signal<string | null>(null) },
    concepto: { error: signal<string | null>(null), aviso: signal<string | null>(null) },
  };

  /** Concepto que se está editando (solo su precio y su estado). */
  protected readonly editando = signal<Concepto | null>(null);

  protected readonly formTarifa = this.fb.group({
    alcance: ['tipo' as Alcance],
    tipo_vehiculo: ['sedan'],
    vin: ['', Validators.pattern(/^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/)],
    temporada_id: [''],
    modalidad: ['diaria' as Modalidad],
    moneda: ['GTQ' as Moneda],
    monto: ['', [Validators.required, Validators.pattern(MONTO)]],
    km_incluido: ['', Validators.pattern(/^\d+$/)],
    costo_km_adicional: ['', Validators.pattern(MONTO)],
    vigente_desde: [hoy(), Validators.required],
  });

  protected readonly formTemporada = this.fb.group({
    nombre: ['', Validators.required],
    fecha_inicio: ['', Validators.required],
    fecha_fin: ['', Validators.required],
  });

  protected readonly formConcepto = this.fb.group({
    nombre: ['', Validators.required],
    naturaleza: ['ingreso' as Naturaleza],
    aplica_iva: [true],
    precio_sugerido: ['', Validators.pattern(MONTO)],
    moneda: ['GTQ' as Moneda],
  });

  protected readonly alcance = toSignal(this.formTarifa.controls.alcance.valueChanges, {
    initialValue: this.formTarifa.controls.alcance.value,
  });

  protected readonly modalidad = toSignal(this.formTarifa.controls.modalidad.valueChanges, {
    initialValue: this.formTarifa.controls.modalidad.value,
  });

  protected readonly naturaleza = toSignal(this.formConcepto.controls.naturaleza.valueChanges, {
    initialValue: this.formConcepto.controls.naturaleza.value,
  });

  constructor() {
    this.cargarTarifas();
    this.cargarTemporadas();
    this.cargarConceptos();
    // Un depósito o un reintegro nunca llevan IVA.
    this.formConcepto.controls.naturaleza.valueChanges.subscribe((valor) => {
      if (valor !== 'ingreso') this.formConcepto.controls.aplica_iva.setValue(false);
    });
  }

  protected etiquetaTipo(valor: string | null): string {
    return this.tipos.find((t) => t.valor === valor)?.etiqueta ?? valor ?? '';
  }

  protected etiquetaModalidad(valor: Modalidad): string {
    return this.modalidades.find((m) => m.valor === valor)?.etiqueta ?? valor;
  }

  protected periodo(valor: Modalidad): string {
    return this.modalidades.find((m) => m.valor === valor)?.periodo ?? '';
  }

  protected tratamiento(c: Concepto): string {
    if (c.naturaleza === 'deposito') return 'Depósito (pasivo)';
    if (c.naturaleza === 'reintegro') return 'Reintegro de terceros';
    return c.aplica_iva ? 'Ingreso con IVA' : 'Ingreso sin IVA';
  }

  private cargarTarifas(): void {
    this.servicio.tarifas().subscribe({
      next: (lista) => this.tarifas.set(lista),
      error: () => this.mensajes.tarifa.error.set('No se pudo consultar las tarifas'),
    });
  }

  private cargarTemporadas(): void {
    this.servicio.temporadas().subscribe({
      next: (lista) => this.temporadas.set(lista),
      error: () => this.mensajes.temporada.error.set('No se pudo consultar las temporadas'),
    });
  }

  private cargarConceptos(): void {
    this.servicio.conceptos().subscribe({
      next: (lista) => this.conceptos.set(lista),
      error: () => this.mensajes.concepto.error.set('No se pudo consultar los conceptos'),
    });
  }

  private detalle(respuesta: HttpErrorResponse, porDefecto: string): string {
    const detalle = respuesta.error?.detail;
    return typeof detalle === 'string' ? detalle : porDefecto;
  }

  // ── Tarifas ──────────────────────────────────────────────────────────────────

  protected guardarTarifa(): void {
    const v = this.formTarifa.getRawValue();
    const porUnidad = v.alcance === 'unidad';
    const kilometraje = v.modalidad === 'kilometraje';
    const faltante =
      (porUnidad && !v.vin.trim() && 'Indique el VIN de la unidad') ||
      (kilometraje &&
        (!v.km_incluido.trim() || !v.costo_km_adicional.trim()) &&
        'La tarifa por kilometraje requiere kilómetros incluidos y costo por kilómetro adicional');
    const { error, aviso } = this.mensajes.tarifa;
    if (this.formTarifa.invalid || faltante) {
      this.formTarifa.markAllAsTouched();
      error.set(faltante || null);
      return;
    }

    const entrada: TarifaEntrada = {
      ...(porUnidad ? { vin: v.vin.trim().toUpperCase() } : { tipo_vehiculo: v.tipo_vehiculo }),
      ...(v.temporada_id ? { temporada_id: Number(v.temporada_id) } : {}),
      modalidad: v.modalidad,
      moneda: v.moneda,
      monto: v.monto.trim(),
      ...(v.km_incluido.trim() ? { km_incluido: Number(v.km_incluido) } : {}),
      ...(v.costo_km_adicional.trim() ? { costo_km_adicional: v.costo_km_adicional.trim() } : {}),
      vigente_desde: v.vigente_desde,
    };

    error.set(null);
    aviso.set(null);
    this.servicio.registrarTarifa(entrada).subscribe({
      next: (tarifa) => {
        aviso.set(`Tarifa registrada, vigente desde el ${tarifa.vigente_desde}`);
        this.formTarifa.reset({
          alcance: v.alcance,
          tipo_vehiculo: v.tipo_vehiculo,
          modalidad: v.modalidad,
          moneda: v.moneda,
          vigente_desde: hoy(),
        });
        this.cargarTarifas();
      },
      error: (r: HttpErrorResponse) => error.set(this.detalle(r, 'No se pudo registrar la tarifa')),
    });
  }

  // ── Temporadas ───────────────────────────────────────────────────────────────

  protected guardarTemporada(): void {
    const { error, aviso } = this.mensajes.temporada;
    if (this.formTemporada.invalid) {
      this.formTemporada.markAllAsTouched();
      error.set(null);
      return;
    }
    const v = this.formTemporada.getRawValue();
    error.set(null);
    aviso.set(null);
    this.servicio.registrarTemporada({ ...v, nombre: v.nombre.trim() }).subscribe({
      next: (t) => {
        aviso.set(`Temporada ${t.nombre} registrada`);
        this.formTemporada.reset();
        this.cargarTemporadas();
      },
      error: (r: HttpErrorResponse) =>
        error.set(this.detalle(r, 'No se pudo registrar la temporada')),
    });
  }

  protected desactivar(temporada: Temporada): void {
    const { error, aviso } = this.mensajes.temporada;
    this.servicio.desactivarTemporada(temporada.id).subscribe({
      next: () => {
        aviso.set(`Temporada ${temporada.nombre} desactivada`);
        this.cargarTemporadas();
      },
      error: (r: HttpErrorResponse) =>
        error.set(this.detalle(r, 'No se pudo desactivar la temporada')),
    });
  }

  // ── Conceptos ────────────────────────────────────────────────────────────────

  protected editar(concepto: Concepto): void {
    this.editando.set(concepto);
    this.mensajes.concepto.error.set(null);
    this.mensajes.concepto.aviso.set(null);
    this.formConcepto.reset({
      nombre: concepto.nombre,
      naturaleza: concepto.naturaleza,
      aplica_iva: concepto.aplica_iva,
      precio_sugerido: concepto.precio_sugerido
        ? concepto.precio_sugerido.replace(/0+$/, '').replace(/\.$/, '')
        : '',
      moneda: concepto.moneda ?? 'GTQ',
    });
  }

  protected cancelarEdicion(): void {
    this.editando.set(null);
    this.formConcepto.reset();
  }

  protected guardarConcepto(): void {
    const { error, aviso } = this.mensajes.concepto;
    if (this.formConcepto.invalid) {
      this.formConcepto.markAllAsTouched();
      error.set(null);
      return;
    }
    const v = this.formConcepto.getRawValue();
    const precio = v.precio_sugerido.trim()
      ? { precio_sugerido: v.precio_sugerido.trim(), moneda: v.moneda }
      : {};
    const concepto = this.editando();
    const peticion = concepto
      ? this.servicio.cambiarConcepto(concepto.id, { ...precio, activo: concepto.activo })
      : this.servicio.registrarConcepto({
          nombre: v.nombre.trim(),
          naturaleza: v.naturaleza,
          aplica_iva: v.naturaleza === 'ingreso' && v.aplica_iva,
          ...precio,
        } satisfies ConceptoEntrada);

    error.set(null);
    aviso.set(null);
    peticion.subscribe({
      next: (c) => {
        aviso.set(`Concepto ${c.nombre} ${concepto ? 'actualizado' : 'registrado'}`);
        this.cancelarEdicion();
        this.cargarConceptos();
      },
      error: (r: HttpErrorResponse) => error.set(this.detalle(r, 'No se pudo guardar el concepto')),
    });
  }

  protected cambiarEstado(concepto: Concepto): void {
    const { error, aviso } = this.mensajes.concepto;
    const precio =
      concepto.precio_sugerido && concepto.moneda
        ? { precio_sugerido: concepto.precio_sugerido, moneda: concepto.moneda }
        : {};
    this.servicio.cambiarConcepto(concepto.id, { ...precio, activo: !concepto.activo }).subscribe({
      next: (c) => {
        aviso.set(`Concepto ${c.nombre} ${c.activo ? 'reactivado' : 'dado de baja'}`);
        this.cargarConceptos();
      },
      error: (r: HttpErrorResponse) => error.set(this.detalle(r, 'No se pudo cambiar el concepto')),
    });
  }
}
