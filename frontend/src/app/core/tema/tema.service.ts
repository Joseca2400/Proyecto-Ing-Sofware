import { DOCUMENT, Injectable, inject, signal } from '@angular/core';

export type Tema = 'claro' | 'oscuro';

/** Misma clave que lee el script de index.html para pintar el tema antes de que arranque Angular. */
export const CLAVE_TEMA = 'km0.tema';

function temaGuardado(): Tema | null {
  try {
    const valor = localStorage.getItem(CLAVE_TEMA);
    return valor === 'claro' || valor === 'oscuro' ? valor : null;
  } catch {
    return null; // almacenamiento bloqueado (ventana privada, sitio sin permisos)
  }
}

/**
 * Modo claro u oscuro. La primera vez sigue la preferencia del sistema; cuando el usuario lo
 * cambia, se recuerda en localStorage y deja de seguir al sistema. Los colores de cada modo están
 * en styles.css, bajo [data-tema='oscuro'].
 */
@Injectable({ providedIn: 'root' })
export class TemaService {
  private readonly html = inject(DOCUMENT).documentElement;
  private readonly sistema = inject(DOCUMENT).defaultView?.matchMedia?.(
    '(prefers-color-scheme: dark)',
  );
  private elegido = temaGuardado() !== null;

  readonly tema = signal<Tema>(temaGuardado() ?? (this.sistema?.matches ? 'oscuro' : 'claro'));

  constructor() {
    this.aplicar();
    // Mientras el usuario no elija, si cambia el modo del sistema la aplicación lo sigue.
    this.sistema?.addEventListener?.('change', (evento) => {
      if (!this.elegido) {
        this.tema.set(evento.matches ? 'oscuro' : 'claro');
        this.aplicar();
      }
    });
  }

  alternar(): void {
    this.tema.set(this.tema() === 'oscuro' ? 'claro' : 'oscuro');
    this.elegido = true;
    this.aplicar();
    try {
      localStorage.setItem(CLAVE_TEMA, this.tema());
    } catch {
      // Sin almacenamiento el cambio vale solo para esta visita.
    }
  }

  private aplicar(): void {
    this.html.dataset['tema'] = this.tema();
  }
}
