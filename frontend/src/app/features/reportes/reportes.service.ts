import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

// ── HU-7.04: unidades por etapa del ciclo ─────────────────────────────────────

export type ReporteUnidadesEtapa = components['schemas']['ReporteUnidadesEtapa'];
export type UnidadReporteEtapa = components['schemas']['UnidadReporteEtapa'];

// ── HU-3.13: rentabilidad por unidad y por contrato ───────────────────────────

export type ReporteRentabilidadUnidades = components['schemas']['ReporteRentabilidadUnidades'];
export type ReporteRentabilidadContratos = components['schemas']['ReporteRentabilidadContratos'];
export interface FiltrosRentabilidad {
  desde: string;
  hasta: string;
  vin: string;
}

// ── HU-7.02: rentabilidad de cada unidad en su ciclo (hasta la flota) ─────────

export type ReporteRentabilidadCiclo = components['schemas']['ReporteRentabilidadCiclo'];
export interface FiltrosCiclo {
  estado: string;
  marca: string;
  linea: string;
  anio_compra: string;
  proveedor_id: string;
  orden: 'resultado' | 'rentabilidad';
}

const sinVacios = (filtros: object): Record<string, string> =>
  Object.fromEntries(
    Object.entries(filtros)
      .filter(([, valor]) => valor !== '' && valor !== null && valor !== undefined)
      .map(([clave, valor]) => [clave, String(valor).trim()]),
  );

@Injectable({ providedIn: 'root' })
export class ReportesService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/reportes`;

  unidadesPorEtapa(limiteDias?: number): Observable<ReporteUnidadesEtapa> {
    const params: Record<string, number> = limiteDias ? { limite_dias: limiteDias } : {};
    return this.http.get<ReporteUnidadesEtapa>(`${this.url}/unidades-por-etapa`, { params });
  }

  rentabilidadUnidades(filtros: FiltrosRentabilidad): Observable<ReporteRentabilidadUnidades> {
    return this.http.get<ReporteRentabilidadUnidades>(`${this.url}/rentabilidad/unidades`, {
      params: sinVacios(filtros),
    });
  }

  rentabilidadContratos(filtros: FiltrosRentabilidad): Observable<ReporteRentabilidadContratos> {
    return this.http.get<ReporteRentabilidadContratos>(`${this.url}/rentabilidad/contratos`, {
      params: sinVacios(filtros),
    });
  }

  rentabilidadCiclo(filtros: FiltrosCiclo): Observable<ReporteRentabilidadCiclo> {
    return this.http.get<ReporteRentabilidadCiclo>(`${this.url}/rentabilidad/ciclo`, {
      params: sinVacios(filtros),
    });
  }

  /** El CSV lo arma el servidor; aquí solo se descarga con la sesión (el token va en el encabezado). */
  rentabilidadCsv(tipo: 'unidades' | 'contratos', filtros: FiltrosRentabilidad): Observable<Blob> {
    return this.http.get(`${this.url}/rentabilidad/${tipo}/csv`, {
      params: sinVacios(filtros),
      responseType: 'blob',
    });
  }
}

/** Entrega un archivo al navegador para que lo guarde. */
export function guardarArchivo(archivo: Blob, nombre: string): void {
  const enlace = document.createElement('a');
  enlace.href = URL.createObjectURL(archivo);
  enlace.download = nombre;
  enlace.click();
  URL.revokeObjectURL(enlace.href);
}
