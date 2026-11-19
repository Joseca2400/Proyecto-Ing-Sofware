import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UnidadesPantalla } from './unidades';

const URL = '/api/v1/unidades';
const VIN = '1HGCM82633A004352';
const URL_GASTOS = `/api/v1/compras/gastos-importacion/unidad/${VIN}`;

const CATALOGOS = {
  estados: [
    'en_transito',
    'en_aduana',
    'en_taller',
    'lista',
    'en_flota',
    'en_venta',
    'vendida',
    'recuperada',
  ],
  tipos_vehiculo: ['sedan', 'pickup'],
  lineas_negocio: ['alquiler', 'venta', 'taller', 'financiamiento', 'administracion'],
};

const HONDA = {
  id: 1,
  vin: VIN,
  marca: 'Honda',
  linea: 'Accord',
  modelo: 2003,
  color: 'Gris',
  tipo_vehiculo: 'sedan',
  linea_negocio: 'alquiler',
  estado: 'en_transito',
  creado_en: '2026-11-06T10:00:00Z',
};

const ALTA = {
  id: 1,
  estado_anterior: null,
  estado_nuevo: 'en_transito',
  documento: 'Alta de la unidad',
  usuario_id: null,
  fecha: '2026-11-06T10:00:00Z',
};

const SIN_GASTOS = {
  vin: VIN,
  gastos: 0,
  total_costo_gtq: '0.000000',
  total_credito_fiscal_gtq: '0.000000',
};

