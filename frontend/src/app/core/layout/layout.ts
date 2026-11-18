import { Component, computed, inject } from '@angular/core';
import {
  ActivatedRoute,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { AuthService, NOMBRE_ROL } from '../auth/auth.service';

interface EntradaMenu {
  etiqueta: string;
  ruta?: string;
}

@Component({
  selector: 'app-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './layout.html',
  styleUrl: './layout.css',
})
export class Layout {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  // Los roles de cada pantalla se declaran una sola vez, en `data` de su ruta (app.routes.ts).
  private readonly rolesPorRuta = new Map<string, string[] | undefined>(
    (inject(ActivatedRoute).routeConfig?.children ?? []).map((hija) => [
      `/${hija.path}`,
      hija.data?.['roles'],
    ]),
  );

  protected readonly usuario = this.auth.usuario;
  protected readonly rol = computed(() => NOMBRE_ROL[this.usuario()?.rol ?? ''] ?? '');
  protected readonly menu = computed(() =>
    this.entradas.filter(
      (entrada) => !entrada.ruta || this.auth.tieneRol(this.rolesPorRuta.get(entrada.ruta)),
    ),
  );

  // Los módulos sin ruta se muestran deshabilitados hasta que se construyan.
  private readonly entradas: EntradaMenu[] = [
    { etiqueta: 'Inicio', ruta: '/inicio' },
    { etiqueta: 'Bitácora', ruta: '/seguridad/bitacora' },
    { etiqueta: 'Mockup del proyecto', ruta: '/mockup' },
    { etiqueta: 'Proveedores', ruta: '/compras/proveedores' },
    { etiqueta: 'Facturas de compras', ruta: '/compras/facturas' },
    { etiqueta: 'Compra en EE. UU.', ruta: '/compras/compra-unidades' },
    { etiqueta: 'Gastos de importación', ruta: '/compras/gastos-importacion' },
    { etiqueta: 'Clientes', ruta: '/facturacion/clientes' },
    { etiqueta: 'Facturas', ruta: '/facturacion/facturas' },
    { etiqueta: 'Tarifario', ruta: '/alquileres/tarifario' },
    { etiqueta: 'Contratos', ruta: '/alquileres/contratos' },
    { etiqueta: 'Depósitos en garantía', ruta: '/alquileres/depositos' },
    { etiqueta: 'Órdenes de taller', ruta: '/taller/ordenes' },
    { etiqueta: 'Tarifas de taller', ruta: '/taller/tarifas' },
    { etiqueta: 'Unidades', ruta: '/unidades' },
    { etiqueta: 'Etapas de importación', ruta: '/unidades/etapas-importacion' },
    { etiqueta: 'Contabilidad', ruta: '/contabilidad/partidas' },
    { etiqueta: 'Reglas de contabilización', ruta: '/contabilidad/reglas' },
    { etiqueta: 'Balance de comprobación', ruta: '/contabilidad/balance' },
    { etiqueta: 'Mayor', ruta: '/contabilidad/mayor' },
    { etiqueta: 'Catálogo de cuentas', ruta: '/configuracion/catalogo' },
    { etiqueta: 'Reportes' },
    { etiqueta: 'Tipo de cambio', ruta: '/configuracion/tipo-cambio' },
    { etiqueta: 'Transacciones USD', ruta: '/configuracion/transacciones-usd' },
    { etiqueta: 'Perfil fiscal', ruta: '/configuracion/perfil-fiscal' },
    { etiqueta: 'Cuentas bancarias', ruta: '/configuracion/cuentas-bancarias' },
  ];

  protected salir(): void {
    this.auth.salir();
    void this.router.navigate(['/entrar']);
  }
}
