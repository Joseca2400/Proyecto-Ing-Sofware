import { DatePipe, JsonPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { FiltroBitacora, RegistroBitacora, SeguridadService } from './seguridad.service';

// HU-1.11 (versión delgada): consulta de la bitácora con filtros por usuario, entidad y VIN.
// Pendiente (Sprint 5): exportación.
@Component({
  selector: 'app-bitacora',
  imports: [ReactiveFormsModule, DatePipe, JsonPipe],
  templateUrl: './bitacora.html',
})
export class BitacoraPantalla {
  private readonly servicio = inject(SeguridadService);

  protected readonly registros = signal<RegistroBitacora[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly filtro = inject(FormBuilder).nonNullable.group({
    usuario_id: [''],
    entidad: [''],
    vin: [''],
  });

  constructor() {
    this.consultar();
  }

  protected consultar(): void {
    const { usuario_id, entidad, vin } = this.filtro.getRawValue();
    // Solo viajan los filtros con valor: el servidor valida la forma del VIN y del usuario.
    const filtro: FiltroBitacora = {
      ...(usuario_id.trim() ? { usuario_id: Number(usuario_id) } : {}),
      ...(entidad.trim() ? { entidad: entidad.trim() } : {}),
      ...(vin.trim() ? { vin: vin.trim().toUpperCase() } : {}),
    };
    this.error.set(null);
    this.servicio.bitacora(filtro).subscribe({
      next: (registros) => this.registros.set(registros),
      error: (respuesta: HttpErrorResponse) => {
        this.registros.set([]);
        const detalle = respuesta.error?.detail;
        this.error.set(
          typeof detalle === 'string'
            ? detalle
            : 'No se pudo consultar la bitácora; revise los filtros (el VIN lleva 17 caracteres)',
        );
      },
    });
  }
}
