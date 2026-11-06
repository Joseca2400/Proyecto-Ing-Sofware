import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';

// ── HU-4.01: proveedores ───────────────────────────────────────────────────────

export type TipoProveedor = 'local' | 'exterior';

export type RubroProveedor =
  | 'subasta'
  | 'dealer'
  | 'naviera'
  | 'agente_aduanal'
  | 'repuestos'
  | 'seguros'
  | 'servicios'
  | 'otros';

export const RUBROS: { valor: RubroProveedor; etiqueta: string }[] = [
  { valor: 'subasta', etiqueta: 'Subasta' },
  { valor: 'dealer', etiqueta: 'Dealer' },
  { valor: 'naviera', etiqueta: 'Naviera' },
  { valor: 'agente_aduanal', etiqueta: 'Agente aduanal' },
  { valor: 'repuestos', etiqueta: 'Repuestos' },
  { valor: 'seguros', etiqueta: 'Seguros' },
  { valor: 'servicios', etiqueta: 'Servicios' },
  { valor: 'otros', etiqueta: 'Otros' },
];

export interface Proveedor {
  id: number;
  tipo: TipoProveedor;
  nombre: string;
  /** Normalizado, sin guion ("12345679"); para mostrar se usa `nit_formateado`. */
  nit: string | null;
  nit_formateado: string | null;
  identificacion_fiscal: string | null;
  pais: string | null;
  rubro: RubroProveedor;
  moneda_habitual: 'GTQ' | 'USD';
  dias_credito: number;
  banco: string | null;
  cuenta_bancaria: string | null;
  creado_en: string;
}

export interface ProveedorEntrada {
  tipo: TipoProveedor;
  nombre: string;
  nit?: string;
  identificacion_fiscal?: string;
  pais?: string;
  rubro: RubroProveedor;
  moneda_habitual: 'GTQ' | 'USD';
  dias_credito: number;
  banco?: string;
  cuenta_bancaria?: string;
}

export interface FiltroProveedores {
  tipo?: TipoProveedor;
  rubro?: RubroProveedor;
  buscar?: string;
}

@Injectable({ providedIn: 'root' })
export class ComprasService {
  private readonly http = inject(HttpClient);
  private readonly urlProveedores = `${API_URL}/compras/proveedores`;

  proveedores(filtro: FiltroProveedores = {}): Observable<Proveedor[]> {
    const params: Record<string, string> = {};
    if (filtro.tipo) params['tipo'] = filtro.tipo;
    if (filtro.rubro) params['rubro'] = filtro.rubro;
    if (filtro.buscar) params['buscar'] = filtro.buscar;
    return this.http.get<Proveedor[]>(this.urlProveedores, { params });
  }

  registrarProveedor(datos: ProveedorEntrada): Observable<Proveedor> {
    return this.http.post<Proveedor>(this.urlProveedores, datos);
  }
}
