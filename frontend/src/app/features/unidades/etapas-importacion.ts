import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  Etapa,
  EtapasImportacion,
  UnidadEnEtapa,
  UnidadesService,
  etiqueta,
} from './unidades.service';

// HU-4.07 (Sprint 1, versión delgada): el gerente financiero ve las unidades en importación por
// etapa (en tránsito, en aduana, en taller y lista), con los días que lleva cada una en su etapa y
// su costo acumulado, y las hace avanzar a la siguiente con el documento que lo respalda. El orden
// lo valida el servidor; los días, el costo y los totales por etapa también los calcula él.
// Diferido: el paso a "en taller" al abrir la orden de reacondicionamiento (HU-5.01), la DUCA y las
// órdenes cerradas para pasar a "lista" (HU-4.06, HU-5.01) y las métricas (HU-7.04).
@Component({
  selector: 'app-etapas-importacion',
  imports: [ReactiveFormsModule, MontoPipe, DatePipe],
  templateUrl: './etapas-importacion.html',
  styleUrl: './etapas-importacion.css',
})
export class EtapasImportacionPantalla {
  private readonly servicio = inject(UnidadesService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly etiqueta = etiqueta;
  protected readonly datos = signal<EtapasImportacion | null>(null);
  protected readonly filtro = signal<Etapa | null>(null);
  /** VIN de la unidad cuyo avance se está capturando. */
  protected readonly avanzando = signal<string | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly avance = this.fb.group({ documento: ['', Validators.required] });

  constructor() {
    this.cargar();
  }

  /** El resumen de arriba siempre muestra las cuatro etapas; el filtro solo se aplica a la tabla. */
  protected filtrar(etapa: Etapa | null): void {
    this.filtro.set(etapa);
  }

  protected cargar(): void {
    this.servicio.etapasImportacion().subscribe({
      next: (datos) => this.datos.set(datos),
      error: () => this.error.set('No se pudo consultar las unidades en importación'),
    });
  }

  protected unidades(): UnidadEnEtapa[] {
    const filtro = this.filtro();
    const todas = this.datos()?.unidades ?? [];
    return filtro ? todas.filter((u) => u.estado === filtro) : todas;
  }

  protected abrirAvance(unidad: UnidadEnEtapa): void {
    this.avanzando.set(unidad.vin);
    this.avance.reset();
    this.error.set(null);
    this.aviso.set(null);
  }

  protected cancelarAvance(): void {
    this.avanzando.set(null);
  }

  protected avanzar(unidad: UnidadEnEtapa): void {
    const siguiente = unidad.siguiente_etapa;
    if (!siguiente) return;
    if (this.avance.invalid) {
      this.avance.markAllAsTouched();
      return;
    }
    const documento = this.avance.controls.documento.value.trim();
    this.guardando.set(true);
    this.error.set(null);
    this.servicio.cambiarEstado(unidad.vin, siguiente, documento).subscribe({
      next: (actualizada) => {
        this.guardando.set(false);
        this.avanzando.set(null);
        this.aviso.set(`La unidad ${actualizada.vin} pasó a ${etiqueta(actualizada.estado)}.`);
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo cambiar la etapa');
      },
    });
  }
}
