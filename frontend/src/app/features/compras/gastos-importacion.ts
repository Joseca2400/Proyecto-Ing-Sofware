import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  ComprasService,
  ConceptoGasto,
  GastoImportacion,
  GastoImportacionEntrada,
  Moneda,
  Proveedor,
  ResumenGastosUnidad,
} from './compras.service';

// Monto como texto: número positivo con hasta 6 decimales. El front no convierte ni suma:
// el equivalente en quetzales, la cuenta por pagar y los totales por VIN los calcula el servidor.
const MONTO = /^\s*\d+(\.\d{1,6})?\s*$/;
const VIN = /^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/;

// HU-4.04 (Sprint 1): gastos de importación ligados a una unidad por su VIN, en GTQ o USD, con su
// cuenta por pagar. El concepto decide la cuenta y si el gasto suma al costo; el IVA de
// importación es crédito fiscal. El servidor valida que la unidad exista y aplica el tipo de
// cambio de la fecha (HU-1.06) a los gastos en dólares.
// Diferido: expediente y prorrateo de gastos compartidos (HU-4.05), DUCA (HU-4.06) y partida.
@Component({
  selector: 'app-gastos-importacion',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './gastos-importacion.html',
  styleUrl: './gastos-importacion.css',
})
export class GastosImportacionPantalla {
  private readonly servicio = inject(ComprasService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly conceptos = signal<ConceptoGasto[]>([]);
  protected readonly proveedores = signal<Proveedor[]>([]);
  protected readonly gastos = signal<GastoImportacion[]>([]);
  protected readonly resumen = signal<ResumenGastosUnidad | null>(null);
  protected readonly registrado = signal<GastoImportacion | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    vin: ['', [Validators.required, Validators.pattern(VIN)]],
    concepto: ['', Validators.required],
    proveedor_id: [0, Validators.min(1)],
    fecha: ['', Validators.required],
    documento: ['', Validators.required],
    descripcion: [''],
    moneda: ['GTQ' as Moneda],
    monto: ['', [Validators.required, Validators.pattern(MONTO)]],
  });

  protected readonly filtro = this.fb.group({ vin: ['', Validators.pattern(VIN)] });

  constructor() {
    this.servicio.conceptosGasto().subscribe({
      next: (lista) => this.conceptos.set(lista),
      error: () => this.error.set('No se pudo consultar los conceptos de gasto'),
    });
    this.servicio.proveedores().subscribe({
      next: (lista) => this.proveedores.set(lista),
      error: () => this.error.set('No se pudo consultar los proveedores'),
    });
    this.cargar();
  }

  /** Concepto elegido en el formulario, para avisar si no suma al costo. */
  protected conceptoElegido(): ConceptoGasto | undefined {
    return this.conceptos().find((c) => c.codigo === this.formulario.controls.concepto.value);
  }

  protected cargar(): void {
    const filtroVin = this.filtro.controls.vin;
    if (filtroVin.invalid) {
      filtroVin.markAsTouched();
      return;
    }
    const vin = filtroVin.value.trim().toUpperCase();
    this.servicio.gastosImportacion(vin ? { vin } : {}).subscribe({
      next: (lista) => this.gastos.set(lista),
      error: () => this.error.set('No se pudo consultar los gastos de importación'),
    });
    this.resumen.set(null);
    if (vin) {
      this.servicio.resumenGastosUnidad(vin).subscribe({
        next: (resumen) => this.resumen.set(resumen),
        error: (respuesta: HttpErrorResponse) =>
          this.fallo(respuesta, 'No se pudo consultar el total de la unidad'),
      });
    }
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.error.set('Revisa los campos marcados');
      return;
    }
    const valores = this.formulario.getRawValue();
    const descripcion = valores.descripcion.trim();
    const entrada: GastoImportacionEntrada = {
      vin: valores.vin.trim().toUpperCase(),
      concepto: valores.concepto,
      proveedor_id: Number(valores.proveedor_id),
      fecha: valores.fecha,
      documento: valores.documento.trim(),
      ...(descripcion ? { descripcion } : {}),
      moneda: valores.moneda,
      monto: valores.monto.trim(),
    };

    this.guardando.set(true);
    this.error.set(null);
    this.registrado.set(null);
    this.servicio.registrarGastoImportacion(entrada).subscribe({
      next: (gasto) => {
        this.guardando.set(false);
        this.registrado.set(gasto);
        // Se conservan la unidad, el proveedor, la fecha y la moneda para el siguiente gasto.
        this.formulario.reset({
          vin: valores.vin,
          proveedor_id: valores.proveedor_id,
          fecha: valores.fecha,
          moneda: valores.moneda,
        });
        this.filtro.setValue({ vin: gasto.vin });
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) =>
        this.fallo(respuesta, 'No se pudo registrar el gasto'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    this.guardando.set(false);
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
