import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { map } from 'rxjs';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { ConfiguracionService, TransaccionUSD } from './configuracion.service';

// HU-1.07 (Sprint 1): monto original en USD, tipo de cambio y equivalente en quetzales.
// Tipo personalizado positivo con justificación obligatoria.
@Component({
  selector: 'app-transaccion-usd',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './transaccion-usd.html',
  styleUrl: './transaccion-usd.css',
})
export class TransaccionUSDPantalla {
  private readonly servicio = inject(ConfiguracionService);

  protected readonly transacciones = signal<TransaccionUSD[]>([]);
  protected readonly ultimaConversion = signal<TransaccionUSD | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    fecha: [new Date().toLocaleDateString('en-CA'), Validators.required],
    monto_usd: ['', [Validators.required, Validators.pattern(/^\d+(\.\d{1,6})?$/)]],
    tipo_cambio_personalizado: ['', Validators.pattern(/^\d+(\.\d{1,8})?$/)],
    justificacion: [''],
  });

  // Reacciona a cambios del campo de tipo personalizado para mostrar la justificación.
  protected readonly tienePersonalizado = toSignal(
    this.formulario.controls.tipo_cambio_personalizado.valueChanges.pipe(map((v) => !!v?.trim())),
    { initialValue: false },
  );

  constructor() {
    this.cargar();
  }

  protected cargar(): void {
    this.servicio.transaccionesUSD().subscribe({
      next: (lista) => this.transacciones.set(lista),
      error: () => this.error.set('No se pudo consultar las transacciones'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    const { fecha, monto_usd, tipo_cambio_personalizado, justificacion } =
      this.formulario.getRawValue();

    if (tipo_cambio_personalizado.trim() && !justificacion.trim()) {
      this.error.set('El tipo de cambio personalizado requiere justificación');
      return;
    }

    const entrada = {
      fecha,
      monto_usd,
      ...(tipo_cambio_personalizado.trim() && {
        tipo_cambio_personalizado: tipo_cambio_personalizado.trim(),
        justificacion: justificacion.trim(),
      }),
    };

    this.guardando.set(true);
    this.error.set(null);
    this.ultimaConversion.set(null);

    this.servicio.registrarTransaccionUSD(entrada).subscribe({
      next: (tx) => {
        this.guardando.set(false);
        this.ultimaConversion.set(tx);
        this.formulario.controls.monto_usd.reset('');
        this.formulario.controls.tipo_cambio_personalizado.reset('');
        this.formulario.controls.justificacion.reset('');
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(
          typeof detalle === 'string' ? detalle : 'No se pudo registrar la transacción',
        );
      },
    });
  }
}
