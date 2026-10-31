import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

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
  // Los módulos sin ruta se muestran deshabilitados hasta que se construyan.
  protected readonly menu: EntradaMenu[] = [
    { etiqueta: 'Inicio', ruta: '/inicio' },
    { etiqueta: 'Compras' },
    { etiqueta: 'Taller' },
    { etiqueta: 'Unidades' },
    { etiqueta: 'Contabilidad' },
    { etiqueta: 'Reportes' },
  ];
}
