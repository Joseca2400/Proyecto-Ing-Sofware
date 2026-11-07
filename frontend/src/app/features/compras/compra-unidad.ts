import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { Catalogos, UnidadesService, etiqueta } from '../unidades/unidades.service';
import { ComprasService, CompraUnidad, CompraUnidadEntrada, Proveedor } from './compras.service';

// Montos como texto: número con hasta 6 decimales. El front no suma ni convierte: el total en
// USD, el equivalente en quetzales, la cuenta por pagar y la partida los calcula el servidor.
const MONTO = /^\s*\d+(\.\d{1,6})?\s*$/;
const VIN = /^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/;

// HU-4.02 (Sprint 1): compra de una unidad en EE. UU. a un proveedor del exterior, en USD. En una
// sola transacción el servidor crea la unidad en tránsito, registra la compra con el tipo de
// cambio de la fecha, abre la cuenta por pagar en USD y genera la partida contable; si algo falla
// (VIN repetido, sin tipo de cambio, partida rechazada) no se crea nada.
// Diferido: adjuntar la factura, el título y el bill of sale.
@Component({
  selector: 'app-compra-unidad',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './compra-unidad.html',
  styleUrl: './compra-unidad.css',
})
export class CompraUnidadPantalla {
  private readonly servicio = inject(ComprasService);
  private readonly unidades = inject(UnidadesService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly etiqueta = etiqueta;
  protected readonly catalogos = signal<Catalogos>({
    estados: [],
    tipos_vehiculo: [],
    lineas_negocio: [],
  });
  protected readonly proveedores = signal<Proveedor[]>([]);
  protected readonly compras = signal<CompraUnidad[]>([]);
  protected readonly registrada = signal<CompraUnidad | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    proveedor_id: [0, Validators.min(1)],
    fecha: ['', Validators.required],
    documento: ['', Validators.required],
    vin: ['', [Validators.required, Validators.pattern(VIN)]],
    marca: ['', Validators.required],
    linea: ['', Validators.required],
    modelo: [new Date().getFullYear(), [Validators.required, Validators.min(1981)]],
    color: ['', Validators.required],
    tipo_vehiculo: ['sedan'],
    linea_negocio: [''],
    precio_usd: ['', [Validators.required, Validators.pattern(MONTO)]],
    comision_usd: ['', Validators.pattern(MONTO)],
    documentacion_usd: ['', Validators.pattern(MONTO)],
    arrastre_usd: ['', Validators.pattern(MONTO)],
  });

  constructor() {
    this.unidades.catalogos().subscribe({
      next: (catalogos) => this.catalogos.set(catalogos),
      error: () => this.error.set('No se pudo consultar los catálogos de unidades'),
    });
    this.servicio.proveedores({ tipo: 'exterior' }).subscribe({
      next: (lista) => this.proveedores.set(lista),
      error: () => this.error.set('No se pudo consultar los proveedores'),
    });
    this.cargar();
  }

  protected cargar(): void {
    this.servicio.comprasUnidad().subscribe({
      next: (lista) => this.compras.set(lista),
      error: () => this.error.set('No se pudo consultar las compras'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.error.set('Revisa los campos marcados');
      return;
    }
    const v = this.formulario.getRawValue();
    const cargo = (texto: string) => texto.trim() || '0';
    const entrada: CompraUnidadEntrada = {
      proveedor_id: Number(v.proveedor_id),
      fecha: v.fecha,
      documento: v.documento.trim(),
      vin: v.vin.trim().toUpperCase(),
      marca: v.marca.trim(),
      linea: v.linea.trim(),
      modelo: v.modelo,
      color: v.color.trim(),
      tipo_vehiculo: v.tipo_vehiculo,
      ...(v.linea_negocio ? { linea_negocio: v.linea_negocio } : {}),
      precio_usd: v.precio_usd.trim(),
      comision_usd: cargo(v.comision_usd),
      documentacion_usd: cargo(v.documentacion_usd),
      arrastre_usd: cargo(v.arrastre_usd),
    };

    this.guardando.set(true);
    this.error.set(null);
    this.registrada.set(null);
    this.servicio.registrarCompraUnidad(entrada).subscribe({
      next: (compra) => {
        this.guardando.set(false);
        this.registrada.set(compra);
        // Se conservan el proveedor y la fecha para la siguiente unidad del mismo lote.
        this.formulario.reset({ proveedor_id: v.proveedor_id, fecha: v.fecha });
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo registrar la compra');
      },
    });
  }
}
