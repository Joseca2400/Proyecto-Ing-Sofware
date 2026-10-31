import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '../../core/api/api';
import { EstadoSistema } from './estado-sistema';

@Injectable({ providedIn: 'root' })
export class InicioService {
  private readonly http = inject(HttpClient);

  estadoSistema(): Observable<EstadoSistema> {
    return this.http.get<EstadoSistema>(`${API_URL}/sistema/estado`);
  }
}
