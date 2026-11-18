import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

// ── HU-5.02: tarifas de mano de obra ──────────────────────────────────────────

export type Tarifa = components['schemas']['TarifaSalida'];
export type TarifaEntrada = components['schemas']['TarifaEntrada'];

// ── HU-5.01: órdenes de trabajo ───────────────────────────────────────────────

export type Orden = components['schemas']['OrdenSalida'];
export type OrdenEntrada = components['schemas']['OrdenEntrada'];

@Injectable({ providedIn: 'root' })
export class TallerService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/taller`;

  tarifas(): Observable<Tarifa[]> {
    return this.http.get<Tarifa[]>(`${this.url}/tarifas`);
  }

  crearTarifa(datos: TarifaEntrada): Observable<Tarifa> {
    return this.http.post<Tarifa>(`${this.url}/tarifas`, datos);
  }

  ordenes(estado?: 'abierta' | 'cerrada'): Observable<Orden[]> {
    return this.http.get<Orden[]>(`${this.url}/ordenes`, { params: estado ? { estado } : {} });
  }

  orden(id: number): Observable<Orden> {
    return this.http.get<Orden>(`${this.url}/ordenes/${id}`);
  }

  abrirOrden(datos: OrdenEntrada): Observable<Orden> {
    return this.http.post<Orden>(`${this.url}/ordenes`, datos);
  }
}
