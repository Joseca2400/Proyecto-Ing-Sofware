import { Routes } from '@angular/router';
import { Layout } from './core/layout/layout';

// Cada módulo de negocio se agrega como hijo del layout y se carga solo cuando se usa.
export const routes: Routes = [
  {
    path: '',
    component: Layout,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      {
        path: 'inicio',
        title: 'Inicio · Kilómetro Cero',
        loadComponent: () => import('./features/inicio/inicio').then((m) => m.Inicio),
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
        path: 'facturacion/clientes',
        title: 'Registrar cliente · Kilómetro Cero',
        loadComponent: () =>
          import('./features/facturacion/registro-cliente').then((m) => m.RegistroClientePantalla),
      },
      {
        path: 'configuracion/perfil-fiscal',
        title: 'Perfil fiscal · Kilómetro Cero',
        loadComponent: () =>
          import('./features/configuracion/perfil-fiscal').then((m) => m.PerfilFiscalPantalla),
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
    ],
  },
  { path: '**', redirectTo: '' },
];
