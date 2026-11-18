import { Routes } from '@angular/router';
import { conSesion, soloRoles } from './core/auth/auth.guard';
import { Layout } from './core/layout/layout';

// Cada módulo de negocio se agrega como hijo del layout y se carga solo cuando se usa. Todo lo que
// cuelga del layout exige sesión; una ruta con `data: soloRoles(...)` solo la ven esos roles (y el
// menú la oculta a los demás). El servidor aplica los permisos de todas formas.
export const routes: Routes = [
  {
    path: 'mockup',
    title: 'Prototipo · Kilómetro Cero',
    loadComponent: () => import('./features/mockup/mockup').then((m) => m.Mockup),
  },
  {
    path: 'entrar',
    title: 'Iniciar sesión · Kilómetro Cero',
    loadComponent: () => import('./core/auth/entrar').then((m) => m.Entrar),
  },
  {
    path: '',
    component: Layout,
    canActivate: [conSesion],
    canActivateChild: [conSesion],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      {
        path: 'inicio',
        title: 'Inicio · Kilómetro Cero',
        loadComponent: () => import('./features/inicio/inicio').then((m) => m.Inicio),
      },
      {
        path: 'seguridad/bitacora',
        title: 'Bitácora · Kilómetro Cero',
        data: soloRoles('contador', 'gerente_financiero'),
        loadComponent: () =>
          import('./features/seguridad/bitacora').then((m) => m.BitacoraPantalla),
      },
      {
        path: 'compras/proveedores',
        title: 'Proveedores · Kilómetro Cero',
        loadComponent: () =>
          import('./features/compras/proveedores').then((m) => m.ProveedoresPantalla),
      },
      {
        path: 'compras/facturas',
        title: 'Facturas de compras · Kilómetro Cero',
        loadComponent: () =>
          import('./features/compras/facturas').then((m) => m.FacturasComprasPantalla),
      },
      {
        path: 'compras/compra-unidades',
        title: 'Compra en EE. UU. · Kilómetro Cero',
        loadComponent: () =>
          import('./features/compras/compra-unidad').then((m) => m.CompraUnidadPantalla),
      },
      {
        path: 'compras/gastos-importacion',
        title: 'Gastos de importación · Kilómetro Cero',
        loadComponent: () =>
          import('./features/compras/gastos-importacion').then((m) => m.GastosImportacionPantalla),
      },
      {
        path: 'facturacion/clientes',
        title: 'Clientes · Kilómetro Cero',
        loadComponent: () =>
          import('./features/facturacion/clientes').then((m) => m.ClientesPantalla),
      },
      {
        path: 'facturacion/facturas',
        title: 'Facturas · Kilómetro Cero',
        loadComponent: () =>
          import('./features/facturacion/facturas').then((m) => m.FacturasPantalla),
      },
      {
        path: 'alquileres/tarifario',
        title: 'Tarifario · Kilómetro Cero',
        loadComponent: () =>
          import('./features/alquileres/tarifario').then((m) => m.TarifarioPantalla),
      },
      {
        path: 'taller/ordenes',
        title: 'Órdenes de taller · Kilómetro Cero',
        loadComponent: () =>
          import('./features/taller/ordenes').then((m) => m.OrdenesTallerPantalla),
      },
      {
        path: 'taller/tarifas',
        title: 'Tarifas de taller · Kilómetro Cero',
        loadComponent: () =>
          import('./features/taller/tarifas').then((m) => m.TarifasTallerPantalla),
      },
      {
        path: 'unidades',
        title: 'Unidades · Kilómetro Cero',
        loadComponent: () => import('./features/unidades/unidades').then((m) => m.UnidadesPantalla),
      },
      {
        path: 'unidades/etapas-importacion',
        title: 'Etapas de importación · Kilómetro Cero',
        data: soloRoles('gerente_financiero', 'contador', 'gerencia'),
        loadComponent: () =>
          import('./features/unidades/etapas-importacion').then((m) => m.EtapasImportacionPantalla),
      },
      {
        path: 'contabilidad/partidas',
        title: 'Partidas · Kilómetro Cero',
        loadComponent: () =>
          import('./features/contabilidad/partidas').then((m) => m.PartidasPantalla),
      },
      {
        path: 'contabilidad/reglas',
        title: 'Reglas de contabilización · Kilómetro Cero',
        data: soloRoles('contador', 'gerente_financiero'),
        loadComponent: () => import('./features/contabilidad/reglas').then((m) => m.ReglasPantalla),
      },
      {
        path: 'contabilidad/balance',
        title: 'Balance de comprobación · Kilómetro Cero',
        data: soloRoles('contador', 'gerente_financiero', 'gerencia'),
        loadComponent: () =>
          import('./features/contabilidad/balance').then((m) => m.BalancePantalla),
      },
      {
        path: 'contabilidad/mayor',
        title: 'Mayor · Kilómetro Cero',
        data: soloRoles('contador', 'gerente_financiero', 'gerencia'),
        loadComponent: () => import('./features/contabilidad/mayor').then((m) => m.MayorPantalla),
      },
      {
        path: 'configuracion/catalogo',
        title: 'Catálogo de cuentas · Kilómetro Cero',
        loadComponent: () =>
          import('./features/configuracion/catalogo').then((m) => m.CatalogoPantalla),
      },
      {
        path: 'configuracion/tipo-cambio',
        title: 'Tipo de cambio · Kilómetro Cero',
        loadComponent: () =>
          import('./features/configuracion/tipo-cambio').then((m) => m.TipoCambioPantalla),
      },
      {
        path: 'configuracion/transacciones-usd',
        title: 'Transacciones en USD · Kilómetro Cero',
        loadComponent: () =>
          import('./features/configuracion/transaccion-usd').then((m) => m.TransaccionUSDPantalla),
      },
      {
        path: 'configuracion/perfil-fiscal',
        title: 'Perfil fiscal · Kilómetro Cero',
        loadComponent: () =>
          import('./features/configuracion/perfil-fiscal').then((m) => m.PerfilFiscalPantalla),
      },
      {
        path: 'configuracion/cuentas-bancarias',
        title: 'Cuentas bancarias · Kilómetro Cero',
        loadComponent: () =>
          import('./features/configuracion/cuentas-bancarias').then(
            (m) => m.CuentasBancariasPantalla,
          ),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
