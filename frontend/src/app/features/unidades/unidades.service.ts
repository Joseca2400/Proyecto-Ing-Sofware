import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

// ── HU-1.05: unidades por VIN ──────────────────────────────────────────────────

export type EstadoUnidad =
  | 'en_transito'
  | 'en_aduana'
  | 'en_taller'
  | 'lista'
  | 'en_flota'
  | 'alquilada'
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
  alquilada: 'Alquilada',
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

// ── HU-4.07: etapas de importación ─────────────────────────────────────────────

export type Etapa = 'en_transito' | 'en_aduana' | 'en_taller' | 'lista';

/** Días y costo los calcula el servidor; el costo llega como texto y solo se formatea. */
export interface UnidadEnEtapa {
  vin: string;
  marca: string;
  linea: string;
  modelo: number;
  color: string;
  estado: Etapa;
  desde: string;
  dias_en_etapa: number;
  costo_total_gtq: string;
  /** La única etapa a la que puede pasar; null cuando ya está lista. */
  siguiente_etapa: Etapa | null;
}

export interface ResumenEtapa {
  estado: Etapa;
  unidades: number;
  costo_total_gtq: string;
}

export interface EtapasImportacion {
  etapas: ResumenEtapa[];
  unidades: UnidadEnEtapa[];
}

// ── HU-3.01: alta en flota ─────────────────────────────────────────────────────

export type CandidataAltaFlota = components['schemas']['CandidataAltaFlota'];
export type AltaFlota = components['schemas']['AltaFlotaSalida'];
export type AltaFlotaEntrada = components['schemas']['AltaFlotaEntrada'];

// ── HU-3.02: depreciación ──────────────────────────────────────────────────────

export type DepreciacionTipo = components['schemas']['DepreciacionTipoSalida'];
export type DepreciacionTipoEntrada = components['schemas']['DepreciacionTipoEntrada'];
export type ParametroDepreciacion = components['schemas']['ParametroDepreciacionSalida'];
export type ParametroDepreciacionEntrada = components['schemas']['ParametroDepreciacionEntrada'];
export type ValorEnLibros = components['schemas']['ValorEnLibros'];

// ── HU-3.14: fin de vida útil en flota ─────────────────────────────────────────

export type FinVidaUtil = components['schemas']['FinVidaUtil'];
export type ReglaFinVida = components['schemas']['ReglaFinVidaSalida'];
export type ReglaFinVidaEntrada = components['schemas']['ReglaFinVidaEntrada'];

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

  etapasImportacion(etapa?: Etapa): Observable<EtapasImportacion> {
    const params: Record<string, string> = etapa ? { etapa } : {};
    return this.http.get<EtapasImportacion>(`${this.url}/etapas-importacion`, { params });
  }

  historial(vin: string): Observable<CambioEstado[]> {
    return this.http.get<CambioEstado[]>(`${this.url}/${vin}/historial`);
  }

  candidatasAlta(): Observable<CandidataAltaFlota[]> {
    return this.http.get<CandidataAltaFlota[]>(`${this.url}/alta-flota/candidatas`);
  }

  darDeAlta(vin: string, datos: AltaFlotaEntrada): Observable<AltaFlota> {
    return this.http.post<AltaFlota>(`${this.url}/${vin}/alta-flota`, datos);
  }

  depreciacionTipos(): Observable<DepreciacionTipo[]> {
    return this.http.get<DepreciacionTipo[]>(`${this.url}/depreciacion/tipos`);
  }

  definirDepreciacionTipo(
    tipo: string,
    datos: DepreciacionTipoEntrada,
  ): Observable<DepreciacionTipo> {
    return this.http.put<DepreciacionTipo>(`${this.url}/depreciacion/tipos/${tipo}`, datos);
  }

  parametrosDepreciacion(vin: string): Observable<ParametroDepreciacion[]> {
    return this.http.get<ParametroDepreciacion[]>(`${this.url}/${vin}/parametros-depreciacion`);
  }

  cambiarParametros(
    vin: string,
    datos: ParametroDepreciacionEntrada,
  ): Observable<ParametroDepreciacion> {
    return this.http.post<ParametroDepreciacion>(
      `${this.url}/${vin}/parametros-depreciacion`,
      datos,
    );
  }

  finVidaUtil(): Observable<FinVidaUtil> {
    return this.http.get<FinVidaUtil>(`${this.url}/fin-vida-util`);
  }

  definirReglaFinVida(datos: ReglaFinVidaEntrada): Observable<ReglaFinVida> {
    return this.http.put<ReglaFinVida>(`${this.url}/fin-vida-util/regla`, datos);
  }

  valorEnLibros(vin: string, fecha: string): Observable<ValorEnLibros> {
    return this.http.get<ValorEnLibros>(`${this.url}/${vin}/valor-libros`, { params: { fecha } });
  }
}
