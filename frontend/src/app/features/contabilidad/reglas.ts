import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { ContabilidadService, Cuenta, Regla } from './contabilidad.service';

// HU-2.03 (Sprint 2): reglas de contabilización por tipo de documento. Solo el contador cambia la
// cuenta de una regla (lo decide el servidor); cada módulo siembra las reglas de sus documentos.
@Component({
  selector: 'app-reglas',
  templateUrl: './reglas.html',
})
export class ReglasPantalla {
  private readonly servicio = inject(ContabilidadService);

  protected readonly cuentas = signal<Cuenta[]>([]);
  protected readonly reglas = signal<Regla[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly grupos = computed(() => {
    const grupos = new Map<string, Regla[]>();
    for (const regla of this.reglas()) {
      grupos.set(regla.documento_tipo, [...(grupos.get(regla.documento_tipo) ?? []), regla]);
    }
    return [...grupos.entries()].map(([tipo, reglas]) => ({ tipo, reglas }));
  });

  constructor() {
    this.servicio.cuentas().subscribe({
      next: (lista) => this.cuentas.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar las cuentas'),
    });
    this.servicio.reglas().subscribe({
      next: (lista) => this.reglas.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar las reglas'),
    });
  }

  protected guardar(regla: Regla, codigo: string): void {
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.definirRegla(regla.id, codigo).subscribe({
      next: (nueva) => {
        this.reglas.update((lista) => lista.map((r) => (r.id === nueva.id ? nueva : r)));
        this.aviso.set(
          `Regla «${nueva.documento_tipo} · ${nueva.concepto}» ahora usa la cuenta ${nueva.cuenta_codigo}`,
        );
      },
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo guardar la regla'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
