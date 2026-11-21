import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';
import { EstadoSistema } from './estado-sistema';

type Esquemas = components['schemas'];
export type UnidadTablero = Pick<Esquemas['UnidadSalida'], 'id' | 'estado'>;
export type ContratoTablero = Pick<Esquemas['ContratoSalida'], 'id'>;
export type OrdenTablero = Pick<Esquemas['OrdenSalida'], 'id'>;
export type PartidaTablero = Pick<Esquemas['PartidaSalida'], 'id'>;
export type CuentaPorPagarTablero = Pick<
  Esquemas['CuentaPorPagarPendiente'],
  'id' | 'dias_vencida'
>;
export type PagoPorEjecutarTablero = Pick<Esquemas['PagoProgramadoSalida'], 'id'>;
export type TipoCambioTablero = Pick<Esquemas['TipoCambioSalida'], 'fecha' | 'valor' | 'origen'>;
export type DepositosTablero = Pick<
  Esquemas['DepositosVigentes'],
  'depositos' | 'totales' | 'cuadra'
>;
export type UnidadesEtapaTablero = Pick<
  Esquemas['ReporteUnidadesEtapa'],
  'limite_dias' | 'valor_total' | 'unidades'
>;

/**
 * Datos del tablero de inicio. Solo usa endpoints que ya existen y solo los consulta la pantalla
 * cuando el rol tiene la pantalla de destino; el servidor aplica los permisos de todas formas.
 * Los montos llegan como texto y se muestran tal cual (con `MontoPipe`): aquí no se suma nada.
 */
@Injectable({ providedIn: 'root' })
export class InicioService {
  private readonly http = inject(HttpClient);

  estadoSistema(): Observable<EstadoSistema> {
    return this.http.get<EstadoSistema>(`${API_URL}/sistema/estado`);
  }

  unidades(): Observable<UnidadTablero[]> {
    return this.http.get<UnidadTablero[]>(`${API_URL}/unidades`);
  }

  contratosAbiertos(): Observable<ContratoTablero[]> {
    return this.http.get<ContratoTablero[]>(`${API_URL}/alquileres/contratos`, {
      params: { estado: 'abierto' },
    });
  }

  ordenesAbiertas(): Observable<OrdenTablero[]> {
    return this.http.get<OrdenTablero[]>(`${API_URL}/taller/ordenes`, {
      params: { estado: 'abierta' },
    });
  }

  partidas(estado: 'en_revision' | 'devuelta'): Observable<PartidaTablero[]> {
    return this.http.get<PartidaTablero[]>(`${API_URL}/contabilidad/partidas`, {
      params: { estado },
    });
  }

  cuentasPorPagar(): Observable<CuentaPorPagarTablero[]> {
    return this.http.get<CuentaPorPagarTablero[]>(`${API_URL}/compras/cuentas-por-pagar`);
  }

  pagosPorEjecutar(): Observable<PagoPorEjecutarTablero[]> {
    return this.http.get<PagoPorEjecutarTablero[]>(`${API_URL}/compras/pagos-por-ejecutar`);
  }

  /** Los del último mes, del más reciente al más antiguo (así los ordena el servidor). */
  tiposCambio(desde: string): Observable<TipoCambioTablero[]> {
    return this.http.get<TipoCambioTablero[]>(`${API_URL}/configuracion/tipos-cambio`, {
      params: { desde },
    });
  }

  depositos(): Observable<DepositosTablero> {
    return this.http.get<DepositosTablero>(`${API_URL}/alquileres/depositos`);
  }

  unidadesPorEtapa(): Observable<UnidadesEtapaTablero> {
    return this.http.get<UnidadesEtapaTablero>(`${API_URL}/reportes/unidades-por-etapa`);
  }
}
