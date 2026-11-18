import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { DepreciacionTipo, UnidadesService, etiqueta } from './unidades.service';

const PORCENTAJE = /^\s*\d+(\.\d{1,2})?\s*$/;

// HU-3.02: valores de depreciación por defecto de cada tipo de vehículo, que se proponen al dar de
// alta la unidad (vida útil, residual como % del costo y porcentaje fiscal anual). Solo el contador
// los cambia; afectan las altas siguientes, no las unidades ya dadas de alta.
@Component({
  selector: 'app-depreciacion',
  imports: [ReactiveFormsModule],
  templateUrl: './depreciacion.html',
})
export class DepreciacionPantalla {
  private readonly servicio = inject(UnidadesService);

  protected readonly etiqueta = etiqueta;
  protected readonly tipos = signal<DepreciacionTipo[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    tipo_vehiculo: ['', Validators.required],
    vida_util_meses: [60, [Validators.required, Validators.min(1)]],
    porcentaje_residual: ['', [Validators.required, Validators.pattern(PORCENTAJE)]],
    porcentaje_fiscal: ['', [Validators.required, Validators.pattern(PORCENTAJE)]],
  });

  constructor() {
    this.cargar();
  }

  private cargar(): void {
    this.servicio.depreciacionTipos().subscribe({
      next: (lista) => this.tipos.set(lista),
      error: () => this.error.set('No se pudo consultar los valores por defecto'),
    });
  }

  protected editar(tipo: DepreciacionTipo): void {
    this.formulario.setValue({
      tipo_vehiculo: tipo.tipo_vehiculo,
      vida_util_meses: tipo.vida_util_meses,
      porcentaje_residual: tipo.porcentaje_residual,
      porcentaje_fiscal: tipo.porcentaje_fiscal,
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    const { tipo_vehiculo, vida_util_meses, porcentaje_residual, porcentaje_fiscal } =
      this.formulario.getRawValue();
    this.error.set(null);
    this.aviso.set(null);
    this.servicio
      .definirDepreciacionTipo(tipo_vehiculo, {
        vida_util_meses,
        porcentaje_residual: porcentaje_residual.trim(),
        porcentaje_fiscal: porcentaje_fiscal.trim(),
      })
      .subscribe({
        next: (tipo) => {
          this.aviso.set(`Valores de ${etiqueta(tipo.tipo_vehiculo)} guardados`);
          this.cargar();
        },
        error: (respuesta: HttpErrorResponse) => {
          const detalle = respuesta.error?.detail;
          this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo guardar');
        },
      });
  }
}
