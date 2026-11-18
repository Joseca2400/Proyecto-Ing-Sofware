import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { Orden, TallerService } from './taller.service';

const VIN = /^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/;

// HU-5.01 (Sprint 2, versión delgada): órdenes de reacondicionamiento ligadas a un VIN. Abrir una
// pasa la unidad a "en taller"; la lista muestra la antigüedad y el costo acumulado (HU-5.07,
// criterio 5, de las abiertas). Diferido: postventa (comprador y venta), contrato de alquiler y
// los demás tipos de trabajo (Sprints 5 y 6).
@Component({
  selector: 'app-ordenes-taller',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './ordenes.html',
  styleUrl: './ordenes.css',
})
export class OrdenesTallerPantalla {
  private readonly servicio = inject(TallerService);

  protected readonly ordenes = signal<Orden[]>([]);
  protected readonly seleccionada = signal<Orden | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    vin: ['', [Validators.required, Validators.pattern(VIN)]],
    fecha_apertura: [new Date().toLocaleDateString('en-CA'), Validators.required],
    kilometraje: [0, [Validators.required, Validators.min(0)]],
    descripcion: ['', Validators.required],
    responsable: ['', Validators.required],
  });

  constructor() {
    this.cargar();
  }

  protected cargar(): void {
    this.servicio.ordenes().subscribe({
      next: (lista) => this.ordenes.set(lista),
      error: () => this.error.set('No se pudo consultar las órdenes'),
    });
  }

  protected abrirDetalle(orden: Orden): void {
    this.seleccionada.set(orden);
  }

  protected abrir(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    const valores = this.formulario.getRawValue();
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio
      .abrirOrden({
        vin: valores.vin.trim().toUpperCase(),
        tipo: 'reacondicionamiento',
        fecha_apertura: valores.fecha_apertura,
        kilometraje: Number(valores.kilometraje),
        descripcion: valores.descripcion.trim(),
        responsable: valores.responsable.trim(),
      })
      .subscribe({
        next: (orden) => {
          this.guardando.set(false);
          this.aviso.set(`Orden ${orden.numero} abierta: la unidad pasó a «en taller»`);
          this.formulario.reset({ fecha_apertura: valores.fecha_apertura });
          this.seleccionada.set(orden);
          this.cargar();
        },
        error: (respuesta: HttpErrorResponse) => this.fallo(respuesta, 'No se pudo abrir la orden'),
      });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    this.guardando.set(false);
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
