import { Routes } from '@angular/router';
import { Layout } from './core/layout/layout';

// Cada módulo de negocio se agrega como hijo del layout y se carga solo cuando se usa.
export const routes: Routes = [
  {
    path: 'mockup',
    title: 'Prototipo · Kilómetro Cero',
    loadComponent: () => import('./features/mockup/mockup').then((m) => m.Mockup),
  },
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
        path: 'unidades',
        title: 'Unidades · Kilómetro Cero',
        loadComponent: () => import('./features/unidades/unidades').then((m) => m.UnidadesPantalla),
      },
      {
        path: 'contabilidad/partidas',
        title: 'Partidas · Kilómetro Cero',
        loadComponent: () =>
          import('./features/contabilidad/partidas').then((m) => m.PartidasPantalla),
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
    ],
  },
  { path: '**', redirectTo: '' },
];
