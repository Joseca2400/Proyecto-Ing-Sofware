import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { API_URL } from '../api/api';
import { components } from '../api/esquema';

export type Usuario = components['schemas']['UsuarioSalida'];
export type Rol = 'auxiliar_contable' | 'contador' | 'gerente_financiero' | 'gerencia';
type Sesion = components['schemas']['LoginSalida'];

export const NOMBRE_ROL: Record<string, string> = {
  auxiliar_contable: 'Auxiliar contable',
  contador: 'Contador',
  gerente_financiero: 'Gerente financiero',
  gerencia: 'Gerencia',
};

const CLAVE = 'km0.sesion';

function sesionGuardada(): Sesion | null {
  // sessionStorage puede no estar disponible o traer algo ajeno: se trata como "sin sesión".
  try {
    return JSON.parse(sessionStorage.getItem(CLAVE) ?? 'null');
  } catch {
    return null;
  }
}

/** Sesión del usuario (HU-1.09). Solo decide qué se muestra: los permisos los aplica el servidor. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  // Dura lo que la pestaña: al cerrarla hay que volver a entrar.
  private readonly sesion = signal<Sesion | null>(sesionGuardada());

  readonly usuario = computed<Usuario | null>(() => this.sesion()?.usuario ?? null);
  readonly token = computed(() => this.sesion()?.token ?? null);

  entrar(correo: string, clave: string): Observable<Sesion> {
    return this.http
      .post<Sesion>(`${API_URL}/seguridad/login`, { correo, clave })
      .pipe(tap((sesion) => this.guardar(sesion)));
  }

  /** Cierra la sesión en el servidor y la olvida aquí aunque el servidor no responda. */
  salir(): void {
    const token = this.token();
    this.olvidar();
    if (token) {
      this.http
        .post(`${API_URL}/seguridad/logout`, {}, { headers: { Authorization: `Bearer ${token}` } })
        .subscribe({ error: () => undefined });
    }
  }

  olvidar(): void {
    this.guardar(null);
  }

  /** Sin lista de roles, basta con tener sesión. */
  tieneRol(roles?: readonly string[]): boolean {
    const rol = this.usuario()?.rol;
    return !!rol && (!roles?.length || roles.includes(rol));
  }

  private guardar(sesion: Sesion | null): void {
    this.sesion.set(sesion);
    try {
      if (sesion) sessionStorage.setItem(CLAVE, JSON.stringify(sesion));
      else sessionStorage.removeItem(CLAVE);
    } catch {
      // Sin almacenamiento la sesión vive solo en memoria.
    }
  }
}
