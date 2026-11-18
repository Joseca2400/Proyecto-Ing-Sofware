import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  AlquileresService,
  ClienteAlquiler,
  Contrato,
  ContratoEntrada,
  CuentaBancaria,
  Deposito,
  DepositoEntrada,
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
// HU-3.08: cierre con la devolución (el cálculo es del servidor). HU-3.07: recibir, aplicar y
// devolver depósitos en garantía desde el detalle. Diferido: cargos adicionales (HU-3.09).
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

  // HU-3.08: devolución; el servidor calcula días, km excedentes, combustible faltante y monto final.
  protected readonly cierre = this.fb.group({
    devolucion: [ahoraLocal(), Validators.required],
    km_devolucion: [0, [Validators.required, Validators.min(0)]],
    combustible_devolucion: [8, [Validators.required, Validators.min(0), Validators.max(8)]],
    observaciones_danos: [''],
  });

  // HU-3.07: depósitos del contrato; el servidor genera las partidas y lleva el saldo.
  protected readonly cuentas = signal<CuentaBancaria[]>([]);
  protected readonly depositos = signal<Deposito[]>([]);
  protected readonly deposito = this.fb.group({
    tipo: ['deposito' as DepositoEntrada['tipo']],
    fecha: [new Date().toLocaleDateString('en-CA'), Validators.required],
    moneda: ['GTQ' as 'GTQ' | 'USD'],
    monto: ['', [Validators.required, Validators.pattern(/^\d+(\.\d{1,6})?$/)]],
    cuenta_bancaria_id: [0],
    referencia: [''],
  });
  protected readonly tipoDeposito = toSignal(this.deposito.controls.tipo.valueChanges, {
    initialValue: this.deposito.controls.tipo.value,
  });
  protected readonly monedaDeposito = toSignal(this.deposito.controls.moneda.valueChanges, {
    initialValue: this.deposito.controls.moneda.value,
  });
  protected readonly movimiento = this.fb.group({
    fecha: [new Date().toLocaleDateString('en-CA'), Validators.required],
    monto: ['', [Validators.required, Validators.pattern(/^\d+(\.\d{1,6})?$/)]],
    cuenta_bancaria_id: [0],
  });

  constructor() {
    this.servicio.clientes().subscribe((lista) => this.clientes.set(lista));
    this.servicio.cuentasBancarias().subscribe((lista) => this.cuentas.set(lista));
    this.cargar();
  }

  protected cuentasEn(moneda: string): CuentaBancaria[] {
    return this.cuentas().filter((c) => c.moneda === moneda);
  }

  private fallo(porDefecto: string) {
    return (respuesta: HttpErrorResponse) => {
      const detalle = respuesta.error?.detail;
      this.error.set(typeof detalle === 'string' ? detalle : porDefecto);
    };
  }

  protected facturar(contrato: Contrato): void {
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.facturarContrato(contrato.id).subscribe({
      next: (factura) => {
        this.guardando.set(false);
        if (factura.estado === 'certificada') {
          this.aviso.set(`Factura ${factura.serie}-${factura.numero} certificada`);
        } else {
          this.error.set(`El certificador rechazó la factura: ${factura.motivo_rechazo ?? ''}`);
        }
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        this.fallo('No se pudo facturar el contrato')(respuesta);
      },
    });
  }

  private cargarDepositos(contrato: Contrato): void {
    this.servicio.depositosDeContrato(contrato.id).subscribe((lista) => this.depositos.set(lista));
  }

  protected recibir(contrato: Contrato): void {
    const v = this.deposito.getRawValue();
    if (this.deposito.invalid) {
      this.deposito.markAllAsTouched();
      return;
    }
    const tarjeta = v.tipo === 'autorizacion_tarjeta';
    this.error.set(null);
    this.servicio
      .recibirDeposito(contrato.id, {
        tipo: v.tipo,
        fecha: v.fecha,
        moneda: v.moneda,
        monto: v.monto,
        cuenta_bancaria_id: tarjeta ? null : Number(v.cuenta_bancaria_id) || null,
        referencia: v.referencia.trim() || null,
      })
      .subscribe({
        next: () => {
          this.aviso.set(tarjeta ? 'Autorización registrada como referencia' : 'Depósito recibido');
          this.deposito.patchValue({ monto: '', referencia: '' });
          this.cargarDepositos(contrato);
        },
        error: this.fallo('No se pudo registrar el depósito'),
      });
  }

  protected mover(contrato: Contrato, deposito: Deposito, accion: 'aplicar' | 'devolver'): void {
    const v = this.movimiento.getRawValue();
    if (this.movimiento.invalid) {
      this.movimiento.markAllAsTouched();
      return;
    }
    this.error.set(null);
    const peticion =
      accion === 'aplicar'
        ? this.servicio.aplicarDeposito(deposito.id, { fecha: v.fecha, monto: v.monto })
        : this.servicio.devolverDeposito(deposito.id, {
            fecha: v.fecha,
            monto: v.monto,
            cuenta_bancaria_id: Number(v.cuenta_bancaria_id),
          });
    peticion.subscribe({
      next: () => {
        this.aviso.set(
          accion === 'aplicar' ? 'Depósito aplicado a los cargos' : 'Depósito devuelto',
        );
        this.movimiento.patchValue({ monto: '' });
        this.cargarDepositos(contrato);
      },
      error: this.fallo('No se pudo registrar el movimiento del depósito'),
    });
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
    this.cierre.patchValue({ km_devolucion: contrato.km_salida });
    this.deposito.patchValue({ moneda: contrato.moneda });
    this.cargarDepositos(contrato);
  }

  protected cerrar(contrato: Contrato): void {
    if (this.cierre.invalid) {
      this.cierre.markAllAsTouched();
      return;
    }
    const v = this.cierre.getRawValue();
    this.error.set(null);
    this.aviso.set(null);
    this.servicio
      .cerrarContrato(contrato.id, {
        devolucion: new Date(v.devolucion).toISOString(),
        km_devolucion: Number(v.km_devolucion),
        combustible_devolucion: Number(v.combustible_devolucion),
        observaciones_danos: v.observaciones_danos.trim() || null,
      })
      .subscribe({
        next: (cerrado) => {
          this.aviso.set(`Contrato ${cerrado.numero} cerrado; la unidad volvió a la flota`);
          this.seleccionado.set(cerrado);
          this.cargar();
        },
        error: this.fallo('No se pudo cerrar el contrato'),
      });
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
        this.ver(contrato);
        this.formulario.patchValue({ vin: '', devolucion_prevista: '' });
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        this.fallo('No se pudo registrar el contrato')(respuesta);
      },
    });
  }
}
