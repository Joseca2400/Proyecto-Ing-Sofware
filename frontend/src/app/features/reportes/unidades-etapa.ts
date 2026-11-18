import { DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { etiqueta } from '../unidades/unidades.service';
import { ReporteUnidadesEtapa, ReportesService } from './reportes.service';

// HU-7.04 (Sprint 2): cuántas unidades hay en cada estado del ciclo y cuánto valen (costo
// acumulado mientras están en proceso, valor en libros ya en la flota), los días promedio en cada
// estado y las que superan el plazo, que se puede cambiar. Al elegir un estado se listan sus
// unidades. Todo lo calcula el servidor. Diferido: exportar a PDF y Excel (HU-7.09).
@Component({
  selector: 'app-unidades-etapa',
  imports: [ReactiveFormsModule, DatePipe, MontoPipe],
  templateUrl: './unidades-etapa.html',
})
export class UnidadesEtapaPantalla {
  private readonly servicio = inject(ReportesService);

  protected readonly etiqueta = etiqueta;
  protected readonly reporte = signal<ReporteUnidadesEtapa | null>(null);
  protected readonly filtro = signal<string | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly unidades = computed(() => {
    const filtro = this.filtro();
    const todas = this.reporte()?.unidades ?? [];
    return filtro ? todas.filter((u) => u.estado === filtro) : todas;
  });

  protected readonly limite = inject(FormBuilder).nonNullable.control<number | null>(null, [
    Validators.min(1),
  ]);

  constructor() {
    this.consultar();
  }

  protected consultar(): void {
    if (this.limite.invalid) return;
    this.error.set(null);
    this.servicio.unidadesPorEtapa(this.limite.value ?? undefined).subscribe({
      next: (reporte) => {
        this.reporte.set(reporte);
        if (this.limite.value === null) this.limite.setValue(reporte.limite_dias);
      },
      error: () => this.error.set('No se pudo consultar el reporte'),
    });
  }
}
