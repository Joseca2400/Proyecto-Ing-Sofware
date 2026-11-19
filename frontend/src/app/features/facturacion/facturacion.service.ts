import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';

// ── HU-6.01: clientes ──────────────────────────────────────────────────────────

export type TipoCliente = 'individual' | 'empresa';

export interface Cliente {
  id: number;
  tipo: TipoCliente;
  nombre: string;
  /** Normalizado, sin guion ("12345679"); para mostrar se usa `nit_formateado`. */
  nit: string | null;
  nit_formateado: string | null;
  cui: string | null;
  /** Solo los extranjeros: pasaporte y país (código de dos letras) van juntos. */
  pasaporte: string | null;
  pais: string | null;
  direccion: string | null;
  telefono: string | null;
  correo: string | null;
  agente_retencion_iva: boolean;
  agente_retencion_isr: boolean;
  creado_en: string;
}

export interface ClienteEntrada {
  tipo: TipoCliente;
  nombre: string;
  nit?: string;
  cui?: string;
  pasaporte?: string;
  pais?: string;
  direccion?: string;
  telefono?: string;
  correo?: string;
  agente_retencion_iva: boolean;
  agente_retencion_isr: boolean;
}

export interface FiltroClientes {
  tipo?: TipoCliente;
  buscar?: string;
}

@Injectable({ providedIn: 'root' })
export class FacturacionService {
  private readonly http = inject(HttpClient);
  private readonly urlClientes = `${API_URL}/facturacion/clientes`;

  clientes(filtro: FiltroClientes = {}): Observable<Cliente[]> {
    const params: Record<string, string> = {};
    if (filtro.tipo) params['tipo'] = filtro.tipo;
    if (filtro.buscar) params['buscar'] = filtro.buscar;
    return this.http.get<Cliente[]>(this.urlClientes, { params });
  }

  registrarCliente(datos: ClienteEntrada): Observable<Cliente> {
    return this.http.post<Cliente>(this.urlClientes, datos);
  }
}
