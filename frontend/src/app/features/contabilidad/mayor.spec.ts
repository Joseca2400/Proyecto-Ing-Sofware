import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { MayorPantalla } from './mayor';

const CUENTAS = [
  {
    id: 12,
    codigo: '1.1.01.03',
    nombre: 'Bancos en dólares',
    es_detalle: true,
    nivel: 4,
    padre_id: 1,
    tipo: 'activo',
    naturaleza: 'deudora',
    monetaria_usd: true,
  },
];
const MAYOR = {
  cuenta_id: 12,
  codigo: '1.1.01.03',
  nombre: 'Bancos en dólares',
  naturaleza: 'deudora',
  monetaria_usd: true,
  saldo_inicial: '100.000000',
  saldo_final: '875.000000',
  movimientos: [
    {
      fecha: '2026-02-05',
      partida_id: 5,
      numero: 2,
      concepto: 'Pago al proveedor',
      documento_tipo: 'compra_unidad',
      documento_id: '9',
      debe: '775.000000',
      haber: '0.000000',
      saldo: '875.000000',
      moneda: 'USD',
      monto_usd: '100.000000',
      tipo_cambio: '7.75000000',
      linea_negocio: 'administracion',
      vin: null,
    },
  ],
};

describe('MayorPantalla', () => {
  let http: HttpTestingController;

  function configurar(consulta: Record<string, string>): void {
    TestBed.configureTestingModule({
      imports: [MayorPantalla],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: convertToParamMap(consulta) } },
        },
      ],
    });
    http = TestBed.inject(HttpTestingController);
  }

  afterEach(() => http.verify());

  function catalogos(): void {
    http.expectOne((r) => r.url.endsWith('/configuracion/cuentas')).flush(CUENTAS);
    http.expectOne('/api/v1/configuracion/lineas-negocio').flush([]);
  }

  it('llega con la cuenta del balance y muestra saldos, USD y enlace a la partida', async () => {
    configurar({ cuenta: '12' });
    const fixture = TestBed.createComponent(MayorPantalla);
    catalogos();
    http.expectOne((r) => r.url === '/api/v1/contabilidad/mayor/12').flush(MAYOR);
    await fixture.whenStable();

    const el = fixture.nativeElement as HTMLElement;
    const texto = el.textContent ?? '';
    expect(texto).toMatch(/Saldo inicial\s*Q\s*100\.00/);
    expect(texto).toContain('compra_unidad 9');
    expect(texto).toMatch(/USD\s*100\.00/);
    expect(texto).toContain('7.75000000');
    expect(el.querySelector('tfoot')!.textContent).toMatch(/Q\s*875\.00/);
    expect(el.querySelector('tbody a')!.getAttribute('href')).toBe(
      '/contabilidad/partidas?partida=5',
    );
  });

  it('pide elegir la cuenta antes de consultar', async () => {
    configurar({});
    const fixture = TestBed.createComponent(MayorPantalla);
    catalogos();
    await fixture.whenStable();
    const el = fixture.nativeElement as HTMLElement;
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();
    expect(el.textContent).toContain('Elige la cuenta');
  });
});
