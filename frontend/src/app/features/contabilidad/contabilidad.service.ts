import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

export type Partida = components['schemas']['PartidaSalida'];
export type PartidaEntrada = components['schemas']['PartidaEntrada'];
export type Cuenta = components['schemas']['CuentaSalida'];

@Injectable({ providedIn: 'root' })
export class ContabilidadService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/contabilidad/partidas`;

  /** Solo cuentas de detalle: las únicas que reciben movimientos. */
  cuentas(): Observable<Cuenta[]> {
    return this.http.get<Cuenta[]>(`${API_URL}/configuracion/cuentas`, {
      params: { solo_detalle: true },
    });
  }

  lineasNegocio(): Observable<string[]> {
    return this.http.get<string[]>(`${API_URL}/configuracion/lineas-negocio`);
  }

  partidas(estado?: string): Observable<Partida[]> {
    return this.http.get<Partida[]>(this.url, { params: estado ? { estado } : {} });
  }

  registrar(datos: PartidaEntrada): Observable<Partida> {
    return this.http.post<Partida>(this.url, datos);
  }

  corregir(id: number, datos: PartidaEntrada): Observable<Partida> {
    return this.http.put<Partida>(`${this.url}/${id}`, datos);
  }

  enviarARevision(id: number): Observable<Partida> {
    return this.http.post<Partida>(`${this.url}/${id}/enviar-a-revision`, {});
  }

  contabilizar(id: number): Observable<Partida> {
    return this.http.post<Partida>(`${this.url}/${id}/contabilizar`, {});
  }

  devolver(id: number, comentario: string): Observable<Partida> {
    return this.http.post<Partida>(`${this.url}/${id}/devolver`, { comentario });
  }
}
