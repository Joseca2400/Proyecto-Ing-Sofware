import { Component, input } from '@angular/core';

const trazos: Record<string, string> = {
  panel: 'M3 3h7v7H3z M14 3h7v4h-7z M14 11h7v10h-7z M3 14h7v7H3z',
  auto: 'm5 7 2-4h10l2 4 M3 8h18v10H3z M6 18v3 M18 18v3 M6 12h2 M16 12h2 M3 8l-1-2 M21 8l1-2',
  barco: 'M4 15 8 19h8l4-4-8-3z M7 13V6h10v7 M10 6V3h4v3 M2 21q2-2 5 0t5 0t5 0t5 0',
  taller: 'm14 6-4 4 4 4 4-4 M14 6a6 6 0 0 1 7 7 6 6 0 0 1-7 5L7 22l-4-4 7-7a6 6 0 0 1 4-9z',
  contrato: 'M6 3h9l4 4v14H6z M14 3v5h5 M9 12h7 M9 16h5',
  factura: 'M5 3h14v18l-3-2-4 2-4-2-3 2z M8 8h8 M8 12h8 M8 16h4',
  libro: 'M12 5v16 M12 5Q7 2 3 4v15q4-2 9 2 5-4 9-2V4q-4-2-9 1',
  grafica: 'M4 3v18h17 M8 16v-5 M13 16V7 M18 16V4',
  venta: 'M3 3h8l11 11-8 8L3 11z M7 7h.01',
  cartera: 'M3 7h18v14H3z M3 7V4h15v3 M16 12h5v5h-5z',
  ajustes:
    'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1z',
  carga: 'M12 16V3 M7 8l5-5 5 5 M4 15v6h16v-6',
  buscar: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M15 15l6 6',
  flecha: 'M4 12h16 M14 6l6 6-6 6',
  mas: 'M12 5v14 M5 12h14',
  abajo: 'm7 10 5 5 5-5',
  reloj: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M12 7v5l3 2',
  check: 'm5 12 4 4L19 6',
  cerrar: 'm6 6 12 12 M6 18 18 6',
  descargar: 'M12 3v12 M7 10l5 5 5-5 M4 16v5h16v-5',
  calendario: 'M4 5h16v16H4z M4 10h16 M8 2v6 M16 2v6',
  escudo: 'm12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6z m-4 10 3 3 5-6',
  menu: 'M4 6h16 M4 12h16 M4 18h16',
  salir: 'M9 3H3v18h6 M9 12h12 M16 7l5 5-5 5',
};

@Component({
  selector: 'app-icono',
  template:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path [attr.d]="trazos[nombre()] || trazos[\'panel\']" /></svg>',
  styles:
    ':host { display: inline-flex; width: 20px; height: 20px; flex-shrink: 0; } svg { width: 100%; height: 100%; }',
})
export class Icono {
  readonly nombre = input('panel');
  protected readonly trazos = trazos;
}
