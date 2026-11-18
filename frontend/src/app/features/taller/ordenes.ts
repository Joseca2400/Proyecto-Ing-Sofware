import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { Hora, Orden, TallerService } from './taller.service';

const VIN = /^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/;

// HU-5.01 (Sprint 2, versión delgada): órdenes de reacondicionamiento ligadas a un VIN. Abrir una
// pasa la unidad a "en taller"; la lista muestra la antigüedad y el costo acumulado (HU-5.07,
// criterio 5, de las abiertas). Diferido: postventa (comprador y venta), contrato de alquiler y
// los demás tipos de trabajo (Sprints 5 y 6). HU-5.03: en el detalle se registran las horas, que el
// servidor costea con la tarifa vigente en su fecha.
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
  protected readonly horas = signal<Hora[]>([]);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    vin: ['', [Validators.required, Validators.pattern(VIN)]],
    fecha_apertura: [new Date().toLocaleDateString('en-CA'), Validators.required],
    kilometraje: [0, [Validators.required, Validators.min(0)]],
    descripcion: ['', Validators.required],
    responsable: ['', Validators.required],
  });

  protected readonly formularioHoras = inject(FormBuilder).nonNullable.group({
    mecanico: ['', Validators.required],
    fecha: [new Date().toLocaleDateString('en-CA'), Validators.required],
    horas: ['', [Validators.required, Validators.pattern(/^\s*\d+(\.\d{1,2})?\s*$/)]],
    tarea: ['', Validators.required],
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
    this.horas.set([]);
    this.servicio.horas(orden.id).subscribe({
      next: (lista) => this.horas.set(lista),
      error: () => this.error.set('No se pudo consultar las horas de la orden'),
    });
  }

  protected registrarHoras(orden: Orden): void {
    if (this.formularioHoras.invalid) {
      this.formularioHoras.markAllAsTouched();
      return;
    }
    const valores = this.formularioHoras.getRawValue();
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio
      .registrarHoras(orden.id, {
        mecanico: valores.mecanico.trim(),
        fecha: valores.fecha,
        horas: valores.horas.trim(),
        tarea: valores.tarea.trim(),
      })
      .subscribe({
        next: () => {
          this.guardando.set(false);
          this.formularioHoras.reset({ mecanico: valores.mecanico, fecha: valores.fecha });
          this.recargar(orden.id);
        },
        error: (respuesta: HttpErrorResponse) =>
          this.fallo(respuesta, 'No se pudieron registrar las horas'),
      });
  }

  /** Vuelve a pedir la orden (su costo acumulado cambió) y sus horas. */
  private recargar(id: number): void {
    this.servicio.orden(id).subscribe({
      next: (orden) => {
        this.abrirDetalle(orden);
        this.cargar();
      },
      error: () => this.error.set('No se pudo consultar la orden'),
    });
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
