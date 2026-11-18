import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ContratosPantalla } from './contratos';

const URL = '/api/v1/alquileres/contratos';
const URL_CLIENTES = '/api/v1/facturacion/clientes';
const URL_UNIDADES = '/api/v1/unidades?estado=en_flota';
const VIN = '1HGCM82633A004352';

const URL_BANCOS = '/api/v1/configuracion/cuentas-bancarias?solo_activas=true';
const URL_DEPOSITOS = `${URL}/1/depositos`;
const BANCOS = [
  { id: 1, banco: 'Banco Industrial', numero: '000-GTQ', moneda: 'GTQ' },
  { id: 2, banco: 'Banco Industrial', numero: '000-USD', moneda: 'USD' },
];
const DEPOSITO = {
  id: 9,
  contrato_id: 1,
  contrato_numero: 7,
  vin: VIN,
  tipo: 'deposito',
  fecha: '2026-11-10',
  moneda: 'GTQ',
  monto: '2000.000000',
  saldo: '2000.000000',
  cuenta_bancaria_id: 1,
  referencia: null,
  devuelto: false,
  creado_en: '2026-11-10T15:00:00Z',
};

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
const CERRADO = {
  ...CONTRATO,
  estado: 'cerrado',
  devolucion: '2026-11-13T15:00:00Z',
  km_devolucion: 42600,
  combustible_devolucion: 5,
  observaciones_danos: 'Rayón',
  dias_efectivos: 3,
  km_recorridos: 600,
  km_excedentes: 150,
  combustible_faltante: 3,
  monto_final: '1425.000000',
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
    http.expectOne(URL_BANCOS).flush(BANCOS);
    http.expectOne(URL_UNIDADES).flush([UNIDAD]);
    http.expectOne(URL).flush(lista);
    await fixture.whenStable();
    return fixture;
  }

  const elemento = (f: ComponentFixture<ContratosPantalla>) => f.nativeElement as HTMLElement;

  /** Abre el detalle del primer contrato de la lista y responde sus depósitos. */
  async function ver(f: ComponentFixture<ContratosPantalla>, depositos: unknown[]): Promise<void> {
    elemento(f).querySelector<HTMLButtonElement>('tbody button')!.click();
    http.expectOne(URL_DEPOSITOS).flush(depositos);
    await f.whenStable();
  }

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
    http.expectOne(URL_DEPOSITOS).flush([]);
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

  it('cierra un contrato abierto y muestra el cálculo del servidor', async () => {
    const fixture = await crear([CONTRATO]);
    const el = elemento(fixture);
    await ver(fixture, []);

    escribir(el, 'devolucion', '2026-11-13T09:00');
    escribir(el, 'km_devolucion', '42600');
    escribir(el, 'combustible_devolucion', '5');
    escribir(el, 'observaciones_danos', ' Rayón ');
    el.querySelector('form.cierre')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: `${URL}/1/cierre` });
    expect(envio.request.body).toEqual({
      devolucion: new Date('2026-11-13T09:00').toISOString(),
      km_devolucion: 42600,
      combustible_devolucion: 5,
      observaciones_danos: 'Rayón',
    });
    envio.flush(CERRADO);
    http.expectOne(URL_UNIDADES).flush([UNIDAD]);
    http.expectOne(URL).flush([CERRADO]);
    await fixture.whenStable();

    const detalle = el.querySelector('.impresion')!.textContent ?? '';
    expect(detalle).toContain('150 excedentes');
    expect(detalle).toContain('faltan 3/8');
    expect(detalle).toMatch(/1,425\.00/);
    expect(el.querySelector('form.cierre')).toBeNull();
  });

  it('recibe un depósito en garantía en el contrato abierto', async () => {
    const fixture = await crear([CONTRATO]);
    const el = elemento(fixture);
    await ver(fixture, []);

    escribir(el, 'dep_fecha', '2026-11-10');
    escribir(el, 'dep_monto', '2000');
    escribir(el, 'dep_cuenta', '1');
    el.querySelector('.depositos form')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL_DEPOSITOS });
    expect(envio.request.body).toEqual({
      tipo: 'deposito',
      fecha: '2026-11-10',
      moneda: 'GTQ',
      monto: '2000',
      cuenta_bancaria_id: 1,
      referencia: null,
    });
    envio.flush(DEPOSITO);
    http.expectOne(URL_DEPOSITOS).flush([DEPOSITO]);
    await fixture.whenStable();

    expect(el.textContent).toContain('Depósito recibido');
    expect(el.querySelector('.depositos tbody')!.textContent).toMatch(/2,000\.00/);
  });

  it('aplica el depósito y devuelve el resto con el contrato cerrado', async () => {
    const fixture = await crear([CERRADO]);
    const el = elemento(fixture);
    await ver(fixture, [DEPOSITO]);
    const boton = (texto: string) =>
      [...el.querySelectorAll<HTMLButtonElement>('.depositos button')].find((b) =>
        b.textContent!.includes(texto),
      );

    escribir(el, 'mov_fecha', '2026-11-13');
    escribir(el, 'mov_monto', '1425');
    boton('Aplicar')!.click();
    const aplicacion = http.expectOne({
      method: 'POST',
      url: '/api/v1/alquileres/depositos/9/aplicacion',
    });
    expect(aplicacion.request.body).toEqual({ fecha: '2026-11-13', monto: '1425' });
    aplicacion.flush({ ...DEPOSITO, saldo: '575.000000' });
    http.expectOne(URL_DEPOSITOS).flush([{ ...DEPOSITO, saldo: '575.000000' }]);
    await fixture.whenStable();

    escribir(el, 'mov_monto', '575');
    escribir(el, 'mov_cuenta', '1');
    boton('Devolver')!.click();
    const devolucion = http.expectOne({
      method: 'POST',
      url: '/api/v1/alquileres/depositos/9/devolucion',
    });
    expect(devolucion.request.body).toEqual({
      fecha: '2026-11-13',
      monto: '575',
      cuenta_bancaria_id: 1,
    });
    const devuelto = { ...DEPOSITO, saldo: '0.000000', devuelto: true };
    devolucion.flush(devuelto);
    http.expectOne(URL_DEPOSITOS).flush([devuelto]);
    await fixture.whenStable();

    expect(el.textContent).toContain('Depósito devuelto');
    expect(boton('Devolver')).toBeUndefined();
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
