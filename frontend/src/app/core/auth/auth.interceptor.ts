import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { API_URL } from '../api/api';
import { AuthService } from './auth.service';

/** Agrega el token a las llamadas a la API y vuelve a pedir la sesión cuando el servidor la rechaza. */
export const authInterceptor: HttpInterceptorFn = (peticion, siguiente) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.token();
  const conToken =
    token && peticion.url.startsWith(API_URL)
      ? peticion.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : peticion;
  return siguiente(conToken).pipe(
    catchError((error: HttpErrorResponse) => {
      // 401 fuera del login: la sesión venció o se cerró en el servidor.
      if (error.status === 401 && !peticion.url.endsWith('/seguridad/login')) {
        auth.olvidar();
        void router.navigate(['/entrar']);
      }
      return throwError(() => error);
    }),
  );
};
