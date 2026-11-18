import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Moneda, MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  Cliente,
  FacturacionService,
  Factura,
  FacturaEntrada,
  LINEAS_FACTURA,
} from './facturacion.service';

// Cantidad y precio como texto: número positivo con hasta 6 decimales. El front no suma ni
// redondea: base, IVA, totales y equivalente en quetzales los calcula el servidor.
const NUMERO = /^\s*\d+(\.\d{1,6})?\s*$/;
const VIN = /^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/;

// HU-6.02 parte 1 (Sprint 2): emisión de facturas FEL contra el certificador simulado, con su
// estado (certificada o rechazada), los datos de certificación, el XML y el motivo de un rechazo.
// Diferido: PDF certificado (Sprint 3), anulación (HU-6.05) y notas de crédito (HU-6.03).
@Component({
  selector: 'app-facturas',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './facturas.html',
  styleUrl: './facturas.css',
})
export class FacturasPantalla {
  private readonly servicio = inject(FacturacionService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly lineasNegocio = LINEAS_FACTURA;
  protected readonly clientes = signal<Cliente[]>([]);
  protected readonly facturas = signal<Factura[]>([]);
  protected readonly seleccionada = signal<Factura | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    cliente_id: [0], // 0 = Consumidor Final
    fecha: ['', Validators.required],
    moneda: ['GTQ' as Moneda],
    dias_credito: [0, [Validators.min(0), Validators.max(365)]],
    lineas: this.fb.array([this.nuevaLinea()]),
  });

  constructor() {
    this.servicio.clientes().subscribe({
      next: (lista) => this.clientes.set(lista),
      error: () => this.error.set('No se pudo consultar los clientes'),
    });
    this.cargar();
  }

  protected get lineas() {
    return this.formulario.controls.lineas;
  }

  protected moneda(f: Factura): Moneda {
    return f.moneda as Moneda;
  }

  protected agregarLinea(): void {
    this.lineas.push(this.nuevaLinea());
  }

  protected quitarLinea(indice: number): void {
    if (this.lineas.length > 1) this.lineas.removeAt(indice);
  }

  protected cargar(): void {
    this.servicio.facturas().subscribe({
      next: (lista) => this.facturas.set(lista),
      error: () => this.error.set('No se pudo consultar las facturas'),
    });
  }

  protected emitir(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.error.set('Revisa los campos marcados');
      return;
    }
    const v = this.formulario.getRawValue();
    const entrada: FacturaEntrada = {
      cliente_id: v.cliente_id || null,
      fecha: v.fecha,
      moneda: v.moneda,
      dias_credito: Number(v.dias_credito),
      lineas: v.lineas.map((linea) => ({
        descripcion: linea.descripcion.trim(),
        cantidad: linea.cantidad.trim(),
        precio_unitario: linea.precio_unitario.trim(),
        linea_negocio: linea.linea_negocio,
        ...(linea.vin.trim() ? { vin: linea.vin.trim().toUpperCase() } : {}),
      })),
    };

    this.guardando.set(true);
    this.error.set(null);
    this.seleccionada.set(null);
    this.servicio.emitirFactura(entrada).subscribe({
      next: (factura) => {
        this.guardando.set(false);
        this.seleccionada.set(factura);
        if (factura.estado === 'certificada') {
          while (this.lineas.length > 1) this.lineas.removeAt(1);
          this.formulario.reset({ fecha: v.fecha, moneda: v.moneda });
        }
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo emitir la factura');
      },
    });
  }

  private nuevaLinea() {
    return this.fb.group({
      descripcion: ['', Validators.required],
      cantidad: ['1', [Validators.required, Validators.pattern(NUMERO)]],
      precio_unitario: ['', [Validators.required, Validators.pattern(NUMERO)]],
      linea_negocio: ['alquiler'],
      vin: ['', Validators.pattern(VIN)],
    });
  }
}
