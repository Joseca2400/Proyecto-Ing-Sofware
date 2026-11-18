import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TarifarioPantalla } from './tarifario';

const URL = '/api/v1/alquileres/tarifas';

const CATALOGOS = {
  modalidades: ['diaria', 'semanal', 'mensual', 'por_kilometraje'],
  monedas: ['GTQ', 'USD'],
  tipos_vehiculo: ['sedan', 'suv', 'pickup'],
};

const TARIFA = {
  id: 1,
  tipo_vehiculo: 'sedan',
  vin: null,
  modalidad: 'diaria',
  moneda: 'GTQ',
  monto: '350.000000',
  km_incluido: 150,
  precio_km_adicional: '2.500000',
  vigente_desde: '2026-01-01',
  vigente_hasta: null,
  creado_en: '2026-11-18T10:00:00Z',
};

describe('TarifarioPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TarifarioPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(lista: unknown[] = []): Promise<ComponentFixture<TarifarioPantalla>> {
    const fixture = TestBed.createComponent(TarifarioPantalla);
    http.expectOne(`${URL}/catalogos`).flush(CATALOGOS);
    http.expectOne(URL).flush(lista);
    await fixture.whenStable();
    return fixture;
  }

  const elemento = (f: ComponentFixture<TarifarioPantalla>) => f.nativeElement as HTMLElement;

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  function enviar(el: HTMLElement): void {
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
  }

  it('lista las tarifas con su vigencia y montos formateados', async () => {
    const el = elemento(await crear([TARIFA]));
    const fila = el.querySelector('tbody')!.textContent ?? '';

    expect(fila).toContain('sedan');
    expect(fila).toContain('Diaria');
    expect(fila).toMatch(/350\.00/);
    expect(fila).toContain('2026-01-01 → sin fin');
  });

  it('registra una tarifa por tipo de vehículo', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'tipo_vehiculo', 'suv');
    escribir(el, 'monto', '450.00');
    escribir(el, 'km_incluido', '200');
    escribir(el, 'vigente_desde', '2026-07-01');
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      tipo_vehiculo: 'suv',
      modalidad: 'diaria',
      moneda: 'GTQ',
      monto: '450.00',
      km_incluido: 200,
      precio_km_adicional: '0',
      vigente_desde: '2026-07-01',
    });
    envio.flush(TARIFA);
    http.expectOne(URL).flush([TARIFA]);
    await fixture.whenStable();

    expect(el.textContent).toContain('Tarifa registrada');
  });

  it('registra una tarifa de excepción por VIN', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'aplica_a', 'vin');
    await fixture.whenStable();
    expect(el.querySelector('[name=tipo_vehiculo]')).toBeNull();

    escribir(el, 'vin', '1HGCM82633A004352');
    escribir(el, 'monto', '500');
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body.vin).toBe('1HGCM82633A004352');
    expect(envio.request.body.tipo_vehiculo).toBeUndefined();
    envio.flush({ ...TARIFA, tipo_vehiculo: null, vin: '1HGCM82633A004352' });
    http.expectOne(URL).flush([]);
  });

  it('no envía sin monto ni VIN', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    enviar(el);
    await fixture.whenStable();
    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('Número positivo');

    escribir(el, 'aplica_a', 'vin');
    escribir(el, 'monto', '500');
    enviar(el);
    await fixture.whenStable();
    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('Indique el VIN');
  });

  it('muestra el rechazo del servidor por vigencia traslapada', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'monto', '450');
    enviar(el);
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'La vigencia se traslapa con la tarifa 1' },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(el.textContent).toContain('La vigencia se traslapa con la tarifa 1');
  });
});
