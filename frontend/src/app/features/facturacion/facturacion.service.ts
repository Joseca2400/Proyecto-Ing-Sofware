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

  facturas(): Observable<Factura[]> {
    return this.http.get<Factura[]>(`${this.url}/facturas`);
  }

  emitirFactura(entrada: FacturaEntrada): Observable<Factura> {
    return this.http.post<Factura>(`${this.url}/facturas`, entrada);
  }
}

// ── HU-6.02: facturas FEL ──────────────────────────────────────────────────────

export type Factura = components['schemas']['FacturaSalida'];
export type FacturaEntrada = components['schemas']['FacturaEntrada'];

// Líneas de negocio con regla de ingreso para la factura (las demás las rechaza el servidor).
export const LINEAS_FACTURA = [
  { valor: 'alquiler', etiqueta: 'Alquiler' },
  { valor: 'venta', etiqueta: 'Venta' },
  { valor: 'taller', etiqueta: 'Taller' },
] as const;
