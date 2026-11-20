import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TarifarioPantalla } from './tarifario';

const URL = '/api/v1/alquileres';
const VIN = '1HGCM82633A004352';

const TARIFA = {
  id: 1,
  tipo_vehiculo: 'sedan',
  vin: null,
  temporada: null,
  modalidad: 'diaria',
  moneda: 'GTQ',
  monto: '300.000000',
  km_incluido: 200,
  costo_km_adicional: '2.500000',
  vigente_desde: '2026-01-01',
  creado_en: '2026-01-01T10:00:00Z',
};

const TEMPORADA = {
  id: 1,
  nombre: 'Semana Santa',
  fecha_inicio: '2026-03-29',
  fecha_fin: '2026-04-05',
  activa: true,
};

const GPS = {
  id: 2,
  nombre: 'GPS',
  naturaleza: 'ingreso',
  aplica_iva: true,
  es_ingreso_acumulable: true,
  precio_sugerido: '25.000000',
  moneda: 'GTQ',
  activo: true,
};

const DEPOSITO = {
  ...GPS,
  id: 1,
  nombre: 'Depósito en garantía',
  naturaleza: 'deposito',
  aplica_iva: false,
  es_ingreso_acumulable: false,
  precio_sugerido: null,
  moneda: null,
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

  async function crear(): Promise<ComponentFixture<TarifarioPantalla>> {
    const fixture = TestBed.createComponent(TarifarioPantalla);
    http.expectOne(`${URL}/tarifas`).flush([TARIFA]);
    http.expectOne(`${URL}/temporadas`).flush([TEMPORADA]);
    http.expectOne(`${URL}/conceptos`).flush([DEPOSITO, GPS]);
    await fixture.whenStable();
    return fixture;
  }

  const el = (f: ComponentFixture<TarifarioPantalla>) => f.nativeElement as HTMLElement;

  function escribir(raiz: HTMLElement, nombre: string, valor: string): void {
    const campo = raiz.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  const formulario = (raiz: HTMLElement, i: number) => raiz.querySelectorAll('form.formulario')[i];

  it('lista tarifas, temporadas y conceptos con su tratamiento fiscal', async () => {
    const raiz = el(await crear());

    const tarifa = raiz.querySelector('tbody.tarifas')!.textContent!;
    expect(tarifa).toContain('Sedán');
    expect(tarifa).toContain('Base');
    expect(tarifa).toMatch(/300\.00\s*\/ día/);
    expect(tarifa).toContain('200 km');
    expect(raiz.querySelector('tbody.temporadas')!.textContent).toContain('Semana Santa');
    const conceptos = raiz.querySelector('tbody.conceptos')!.textContent!;
    expect(conceptos).toContain('Depósito (pasivo)');
    expect(conceptos).toContain('Ingreso con IVA');
    expect(conceptos).toContain('Se captura');
  });

  it('registra una tarifa de excepción por unidad en una temporada', async () => {
    const fixture = await crear();
    const raiz = el(fixture);

    raiz.querySelector<HTMLInputElement>('input[value=unidad]')!.click();
    await fixture.whenStable();
    escribir(raiz, 'vin', VIN.toLowerCase());
    escribir(raiz, 'temporada_id', '1');
    escribir(raiz, 'moneda', 'USD');
    escribir(raiz, 'monto', '60.00');
    escribir(raiz, 'vigente_desde', '2026-03-01');
    formulario(raiz, 0).dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: `${URL}/tarifas` });
    expect(envio.request.body).toEqual({
      vin: VIN,
      temporada_id: 1,
      modalidad: 'diaria',
      moneda: 'USD',
      monto: '60.00',
      vigente_desde: '2026-03-01',
    });
    envio.flush({ ...TARIFA, id: 2, vin: VIN, tipo_vehiculo: null, vigente_desde: '2026-03-01' });
    http.expectOne(`${URL}/tarifas`).flush([TARIFA]);
    await fixture.whenStable();

    expect(raiz.textContent).toContain('Tarifa registrada, vigente desde el 2026-03-01');
  });

  it('la tarifa por kilometraje exige km incluidos y costo adicional', async () => {
    const fixture = await crear();
    const raiz = el(fixture);

    escribir(raiz, 'modalidad', 'kilometraje');
    escribir(raiz, 'monto', '500.00');
    formulario(raiz, 0).dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: `${URL}/tarifas` });
    expect(raiz.textContent).toContain('requiere kilómetros incluidos');
  });

  it('muestra el rechazo del servidor a una temporada que se traslapa', async () => {
    const fixture = await crear();
    const raiz = el(fixture);

    escribir(raiz, 'temporada_nombre', 'Pascua');
    escribir(raiz, 'temporada_inicio', '2026-04-01');
    escribir(raiz, 'temporada_fin', '2026-04-10');
    formulario(raiz, 1).dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: `${URL}/temporadas` })
      .flush(
        { detail: 'Las fechas se traslapan con la temporada «Semana Santa»' },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();

    expect(raiz.textContent).toContain('se traslapan con la temporada «Semana Santa»');
  });

  it('un depósito no puede llevar IVA', async () => {
    const fixture = await crear();
    const raiz = el(fixture);

    escribir(raiz, 'concepto_nombre', 'Depósito VIP');
    escribir(raiz, 'concepto_naturaleza', 'deposito');
    await fixture.whenStable();
    expect(raiz.querySelector('[name=concepto_iva]')).toBeNull();
    formulario(raiz, 2).dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: `${URL}/conceptos` });
    expect(envio.request.body).toEqual({
      nombre: 'Depósito VIP',
      naturaleza: 'deposito',
      aplica_iva: false,
    });
    envio.flush({ ...DEPOSITO, id: 9, nombre: 'Depósito VIP' });
    http.expectOne(`${URL}/conceptos`).flush([DEPOSITO, GPS]);
  });

  it('cambia el precio sugerido de un concepto', async () => {
    const fixture = await crear();
    const raiz = el(fixture);

    const fila = [...raiz.querySelectorAll('tbody.conceptos tr')].find((f) =>
      f.textContent!.includes('Depósito en garantía'),
    )!;
    fila.querySelector<HTMLButtonElement>('button')!.click();
    await fixture.whenStable();
    escribir(raiz, 'concepto_precio', '3000');
    formulario(raiz, 2).dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'PUT', url: `${URL}/conceptos/1` });
    expect(envio.request.body).toEqual({ precio_sugerido: '3000', moneda: 'GTQ', activo: true });
    envio.flush({ ...DEPOSITO, precio_sugerido: '3000.000000', moneda: 'GTQ' });
    http.expectOne(`${URL}/conceptos`).flush([DEPOSITO, GPS]);
    await fixture.whenStable();

    expect(raiz.textContent).toContain('Concepto Depósito en garantía actualizado');
  });
});
