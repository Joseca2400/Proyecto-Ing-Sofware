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
export type CierreContratoEntrada = components['schemas']['CierreContratoEntrada'];

// ── HU-3.07: depósitos en garantía ─────────────────────────────────────────────

export type Deposito = components['schemas']['DepositoSalida'];
export type DepositoEntrada = components['schemas']['DepositoEntrada'];
export type AplicacionEntrada = components['schemas']['AplicacionEntrada'];
export type DevolucionEntrada = components['schemas']['DevolucionDepositoEntrada'];
export type DepositosVigentes = components['schemas']['DepositosVigentes'];
export type FacturaContrato = components['schemas']['FacturaSalida'];
export type CuentaBancaria = components['schemas']['CuentaBancariaSalida'];

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

  cerrarContrato(id: number, entrada: CierreContratoEntrada): Observable<Contrato> {
    return this.http.post<Contrato>(`${API_URL}/alquileres/contratos/${id}/cierre`, entrada);
  }

  /** HU-6.02: emite la factura FEL del cobro de un contrato cerrado. */
  facturarContrato(id: number): Observable<FacturaContrato> {
    return this.http.post<FacturaContrato>(`${API_URL}/alquileres/contratos/${id}/factura`, {});
  }

  depositosDeContrato(id: number): Observable<Deposito[]> {
    return this.http.get<Deposito[]>(`${API_URL}/alquileres/contratos/${id}/depositos`);
  }

  recibirDeposito(id: number, entrada: DepositoEntrada): Observable<Deposito> {
    return this.http.post<Deposito>(`${API_URL}/alquileres/contratos/${id}/depositos`, entrada);
  }

  aplicarDeposito(id: number, entrada: AplicacionEntrada): Observable<Deposito> {
    return this.http.post<Deposito>(`${API_URL}/alquileres/depositos/${id}/aplicacion`, entrada);
  }

  devolverDeposito(id: number, entrada: DevolucionEntrada): Observable<Deposito> {
    return this.http.post<Deposito>(`${API_URL}/alquileres/depositos/${id}/devolucion`, entrada);
  }

  depositosVigentes(): Observable<DepositosVigentes> {
    return this.http.get<DepositosVigentes>(`${API_URL}/alquileres/depositos`);
  }

  cuentasBancarias(): Observable<CuentaBancaria[]> {
    return this.http.get<CuentaBancaria[]>(`${API_URL}/configuracion/cuentas-bancarias`, {
      params: { solo_activas: true },
    });
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
