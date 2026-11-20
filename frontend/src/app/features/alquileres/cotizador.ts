import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  AlquileresService,
  CargoCotizacion,
  Concepto,
  Cotizacion,
  CotizacionEntrada,
  MODALIDADES,
  Modalidad,
  Moneda,
  Naturaleza,
  TIPOS_VEHICULO,
} from './alquileres.service';

const hoy = () => new Date().toLocaleDateString('en-CA');

type CargoForm = FormGroup<{
  concepto_id: FormControl<number>;
  incluir: FormControl<boolean>;
  cantidad: FormControl<number>;
  precio: FormControl<string>;
}>;

// HU-3.05 (Sprint 1): cotización con la tarifa vigente a la fecha de salida. El servidor convierte
// de moneda con el tipo de cambio del Banguat (HU-1.06) y separa base e IVA con la tasa del perfil
// fiscal (HU-1.01); el front solo presenta. El contrato (HU-3.06) partirá de esta cotización.
@Component({
  selector: 'app-cotizador',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './cotizador.html',
  styleUrl: './tarifario.css',
})
export class CotizadorPantalla {
  private readonly servicio = inject(AlquileresService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly tipos = TIPOS_VEHICULO;
  protected readonly modalidades = MODALIDADES;
  protected readonly conceptos = signal<Concepto[]>([]);
  protected readonly cotizacion = signal<Cotizacion | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly calculando = signal(false);

  protected readonly formulario = this.fb.group({
    tipo_vehiculo: ['sedan'],
    vin: ['', Validators.pattern(/^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/)],
    modalidad: ['diaria' as Modalidad],
    moneda: ['GTQ' as Moneda],
    fecha_salida: [hoy(), Validators.required],
    fecha_devolucion: [hoy(), Validators.required],
    km_estimados: ['', Validators.pattern(/^\d+$/)],
    cargos: this.fb.array<CargoForm>([]),
  });

  protected readonly modalidad = toSignal(this.formulario.controls.modalidad.valueChanges, {
    initialValue: this.formulario.controls.modalidad.value,
  });

  constructor() {
    this.servicio.conceptos(true).subscribe({
      next: (lista) => {
        this.conceptos.set(lista);
        for (const concepto of lista) this.cargos.push(this.cargo(concepto));
      },
      error: () => this.error.set('No se pudo consultar los cargos adicionales'),
    });
  }

  private cargo(concepto: Concepto): CargoForm {
    return this.fb.group({
      concepto_id: [concepto.id],
      incluir: [false],
      cantidad: [1, [Validators.min(1), Validators.max(1000)]],
      precio: ['', Validators.pattern(/^\d+(\.\d{1,2})?$/)],
    });
  }

  protected get cargos(): FormArray<CargoForm> {
    return this.formulario.controls.cargos;
  }

  protected etiqueta(naturaleza: Naturaleza): string {
    return { ingreso: 'Ingreso', deposito: 'Depósito', reintegro: 'Reintegro' }[naturaleza];
  }

  protected cotizar(): void {
    const v = this.formulario.getRawValue();
    const seleccionados = v.cargos.filter((c) => c.incluir);
    const sinPrecio = seleccionados.find((c) => {
      const concepto = this.conceptos().find((x) => x.id === c.concepto_id);
      return !concepto?.precio_sugerido && !c.precio.trim();
    });
    const faltante =
      (v.modalidad === 'kilometraje' &&
        !v.km_estimados.trim() &&
        'Indique los kilómetros estimados') ||
      (sinPrecio &&
        `Indique el monto de ${this.conceptos().find((x) => x.id === sinPrecio.concepto_id)?.nombre}`);
    if (this.formulario.invalid || faltante) {
      this.formulario.markAllAsTouched();
      this.error.set(faltante || null);
      return;
    }

    const cargos: CargoCotizacion[] = seleccionados.map((c) => ({
      concepto_id: c.concepto_id,
      cantidad: Number(c.cantidad),
      ...(c.precio.trim() ? { precio: c.precio.trim() } : {}),
    }));
    const entrada: CotizacionEntrada = {
      tipo_vehiculo: v.tipo_vehiculo,
      ...(v.vin.trim() ? { vin: v.vin.trim().toUpperCase() } : {}),
      modalidad: v.modalidad,
      moneda: v.moneda,
      fecha_salida: v.fecha_salida,
      fecha_devolucion: v.fecha_devolucion,
      ...(v.km_estimados.trim() ? { km_estimados: Number(v.km_estimados) } : {}),
      cargos,
    };

    this.calculando.set(true);
    this.error.set(null);
    this.servicio.cotizar(entrada).subscribe({
      next: (cotizacion) => {
        this.calculando.set(false);
        this.cotizacion.set(cotizacion);
      },
      error: (respuesta: HttpErrorResponse) => {
        this.calculando.set(false);
        this.cotizacion.set(null);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo cotizar el alquiler');
      },
    });
  }
}
