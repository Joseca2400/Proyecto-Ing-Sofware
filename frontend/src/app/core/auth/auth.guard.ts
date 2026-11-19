import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService, Rol } from './auth.service';

/** `data` de una ruta que solo ven ciertos roles; el menú la oculta a los demás. */
export const soloRoles = (...roles: Rol[]) => ({ roles });

/** Exige sesión y, si la ruta declara `data.roles`, uno de esos roles. */
export const conSesion: CanActivateFn = (ruta) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.usuario()) return router.createUrlTree(['/entrar']);
  return auth.tieneRol(ruta.data['roles']) || router.createUrlTree(['/inicio']);
};
