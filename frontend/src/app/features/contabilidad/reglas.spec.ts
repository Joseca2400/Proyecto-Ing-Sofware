import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ReglasPantalla } from './reglas';

const URL = '/api/v1/contabilidad/reglas';
const BASE = { es_detalle: true, nivel: 4, padre_id: 1, tipo: 'pasivo', naturaleza: 'acreedora' };
const CUENTAS = [
  { ...BASE, id: 21, codigo: '2.1.01.01', nombre: 'Proveedores del exterior', monetaria_usd: true },
  { ...BASE, id: 22, codigo: '2.1.01.02', nombre: 'Proveedores locales', monetaria_usd: false },
];
const REGLAS = [
  {
    id: 1,
    documento_tipo: 'compra_unidad',
    concepto: 'por_pagar_usd',
    descripcion: 'Deuda con el proveedor del exterior',
    cuenta_codigo: '2.1.01.01',
  },
  {
    id: 2,
    documento_tipo: 'factura_compra',
    concepto: 'por_pagar_gtq',
    descripcion: 'Deuda con el proveedor local',
    cuenta_codigo: '2.1.01.02',
  },
];

describe('ReglasPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ReglasPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear() {
    const fixture = TestBed.createComponent(ReglasPantalla);
    http.expectOne((r) => r.url.endsWith('/configuracion/cuentas')).flush(CUENTAS);
    http.expectOne(URL).flush(REGLAS);
    await fixture.whenStable();
    return fixture;
  }

  it('agrupa las reglas por tipo de documento con su cuenta actual', async () => {
    const el = (await crear()).nativeElement as HTMLElement;
    expect([...el.querySelectorAll('h2')].map((h) => h.textContent!.trim())).toEqual([
      'compra_unidad',
      'factura_compra',
    ]);
    expect(el.querySelector<HTMLSelectElement>('[name=cuenta1]')!.value).toBe('2.1.01.01');
  });

  it('cambia la cuenta de una regla y muestra el rechazo del servidor', async () => {
    const fixture = await crear();
    const el = fixture.nativeElement as HTMLElement;
    const select = el.querySelector<HTMLSelectElement>('[name=cuenta1]')!;
    select.value = '2.1.01.02';
    select.dispatchEvent(new Event('change'));
    el.querySelector<HTMLButtonElement>('tbody button')!.click();

    const envio = http.expectOne({ method: 'PUT', url: `${URL}/1` });
    expect(envio.request.body).toEqual({ cuenta_codigo: '2.1.01.02' });
    envio.flush({ ...REGLAS[0], cuenta_codigo: '2.1.01.02' });
    await fixture.whenStable();
    expect(el.textContent).toContain('ahora usa la cuenta 2.1.01.02');

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    http
      .expectOne({ method: 'PUT', url: `${URL}/1` })
      .flush({ detail: 'Permiso denegado' }, { status: 403, statusText: 'Forbidden' });
    await fixture.whenStable();
    expect(el.querySelector('[role=alert]')!.textContent).toContain('Permiso denegado');
  });
});
