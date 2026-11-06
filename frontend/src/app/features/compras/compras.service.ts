import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';

// ── HU-4.01: proveedores ───────────────────────────────────────────────────────

export type TipoProveedor = 'local' | 'exterior';

export type RegimenProveedor = 'general' | 'pequeno_contribuyente';

export const REGIMENES: { valor: RegimenProveedor; etiqueta: string }[] = [
  { valor: 'general', etiqueta: 'General' },
  { valor: 'pequeno_contribuyente', etiqueta: 'Pequeño contribuyente' },
];

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
  /** Régimen de IVA; solo los proveedores locales lo tienen. */
  regimen: RegimenProveedor | null;
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
  regimen?: RegimenProveedor;
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

// ── HU-4.09: facturas de compras y gastos locales ─────────────────────────────

export type LineaNegocio = 'alquiler' | 'venta' | 'taller' | 'financiamiento' | 'administracion';

export const LINEAS_NEGOCIO: { valor: LineaNegocio; etiqueta: string }[] = [
  { valor: 'alquiler', etiqueta: 'Alquiler' },
  { valor: 'venta', etiqueta: 'Venta' },
  { valor: 'taller', etiqueta: 'Taller' },
  { valor: 'financiamiento', etiqueta: 'Financiamiento' },
  { valor: 'administracion', etiqueta: 'Administración' },
];

/** Los montos viajan como texto ("1250.00"); el front no los suma, solo les da formato. */
export interface LineaFacturaEntrada {
  descripcion: string;
  cuenta: string;
  linea_negocio: LineaNegocio;
  vin?: string;
  base: string;
  iva: string;
}

export interface FacturaCompraEntrada {
  proveedor_id: number;
  serie: string;
  numero: string;
  autorizacion: string;
  fecha: string;
  lineas: LineaFacturaEntrada[];
}

export interface LineaFactura {
  numero_linea: number;
  descripcion: string;
  cuenta: string;
  linea_negocio: LineaNegocio;
  vin: string | null;
  base: string;
  iva: string;
}

export interface CuentaPorPagar {
  id: number;
  fecha: string;
  fecha_vencimiento: string;
  moneda: 'GTQ' | 'USD';
  monto: string;
  saldo: string;
}

export interface FacturaCompra {
  id: number;
  proveedor: {
    id: number;
    nombre: string;
    nit: string | null;
    nit_formateado: string | null;
    regimen: RegimenProveedor | null;
  };
  serie: string;
  numero: string;
  autorizacion: string;
  fecha: string;
  regimen_proveedor: RegimenProveedor;
  genera_credito_fiscal: boolean;
  total_base: string;
  total_iva: string;
  credito_fiscal: string;
  total: string;
  lineas: LineaFactura[];
  cuenta_por_pagar: CuentaPorPagar;
  creado_en: string;
}

@Injectable({ providedIn: 'root' })
export class ComprasService {
  private readonly http = inject(HttpClient);
  private readonly urlProveedores = `${API_URL}/compras/proveedores`;
  private readonly urlFacturas = `${API_URL}/compras/facturas`;

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

  facturas(proveedorId?: number): Observable<FacturaCompra[]> {
    const params: Record<string, string> = {};
    if (proveedorId) params['proveedor_id'] = String(proveedorId);
    return this.http.get<FacturaCompra[]>(this.urlFacturas, { params });
  }

  registrarFactura(datos: FacturaCompraEntrada): Observable<FacturaCompra> {
    return this.http.post<FacturaCompra>(this.urlFacturas, datos);
  }
}
