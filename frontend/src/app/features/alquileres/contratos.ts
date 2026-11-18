import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  AlquileresService,
  ClienteAlquiler,
  Contrato,
  ContratoEntrada,
  ETIQUETAS_MODALIDAD,
  Modalidad,
  UnidadAlquiler,
} from './alquileres.service';

/** Valor inicial de un `datetime-local`: ahora, en la hora local. */
function ahoraLocal(): string {
  const ahora = new Date();
  return new Date(ahora.getTime() - ahora.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

// HU-3.06 (Sprint 2): contrato de alquiler. El servidor toma y copia la tarifa vigente, valida la
// disponibilidad, pasa la unidad a "alquilada" y calcula el monto estimado; aquí solo se muestra.
@Component({
  selector: 'app-contratos',
  imports: [ReactiveFormsModule, MontoPipe, DatePipe],
  templateUrl: './contratos.html',
})
export class ContratosPantalla {
  private readonly servicio = inject(AlquileresService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly etiquetas = ETIQUETAS_MODALIDAD;
  protected readonly modalidades = Object.keys(ETIQUETAS_MODALIDAD) as Modalidad[];
  protected readonly contratos = signal<Contrato[]>([]);
  protected readonly clientes = signal<ClienteAlquiler[]>([]);
  protected readonly unidades = signal<UnidadAlquiler[]>([]);
  protected readonly seleccionado = signal<Contrato | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    cliente_id: [0, Validators.min(1)],
    vin: ['', Validators.required],
    salida: [ahoraLocal(), Validators.required],
    devolucion_prevista: ['', Validators.required],
    modalidad: ['diaria' as Modalidad],
    moneda: ['GTQ' as 'GTQ' | 'USD'],
    km_salida: [0, [Validators.required, Validators.min(0)]],
    combustible_salida: [8, [Validators.required, Validators.min(0), Validators.max(8)]],
    deposito_esperado: ['0', [Validators.required, Validators.pattern(/^\d+(\.\d{1,6})?$/)]],
  });

  constructor() {
    this.servicio.clientes().subscribe((lista) => this.clientes.set(lista));
    this.cargar();
  }

  protected cargar(): void {
    this.servicio.unidadesEnFlota().subscribe((lista) => this.unidades.set(lista));
    this.servicio.contratos().subscribe({
      next: (lista) => this.contratos.set(lista),
      error: () => this.error.set('No se pudieron consultar los contratos'),
    });
  }

  protected nombreCliente(id: number): string {
    return this.clientes().find((c) => c.id === id)?.nombre ?? `Cliente ${id}`;
  }

  protected ver(contrato: Contrato): void {
    this.seleccionado.set(contrato);
  }

  protected imprimir(): void {
    window.print();
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.error.set('Complete cliente, unidad, fechas, kilometraje y combustible');
      return;
    }
    const v = this.formulario.getRawValue();
    const entrada: ContratoEntrada = {
      ...v,
      cliente_id: Number(v.cliente_id),
      km_salida: Number(v.km_salida),
      combustible_salida: Number(v.combustible_salida),
      salida: new Date(v.salida).toISOString(),
    };

    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.registrarContrato(entrada).subscribe({
      next: (contrato) => {
        this.guardando.set(false);
        this.aviso.set(`Contrato ${contrato.numero} registrado; la unidad quedó alquilada`);
        this.seleccionado.set(contrato);
        this.formulario.patchValue({ vin: '', devolucion_prevista: '' });
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo registrar el contrato');
      },
    });
  }
}
