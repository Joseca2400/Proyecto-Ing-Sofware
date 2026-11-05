import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';

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

@Injectable({ providedIn: 'root' })
export class ConfiguracionService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_URL}/configuracion/tipos-cambio`;

  tiposCambio(): Observable<TipoCambio[]> {
    return this.http.get<TipoCambio[]>(this.url);
  }

  registrarTipoCambio(datos: TipoCambioEntrada): Observable<TipoCambio> {
    return this.http.post<TipoCambio>(this.url, datos);
  }
}
