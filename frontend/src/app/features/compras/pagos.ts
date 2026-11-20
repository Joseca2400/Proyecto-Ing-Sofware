import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { AuthService } from '../../core/auth/auth.service';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { ComprasService, CuentaBancaria, PagoProgramado, PagoProveedor } from './compras.service';

type FormaPago = 'cheque' | 'transferencia';

const REGISTRAN = ['auxiliar_contable', 'contador'];
const ANULAN = ['contador', 'gerente_financiero'];

function hoy(): string {
  return new Date().toLocaleDateString('en-CA'); // AAAA-MM-DD en la zona del navegador
}

// HU-4.14 (Sprint 3): el área contable ejecuta pagos aprobados (HU-4.13) de un proveedor desde
// la cuenta bancaria aprobada, por cheque o transferencia; cada uno cancela su documento total o
// parcialmente, aun en otra moneda. El servidor aplica el tipo de cambio, calcula el diferencial
// cambiario y genera la partida. El comprobante se imprime desde aquí; anular un pago reabre los
// documentos y revierte su partida. Diferido: imprimir el cheque.
@Component({
  selector: 'app-pagos',
  imports: [MontoPipe, DatePipe],
  templateUrl: './pagos.html',
  styleUrl: './pagos.css',
})
export class PagosPantalla {
  private readonly servicio = inject(ComprasService);
  private readonly auth = inject(AuthService);

  protected readonly porEjecutar = signal<PagoProgramado[]>([]);
  protected readonly elegidos = signal<number[]>([]);
  protected readonly bancos = signal<CuentaBancaria[]>([]);
  protected readonly pagos = signal<PagoProveedor[]>([]);
  protected readonly detalleId = signal<number | null>(null);
  protected readonly forma = signal<FormaPago>('cheque');
  protected readonly referencia = signal('');
  protected readonly fecha = signal(hoy());
  protected readonly fechaAnulacion = signal(hoy());
  protected readonly motivo = signal('');
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly puedeRegistrar = computed(() => this.auth.tieneRol(REGISTRAN));
  protected readonly puedeAnular = computed(() => this.auth.tieneRol(ANULAN));
  protected readonly seleccion = computed(() =>
    this.porEjecutar().filter((p) => this.elegidos().includes(p.id)),
  );
  /** La cuenta bancaria del pago es la que se aprobó para los pagos elegidos. */
  protected readonly banco = computed(() => {
    const primero = this.seleccion()[0];
    return this.bancos().find((b) => b.id === primero?.cuenta_bancaria_id) ?? null;
  });
  protected readonly detalle = computed(
    () => this.pagos().find((p) => p.id === this.detalleId()) ?? null,
  );

  constructor() {
    this.servicio.cuentasBancarias().subscribe({
      next: (lista) => this.bancos.set(lista),
      error: () => this.error.set('No se pudo consultar las cuentas bancarias'),
    });
    this.cargar();
  }

  private cargar(): void {
    this.servicio.pagosPorEjecutar().subscribe({
      next: (lista) => {
        this.porEjecutar.set(lista);
        this.elegidos.update((ids) => ids.filter((id) => lista.some((p) => p.id === id)));
      },
      error: () => this.error.set('No se pudo consultar los pagos aprobados'),
    });
    this.servicio.pagos().subscribe({
      next: (lista) => this.pagos.set(lista),
      error: () => this.error.set('No se pudo consultar los pagos registrados'),
    });
  }

  /** Solo se combinan pagos del mismo proveedor y cuenta bancaria; el servidor lo vuelve a revisar. */
  protected combinable(pago: PagoProgramado): boolean {
    const primero = this.seleccion()[0];
    return (
      !primero ||
      (primero.proveedor_id === pago.proveedor_id &&
        primero.cuenta_bancaria_id === pago.cuenta_bancaria_id)
    );
  }

  protected alternar(pago: PagoProgramado, elegido: boolean): void {
    this.elegidos.update((ids) =>
      elegido ? [...ids, pago.id] : ids.filter((id) => id !== pago.id),
    );
    this.sugerirCheque();
  }

  protected cambiarForma(forma: FormaPago): void {
    this.forma.set(forma);
    this.referencia.set('');
    this.sugerirCheque();
  }

  /** Con cheque, propone el siguiente número de la chequera de la cuenta (HU-1.08). */
  private sugerirCheque(): void {
    const siguiente = this.banco()?.siguiente_cheque;
    if (this.forma() === 'cheque' && !this.referencia() && siguiente) {
      this.referencia.set(String(siguiente));
    }
  }

  protected registrar(): void {
    const banco = this.banco();
    const referencia = this.referencia().trim();
    if (!banco || !this.seleccion().length) {
      this.error.set('Elige al menos un pago aprobado');
      return;
    }
    if (!referencia) {
      this.error.set(
        this.forma() === 'cheque'
          ? 'Escribe el número de cheque'
          : 'Escribe la referencia de la transferencia',
      );
      return;
    }
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio
      .registrarPago({
        cuenta_bancaria_id: banco.id,
        forma_pago: this.forma(),
        referencia,
        fecha: this.fecha(),
        pagos_programados: this.elegidos(),
      })
      .subscribe({
        next: (pago) => {
          this.guardando.set(false);
          this.elegidos.set([]);
          this.referencia.set('');
          this.aviso.set(`Pago ${pago.id} registrado con la partida No. ${pago.partida_numero}`);
          this.detalleId.set(pago.id);
          this.cargar();
        },
        error: (respuesta: HttpErrorResponse) =>
          this.fallo(respuesta, 'No se pudo registrar el pago'),
      });
  }

  protected ver(id: number): void {
    this.detalleId.set(id);
    this.motivo.set('');
  }

  protected imprimir(): void {
    window.print();
  }

  protected anular(pago: PagoProveedor): void {
    const motivo = this.motivo().trim();
    if (!motivo) {
      this.error.set('Escribe el motivo de la anulación');
      return;
    }
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.anularPago(pago.id, { fecha: this.fechaAnulacion(), motivo }).subscribe({
      next: (anulado) => {
        this.aviso.set(
          `Pago ${anulado.id} anulado; su partida se revirtió con la No. ${anulado.reversion_numero}`,
        );
        this.motivo.set('');
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => this.fallo(respuesta, 'No se pudo anular el pago'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    this.guardando.set(false);
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
