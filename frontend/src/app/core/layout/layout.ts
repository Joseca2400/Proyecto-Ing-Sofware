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
    { etiqueta: 'Mockup del proyecto', ruta: '/mockup' },
    { etiqueta: 'Proveedores', ruta: '/compras/proveedores' },
    { etiqueta: 'Facturas de compras', ruta: '/compras/facturas' },
    { etiqueta: 'Taller' },
    { etiqueta: 'Unidades', ruta: '/unidades' },
    { etiqueta: 'Contabilidad', ruta: '/contabilidad/partidas' },
    { etiqueta: 'Catálogo de cuentas', ruta: '/configuracion/catalogo' },
    { etiqueta: 'Reportes' },
    { etiqueta: 'Tipo de cambio', ruta: '/configuracion/tipo-cambio' },
    { etiqueta: 'Transacciones USD', ruta: '/configuracion/transacciones-usd' },
  ];
}
