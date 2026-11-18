import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

// ── HU-5.02: tarifas de mano de obra ──────────────────────────────────────────

export type Tarifa = components['schemas']['TarifaSalida'];
export type TarifaEntrada = components['schemas']['TarifaEntrada'];

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
}
