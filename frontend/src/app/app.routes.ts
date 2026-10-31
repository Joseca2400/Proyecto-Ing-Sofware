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
    ],
  },
  { path: '**', redirectTo: '' },
];
