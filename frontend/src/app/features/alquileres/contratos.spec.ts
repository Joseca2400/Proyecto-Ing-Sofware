import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ContratosPantalla } from './contratos';

const URL = '/api/v1/alquileres/contratos';
const URL_CLIENTES = '/api/v1/facturacion/clientes';
const URL_UNIDADES = '/api/v1/unidades?estado=en_flota';
const VIN = '1HGCM82633A004352';

const CLIENTE = { id: 3, nombre: 'María López' };
const UNIDAD = { vin: VIN, marca: 'Honda', linea: 'Accord', modelo: 2007 };

const CONTRATO = {
  id: 1,
  numero: 7,
  cliente_id: 3,
  vin: VIN,
  salida: '2026-11-10T15:00:00Z',
  devolucion_prevista: '2026-11-13',
  tarifa_id: 1,
  modalidad: 'diaria',
  moneda: 'GTQ',
  tarifa_monto: '350.000000',
  km_incluido: 150,
  precio_km_adicional: '2.500000',
  km_salida: 42000,
  combustible_salida: 8,
  deposito_esperado: '2000.000000',
  dias_previstos: 3,
  monto_estimado: '1050.000000',
  estado: 'abierto',
  creado_en: '2026-11-10T15:00:00Z',
};

describe('ContratosPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ContratosPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(lista: unknown[] = []): Promise<ComponentFixture<ContratosPantalla>> {
    const fixture = TestBed.createComponent(ContratosPantalla);
    http.expectOne(URL_CLIENTES).flush([CLIENTE]);
    http.expectOne(URL_UNIDADES).flush([UNIDAD]);
    http.expectOne(URL).flush(lista);
    await fixture.whenStable();
    return fixture;
  }

  const elemento = (f: ComponentFixture<ContratosPantalla>) => f.nativeElement as HTMLElement;

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  it('lista los contratos con el nombre del cliente y el monto estimado', async () => {
    const el = elemento(await crear([CONTRATO]));
    const fila = el.querySelector('tbody')!.textContent ?? '';

    expect(fila).toContain('7');
    expect(fila).toContain('María López');
    expect(fila).toContain(VIN);
    expect(fila).toMatch(/1,050\.00/);
  });

  it('registra un contrato y muestra su detalle para imprimir', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'cliente_id', '3');
    escribir(el, 'vin', VIN);
    escribir(el, 'salida', '2026-11-10T09:00');
    escribir(el, 'devolucion_prevista', '2026-11-13');
    escribir(el, 'km_salida', '42000');
    escribir(el, 'deposito_esperado', '2000.00');
    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      cliente_id: 3,
      vin: VIN,
      salida: new Date('2026-11-10T09:00').toISOString(),
      devolucion_prevista: '2026-11-13',
      modalidad: 'diaria',
      moneda: 'GTQ',
      km_salida: 42000,
      combustible_salida: 8,
      deposito_esperado: '2000.00',
    });
    envio.flush(CONTRATO);
    http.expectOne(URL_UNIDADES).flush([]);
    http.expectOne(URL).flush([CONTRATO]);
    await fixture.whenStable();

    expect(el.textContent).toContain('Contrato 7 registrado');
    const detalle = el.querySelector('.impresion')!.textContent ?? '';
    expect(detalle).toContain('Contrato de alquiler No. 7');
    expect(detalle).toContain('8/8 de tanque');

    const imprimir = vi.spyOn(window, 'print').mockImplementation(() => undefined);
    el.querySelector<HTMLButtonElement>('.impresion button')!.click();
    expect(imprimir).toHaveBeenCalled();
  });

  it('no envía sin cliente ni unidad', async () => {
    const fixture = await crear();
    const el = elemento(fixture);
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('Complete cliente');
  });

  it('muestra el rechazo del servidor por unidad no disponible', async () => {
    const fixture = await crear();
    const el = elemento(fixture);
    escribir(el, 'cliente_id', '3');
    escribir(el, 'vin', VIN);
    escribir(el, 'devolucion_prevista', '2026-11-13');
    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'La unidad no está disponible: su estado es alquilada' },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(el.textContent).toContain('su estado es alquilada');
  });
});
