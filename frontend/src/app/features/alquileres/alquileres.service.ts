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

// ── HU-3.06: contratos ─────────────────────────────────────────────────────────

export type Contrato = components['schemas']['ContratoSalida'];
export type ContratoEntrada = components['schemas']['ContratoEntrada'];
export type ClienteAlquiler = components['schemas']['ClienteSalida'];
export type UnidadAlquiler = components['schemas']['UnidadSalida'];
export type CierreEntrada = components['schemas']['CierreEntrada'];

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

  contratos(): Observable<Contrato[]> {
    return this.http.get<Contrato[]>(`${API_URL}/alquileres/contratos`);
  }

  registrarContrato(entrada: ContratoEntrada): Observable<Contrato> {
    return this.http.post<Contrato>(`${API_URL}/alquileres/contratos`, entrada);
  }

  cerrarContrato(id: number, entrada: CierreEntrada): Observable<Contrato> {
    return this.http.post<Contrato>(`${API_URL}/alquileres/contratos/${id}/cierre`, entrada);
  }

  clientes(): Observable<ClienteAlquiler[]> {
    return this.http.get<ClienteAlquiler[]>(`${API_URL}/facturacion/clientes`);
  }

  /** Unidades disponibles para alquilar; el servidor vuelve a validar la disponibilidad. */
  unidadesEnFlota(): Observable<UnidadAlquiler[]> {
    return this.http.get<UnidadAlquiler[]>(`${API_URL}/unidades`, {
      params: { estado: 'en_flota' },
    });
  }
}
