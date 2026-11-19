import { Pipe, PipeTransform } from '@angular/core';
import { MontoPipe } from '../../shared/pipes/monto.pipe';

/** Monto de un reporte de rentabilidad: null es un concepto pendiente (su regla no tiene cuenta). */
@Pipe({ name: 'cifra' })
export class CifraPipe implements PipeTransform {
  private readonly monto = new MontoPipe();

  transform(valor: string | null | undefined): string {
    return valor === null ? 'pendiente' : this.monto.transform(valor);
  }
}
