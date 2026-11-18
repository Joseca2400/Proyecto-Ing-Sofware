import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { DepositosPantalla } from './depositos';

const URL = '/api/v1/alquileres/depositos';

const DEPOSITO = {
  id: 9,
  contrato_id: 1,
  contrato_numero: 7,
  vin: '1HGCM82633A004352',
  tipo: 'deposito',
  fecha: '2026-11-10',
  moneda: 'GTQ',
  monto: '2000.000000',
  saldo: '575.000000',
  cuenta_bancaria_id: 1,
  referencia: null,
  devuelto: false,
  creado_en: '2026-11-10T15:00:00Z',
};

describe('DepositosPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [DepositosPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lista los depósitos vigentes con el total por moneda del servidor', async () => {
    const fixture = TestBed.createComponent(DepositosPantalla);
    http.expectOne(URL).flush({
      depositos: [DEPOSITO],
      totales: { GTQ: '575.000000', USD: '200.000000' },
    });
    await fixture.whenStable();
    const el = fixture.nativeElement as HTMLElement;

    expect(el.querySelector('tbody')!.textContent).toContain('7');
    expect(el.querySelector('tbody')!.textContent).toMatch(/575\.00/);
    const pie = el.querySelector('tfoot')!.textContent ?? '';
    expect(pie).toMatch(/575\.00/);
    expect(pie).toMatch(/200\.00/);
  });

  it('avisa si no hay depósitos vigentes', async () => {
    const fixture = TestBed.createComponent(DepositosPantalla);
    http.expectOne(URL).flush({ depositos: [], totales: { GTQ: '0.000000', USD: '0.000000' } });
    await fixture.whenStable();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'No hay depósitos vigentes',
    );
  });
});
