import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ConfiguracionService, TipoCambio } from './configuracion.service';

// HU-1.06 (Sprint 1): carga manual del tipo de cambio por fecha. La consulta al Banguat es diferida.
@Component({
  selector: 'app-tipo-cambio',
  imports: [ReactiveFormsModule],
  templateUrl: './tipo-cambio.html',
  styleUrl: './tipo-cambio.css',
})
export class TipoCambioPantalla {
  private readonly servicio = inject(ConfiguracionService);

  protected readonly tipos = signal<TipoCambio[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    fecha: [new Date().toLocaleDateString('en-CA'), Validators.required],
    // Solo se valida la forma; el backend decide si el valor es aceptable.
    valor: ['', [Validators.required, Validators.pattern(/^\d+(\.\d{1,8})?$/)]],
  });

  constructor() {
    this.cargar();
  }

  protected cargar(): void {
    this.servicio.tiposCambio().subscribe({
      next: (tipos) => this.tipos.set(tipos),
      error: () => this.error.set('No se pudo consultar el tipo de cambio'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.registrarTipoCambio(this.formulario.getRawValue()).subscribe({
      next: (tipo) => {
        this.guardando.set(false);
        this.aviso.set(`Tipo de cambio del ${tipo.fecha} guardado`);
        this.formulario.controls.valor.reset('');
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(
          typeof detalle === 'string' ? detalle : 'No se pudo guardar el tipo de cambio',
        );
      },
    });
  }
}
