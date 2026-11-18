import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  AlquileresService,
  CatalogosTarifas,
  ETIQUETAS_MODALIDAD,
  Modalidad,
  Tarifa,
  TarifaEntrada,
} from './alquileres.service';

// HU-3.05 (Sprint 2): tarifario por tipo de vehículo o, como excepción, por unidad (VIN).
// Una tarifa no se edita: el cambio es una tarifa nueva y el servidor cierra la anterior.
// Diferido: aprobación de descuentos sobre el porcentaje configurado (con el contrato, Sprint 3).
@Component({
  selector: 'app-tarifario',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './tarifario.html',
})
export class TarifarioPantalla {
  private readonly servicio = inject(AlquileresService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly etiquetas = ETIQUETAS_MODALIDAD;
  protected readonly catalogos = signal<CatalogosTarifas>({
    modalidades: [],
    monedas: [],
    tipos_vehiculo: [],
  });
  protected readonly tarifas = signal<Tarifa[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    aplica_a: ['tipo' as 'tipo' | 'vin'],
    tipo_vehiculo: ['sedan'],
    vin: [''],
    modalidad: ['diaria' as Modalidad],
    moneda: ['GTQ' as 'GTQ' | 'USD'],
    // Solo se valida la forma; el servidor decide si el monto es aceptable.
    monto: ['', [Validators.required, Validators.pattern(/^\d+(\.\d{1,6})?$/)]],
    km_incluido: [0, [Validators.required, Validators.min(0)]],
    precio_km_adicional: ['0', [Validators.required, Validators.pattern(/^\d+(\.\d{1,6})?$/)]],
    vigente_desde: [new Date().toLocaleDateString('en-CA'), Validators.required],
    vigente_hasta: [''],
  });

  protected readonly aplicaA = toSignal(this.formulario.controls.aplica_a.valueChanges, {
    initialValue: this.formulario.controls.aplica_a.value,
  });

  constructor() {
    this.servicio.catalogos().subscribe((c) => this.catalogos.set(c));
    this.cargar();
  }

  protected cargar(): void {
    this.servicio.tarifas().subscribe({
      next: (lista) => this.tarifas.set(lista),
      error: () => this.error.set('No se pudo consultar el tarifario'),
    });
  }

  protected guardar(): void {
    const v = this.formulario.getRawValue();
    if (this.formulario.invalid || (v.aplica_a === 'vin' && !v.vin.trim())) {
      this.formulario.markAllAsTouched();
      if (v.aplica_a === 'vin' && !v.vin.trim()) this.error.set('Indique el VIN de la unidad');
      return;
    }
    const entrada: TarifaEntrada = {
      ...(v.aplica_a === 'vin' ? { vin: v.vin.trim() } : { tipo_vehiculo: v.tipo_vehiculo }),
      modalidad: v.modalidad,
      moneda: v.moneda,
      monto: v.monto,
      km_incluido: v.km_incluido,
      precio_km_adicional: v.precio_km_adicional,
      vigente_desde: v.vigente_desde,
      vigente_hasta: v.vigente_hasta || undefined,
    };

    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.registrarTarifa(entrada).subscribe({
      next: () => {
        this.guardando.set(false);
        this.aviso.set('Tarifa registrada; la anterior abierta quedó cerrada el día previo');
        this.formulario.patchValue({ monto: '', vigente_hasta: '' });
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo registrar la tarifa');
      },
    });
  }
}
