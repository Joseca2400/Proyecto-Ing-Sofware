import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  CambioEstado,
  Catalogos,
  EstadoUnidad,
  Unidad,
  UnidadEntrada,
  UnidadesService,
  etiqueta,
} from './unidades.service';

const VIN = /^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/;
const ESTADOS_FINALES: EstadoUnidad[] = ['vendida', 'recuperada'];

// HU-1.05 (Sprint 1): alta de unidades por VIN con su ficha mínima, estado vigente e historial.
// Aquí solo se revisa la forma del VIN; el dígito verificador y la unicidad los valida el servidor.
// Diferido: placa, número de motor, expediente y movimientos contables ligados al VIN.
@Component({
  selector: 'app-unidades',
  imports: [ReactiveFormsModule, DatePipe],
  templateUrl: './unidades.html',
  styleUrl: './unidades.css',
})
export class UnidadesPantalla {
  private readonly servicio = inject(UnidadesService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly etiqueta = etiqueta;
  protected readonly catalogos = signal<Catalogos>({
    estados: [],
    tipos_vehiculo: [],
    lineas_negocio: [],
  });
  protected readonly unidades = signal<Unidad[]>([]);
  protected readonly seleccionada = signal<Unidad | null>(null);
  protected readonly historial = signal<CambioEstado[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    vin: ['', [Validators.required, Validators.pattern(VIN)]],
    marca: ['', Validators.required],
    linea: ['', Validators.required],
    modelo: [new Date().getFullYear(), [Validators.required, Validators.min(1981)]],
    color: ['', Validators.required],
    tipo_vehiculo: ['sedan'],
    linea_negocio: [''],
    estado: ['en_transito' as EstadoUnidad],
    documento: [''],
  });

  protected readonly filtro = this.fb.group({
    buscar: [''],
    estado: ['' as EstadoUnidad | ''],
  });

  protected readonly cambio = this.fb.group({
    estado: ['' as EstadoUnidad | '', Validators.required],
    documento: ['', Validators.required],
  });

  constructor() {
    this.servicio.catalogos().subscribe({
      next: (catalogos) => this.catalogos.set(catalogos),
      error: () => this.error.set('No se pudo consultar los catálogos de unidades'),
    });
    this.cargar();
  }

  /** Estados con los que se puede dar de alta una unidad (no vendida ni recuperada). */
  protected estadosIniciales(): EstadoUnidad[] {
    return this.catalogos().estados.filter((e) => !ESTADOS_FINALES.includes(e));
  }

  protected cargar(): void {
    const { buscar, estado } = this.filtro.getRawValue();
    this.servicio
      .unidades({ buscar: buscar.trim() || undefined, estado: estado || undefined })
      .subscribe({
        next: (lista) => this.unidades.set(lista),
        error: () => this.error.set('No se pudo consultar las unidades'),
      });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    const valores = this.formulario.getRawValue();
    const entrada: UnidadEntrada = {
      vin: valores.vin.trim().toUpperCase(),
      marca: valores.marca.trim(),
      linea: valores.linea.trim(),
      modelo: valores.modelo,
      color: valores.color.trim(),
      tipo_vehiculo: valores.tipo_vehiculo,
      linea_negocio: valores.linea_negocio || undefined,
      estado: valores.estado,
      documento: valores.documento.trim() || undefined,
    };

    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.registrar(entrada).subscribe({
      next: (unidad) => {
        this.guardando.set(false);
        this.aviso.set(`Unidad ${unidad.vin} registrada`);
        this.formulario.reset();
        this.cargar();
        this.ver(unidad);
      },
      error: (respuesta: HttpErrorResponse) =>
        this.fallo(respuesta, 'No se pudo registrar la unidad'),
    });
  }

  protected ver(unidad: Unidad): void {
    this.seleccionada.set(unidad);
    this.cambio.reset();
    this.historial.set([]);
    this.servicio.historial(unidad.vin).subscribe({
      next: (cambios) => this.historial.set(cambios),
      error: () => this.error.set('No se pudo consultar el historial de la unidad'),
    });
  }

  protected cambiarEstado(): void {
    const unidad = this.seleccionada();
    const { estado, documento } = this.cambio.getRawValue();
    if (!unidad || this.cambio.invalid || !estado || !documento.trim()) {
      this.cambio.markAllAsTouched();
      return;
    }
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.cambiarEstado(unidad.vin, estado, documento.trim()).subscribe({
      next: (actualizada) => {
        this.guardando.set(false);
        this.aviso.set(`La unidad ${actualizada.vin} pasó a ${etiqueta(actualizada.estado)}`);
        this.cargar();
        this.ver(actualizada);
      },
      error: (respuesta: HttpErrorResponse) =>
        this.fallo(respuesta, 'No se pudo cambiar el estado'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    this.guardando.set(false);
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
