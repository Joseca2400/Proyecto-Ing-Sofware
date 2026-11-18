import { DatePipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { AlquileresService, DepositosVigentes } from './alquileres.service';

// HU-3.07 (Sprint 2): depósitos en garantía vigentes con su saldo y el total por moneda, que
// calcula el servidor. Pendiente: mostrar el cuadre contra el saldo de la cuenta contable cuando
// exista la consulta del mayor (HU-2.16).
@Component({
  selector: 'app-depositos',
  imports: [MontoPipe, DatePipe],
  templateUrl: './depositos.html',
})
export class DepositosPantalla {
  private readonly servicio = inject(AlquileresService);

  protected readonly vigentes = signal<DepositosVigentes>({ depositos: [], totales: {} });
  protected readonly error = signal<string | null>(null);

  constructor() {
    this.servicio.depositosVigentes().subscribe({
      next: (datos) => this.vigentes.set(datos),
      error: () => this.error.set('No se pudieron consultar los depósitos'),
    });
  }
}
