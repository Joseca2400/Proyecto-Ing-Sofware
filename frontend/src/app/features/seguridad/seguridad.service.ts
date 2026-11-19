import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

export type RegistroBitacora = components['schemas']['BitacoraSalida'];

export type UsuarioAdmin = components['schemas']['UsuarioAdminSalida'];
export type UsuarioAlta = components['schemas']['UsuarioAltaEntrada'];

export interface FiltroBitacora {
  usuario_id?: number;
  entidad?: string;
  vin?: string;
}

@Injectable({ providedIn: 'root' })
export class SeguridadService {
  private readonly http = inject(HttpClient);

  /** Los más recientes primero; el servidor limita la cantidad. */
  bitacora(filtro: FiltroBitacora): Observable<RegistroBitacora[]> {
    return this.http.get<RegistroBitacora[]>(`${API_URL}/seguridad/bitacora`, {
      params: { ...filtro },
    });
  }

  usuarios(): Observable<UsuarioAdmin[]> {
    return this.http.get<UsuarioAdmin[]>(`${API_URL}/seguridad/usuarios`);
  }

  altaUsuario(datos: UsuarioAlta): Observable<UsuarioAdmin> {
    return this.http.post<UsuarioAdmin>(`${API_URL}/seguridad/usuarios`, datos);
  }

  cambiarEstado(id: number, accion: 'suspender' | 'reactivar' | 'baja'): Observable<UsuarioAdmin> {
    return this.http.post<UsuarioAdmin>(`${API_URL}/seguridad/usuarios/${id}/${accion}`, {});
  }
}
