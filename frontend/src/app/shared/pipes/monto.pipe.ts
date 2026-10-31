import { Pipe, PipeTransform } from '@angular/core';

export type Moneda = 'GTQ' | 'USD';

/**
 * Da formato a un monto que llega de la API como texto ("1234.567890").
 * Intl.NumberFormat acepta el texto como decimal exacto, así que nunca pasa por float:
 * el front solo presenta, no calcula (acuerdo 2 de K1).
 */
@Pipe({ name: 'monto' })
export class MontoPipe implements PipeTransform {
  transform(valor: string | null | undefined, moneda: Moneda = 'GTQ'): string {
    if (valor === null || valor === undefined || valor === '') {
      return '';
    }
    const formato = new Intl.NumberFormat('es-GT', {
      style: 'currency',
      currency: moneda,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2, // redondeo por defecto: mitad hacia arriba, igual que el backend
    });
    // El tipo de TypeScript solo declara number, pero el estándar acepta cadenas decimales.
    return formato.format(valor as unknown as number);
  }
}
