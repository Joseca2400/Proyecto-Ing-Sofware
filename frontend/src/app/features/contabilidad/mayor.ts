import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { ETIQUETAS_LINEA } from '../configuracion/configuracion.service';
import { ContabilidadService, Cuenta, Mayor } from './contabilidad.service';

const hoy = () => new Date().toLocaleDateString('en-CA');

// HU-2.16 (Sprint 2): mayor de una cuenta con saldo acumulado (lo calcula el servidor), el
// documento de origen y, en cuentas en USD, el monto original. Diferido: exportar (Sprint 5).
@Component({
  selector: 'app-mayor',
  imports: [ReactiveFormsModule, RouterLink, MontoPipe],
  templateUrl: './mayor.html',
})
export class MayorPantalla {
  private readonly servicio = inject(ContabilidadService);

  protected readonly etiquetasLinea = ETIQUETAS_LINEA;
  protected readonly cuentas = signal<Cuenta[]>([]);
  protected readonly lineasNegocio = signal<string[]>([]);
  protected readonly mayor = signal<Mayor | null>(null);
  protected readonly error = signal<string | null>(null);

  protected readonly filtros = inject(FormBuilder).nonNullable.group({
    cuenta_id: [
      Number(inject(ActivatedRoute).snapshot.queryParamMap.get('cuenta')) || 0,
      Validators.min(1),
    ],
    desde: [hoy().slice(0, 8) + '01'],
    hasta: [hoy()],
    linea_negocio: [''],
    vin: [''],
  });

  constructor() {
    this.servicio.cuentas().subscribe({
      next: (lista) => this.cuentas.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar las cuentas'),
    });
    this.servicio.lineasNegocio().subscribe({
      next: (lista) => this.lineasNegocio.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar las líneas de negocio'),
    });
    if (this.filtros.value.cuenta_id) this.consultar();
  }

  protected consultar(): void {
    if (this.filtros.invalid) {
      this.filtros.markAllAsTouched();
      return;
    }
    const { cuenta_id, ...filtros } = this.filtros.getRawValue();
    this.error.set(null);
    this.servicio.mayor(cuenta_id, filtros).subscribe({
      next: (mayor) => this.mayor.set(mayor),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar el mayor'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
