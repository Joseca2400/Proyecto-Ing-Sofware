import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

// ── HU-1.02 y HU-1.04: catálogo de cuentas y dimensiones ──────────────────────

export type Cuenta = components['schemas']['CuentaSalida'];
export type CuentaEntrada = components['schemas']['CuentaEntrada'];
export type DimensionesEntrada = components['schemas']['DimensionesEntrada'];

export const ETIQUETAS_LINEA: Record<string, string> = {
  alquiler: 'Alquiler',
  venta: 'Venta',
  taller: 'Taller',
  financiamiento: 'Financiamiento',
  administracion: 'Administración',
};

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

export type PerfilFiscal = components['schemas']['PerfilFiscalSalida'];
export type PerfilFiscalEntrada = components['schemas']['PerfilFiscalEntrada'];

export const ETIQUETAS_REGIMEN_ISR: Record<string, string> = {
  utilidades: 'Sobre utilidades',
  simplificado: 'Opcional simplificado',
};

// ── HU-1.08: cuentas bancarias ────────────────────────────────────────────────

export type CuentaBancaria = components['schemas']['CuentaBancariaSalida'];
export type CuentaBancariaEntrada = components['schemas']['CuentaBancariaEntrada'];

@Injectable({ providedIn: 'root' })
export class ConfiguracionService {
  private readonly http = inject(HttpClient);
  private readonly urlTipos = `${API_URL}/configuracion/tipos-cambio`;
  private readonly urlTransacciones = `${API_URL}/configuracion/transacciones-usd`;
  private readonly urlCuentas = `${API_URL}/configuracion/cuentas`;

  cuentas(): Observable<Cuenta[]> {
    return this.http.get<Cuenta[]>(this.urlCuentas);
  }

  lineasNegocio(): Observable<string[]> {
    return this.http.get<string[]>(`${API_URL}/configuracion/lineas-negocio`);
  }

  crearCuenta(datos: CuentaEntrada): Observable<Cuenta> {
    return this.http.post<Cuenta>(this.urlCuentas, datos);
  }

  definirDimensiones(cuentaId: number, datos: DimensionesEntrada): Observable<Cuenta> {
    return this.http.put<Cuenta>(`${this.urlCuentas}/${cuentaId}/dimensiones`, datos);
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

  /** Perfil vigente hoy; responde 404 mientras no se haya registrado ninguno. */
  perfilFiscal(): Observable<PerfilFiscal> {
    return this.http.get<PerfilFiscal>(`${API_URL}/configuracion/perfil-fiscal`);
  }

  historialPerfilFiscal(): Observable<PerfilFiscal[]> {
    return this.http.get<PerfilFiscal[]>(`${API_URL}/configuracion/perfil-fiscal/historial`);
  }

  registrarPerfilFiscal(datos: PerfilFiscalEntrada): Observable<PerfilFiscal> {
    return this.http.post<PerfilFiscal>(`${API_URL}/configuracion/perfil-fiscal`, datos);
  }

  cuentasBancarias(): Observable<CuentaBancaria[]> {
    return this.http.get<CuentaBancaria[]>(`${API_URL}/configuracion/cuentas-bancarias`);
  }

  crearCuentaBancaria(datos: CuentaBancariaEntrada): Observable<CuentaBancaria> {
    return this.http.post<CuentaBancaria>(`${API_URL}/configuracion/cuentas-bancarias`, datos);
  }

  definirNumeracionCheques(id: number, siguiente: number | null): Observable<CuentaBancaria> {
    return this.http.put<CuentaBancaria>(
      `${API_URL}/configuracion/cuentas-bancarias/${id}/cheques`,
      {
        siguiente_cheque: siguiente,
      },
    );
  }

  cambiarEstadoCuentaBancaria(id: number, activa: boolean): Observable<CuentaBancaria> {
    const accion = activa ? 'activar' : 'inactivar';
    return this.http.post<CuentaBancaria>(
      `${API_URL}/configuracion/cuentas-bancarias/${id}/${accion}`,
      {},
    );
  }
}
