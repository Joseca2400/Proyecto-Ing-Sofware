import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { ETIQUETAS_LINEA } from '../configuracion/configuracion.service';
import { Balance, ContabilidadService } from './contabilidad.service';

const hoy = () => new Date().toLocaleDateString('en-CA');

// HU-2.16 (Sprint 2): balance de comprobación de partidas contabilizadas. Saldos y totales los
// calcula el servidor. Diferido: exportar (Sprint 5, HU-7.09).
@Component({
  selector: 'app-balance',
  imports: [ReactiveFormsModule, RouterLink, MontoPipe],
  templateUrl: './balance.html',
})
export class BalancePantalla {
  private readonly servicio = inject(ContabilidadService);

  protected readonly etiquetasLinea = ETIQUETAS_LINEA;
  protected readonly lineasNegocio = signal<string[]>([]);
  protected readonly balance = signal<Balance | null>(null);
  protected readonly error = signal<string | null>(null);

  protected readonly filtros = inject(FormBuilder).nonNullable.group({
    desde: [hoy().slice(0, 8) + '01'],
    hasta: [hoy()],
    linea_negocio: [''],
    vin: [''],
  });

  constructor() {
    this.servicio.lineasNegocio().subscribe({
      next: (lista) => this.lineasNegocio.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar las líneas de negocio'),
    });
    this.consultar();
  }

  protected consultar(): void {
    this.error.set(null);
    this.servicio.balance(this.filtros.getRawValue()).subscribe({
      next: (balance) => this.balance.set(balance),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar el balance'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
