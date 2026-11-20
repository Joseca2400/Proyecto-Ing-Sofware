import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { etiqueta } from '../unidades/unidades.service';
import { CifraPipe } from './cifra.pipe';
import { ReporteRentabilidadCiclo, ReportesService } from './reportes.service';

// Opciones del filtro, en el orden del ciclo (los mismos estados de `unidades`).
const ESTADOS = [
  'en_transito',
  'en_aduana',
  'en_taller',
  'lista',
  'en_flota',
  'alquilada',
  'en_venta',
  'vendida',
  'recuperada',
];

// HU-7.02 (Sprint 3, hasta la flota): por VIN, el costo (compra, importación, reacondicionamiento),
// el ingreso de alquiler, los costos de la flota y la depreciación del mayor, el resultado
// acumulado, la rentabilidad sobre el costo, los días en flota y la ocupación. Filtros y orden los
// aplica el servidor, que también calcula todo. Diferido (Release 2): resultado de la venta,
// comisión, garantía e intereses del financiamiento.
@Component({
  selector: 'app-rentabilidad-ciclo',
  imports: [ReactiveFormsModule, DatePipe, CifraPipe],
  templateUrl: './rentabilidad-ciclo.html',
})
export class RentabilidadCicloPantalla {
  private readonly servicio = inject(ReportesService);

  protected readonly etiqueta = etiqueta;
  protected readonly estados = ESTADOS;
  protected readonly reporte = signal<ReporteRentabilidadCiclo | null>(null);
  protected readonly error = signal<string | null>(null);

  protected readonly filtros = inject(FormBuilder).nonNullable.group({
    estado: [''],
    marca: [''],
    linea: [''],
    anio_compra: [''],
    proveedor_id: [''],
    orden: ['resultado' as 'resultado' | 'rentabilidad'],
  });

  constructor() {
    this.consultar();
  }

  protected consultar(): void {
    this.error.set(null);
    this.servicio.rentabilidadCiclo(this.filtros.getRawValue()).subscribe({
      next: (reporte) => this.reporte.set(reporte),
      error: (r: HttpErrorResponse) => {
        const detalle = r.error?.detail;
        this.error.set(
          typeof detalle === 'string' ? detalle : 'No se pudo consultar la rentabilidad',
        );
      },
    });
  }
}
