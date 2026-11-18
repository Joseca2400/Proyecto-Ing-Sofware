import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { Tarifa, TallerService } from './taller.service';

// HU-5.02 (Sprint 2, versión delgada): tarifa horaria de costo general con vigencia. Un cambio es
// una tarifa nueva que aplica a las horas de su fecha en adelante; no se edita la vigente.
// Diferido: tarifa por mecánico o especialidad y tarifa de venta de la postventa (Sprint 5).
@Component({
  selector: 'app-tarifas-taller',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './tarifas.html',
})
export class TarifasTallerPantalla {
  private readonly servicio = inject(TallerService);

  protected readonly tarifas = signal<Tarifa[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    tarifa_hora: ['', [Validators.required, Validators.pattern(/^\s*\d+(\.\d{1,6})?\s*$/)]],
    vigente_desde: [new Date().toLocaleDateString('en-CA'), Validators.required],
  });

  constructor() {
    this.cargar();
  }

  private cargar(): void {
    this.servicio.tarifas().subscribe({
      next: (lista) => this.tarifas.set(lista),
      error: () => this.error.set('No se pudo consultar las tarifas'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    const { tarifa_hora, vigente_desde } = this.formulario.getRawValue();
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.crearTarifa({ tarifa_hora: tarifa_hora.trim(), vigente_desde }).subscribe({
      next: (tarifa) => {
        this.guardando.set(false);
        this.aviso.set(`Tarifa vigente desde el ${tarifa.vigente_desde} guardada`);
        this.formulario.controls.tarifa_hora.reset('');
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo guardar la tarifa');
      },
    });
  }
}
