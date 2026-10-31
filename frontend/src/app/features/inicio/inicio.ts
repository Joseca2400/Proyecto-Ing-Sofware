import { Component, inject, signal } from '@angular/core';
import { EstadoSistema } from './estado-sistema';
import { InicioService } from './inicio.service';

@Component({
  selector: 'app-inicio',
  templateUrl: './inicio.html',
  styleUrl: './inicio.css',
})
export class Inicio {
  private readonly servicio = inject(InicioService);

  protected readonly estado = signal<EstadoSistema | null>(null);
  protected readonly error = signal(false);
  protected readonly cargando = signal(true);

  constructor() {
    this.consultar();
  }

  protected consultar(): void {
    this.cargando.set(true);
    this.error.set(false);
    this.servicio.estadoSistema().subscribe({
      next: (estado) => {
        this.estado.set(estado);
        this.cargando.set(false);
      },
      error: () => {
        this.estado.set(null);
        this.error.set(true);
        this.cargando.set(false);
      },
    });
  }
}
