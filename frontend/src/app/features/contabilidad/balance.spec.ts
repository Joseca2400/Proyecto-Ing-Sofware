import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { BalancePantalla } from './balance';

const URL = '/api/v1/contabilidad/balance';
const BALANCE = {
  filas: [
    {
      cuenta_id: 11,
      codigo: '1.1.01.01',
      nombre: 'Caja general',
      naturaleza: 'deudora',
      saldo_inicial: '1000.000000',
      debe: '0.000000',
      haber: '300.000000',
      saldo_final: '700.000000',
    },
  ],
  total_debe: '1075.000000',
  total_haber: '1075.000000',
};

describe('BalancePantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [BalancePantalla],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear() {
    const fixture = TestBed.createComponent(BalancePantalla);
    http.expectOne('/api/v1/configuracion/lineas-negocio').flush(['venta']);
    const consulta = http.expectOne((r) => r.url === URL);
    expect(consulta.request.params.get('desde')).toMatch(/^\d{4}-\d{2}-01$/);
    expect(consulta.request.params.has('vin')).toBe(false);
    consulta.flush(BALANCE);
    await fixture.whenStable();
    return fixture;
  }

  it('muestra saldos y totales del servidor con enlace al mayor', async () => {
    const fixture = await crear();
    const el = fixture.nativeElement as HTMLElement;
    const texto = el.textContent ?? '';
    expect(texto).toContain('1.1.01.01 · Caja general');
    expect(texto).toMatch(/Q\s*700\.00/);
    expect(el.querySelector('tfoot')!.textContent).toMatch(/Q\s*1,075\.00/);
    expect(el.querySelector('a')!.getAttribute('href')).toBe('/contabilidad/mayor?cuenta=11');
  });

  it('filtra por VIN y línea de negocio', async () => {
    const fixture = await crear();
    const el = fixture.nativeElement as HTMLElement;
    const vin = el.querySelector<HTMLInputElement>('[name=vin]')!;
    vin.value = '1HGCM82633A004352';
    vin.dispatchEvent(new Event('input'));
    const linea = el.querySelector<HTMLSelectElement>('[name=linea_negocio]')!;
    linea.value = 'venta';
    linea.dispatchEvent(new Event('change'));
    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    const consulta = http.expectOne((r) => r.url === URL);
    expect(consulta.request.params.get('vin')).toBe('1HGCM82633A004352');
    expect(consulta.request.params.get('linea_negocio')).toBe('venta');
    consulta.flush({ filas: [], total_debe: '0.000000', total_haber: '0.000000' });
    await fixture.whenStable();
    expect(el.textContent).toContain('No hay movimientos con estos filtros');
  });
});
