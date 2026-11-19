import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';

// ── HU-1.06: tipo de cambio ────────────────────────────────────────────────────

/** Tipo de cambio de referencia (quetzales por un dólar). El valor viaja como texto. */
export interface TipoCambio {
  id: number;
  fecha: string;
  valor: string;
  origen: 'manual' | 'automatico';
}

export interface TipoCambioEntrada {
  fecha: string;
  valor: string;
}

// ── HU-1.07: transacciones en USD ─────────────────────────────────────────────

/** Transacción en USD con triple (monto_usd, tipo_cambio_aplicado, monto_gtq). Los montos viajan como texto. */
export interface TransaccionUSD {
  id: number;
  fecha: string;
  monto_usd: string;
  tipo_cambio_aplicado: string;
  monto_gtq: string;
  justificacion: string | null;
}

export interface TransaccionUSDEntrada {
  fecha: string;
  monto_usd: string;
  tipo_cambio_personalizado?: string;
  justificacion?: string;
}

// ── HU-1.01: perfil fiscal de la empresa ──────────────────────────────────────

export type RegimenISR = 'opcional_simplificado' | 'sobre_utilidades';

export const REGIMENES_ISR: { valor: RegimenISR; etiqueta: string; descripcion: string }[] = [
  {
    valor: 'opcional_simplificado',
    etiqueta: 'Opcional simplificado sobre ingresos',
    descripcion:
      'El ISR se calcula por tramos sobre la facturación bruta del mes; no se deducen costos ni gastos.',
  },
  {
    valor: 'sobre_utilidades',
    etiqueta: 'Sobre utilidades de actividades lucrativas',
    descripcion:
      'El ISR se calcula sobre la utilidad (ingresos menos costos deducibles: importación, repuestos, taller) y se paga además el ISO.',
  },
];

export type TipoTasa =
  | 'IVA_GENERAL'
  | 'ISR_SIMPLIFICADO_1'
  | 'ISR_SIMPLIFICADO_2'
  | 'ISR_UTILIDADES'
  | 'ISO'
  | 'UMBRAL_CF';

/** Qué lleva cada tipo al registrarse: porcentaje, monto límite o ambos. */
export const TIPOS_TASA: {
  valor: TipoTasa;
  etiqueta: string;
  porcentaje: boolean;
  monto: boolean;
}[] = [
  { valor: 'IVA_GENERAL', etiqueta: 'IVA general', porcentaje: true, monto: false },
  {
    valor: 'ISR_SIMPLIFICADO_1',
    etiqueta: 'ISR simplificado, primer tramo',
    porcentaje: true,
    monto: true,
  },
  {
    valor: 'ISR_SIMPLIFICADO_2',
    etiqueta: 'ISR simplificado, excedente',
    porcentaje: true,
    monto: false,
  },
  { valor: 'ISR_UTILIDADES', etiqueta: 'ISR sobre utilidades', porcentaje: true, monto: false },
  { valor: 'ISO', etiqueta: 'Impuesto de Solidaridad (ISO)', porcentaje: true, monto: false },
  {
    valor: 'UMBRAL_CF',
    etiqueta: 'Umbral para facturar a Consumidor Final',
    porcentaje: false,
    monto: true,
  },
];

export interface PerfilFiscal {
  id: number;
  vigente_desde: string;
  razon_social: string;
  nombre_comercial: string;
  /** Normalizado, sin guion; para mostrar se usa `nit_formateado`. */
  nit: string;
  nit_formateado: string;
  direccion_fiscal: string;
  establecimiento_sat: number;
  regimen_isr: RegimenISR;
  agente_retencion_iva: boolean;
  agente_retencion_isr: boolean;
  /** Tipos de tasa que aplican con este régimen; los calcula el servidor. */
  tasas_del_regimen: TipoTasa[];
  creado_en: string;
}

export interface PerfilFiscalEntrada {
  vigente_desde: string;
  razon_social: string;
  nombre_comercial: string;
  nit: string;
  direccion_fiscal: string;
  establecimiento_sat: number;
  regimen_isr: RegimenISR;
  agente_retencion_iva: boolean;
  agente_retencion_isr: boolean;
}

/** Tasa con vigencia. `tasa` es la fracción ("0.120000"); `porcentaje` ya viene listo para mostrar ("12"). */
export interface TasaImpositiva {
  id: number;
  tipo: TipoTasa;
  tasa: string | null;
  porcentaje: string | null;
  monto_limite: string | null;
  vigente_desde: string;
}

export interface TasaImpositivaEntrada {
  tipo: TipoTasa;
  vigente_desde: string;
  porcentaje?: string;
  monto_limite?: string;
}

@Injectable({ providedIn: 'root' })
export class ConfiguracionService {
  private readonly http = inject(HttpClient);
  private readonly urlTipos = `${API_URL}/configuracion/tipos-cambio`;
  private readonly urlTransacciones = `${API_URL}/configuracion/transacciones-usd`;
  private readonly urlPerfil = `${API_URL}/configuracion/perfil-fiscal`;
  private readonly urlTasas = `${API_URL}/configuracion/tasas-impositivas`;

  /** Versiones del perfil fiscal, de la más reciente a la más antigua. */
  historialPerfil(): Observable<PerfilFiscal[]> {
    return this.http.get<PerfilFiscal[]>(this.urlPerfil);
  }

  registrarPerfil(datos: PerfilFiscalEntrada): Observable<PerfilFiscal> {
    return this.http.post<PerfilFiscal>(this.urlPerfil, datos);
  }

  /** Historial de tasas, por tipo y de la más reciente a la más antigua. */
  tasas(): Observable<TasaImpositiva[]> {
    return this.http.get<TasaImpositiva[]>(this.urlTasas);
  }

  registrarTasa(datos: TasaImpositivaEntrada): Observable<TasaImpositiva> {
    return this.http.post<TasaImpositiva>(this.urlTasas, datos);
  }

  tiposCambio(): Observable<TipoCambio[]> {
    return this.http.get<TipoCambio[]>(this.urlTipos);
  }

  registrarTipoCambio(datos: TipoCambioEntrada): Observable<TipoCambio> {
    return this.http.post<TipoCambio>(this.urlTipos, datos);
  }

  transaccionesUSD(desde?: string, hasta?: string): Observable<TransaccionUSD[]> {
    const params: Record<string, string> = {};
    if (desde) params['desde'] = desde;
    if (hasta) params['hasta'] = hasta;
    return this.http.get<TransaccionUSD[]>(this.urlTransacciones, { params });
  }

  registrarTransaccionUSD(datos: TransaccionUSDEntrada): Observable<TransaccionUSD> {
    return this.http.post<TransaccionUSD>(this.urlTransacciones, datos);
  }
}
