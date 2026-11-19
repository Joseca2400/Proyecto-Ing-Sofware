import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { CifraPipe } from './cifra.pipe';
import { etiqueta } from '../unidades/unidades.service';
import {
  ReporteRentabilidadContratos,
  ReporteRentabilidadUnidades,
  ReportesService,
  guardarArchivo,
} from './reportes.service';

const hoy = () => new Date().toLocaleDateString('en-CA');

// HU-3.13 (Sprint 3): rentabilidad por unidad de la flota (en el período elegido) y por contrato
// (con salida en el período), en quetzales y leída del mayor por VIN. El servidor calcula todo,
// también los totales y el CSV; un concepto sin cuenta en su regla llega como pendiente (null).
// Diferido: exportar a Excel (HU-7.09).
@Component({
  selector: 'app-rentabilidad',
  imports: [ReactiveFormsModule, DatePipe, MontoPipe, CifraPipe],
  templateUrl: './rentabilidad.html',
})
export class RentabilidadPantalla {
  private readonly servicio = inject(ReportesService);

  protected readonly etiqueta = etiqueta;
  protected readonly unidades = signal<ReporteRentabilidadUnidades | null>(null);
  protected readonly contratos = signal<ReporteRentabilidadContratos | null>(null);
  protected readonly error = signal<string | null>(null);

  protected readonly filtros = inject(FormBuilder).nonNullable.group({
    desde: [hoy().slice(0, 5) + '01-01'],
    hasta: [hoy()],
    vin: [''],
  });

  constructor() {
    this.consultar();
  }

  protected consultar(): void {
    this.error.set(null);
    const filtros = this.filtros.getRawValue();
    this.servicio.rentabilidadUnidades(filtros).subscribe({
      next: (reporte) => this.unidades.set(reporte),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar la rentabilidad'),
    });
    this.servicio.rentabilidadContratos(filtros).subscribe({
      next: (reporte) => this.contratos.set(reporte),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar la rentabilidad'),
    });
  }

  protected exportar(tipo: 'unidades' | 'contratos'): void {
    const filtros = this.filtros.getRawValue();
    this.servicio.rentabilidadCsv(tipo, filtros).subscribe({
      next: (archivo) =>
        guardarArchivo(archivo, `rentabilidad-${tipo}-${filtros.desde}-${filtros.hasta}.csv`),
      error: () => this.error.set('No se pudo exportar el archivo'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
