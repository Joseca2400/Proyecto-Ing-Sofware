import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { FinVidaUtil, UnidadesService, etiqueta } from './unidades.service';

// HU-3.14: regla de fin de vida útil en flota (kilometraje, meses desde el alta o ambos, con un
// porcentaje de aviso) y las unidades que la alcanzaron o están por alcanzarla, con su valor en
// libros. La alerta solo informa: la baja y la venta las decide la gerencia.
@Component({
  selector: 'app-fin-vida-util',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './fin-vida-util.html',
})
export class FinVidaUtilPantalla {
  private readonly servicio = inject(UnidadesService);

  protected readonly etiqueta = etiqueta;
  protected readonly datos = signal<FinVidaUtil | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);

  protected readonly formulario = inject(FormBuilder).group({
    kilometraje_limite: [null as number | null, Validators.min(1)],
    meses_limite: [null as number | null, Validators.min(1)],
    porcentaje_aviso: ['90', [Validators.required, Validators.pattern(/^\s*\d+(\.\d{1,2})?\s*$/)]],
  });

  constructor() {
    this.cargar();
  }

  private cargar(): void {
    this.servicio.finVidaUtil().subscribe({
      next: (datos) => {
        this.datos.set(datos);
        if (datos.regla) {
          this.formulario.patchValue({
            kilometraje_limite: datos.regla.kilometraje_limite,
            meses_limite: datos.regla.meses_limite,
            porcentaje_aviso: datos.regla.porcentaje_aviso,
          });
        }
      },
      error: () => this.error.set('No se pudo consultar la alerta de fin de vida útil'),
    });
  }

  protected guardar(): void {
    const { kilometraje_limite, meses_limite, porcentaje_aviso } = this.formulario.getRawValue();
    if (this.formulario.invalid || (!kilometraje_limite && !meses_limite)) {
      this.error.set('Indica el límite por kilometraje, por meses o ambos');
      return;
    }
    this.error.set(null);
    this.aviso.set(null);
    this.servicio
      .definirReglaFinVida({
        kilometraje_limite: kilometraje_limite || null,
        meses_limite: meses_limite || null,
        porcentaje_aviso: (porcentaje_aviso ?? '').trim(),
      })
      .subscribe({
        next: () => {
          this.aviso.set('Regla guardada');
          this.cargar();
        },
        error: (respuesta: HttpErrorResponse) => {
          const detalle = respuesta.error?.detail;
          this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo guardar la regla');
        },
      });
  }
}
