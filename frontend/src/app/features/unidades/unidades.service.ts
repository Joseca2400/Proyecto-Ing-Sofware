import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';

// ── HU-1.05: unidades por VIN ──────────────────────────────────────────────────

export type EstadoUnidad =
  | 'en_transito'
  | 'en_aduana'
  | 'en_taller'
  | 'lista'
  | 'en_flota'
  | 'en_venta'
  | 'vendida'
  | 'recuperada';

/** Solo etiquetas para mostrar; las listas válidas las da el servidor en `catalogos()`. */
export const ETIQUETAS: Record<string, string> = {
  en_transito: 'En tránsito',
  en_aduana: 'En aduana',
  en_taller: 'En taller',
  lista: 'Lista',
  en_flota: 'En flota',
  en_venta: 'En venta',
  vendida: 'Vendida',
  recuperada: 'Recuperada',
  sedan: 'Sedán',
  hatchback: 'Hatchback',
  suv: 'SUV',
  pickup: 'Pickup',
  camioneta: 'Camioneta',
  microbus: 'Microbús',
  motocicleta: 'Motocicleta',
  otro: 'Otro',
  alquiler: 'Alquiler',
  venta: 'Venta',
  taller: 'Taller',
  financiamiento: 'Financiamiento',
  administracion: 'Administración',
};

export function etiqueta(valor: string | null): string {
  return valor ? (ETIQUETAS[valor] ?? valor) : '';
}

export interface Catalogos {
  estados: EstadoUnidad[];
  tipos_vehiculo: string[];
  /** Las de configuración (HU-1.04). */
  lineas_negocio: string[];
}

export interface Unidad {
  id: number;
  vin: string;
  marca: string;
  linea: string;
  modelo: number;
  color: string;
  tipo_vehiculo: string;
  linea_negocio: string | null;
  estado: EstadoUnidad;
  creado_en: string;
}

export interface UnidadEntrada {
  vin: string;
  marca: string;
  linea: string;
  modelo: number;
  color: string;
  tipo_vehiculo: string;
  linea_negocio?: string;
  estado: EstadoUnidad;
  documento?: string;
}

export interface CambioEstado {
  id: number;
  estado_anterior: EstadoUnidad | null;
  estado_nuevo: EstadoUnidad;
  documento: string;
  usuario_id: number | null;
  fecha: string;
}

export interface FiltroUnidades {
  estado?: EstadoUnidad;
  buscar?: string;
}

@Injectable({ providedIn: 'root' })
export class UnidadesService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/unidades`;

  catalogos(): Observable<Catalogos> {
    return this.http.get<Catalogos>(`${this.url}/catalogos`);
  }

  unidades(filtro: FiltroUnidades = {}): Observable<Unidad[]> {
    const params: Record<string, string> = {};
    if (filtro.estado) params['estado'] = filtro.estado;
    if (filtro.buscar) params['buscar'] = filtro.buscar;
    return this.http.get<Unidad[]>(this.url, { params });
  }

  registrar(datos: UnidadEntrada): Observable<Unidad> {
    return this.http.post<Unidad>(this.url, datos);
  }

  cambiarEstado(vin: string, estado: EstadoUnidad, documento: string): Observable<Unidad> {
    return this.http.post<Unidad>(`${this.url}/${vin}/estado`, { estado, documento });
  }

  historial(vin: string): Observable<CambioEstado[]> {
    return this.http.get<CambioEstado[]>(`${this.url}/${vin}/historial`);
  }
}
