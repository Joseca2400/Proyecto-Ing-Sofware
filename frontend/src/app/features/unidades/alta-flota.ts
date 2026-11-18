import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { CandidataAltaFlota, UnidadesService } from './unidades.service';

// HU-3.01 (Sprint 2, versión delgada): alta como activo fijo de la flota de una unidad lista, sin
// orden de taller abierta, por el costo de su hoja de costo cuando cuadra con el mayor. El servidor
// genera la partida y pasa la unidad a "en flota". Solo el contador la registra; la aprobación del
// alta que registre el auxiliar queda para el Sprint 5.
@Component({
  selector: 'app-alta-flota',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './alta-flota.html',
})
export class AltaFlotaPantalla {
  private readonly servicio = inject(UnidadesService);

  protected readonly candidatas = signal<CandidataAltaFlota[]>([]);
  protected readonly seleccionada = signal<CandidataAltaFlota | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    fecha: [new Date().toLocaleDateString('en-CA'), Validators.required],
  });

  constructor() {
    this.cargar();
  }

  private cargar(): void {
    this.servicio.candidatasAlta().subscribe({
      next: (lista) => this.candidatas.set(lista),
      error: () => this.error.set('No se pudo consultar las unidades listas'),
    });
  }

  protected elegir(candidata: CandidataAltaFlota): void {
    this.seleccionada.set(candidata);
    this.error.set(null);
    this.aviso.set(null);
  }

  protected confirmar(): void {
    const candidata = this.seleccionada();
    if (!candidata || this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    this.guardando.set(true);
    this.error.set(null);
    this.servicio.darDeAlta(candidata.vin, this.formulario.getRawValue().fecha).subscribe({
      next: (alta) => {
        this.guardando.set(false);
        this.seleccionada.set(null);
        this.aviso.set(`Unidad ${alta.vin} dada de alta en la flota (partida ${alta.partida_id})`);
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo dar de alta la unidad');
      },
    });
  }
}
