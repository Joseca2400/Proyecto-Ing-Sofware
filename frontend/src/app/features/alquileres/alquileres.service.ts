import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

// ── HU-3.05: tarifario ─────────────────────────────────────────────────────────

/** Los montos viajan como texto; el front solo les da formato con `MontoPipe`. */
export type Tarifa = components['schemas']['TarifaSalida'];
export type TarifaEntrada = components['schemas']['TarifaEntrada'];
export type Modalidad = Tarifa['modalidad'];
export type CatalogosTarifas = components['schemas']['CatalogosTarifas'];

export const ETIQUETAS_MODALIDAD: Record<Modalidad, string> = {
  diaria: 'Diaria',
  semanal: 'Semanal',
  mensual: 'Mensual',
  por_kilometraje: 'Por kilometraje',
};

@Injectable({ providedIn: 'root' })
export class AlquileresService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/alquileres/tarifas`;

  catalogos(): Observable<CatalogosTarifas> {
    return this.http.get<CatalogosTarifas>(`${this.url}/catalogos`);
  }

  tarifas(): Observable<Tarifa[]> {
    return this.http.get<Tarifa[]>(this.url);
  }

  registrarTarifa(entrada: TarifaEntrada): Observable<Tarifa> {
    return this.http.post<Tarifa>(this.url, entrada);
  }
}
