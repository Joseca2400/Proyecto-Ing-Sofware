import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

// ── HU-7.04: unidades por etapa del ciclo ─────────────────────────────────────

export type ReporteUnidadesEtapa = components['schemas']['ReporteUnidadesEtapa'];
export type UnidadReporteEtapa = components['schemas']['UnidadReporteEtapa'];

@Injectable({ providedIn: 'root' })
export class ReportesService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/reportes`;

  unidadesPorEtapa(limiteDias?: number): Observable<ReporteUnidadesEtapa> {
    const params: Record<string, number> = limiteDias ? { limite_dias: limiteDias } : {};
    return this.http.get<ReporteUnidadesEtapa>(`${this.url}/unidades-por-etapa`, { params });
  }
}