describe('UnidadesPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [UnidadesPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(lista: unknown[] = []): Promise<ComponentFixture<UnidadesPantalla>> {
    const fixture = TestBed.createComponent(UnidadesPantalla);
    http.expectOne(`${URL}/catalogos`).flush(CATALOGOS);
    http.expectOne(URL).flush(lista);
    await fixture.whenStable();
    return fixture;
  }

  function elemento(fixture: ComponentFixture<UnidadesPantalla>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  it('lista las unidades con su estado y usa las líneas de negocio del servidor', async () => {
    const fixture = await crear([HONDA]);
    const el = elemento(fixture);
    const tabla = el.querySelector('tbody')!.textContent ?? '';

    expect(tabla).toContain(VIN);
    expect(tabla).toContain('Honda Accord 2003');
    expect(tabla).toContain('Sedán');
    expect(tabla).toContain('En tránsito');

    const lineas = [...el.querySelectorAll('[name=linea_negocio] option')].map(
      (o) => o.textContent,
    );
    expect(lineas).toContain('Administración');
    const iniciales = [...el.querySelectorAll('[name=estado] option')].map((o) => o.textContent);
    expect(iniciales).not.toContain('Vendida');
    expect(iniciales).not.toContain('Recuperada');
  });

  it('registra una unidad y muestra su ficha con el historial', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'vin', '1hgcm82633a004352');
    escribir(el, 'marca', ' Honda ');
    escribir(el, 'linea', 'Accord');
    escribir(el, 'modelo', '2003');
    escribir(el, 'color', 'Gris');
    escribir(el, 'linea_negocio', 'alquiler');
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      vin: VIN,
      marca: 'Honda',
      linea: 'Accord',
      modelo: 2003,
      color: 'Gris',
      tipo_vehiculo: 'sedan',
      linea_negocio: 'alquiler',
      estado: 'en_transito',
    });
    envio.flush(HONDA);
    http.expectOne(URL).flush([HONDA]);
    http.expectOne(`${URL}/${VIN}/historial`).flush([ALTA]);
    http.expectOne(URL_GASTOS).flush(SIN_GASTOS);
    await fixture.whenStable();

    expect(el.textContent).toContain(`Unidad ${VIN} registrada`);
    const ficha = el.querySelector('.ficha')!.textContent ?? '';
    expect(ficha).toContain('Honda Accord 2003');
    expect(ficha).toContain('Alta de la unidad');
  });

  it('no envía un VIN con I, O o Q', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'vin', '1HGCM82633A0O4352');
    escribir(el, 'marca', 'Honda');
    escribir(el, 'linea', 'Accord');
    escribir(el, 'color', 'Gris');
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('17 caracteres, sin I, O ni Q');
  });

  it('muestra el rechazo del servidor por dígito verificador', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'vin', '1HGCM82623A004352');
    escribir(el, 'marca', 'Honda');
    escribir(el, 'linea', 'Accord');
    escribir(el, 'color', 'Gris');
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'El VIN 1HGCM82623A004352 no pasa el dígito verificador' },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();

    expect(el.textContent).toContain('no pasa el dígito verificador');
  });

  it('cambia el estado con su documento y refresca el historial', async () => {
    const fixture = await crear([HONDA]);
    const el = elemento(fixture);

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    http.expectOne(`${URL}/${VIN}/historial`).flush([ALTA]);
    http.expectOne(URL_GASTOS).flush(SIN_GASTOS);
    await fixture.whenStable();

    const opciones = [...el.querySelectorAll('[name=nuevo_estado] option')].map(
      (o) => o.textContent,
    );
    expect(opciones).not.toContain('En tránsito');

    escribir(el, 'nuevo_estado', 'en_aduana');
    escribir(el, 'documento_cambio', ' BL MSCU1234567 ');
    el.querySelector('form.cambio')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: `${URL}/${VIN}/estado` });
    expect(envio.request.body).toEqual({ estado: 'en_aduana', documento: 'BL MSCU1234567' });
    const actualizada = { ...HONDA, estado: 'en_aduana' };
    envio.flush(actualizada);
    http.expectOne(URL).flush([actualizada]);
    http.expectOne(`${URL}/${VIN}/historial`).flush([
      ALTA,
      {
        ...ALTA,
        id: 2,
        estado_anterior: 'en_transito',
        estado_nuevo: 'en_aduana',
        documento: 'BL MSCU1234567',
      },
    ]);
    http.expectOne(URL_GASTOS).flush(SIN_GASTOS);
    await fixture.whenStable();

    expect(el.textContent).toContain(`La unidad ${VIN} pasó a En aduana`);
    expect(el.querySelector('.ficha tbody')!.textContent).toContain('BL MSCU1234567');
  });

  it('no cambia el estado sin documento', async () => {
    const fixture = await crear([HONDA]);
    const el = elemento(fixture);

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    http.expectOne(`${URL}/${VIN}/historial`).flush([ALTA]);
    http.expectOne(URL_GASTOS).flush(SIN_GASTOS);
    await fixture.whenStable();

    escribir(el, 'nuevo_estado', 'en_aduana');
    el.querySelector('form.cambio')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: `${URL}/${VIN}/estado` });
    expect(el.textContent).toContain('Indica el documento');
  });

  it('muestra en la ficha los gastos de importación que suman al costo', async () => {
    const fixture = await crear([HONDA]);
    const el = elemento(fixture);

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    http.expectOne(`${URL}/${VIN}/historial`).flush([ALTA]);
    http.expectOne(URL_GASTOS).flush({
      vin: VIN,
      gastos: 3,
      total_costo_gtq: '4275.100000',
      total_credito_fiscal_gtq: '1020.000000',
    });
    await fixture.whenStable();

    const ficha = el.querySelector('.ficha dl')!.textContent ?? '';
    expect(ficha).toContain('Gastos de importación');
    expect(ficha).toMatch(/4,275\.10\s+suman al costo/);
    expect(ficha).toMatch(/IVA de importación \D*1,020\.00: crédito fiscal, no suma/);
  });

  it('consulta con los filtros de búsqueda y estado', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'buscar', ' accord ');
    escribir(el, 'filtro_estado', 'lista');
    el.querySelector('form.filtros')!.dispatchEvent(new Event('submit'));

    const consulta = http.expectOne((r) => r.url === URL && r.method === 'GET');
    expect(consulta.request.params.get('buscar')).toBe('accord');
    expect(consulta.request.params.get('estado')).toBe('lista');
    consulta.flush([]);
    await fixture.whenStable();
  });
});
