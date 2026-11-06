import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  ComprasService,
  FacturaCompra,
  FacturaCompraEntrada,
  LINEAS_NEGOCIO,
  LineaNegocio,
  Proveedor,
  REGIMENES,
  RegimenProveedor,
} from './compras.service';

// Monto como texto: número positivo con hasta 6 decimales. El front no suma ni redondea:
// los totales, el crédito fiscal y la cuenta por pagar los calcula el servidor.
const MONTO = /^\s*\d+(\.\d{1,6})?\s*$/;
const AUTORIZACION =
  /^\s*[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\s*$/;
const VIN = /^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/;

// HU-4.09 (Sprint 1): captura del DTE recibido de un proveedor local, con su cuenta por pagar.
// Aquí solo se revisa la forma. El servidor valida la línea de negocio contra configuración
// (HU-1.04), el dígito verificador del VIN y que la unidad exista (HU-1.05); la cuenta, hasta que
// se conecte el catálogo (HU-1.02), solo en su forma.
// Diferido: importar el XML del DTE y el libro de compras.
@Component({
  selector: 'app-facturas-compras',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './facturas.html',
  styleUrl: './facturas.css',
})
export class FacturasComprasPantalla {
  private readonly servicio = inject(ComprasService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly lineasNegocio = LINEAS_NEGOCIO;
  protected readonly proveedores = signal<Proveedor[]>([]);
  protected readonly facturas = signal<FacturaCompra[]>([]);
  protected readonly registrada = signal<FacturaCompra | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    proveedor_id: [0, Validators.min(1)],
    serie: ['', [Validators.required, Validators.pattern(/^\s*[A-Za-z0-9]{1,20}\s*$/)]],
    numero: ['', [Validators.required, Validators.pattern(/^\s*\d{1,20}\s*$/)]],
    autorizacion: ['', [Validators.required, Validators.pattern(AUTORIZACION)]],
    fecha: ['', Validators.required],
    lineas: this.fb.array([this.nuevaLinea()]),
  });

  protected readonly filtroProveedor = this.fb.control(0);

  constructor() {
    this.servicio.proveedores({ tipo: 'local' }).subscribe({
      next: (lista) => this.proveedores.set(lista),
      error: () => this.error.set('No se pudo consultar los proveedores'),
    });
    this.cargar();
    this.filtroProveedor.valueChanges.pipe(takeUntilDestroyed()).subscribe(() => this.cargar());
  }

  protected get lineas() {
    return this.formulario.controls.lineas;
  }

  protected etiquetaRegimen(valor: RegimenProveedor | null): string {
    return REGIMENES.find((r) => r.valor === valor)?.etiqueta ?? '';
  }

  protected etiquetaLinea(valor: LineaNegocio): string {
    return this.lineasNegocio.find((l) => l.valor === valor)?.etiqueta ?? valor;
  }

  protected agregarLinea(): void {
    this.lineas.push(this.nuevaLinea());
  }

  protected quitarLinea(indice: number): void {
    if (this.lineas.length > 1) {
      this.lineas.removeAt(indice);
    }
  }

  protected cargar(): void {
    this.servicio.facturas(this.filtroProveedor.value || undefined).subscribe({
      next: (lista) => this.facturas.set(lista),
      error: () => this.error.set('No se pudo consultar las facturas'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.error.set('Revisa los campos marcados');
      return;
    }

    const valores = this.formulario.getRawValue();
    const entrada: FacturaCompraEntrada = {
      proveedor_id: Number(valores.proveedor_id),
      serie: valores.serie.trim().toUpperCase(),
      numero: valores.numero.trim(),
      autorizacion: valores.autorizacion.trim().toUpperCase(),
      fecha: valores.fecha,
      lineas: valores.lineas.map((linea) => ({
        descripcion: linea.descripcion.trim(),
        cuenta: linea.cuenta.trim(),
        linea_negocio: linea.linea_negocio,
        ...(linea.vin.trim() ? { vin: linea.vin.trim().toUpperCase() } : {}),
        base: linea.base.trim(),
        iva: linea.iva.trim() || '0',
      })),
    };

    this.guardando.set(true);
    this.error.set(null);
    this.registrada.set(null);
    this.servicio.registrarFactura(entrada).subscribe({
      next: (factura) => {
        this.guardando.set(false);
        this.registrada.set(factura);
        // Queda una sola línea, vacía, para la siguiente factura del mismo proveedor.
        while (this.lineas.length > 1) this.lineas.removeAt(1);
        this.formulario.reset({ proveedor_id: valores.proveedor_id });
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo registrar la factura');
      },
    });
  }

  private nuevaLinea() {
    return this.fb.group({
      descripcion: ['', Validators.required],
      cuenta: ['', [Validators.required, Validators.pattern(/^\s*\d+([.-]\d+)*\s*$/)]],
      linea_negocio: ['taller' as LineaNegocio],
      vin: ['', Validators.pattern(VIN)],
      base: ['', [Validators.required, Validators.pattern(MONTO)]],
      iva: ['', Validators.pattern(MONTO)],
    });
  }
}
