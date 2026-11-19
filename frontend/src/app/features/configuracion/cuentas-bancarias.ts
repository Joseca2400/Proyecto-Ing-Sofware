import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ConfiguracionService, Cuenta, CuentaBancaria } from './configuracion.service';

// HU-1.08 (Sprint 2): cuentas bancarias en GTQ y USD ligadas al catálogo. Diferido: bloquear la
// inactivación con movimientos y usar la numeración de cheques (pagos, cobros y conciliación, Sprint 3).
@Component({
  selector: 'app-cuentas-bancarias',
  imports: [ReactiveFormsModule],
  templateUrl: './cuentas-bancarias.html',
})
export class CuentasBancariasPantalla {
  private readonly servicio = inject(ConfiguracionService);

  protected readonly cuentasBancarias = signal<CuentaBancaria[]>([]);
  protected readonly catalogo = signal<Cuenta[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    banco: ['', Validators.required],
    numero: ['', Validators.required],
    tipo: ['monetaria' as 'monetaria' | 'ahorro', Validators.required],
    moneda: ['GTQ' as 'GTQ' | 'USD', Validators.required],
    cuenta_id: [0, Validators.min(1)],
    siguiente_cheque: [null as number | null, Validators.min(1)],
  });
  private readonly moneda = toSignal(this.formulario.controls.moneda.valueChanges, {
    initialValue: 'GTQ' as 'GTQ' | 'USD',
  });

  // Solo cuentas de detalle; las de USD, solo las marcadas como monetarias en USD.
  protected readonly opcionesCuenta = computed(() =>
    this.catalogo().filter((c) => c.es_detalle && (this.moneda() === 'GTQ' || c.monetaria_usd)),
  );

  constructor() {
    this.servicio.cuentas().subscribe({
      next: (cuentas) => this.catalogo.set(cuentas),
      error: () => this.error.set('No se pudo consultar el catálogo de cuentas'),
    });
    this.cargar();
    this.formulario.controls.moneda.valueChanges.subscribe(() =>
      this.formulario.controls.cuenta_id.setValue(0),
    );
  }

  protected cargar(): void {
    this.servicio.cuentasBancarias().subscribe({
      next: (cuentas) => this.cuentasBancarias.set(cuentas),
      error: () => this.error.set('No se pudieron consultar las cuentas bancarias'),
    });
  }

  protected nombreCuenta(id: number): string {
    const cuenta = this.catalogo().find((c) => c.id === id);
    return cuenta ? `${cuenta.codigo} ${cuenta.nombre}` : String(id);
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.crearCuentaBancaria(this.formulario.getRawValue()).subscribe({
      next: (cuenta) => {
        this.guardando.set(false);
        this.aviso.set(`Cuenta ${cuenta.numero} de ${cuenta.banco} guardada`);
        this.formulario.patchValue({ banco: '', numero: '', siguiente_cheque: null, cuenta_id: 0 });
        this.formulario.markAsUntouched();
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) =>
        this.fallo(respuesta, 'No se pudo guardar la cuenta'),
    });
  }

  protected cambiarEstado(cuenta: CuentaBancaria): void {
    this.error.set(null);
    this.servicio.cambiarEstadoCuentaBancaria(cuenta.id, !cuenta.activa).subscribe({
      next: () => this.cargar(),
      error: (respuesta: HttpErrorResponse) =>
        this.fallo(respuesta, 'No se pudo cambiar el estado'),
    });
  }

  protected guardarCheques(cuenta: CuentaBancaria, texto: string): void {
    this.error.set(null);
    this.aviso.set(null);
    const numero = texto.trim() === '' ? null : Number(texto);
    this.servicio.definirNumeracionCheques(cuenta.id, numero).subscribe({
      next: () => {
        this.aviso.set(`Numeración de cheques de la cuenta ${cuenta.numero} guardada`);
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) =>
        this.fallo(respuesta, 'No se pudo guardar la numeración'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, porDefecto: string): void {
    this.guardando.set(false);
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : porDefecto);
  }
}
