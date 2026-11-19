import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { AuthService } from '../../core/auth/auth.service';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import {
  ComprasService,
  CuentaBancaria,
  CuentaPorPagarPendiente,
  DecisionPagoEntrada,
  Moneda,
  PagoProgramado,
  ProgramacionPago,
} from './compras.service';

const MONTO = /^\d+(\.\d{1,6})?$/;
const PROPONEN = ['auxiliar_contable', 'contador', 'gerente_financiero'];

/** Una cuenta por pagar en la lista para proponer: si se eligió, cuánto y desde qué banco. */
interface FilaPendiente {
  cuenta: CuentaPorPagarPendiente;
  elegida: boolean;
  monto: string;
  banco: number;
}

/** Lo que el gerente escribe antes de decidir un pago propuesto. */
interface Decision {
  monto: string;
  banco: number;
  comentario: string;
}

const ESTADOS: Record<string, string> = {
  propuesto: 'Propuesto',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
  ejecutado: 'Ejecutado',
};

// HU-4.13 (Sprint 3): el área contable propone pagos con las cuentas por pagar vencidas o por
// vencer, cada una con su cuenta bancaria y su monto (parcial si es menor que el saldo); el gerente
// financiero aprueba, modifica o rechaza cada pago. Totales, saldo disponible por banco y la regla
// de que quien propone no aprueba vienen del servidor; el front no suma ni convierte montos.
@Component({
  selector: 'app-programacion-pagos',
  imports: [MontoPipe, DatePipe],
  templateUrl: './programacion-pagos.html',
  styleUrl: './programacion-pagos.css',
})
export class ProgramacionPagosPantalla {
  private readonly servicio = inject(ComprasService);
  private readonly auth = inject(AuthService);

  protected readonly estados = ESTADOS;
  protected readonly filas = signal<FilaPendiente[]>([]);
  protected readonly bancos = signal<CuentaBancaria[]>([]);
  protected readonly programaciones = signal<ProgramacionPago[]>([]);
  protected readonly elegidaId = signal<number | null>(null);
  protected readonly decisiones = signal<Record<number, Decision>>({});
  protected readonly filtroMoneda = signal<Moneda | ''>('');
  protected readonly filtroVence = signal('');
  protected readonly fecha = signal(new Date().toLocaleDateString('en-CA'));
  protected readonly descripcion = signal('');
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly puedeProponer = computed(() => this.auth.tieneRol(PROPONEN));
  protected readonly elegidas = computed(() => this.filas().filter((f) => f.elegida));
  protected readonly programacion = computed(
    () => this.programaciones().find((p) => p.id === this.elegidaId()) ?? null,
  );

  constructor() {
    this.servicio.cuentasBancarias().subscribe({
      next: (lista) => this.bancos.set(lista),
      error: () => this.error.set('No se pudo consultar las cuentas bancarias'),
    });
    this.cargarPendientes();
    this.cargarProgramaciones();
  }

  protected cargarPendientes(): void {
    const moneda = this.filtroMoneda();
    const vence = this.filtroVence();
    this.servicio
      .cuentasPorPagar({ ...(moneda ? { moneda } : {}), ...(vence ? { vence_hasta: vence } : {}) })
      .subscribe({
        next: (lista) =>
          this.filas.set(
            lista.map((cuenta) => ({
              cuenta,
              elegida: false,
              monto: Number(cuenta.saldo).toFixed(2),
              banco: this.bancoSugerido(cuenta.moneda),
            })),
          ),
        error: () => this.error.set('No se pudo consultar las cuentas por pagar'),
      });
  }

  private cargarProgramaciones(elegir?: number): void {
    this.servicio.programaciones().subscribe({
      next: (lista) => {
        this.programaciones.set(lista);
        this.elegir(elegir ?? this.elegidaId() ?? lista[0]?.id ?? null);
      },
      error: () => this.error.set('No se pudo consultar las programaciones de pago'),
    });
  }

  /** Primera cuenta bancaria en la moneda del documento, o la primera que haya. */
  private bancoSugerido(moneda: string): number {
    const bancos = this.bancos();
    return (bancos.find((b) => b.moneda === moneda) ?? bancos[0])?.id ?? 0;
  }

  protected etiquetaBanco(banco: CuentaBancaria): string {
    return `${banco.banco} ${banco.numero} (${banco.moneda})`;
  }

