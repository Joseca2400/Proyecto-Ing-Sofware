import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  ConfiguracionService,
  PerfilFiscal,
  PerfilFiscalEntrada,
  REGIMENES_ISR,
  RegimenISR,
  TasaImpositiva,
  TasaImpositivaEntrada,
  TIPOS_TASA,
  TipoTasa,
} from './configuracion.service';

/** Fecha local en formato ISO ("2026-11-19"); se compara como texto, sin cálculos. */
const hoy = () => new Date().toLocaleDateString('en-CA');

// HU-1.01 (Sprint 1): perfil fiscal de la empresa y tasas impositivas, ambos con vigencia.
// Cada cambio guarda una versión nueva; las transacciones anteriores conservan la que tenían.
// El NIT, la vigencia y las tasas los valida el servidor; aquí solo se revisa la forma.
// Pendiente (criterio 5): solo contador y gerente financiero guardan, cuando exista el login (C1).
@Component({
  selector: 'app-perfil-fiscal',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './perfil-fiscal.html',
  styleUrl: './perfil-fiscal.css',
})
export class PerfilFiscalPantalla {
  private readonly servicio = inject(ConfiguracionService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly hoy = hoy();
  protected readonly regimenes = REGIMENES_ISR;
  protected readonly tiposTasa = TIPOS_TASA;
  protected readonly versiones = signal<PerfilFiscal[]>([]);
  protected readonly tasas = signal<TasaImpositiva[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly errorTasa = signal<string | null>(null);
  protected readonly avisoTasa = signal<string | null>(null);
  protected readonly guardando = signal(false);

  /** La versión que aplica hoy: la más reciente con vigencia hasta hoy. */
  protected readonly vigente = computed(() =>
    this.versiones().find((v) => v.vigente_desde <= hoy()),
  );

  /** Ids de las tasas vigentes hoy: la primera de cada tipo con vigencia hasta hoy. */
  protected readonly tasasVigentes = computed(() => {
    const vistas = new Set<TipoTasa>();
    const ids = new Set<number>();
    for (const tasa of this.tasas()) {
      if (tasa.vigente_desde <= hoy() && !vistas.has(tasa.tipo)) {
        vistas.add(tasa.tipo);
        ids.add(tasa.id);
      }
    }
    return ids;
  });

  protected readonly formulario = this.fb.group({
    vigente_desde: [hoy(), Validators.required],
    razon_social: ['', Validators.required],
    nombre_comercial: ['', Validators.required],
    nit: ['', [Validators.required, Validators.pattern(/^\s*\d[\d\s]*-?\s*[\dkK]\s*$/)]],
    direccion_fiscal: ['', Validators.required],
    establecimiento_sat: [1, [Validators.required, Validators.min(1), Validators.max(9999)]],
    regimen_isr: ['sobre_utilidades' as RegimenISR],
    agente_retencion_iva: [false],
    agente_retencion_isr: [false],
  });

  protected readonly formularioTasa = this.fb.group({
    tipo: ['IVA_GENERAL' as TipoTasa],
    porcentaje: ['', Validators.pattern(/^\d+(\.\d{1,4})?$/)],
    monto_limite: ['', Validators.pattern(/^\d+(\.\d{1,2})?$/)],
    vigente_desde: [hoy(), Validators.required],
  });

  protected readonly regimen = toSignal(this.formulario.controls.regimen_isr.valueChanges, {
    initialValue: this.formulario.controls.regimen_isr.value,
  });

  protected readonly tipoTasa = toSignal(this.formularioTasa.controls.tipo.valueChanges, {
    initialValue: this.formularioTasa.controls.tipo.value,
  });

  protected readonly descripcionRegimen = computed(
    () => this.regimenes.find((r) => r.valor === this.regimen())?.descripcion ?? '',
  );

  protected readonly reglaTasa = computed(
    () => this.tiposTasa.find((t) => t.valor === this.tipoTasa()) ?? this.tiposTasa[0],
  );

  constructor() {
    this.cargar();
  }

  protected etiquetaRegimen(valor: RegimenISR): string {
    return this.regimenes.find((r) => r.valor === valor)?.etiqueta ?? valor;
  }

  protected etiquetaTasa(valor: TipoTasa): string {
    return this.tiposTasa.find((t) => t.valor === valor)?.etiqueta ?? valor;
  }

  protected aplica(tasa: TasaImpositiva): boolean {
    return this.vigente()?.tasas_del_regimen.includes(tasa.tipo) ?? false;
  }

  protected cargar(): void {
    this.servicio.historialPerfil().subscribe({
      next: (versiones) => {
        this.versiones.set(versiones);
        // El formulario parte de la última versión: un cambio solo toca lo que cambia.
        const ultima = versiones[0];
        if (ultima) {
          this.formulario.reset({
            vigente_desde: hoy(),
            razon_social: ultima.razon_social,
            nombre_comercial: ultima.nombre_comercial,
            nit: ultima.nit_formateado,
            direccion_fiscal: ultima.direccion_fiscal,
            establecimiento_sat: ultima.establecimiento_sat,
            regimen_isr: ultima.regimen_isr,
            agente_retencion_iva: ultima.agente_retencion_iva,
            agente_retencion_isr: ultima.agente_retencion_isr,
          });
        }
      },
      error: () => this.error.set('No se pudo consultar el perfil fiscal'),
    });
    this.cargarTasas();
  }

  private cargarTasas(): void {
    this.servicio.tasas().subscribe({
      next: (tasas) => this.tasas.set(tasas),
      error: () => this.errorTasa.set('No se pudo consultar las tasas impositivas'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.error.set(null);
      return;
    }
    const valores = this.formulario.getRawValue();
    const entrada: PerfilFiscalEntrada = {
      ...valores,
      razon_social: valores.razon_social.trim(),
      nombre_comercial: valores.nombre_comercial.trim(),
      nit: valores.nit.trim(),
      direccion_fiscal: valores.direccion_fiscal.trim(),
    };

    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.registrarPerfil(entrada).subscribe({
      next: (perfil) => {
        this.guardando.set(false);
        this.aviso.set(`Perfil fiscal guardado, vigente desde el ${perfil.vigente_desde}`);
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        this.error.set(this.detalle(respuesta, 'No se pudo guardar el perfil fiscal'));
      },
    });
  }

  protected guardarTasa(): void {
    const valores = this.formularioTasa.getRawValue();
    const regla = this.reglaTasa();
    const faltante =
      (regla.porcentaje && !valores.porcentaje.trim() && 'Indique el porcentaje') ||
      (regla.monto && !valores.monto_limite.trim() && 'Indique el monto límite');
    if (this.formularioTasa.invalid || faltante) {
      this.formularioTasa.markAllAsTouched();
      this.errorTasa.set(faltante || null);
      return;
    }
    const entrada: TasaImpositivaEntrada = {
      tipo: valores.tipo,
      vigente_desde: valores.vigente_desde,
      ...(regla.porcentaje ? { porcentaje: valores.porcentaje.trim() } : {}),
      ...(regla.monto ? { monto_limite: valores.monto_limite.trim() } : {}),
    };

    this.errorTasa.set(null);
    this.avisoTasa.set(null);
    this.servicio.registrarTasa(entrada).subscribe({
      next: (tasa) => {
        this.avisoTasa.set(
          `${this.etiquetaTasa(tasa.tipo)} registrada, vigente desde el ${tasa.vigente_desde}`,
        );
        this.formularioTasa.reset({ tipo: valores.tipo, vigente_desde: hoy() });
        this.cargarTasas();
      },
      error: (respuesta: HttpErrorResponse) =>
        this.errorTasa.set(this.detalle(respuesta, 'No se pudo registrar la tasa')),
    });
  }

  private detalle(respuesta: HttpErrorResponse, porDefecto: string): string {
    const detalle = respuesta.error?.detail;
    return typeof detalle === 'string' ? detalle : porDefecto;
  }
}
