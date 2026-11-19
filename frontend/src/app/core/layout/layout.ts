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
  // Un título sin entradas visibles para el rol tampoco se muestra.
  protected readonly menu = computed(() => {
    const visibles = this.entradas.filter(
      (entrada) => !entrada.ruta || this.auth.tieneRol(this.rolesPorRuta.get(entrada.ruta)),
    );
    return visibles.filter((entrada, i) => entrada.ruta || visibles[i + 1]?.ruta);
  });

  // Una entrada sin ruta es el título de su grupo; los grupos siguen el recorrido de la unidad.
  private readonly entradas: EntradaMenu[] = [
    { etiqueta: 'Inicio', ruta: '/inicio' },
    { etiqueta: 'Compras e importación' },
    { etiqueta: 'Proveedores', ruta: '/compras/proveedores' },
    { etiqueta: 'Compra en EE. UU.', ruta: '/compras/compra-unidades' },
    { etiqueta: 'Gastos de importación', ruta: '/compras/gastos-importacion' },
    { etiqueta: 'Facturas de compras', ruta: '/compras/facturas' },
    { etiqueta: 'Hoja de costo', ruta: '/compras/hoja-costo' },
    { etiqueta: 'Unidades y flota' },
    { etiqueta: 'Unidades', ruta: '/unidades' },
    { etiqueta: 'Etapas de importación', ruta: '/unidades/etapas-importacion' },
    { etiqueta: 'Órdenes de taller', ruta: '/taller/ordenes' },
    { etiqueta: 'Tarifas de taller', ruta: '/taller/tarifas' },
    { etiqueta: 'Alta en flota', ruta: '/unidades/alta-flota' },
    { etiqueta: 'Depreciación', ruta: '/unidades/depreciacion' },
    { etiqueta: 'Fin de vida útil', ruta: '/unidades/fin-vida-util' },
    { etiqueta: 'Alquiler y facturación' },
    { etiqueta: 'Clientes', ruta: '/facturacion/clientes' },
    { etiqueta: 'Tarifario', ruta: '/alquileres/tarifario' },
    { etiqueta: 'Contratos', ruta: '/alquileres/contratos' },
    { etiqueta: 'Depósitos en garantía', ruta: '/alquileres/depositos' },
    { etiqueta: 'Facturas', ruta: '/facturacion/facturas' },
    { etiqueta: 'Contabilidad' },
    { etiqueta: 'Partidas', ruta: '/contabilidad/partidas' },
    { etiqueta: 'Balance de comprobación', ruta: '/contabilidad/balance' },
    { etiqueta: 'Mayor', ruta: '/contabilidad/mayor' },
    { etiqueta: 'Cierre de mes', ruta: '/contabilidad/cierre-mes' },
    { etiqueta: 'Reglas de contabilización', ruta: '/contabilidad/reglas' },
    { etiqueta: 'Catálogo de cuentas', ruta: '/configuracion/catalogo' },
    { etiqueta: 'Reportes' },
    { etiqueta: 'Unidades por etapa', ruta: '/reportes/unidades-etapa' },
    { etiqueta: 'Rentabilidad', ruta: '/reportes/rentabilidad' },
    { etiqueta: 'Configuración' },
    { etiqueta: 'Tipo de cambio', ruta: '/configuracion/tipo-cambio' },
    { etiqueta: 'Transacciones USD', ruta: '/configuracion/transacciones-usd' },
    { etiqueta: 'Cuentas bancarias', ruta: '/configuracion/cuentas-bancarias' },
    { etiqueta: 'Perfil fiscal', ruta: '/configuracion/perfil-fiscal' },
    { etiqueta: 'Usuarios', ruta: '/seguridad/usuarios' },
    { etiqueta: 'Bitácora', ruta: '/seguridad/bitacora' },
    { etiqueta: 'Mockup del proyecto', ruta: '/mockup' },
  ];

  protected salir(): void {
    this.auth.salir();
    void this.router.navigate(['/entrar']);
  }
}
