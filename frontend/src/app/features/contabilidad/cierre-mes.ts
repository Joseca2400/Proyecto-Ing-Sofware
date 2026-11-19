import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { ContabilidadService, Depreciacion } from './contabilidad.service';

const ESTADOS: Record<string, string> = {
  borrador: 'en borrador',
  en_revision: 'en revisión',
  devuelta: 'devuelta',
  contabilizada: 'contabilizada',
};

/** Mes anterior al de hoy, como lo entrega `<input type="month">` ("2026-11"). */
function mesAnterior(): string {
  const hoy = new Date();
  const fecha = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
  return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}`;
}

// Procesos del cierre de mes, en su orden. HU-2.07 (Sprint 3): depreciación mensual de la flota; el
// servidor calcula y arma la partida en borrador, que sigue la revisión normal en «Partidas».
@Component({
  selector: 'app-cierre-mes',
  templateUrl: './cierre-mes.html',
  imports: [RouterLink, MontoPipe],
})
export class CierreMesPantalla {
  private readonly servicio = inject(ContabilidadService);

  protected readonly estados = ESTADOS;
  protected readonly mes = signal(mesAnterior());
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);

  private readonly depreciaciones = signal<Depreciacion[]>([]);
  protected readonly depreciacion = computed(() =>
    this.depreciaciones().find((d) => d.anio === this.anio() && d.mes === this.numeroMes()),
  );

  private readonly anio = computed(() => Number(this.mes().slice(0, 4)));
  private readonly numeroMes = computed(() => Number(this.mes().slice(5, 7)));

  constructor() {
    this.servicio.depreciaciones().subscribe({
      next: (lista) => this.depreciaciones.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar la depreciación'),
    });
  }

  protected elegirMes(valor: string): void {
    this.error.set(null);
    this.aviso.set(null);
    if (valor) this.mes.set(valor);
  }

  protected depreciar(): void {
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.calcularDepreciacion(this.anio(), this.numeroMes()).subscribe({
      next: (nueva) => {
        this.depreciaciones.update((lista) => [
          nueva,
          ...lista.filter((d) => d.anio !== nueva.anio || d.mes !== nueva.mes),
        ]);
        this.aviso.set(
          'Depreciación calculada: su partida quedó en borrador para revisión en «Partidas»',
        );
      },
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo calcular la depreciación'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
