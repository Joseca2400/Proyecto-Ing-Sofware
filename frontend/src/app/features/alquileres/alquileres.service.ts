import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';

// ── HU-3.05: tarifario de alquiler ─────────────────────────────────────────────

export type Moneda = 'GTQ' | 'USD';
export type Modalidad = 'diaria' | 'semanal' | 'mensual' | 'kilometraje';
export type Naturaleza = 'ingreso' | 'deposito' | 'reintegro';

/** Pendiente HU-1.05: cuando exista `unidades`, el catálogo de tipos sale de ahí. */
export const TIPOS_VEHICULO: { valor: string; etiqueta: string }[] = [
  { valor: 'sedan', etiqueta: 'Sedán' },
  { valor: 'hatchback', etiqueta: 'Hatchback' },
  { valor: 'suv', etiqueta: 'SUV' },
  { valor: 'pickup', etiqueta: 'Pick-up' },
  { valor: 'microbus', etiqueta: 'Microbús' },
  { valor: 'panel', etiqueta: 'Panel' },
];

export const MODALIDADES: { valor: Modalidad; etiqueta: string; periodo: string }[] = [
  { valor: 'diaria', etiqueta: 'Diaria', periodo: 'día' },
  { valor: 'semanal', etiqueta: 'Semanal', periodo: 'semana' },
  { valor: 'mensual', etiqueta: 'Mensual', periodo: 'mes' },
  { valor: 'kilometraje', etiqueta: 'Por kilometraje', periodo: 'contrato' },
];

export const NATURALEZAS: { valor: Naturaleza; etiqueta: string; ayuda: string }[] = [
  { valor: 'ingreso', etiqueta: 'Ingreso', ayuda: 'Cuenta para el ISR; puede llevar IVA' },
  { valor: 'deposito', etiqueta: 'Depósito', ayuda: 'Pasivo: no es ingreso ni lleva IVA' },
  {
    valor: 'reintegro',
    etiqueta: 'Reintegro',
    ayuda: 'Gasto de terceros (multas): no es ingreso ni lleva IVA',
  },
];

export interface Temporada {
  id: number;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  activa: boolean;
}

export interface TemporadaEntrada {
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
}

/** Tarifa con IVA incluido. Los montos viajan como texto. */
export interface Tarifa {
  id: number;
  tipo_vehiculo: string | null;
  vin: string | null;
  temporada: Temporada | null;
  modalidad: Modalidad;
  moneda: Moneda;
  monto: string;
  km_incluido: number | null;
  costo_km_adicional: string | null;
  vigente_desde: string;
  creado_en: string;
}

export interface TarifaEntrada {
  tipo_vehiculo?: string;
  vin?: string;
  temporada_id?: number;
  modalidad: Modalidad;
  moneda: Moneda;
  monto: string;
  km_incluido?: number;
  costo_km_adicional?: string;
  vigente_desde: string;
}

export interface Concepto {
  id: number;
  nombre: string;
  naturaleza: Naturaleza;
  aplica_iva: boolean;
  es_ingreso_acumulable: boolean;
  precio_sugerido: string | null;
  moneda: Moneda | null;
  activo: boolean;
}

export interface ConceptoEntrada {
  nombre: string;
  naturaleza: Naturaleza;
  aplica_iva: boolean;
  precio_sugerido?: string;
  moneda?: Moneda;
}

export interface ConceptoCambio {
  precio_sugerido?: string;
  moneda?: Moneda;
  activo: boolean;
}

export interface CargoCotizacion {
  concepto_id: number;
  cantidad: number;
  precio?: string;
}

export interface CotizacionEntrada {
  tipo_vehiculo: string;
  vin?: string;
  modalidad: Modalidad;
  moneda: Moneda;
  fecha_salida: string;
  fecha_devolucion: string;
  km_estimados?: number;
  cargos: CargoCotizacion[];
}

export interface LineaCotizacion {
  descripcion: string;
  naturaleza: Naturaleza;
  aplica_iva: boolean;
  cantidad: string;
  precio_unitario: string;
  total: string;
  base: string;
  iva: string;
}

/** Calculada en el servidor: el front solo presenta los montos. */
export interface Cotizacion {
  moneda: Moneda;
  tarifa: Tarifa;
  periodos: number;
  dias: number;
  tipo_cambio: string | null;
  tasa_iva: string;
  lineas: LineaCotizacion[];
  total_ingresos: string;
  total_base: string;
  total_iva: string;
  total_depositos: string;
  total_reintegros: string;
  total_a_pagar: string;
}

@Injectable({ providedIn: 'root' })
export class AlquileresService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/alquileres`;

  temporadas(): Observable<Temporada[]> {
    return this.http.get<Temporada[]>(`${this.url}/temporadas`);
  }

  registrarTemporada(datos: TemporadaEntrada): Observable<Temporada> {
    return this.http.post<Temporada>(`${this.url}/temporadas`, datos);
  }

  desactivarTemporada(id: number): Observable<Temporada> {
    return this.http.post<Temporada>(`${this.url}/temporadas/${id}/desactivar`, {});
  }

  tarifas(): Observable<Tarifa[]> {
    return this.http.get<Tarifa[]>(`${this.url}/tarifas`);
  }

  registrarTarifa(datos: TarifaEntrada): Observable<Tarifa> {
    return this.http.post<Tarifa>(`${this.url}/tarifas`, datos);
  }

  conceptos(soloActivos = false): Observable<Concepto[]> {
    const params: Record<string, string> = soloActivos ? { solo_activos: 'true' } : {};
    return this.http.get<Concepto[]>(`${this.url}/conceptos`, { params });
  }

  registrarConcepto(datos: ConceptoEntrada): Observable<Concepto> {
    return this.http.post<Concepto>(`${this.url}/conceptos`, datos);
  }

  cambiarConcepto(id: number, datos: ConceptoCambio): Observable<Concepto> {
    return this.http.put<Concepto>(`${this.url}/conceptos/${id}`, datos);
  }

  cotizar(datos: CotizacionEntrada): Observable<Cotizacion> {
    return this.http.post<Cotizacion>(`${this.url}/cotizaciones`, datos);
  }
}