  protected cambiarFila(id: number, cambios: Partial<FilaPendiente>): void {
    this.filas.update((filas) =>
      filas.map((f) =>
        f.cuenta.id === id
          ? {
              ...f,
              ...cambios,
              banco: cambios.banco ?? (f.banco || this.bancoSugerido(f.cuenta.moneda)),
            }
          : f,
      ),
    );
  }

  protected proponer(): void {
    const elegidas = this.elegidas();
    if (!elegidas.length) {
      this.error.set('Elige al menos una cuenta por pagar');
      return;
    }
    const invalida = elegidas.find((f) => !MONTO.test(f.monto.trim()) || !f.banco);
    if (invalida) {
      this.error.set(`Revisa el monto y la cuenta bancaria de ${invalida.cuenta.documento}`);
      return;
    }
    const descripcion = this.descripcion().trim();
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio
      .proponerPagos({
        fecha: this.fecha(),
        ...(descripcion ? { descripcion } : {}),
        pagos: elegidas.map((f) => ({
          cuenta_por_pagar_id: f.cuenta.id,
          cuenta_bancaria_id: f.banco,
          monto: f.monto.trim(),
        })),
      })
      .subscribe({
        next: (programacion) => {
          this.guardando.set(false);
          this.aviso.set(
            `Programación ${programacion.id} propuesta; la revisa el gerente financiero`,
          );
          this.descripcion.set('');
          this.cargarPendientes();
          this.cargarProgramaciones(programacion.id);
        },
        error: (respuesta: HttpErrorResponse) => this.fallo(respuesta, 'No se pudo proponer'),
      });
  }

  protected elegir(id: number | null): void {
    this.elegidaId.set(id);
    const programacion = this.programaciones().find((p) => p.id === id);
    const decisiones: Record<number, Decision> = {};
    for (const pago of programacion?.pagos ?? []) {
      decisiones[pago.id] = {
        monto: Number(pago.monto).toFixed(2),
        banco: pago.cuenta_bancaria_id,
        comentario: '',
      };
    }
    this.decisiones.set(decisiones);
  }

  /** Solo el gerente financiero decide, y no en una programación que propuso él mismo. */
  protected puedeDecidir(programacion: ProgramacionPago): boolean {
    const usuario = this.auth.usuario();
    return usuario?.rol === 'gerente_financiero' && usuario.id !== programacion.propuesta_por;
  }

  protected propusoYo(programacion: ProgramacionPago): boolean {
    return this.auth.usuario()?.id === programacion.propuesta_por;
  }

  protected cambiarDecision(id: number, cambios: Partial<Decision>): void {
    this.decisiones.update((d) => ({ ...d, [id]: { ...d[id], ...cambios } }));
  }

  protected decidir(
    programacion: ProgramacionPago,
    pago: PagoProgramado,
    accion: 'aprobar' | 'rechazar',
  ): void {
    const decision = this.decisiones()[pago.id];
    const comentario = decision.comentario.trim();
    let datos: DecisionPagoEntrada = { accion, ...(comentario ? { comentario } : {}) };
    if (accion === 'rechazar' && !comentario) {
      this.error.set('Escribe el motivo del rechazo');
      return;
    }
    if (accion === 'aprobar') {
      const monto = decision.monto.trim();
      if (!MONTO.test(monto)) {
        this.error.set('Revisa el monto a aprobar');
        return;
      }
      // Solo se envía lo que el gerente cambió: así queda claro qué se modificó.
      if (Number(monto) !== Number(pago.monto)) datos = { ...datos, monto };
      if (decision.banco !== pago.cuenta_bancaria_id)
        datos = { ...datos, cuenta_bancaria_id: decision.banco };
    }
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.decidirPago(programacion.id, pago.id, datos).subscribe({
      next: (actualizada) => {
        this.programaciones.update((lista) =>
          lista.map((p) => (p.id === actualizada.id ? actualizada : p)),
        );
        this.elegir(actualizada.id);
        this.aviso.set(
          `Pago de ${pago.documento} ${accion === 'aprobar' ? 'aprobado' : 'rechazado'}`,
        );
        this.cargarPendientes();
      },
      error: (respuesta: HttpErrorResponse) =>
        this.fallo(respuesta, 'No se pudo registrar la decisión'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    this.guardando.set(false);
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
