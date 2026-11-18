import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { components } from '../../core/api/esquema';

// ── HU-6.01: clientes ──────────────────────────────────────────────────────────

export type Cliente = components['schemas']['ClienteSalida'];
export type ClienteEntrada = components['schemas']['ClienteEntrada'];
export type TipoIdentificacion = Cliente['tipo_identificacion'];

@Injectable({ providedIn: 'root' })
export class FacturacionService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/facturacion`;

  clientes(buscar?: string): Observable<Cliente[]> {
    return this.http.get<Cliente[]>(`${this.url}/clientes`, {
      params: buscar ? { buscar } : {},
    });
  }

  registrarCliente(entrada: ClienteEntrada): Observable<Cliente> {
    return this.http.post<Cliente>(`${this.url}/clientes`, entrada);
  }
}
