import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { Unidad, UnidadesService } from '../unidades/unidades.service';
import { ComprasService, HojaCosto } from './compras.service';

// HU-4.08 (Sprint 2, versión delgada): costo de la unidad agrupado en compra, importación y
// reacondicionamiento, con su cuadre contra el saldo de unidades en proceso del VIN en el mayor.
// Todo lo calcula el servidor; aquí solo se presenta e imprime.
// Diferido: exportar a PDF y Excel (Sprint 5, HU-7.09).
@Component({
  selector: 'app-hoja-costo',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './hoja-costo.html',
})
export class HojaCostoPantalla {
  private readonly servicio = inject(ComprasService);

  protected readonly unidades = signal<Unidad[]>([]);
  protected readonly hoja = signal<HojaCosto | null>(null);
  protected readonly error = signal<string | null>(null);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    vin: ['', [Validators.required, Validators.pattern(/^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/)]],
  });

  constructor() {
    inject(UnidadesService)
      .unidades()
      .subscribe({
        next: (lista) => this.unidades.set(lista),
        error: () => this.error.set('No se pudo consultar las unidades'),
      });
  }

  protected consultar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    this.error.set(null);
    this.hoja.set(null);
    this.servicio.hojaCosto(this.formulario.getRawValue().vin.trim().toUpperCase()).subscribe({
      next: (hoja) => this.hoja.set(hoja),
      error: (respuesta: HttpErrorResponse) => {
        const detalle = respuesta.error?.detail;
        this.error.set(
          typeof detalle === 'string' ? detalle : 'No se pudo consultar la hoja de costo',
        );
      },
    });
  }

  protected imprimir(): void {
    window.print();
  }
}
