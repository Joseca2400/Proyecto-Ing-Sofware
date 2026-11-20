import { Component, Signal, WritableSignal, computed, inject, signal } from '@angular/core';
import { Router, RouterLink, Routes } from '@angular/router';
import {
  LucideActivity,
  LucideArrowLeftRight,
  LucideArrowRight,
  LucideBanknote,
  LucideBookOpen,
  LucideCalendarClock,
  LucideCar,
  LucideDynamicIcon,
  LucideFileSignature,
  LucideRefreshCw,
  LucideShieldCheck,
  LucideWrench,
} from '@lucide/angular';
import { Observable } from 'rxjs';
import { AuthService, NOMBRE_ROL } from '../../core/auth/auth.service';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { ETIQUETAS, etiqueta } from '../unidades/unidades.service';
import { EstadoSistema } from './estado-sistema';
import { InicioService } from './inicio.service';

/** Resultado de una consulta del tablero: cada tarjeta carga y falla por su cuenta. */
export type Dato<T> = { estado: 'cargando' } | { estado: 'listo'; valor: T } | { estado: 'error' };

/** Roles de una ruta según `app.routes.ts`; `null` si la ruta no existe. */
function rolesDe(rutas: Routes, destino: string, base = ''): string[] | undefined | null {
  for (const ruta of rutas) {
    const camino = ruta.path ? `${base}/${ruta.path}` : base;
    if (camino === destino && !ruta.children) {
      return ruta.data?.['roles'];
    }
    const hallado = ruta.children ? rolesDe(ruta.children, destino, camino) : null;
    if (hallado !== null) {
      return hallado;
    }
  }
  return null;
}

/** "2026-11-20" → "20/11/2026", sin pasar por Date (evita el corrimiento de zona horaria). */
function fechaCorta(fecha: string): string {
  return fecha.split('-').reverse().join('/');
}

// Tablero de inicio: números clave de la operación con los endpoints que ya existen. Cada tarjeta
// aparece solo si el rol puede abrir la pantalla a la que lleva (los mismos `roles` de la ruta) y
// solo entonces se consulta. Los montos vienen del servidor; el front cuenta elementos, no suma.
@Component({
  selector: 'app-inicio',
  imports: [RouterLink, MontoPipe, LucideDynamicIcon],
  templateUrl: './inicio.html',
  styleUrl: './inicio.css',
})
export class Inicio {
  private readonly servicio = inject(InicioService);
  private readonly auth = inject(AuthService);
  private readonly rutas = inject(Router).config;

  protected readonly iconos = {
    unidades: LucideCar,
    contratos: LucideFileSignature,
    taller: LucideWrench,
    cuentas: LucideCalendarClock,
    pagos: LucideBanknote,
    partidas: LucideBookOpen,
    cambio: LucideArrowLeftRight,
    depositos: LucideShieldCheck,
    sistema: LucideActivity,
    ir: LucideArrowRight,
    reintentar: LucideRefreshCw,
  };
  protected readonly fechaCorta = fechaCorta;
  protected readonly etiqueta = etiqueta;

  protected readonly nombre = computed(() => this.auth.usuario()?.nombre.split(/\s+/)[0] ?? '');
  protected readonly rol = computed(() => NOMBRE_ROL[this.auth.usuario()?.rol ?? ''] ?? '');
  protected readonly hoy = new Intl.DateTimeFormat('es-GT', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date());

  protected readonly unidades = this.siPuede('/unidades', () => this.servicio.unidades());
  protected readonly contratos = this.siPuede('/alquileres/contratos', () =>
    this.servicio.contratosAbiertos(),
  );
  protected readonly ordenes = this.siPuede('/taller/ordenes', () =>
    this.servicio.ordenesAbiertas(),
  );
  protected readonly cuentas = this.siPuede('/compras/programacion-pagos', () =>
    this.servicio.cuentasPorPagar(),
  );
  protected readonly pagos = this.siPuede('/compras/pagos', () => this.servicio.pagosPorEjecutar());
  protected readonly enRevision = this.siPuede('/contabilidad/partidas', () =>
    this.servicio.partidas('en_revision'),
  );
  protected readonly devueltas = this.siPuede('/contabilidad/partidas', () =>
    this.servicio.partidas('devuelta'),
  );
  protected readonly tiposCambio = this.siPuede('/configuracion/tipo-cambio', () =>
    this.servicio.tiposCambio(this.haceDias(30)),
  );
  protected readonly depositos = this.siPuede('/alquileres/depositos', () =>
    this.servicio.depositos(),
  );
  protected readonly etapas = this.siPuede('/reportes/unidades-etapa', () =>
    this.servicio.unidadesPorEtapa(),
  );

  protected readonly unidadesTotal = computed(() => {
    const dato = this.unidades?.();
    return dato?.estado === 'listo' ? dato.valor.length : 0;
  });

  /** El servidor los entrega del más reciente al más antiguo. */
  protected readonly ultimoTipoCambio = computed(() => {
    const dato = this.tiposCambio?.();
    return dato?.estado === 'listo' ? (dato.valor[0] ?? null) : null;
  });

  /** Unidades por estado, en el orden del ciclo de la unidad. */
  protected readonly porEstado = computed(() => {
    const dato = this.unidades?.();
    if (dato?.estado !== 'listo') {
      return [];
    }
    const conteo = new Map<string, number>();
    for (const unidad of dato.valor) {
      conteo.set(unidad.estado, (conteo.get(unidad.estado) ?? 0) + 1);
    }
    const orden = Object.keys(ETIQUETAS);
    return [...conteo.entries()]
      .sort(([a], [b]) => orden.indexOf(a) - orden.indexOf(b))
      .map(([estado, cantidad]) => ({ estado, cantidad }));
  });

  protected readonly vencidas = computed(() => {
    const dato = this.cuentas?.();
    return dato?.estado === 'listo' ? dato.valor.filter((c) => c.dias_vencida > 0).length : 0;
  });

  protected readonly excedidas = computed(() => {
    const dato = this.etapas?.();
    return dato?.estado === 'listo' ? dato.valor.unidades.filter((u) => u.excede).length : 0;
  });

  protected readonly sistema = signal<Dato<EstadoSistema>>({ estado: 'cargando' });

  constructor() {
    this.consultarSistema();
  }

  protected cantidad(dato: Dato<unknown[]>): number {
    return dato.estado === 'listo' ? dato.valor.length : 0;
  }

  protected consultarSistema(): void {
    this.cargar(this.servicio.estadoSistema(), this.sistema);
  }

  private siPuede<T>(ruta: string, fuente: () => Observable<T>): Signal<Dato<T>> | null {
    const roles = rolesDe(this.rutas, ruta);
    if (roles === null || !this.auth.tieneRol(roles)) {
      return null;
    }
    const dato = signal<Dato<T>>({ estado: 'cargando' });
    this.cargar(fuente(), dato);
    return dato.asReadonly();
  }

  private cargar<T>(fuente: Observable<T>, destino: WritableSignal<Dato<T>>): void {
    destino.set({ estado: 'cargando' });
    fuente.subscribe({
      next: (valor) => destino.set({ estado: 'listo', valor }),
      error: () => destino.set({ estado: 'error' }),
    });
  }

  private haceDias(dias: number): string {
    const fecha = new Date();
    fecha.setDate(fecha.getDate() - dias);
    return fecha.toLocaleDateString('en-CA');
  }
}
