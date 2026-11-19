import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { CierreMesPantalla } from './cierre-mes';

const API = '/api/v1/contabilidad';
const VIN = '1HGCM82633A004352';
const DEPRECIACION = {
  id: 1,
  anio: 2024,
  mes: 2,
  calculado_por: 2,
  calculado_en: '2024-03-01T10:00:00Z',
  partida: { id: 9, numero: null, estado: 'borrador', fecha: '2024-02-29', lineas: [] },
  lineas: [
    { vin: VIN, financiera: '1157.950000', fiscal: '1286.610000', diferencia: '128.660000' },
  ],
  total_financiera: '1157.950000',
  total_fiscal: '1286.610000',
};

const CUENTAS = [{ id: 13, codigo: '1.1.01.03', nombre: 'Bancos en dólares' }];
const REVALUACION = {
  id: 1,
  anio: 2024,
  mes: 2,
  fecha: '2024-02-29',
  tipo_cambio: '7.80000000',
  politica: 'mantener',
  partida_id: 20,
  reversion_id: null,
  lineas: [
    {
      cuenta_id: 13,
      linea_negocio: 'administracion',
      vin: null,
      saldo_usd: '100.000000',
      tipo_cambio_anterior: '7.75000000',
      diferencial: '5.000000',
    },
  ],
  total_diferencial: '5.000000',
};

describe('CierreMesPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [CierreMesPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    vi.restoreAllMocks();
  });

  async function crear(
    depreciaciones: unknown[] = [],
    revaluaciones: unknown[] = [],
    periodos: unknown[] = [],
  ) {
    const fixture = TestBed.createComponent(CierreMesPantalla);
    http.expectOne(`${API}/depreciaciones`).flush(depreciaciones);
    http.expectOne(`${API}/revaluaciones`).flush(revaluaciones);
    http.expectOne(`${API}/periodos`).flush(periodos);
    http.expectOne((r) => r.url.endsWith('/configuracion/cuentas')).flush(CUENTAS);
    await fixture.whenStable();
    const el = fixture.nativeElement as HTMLElement;
    const mes = el.querySelector<HTMLInputElement>('[name=mes]')!;
    mes.value = '2024-02';
    mes.dispatchEvent(new Event('change'));
    await fixture.whenStable();
    return { fixture, el };
  }

  it('calcula la depreciación del mes elegido y muestra el detalle por unidad', async () => {
    const { fixture, el } = await crear();
    expect(el.textContent).toContain('no se ha calculado');

    el.querySelector<HTMLButtonElement>('[name=depreciar]')!.click();
    const peticion = http.expectOne(`${API}/depreciaciones`);
    expect(peticion.request.body).toEqual({ anio: 2024, mes: 2 });
    peticion.flush(DEPRECIACION);
    await fixture.whenStable();

    const celdas = [...el.querySelectorAll('tbody td')].map((td) => td.textContent!.trim());
    expect(celdas[0]).toBe(VIN);
    // El pipe separa el símbolo con un espacio duro: se compara solo la cifra.
    expect(celdas.slice(1).map((c) => c.replace(/^Q\s/, ''))).toEqual([
      '1,157.95',
      '1,286.61',
      '128.66',
    ]);
    expect(el.textContent).toContain('en borrador');
    expect(el.querySelector('[name=depreciar]')!.textContent).toContain('Volver a calcular');
  });

  it('no ofrece recalcular un mes contabilizado y muestra el rechazo del servidor', async () => {
    const contabilizada = {
      ...DEPRECIACION,
      partida: { ...DEPRECIACION.partida, numero: 14, estado: 'contabilizada' },
    };
    const { fixture, el } = await crear([contabilizada]);
    expect(el.textContent).toContain('No. 14');
    expect(el.querySelector('[name=depreciar]')).toBeNull();

    const mes = el.querySelector<HTMLInputElement>('[name=mes]')!;
    mes.value = '2024-03';
    mes.dispatchEvent(new Event('change'));
    await fixture.whenStable();
    el.querySelector<HTMLButtonElement>('[name=depreciar]')!.click();
    http
      .expectOne(`${API}/depreciaciones`)
      .flush(
        { detail: 'No hay unidades de la flota por depreciar' },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();
    expect(el.querySelector('[role=alert]')!.textContent).toContain('No hay unidades');
  });

  it('revalúa con la política elegida y muestra el reporte por cuenta', async () => {
    const { fixture, el } = await crear();
    el.querySelector<HTMLSelectElement>('[name=politica]')!.value = 'mantener';
    el.querySelector<HTMLButtonElement>('[name=revaluar]')!.click();
    const peticion = http.expectOne(`${API}/revaluaciones`);
    expect(peticion.request.body).toEqual({ anio: 2024, mes: 2, politica: 'mantener' });
    peticion.flush(REVALUACION);
    await fixture.whenStable();

    const fila = el.querySelector('#revaluacion tbody tr')!.textContent!;
    expect(fila).toContain('1.1.01.03 · Bancos en dólares');
    expect(fila).toContain('7.75000000');
    expect(fila).toContain('5.00');
    expect(el.textContent).toContain('El saldo revaluado se mantiene');
    expect(el.querySelector('[name=revaluar]')).toBeNull();
  });

  it('cierra el mes tras confirmar y muestra quién lo cerró y su balance', async () => {
    const { fixture, el } = await crear();
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(false);
    el.querySelector<HTMLButtonElement>('[name=cerrar]')!.click();
    http.expectNone(`${API}/periodos`);

    confirmar.mockReturnValue(true);
    el.querySelector<HTMLButtonElement>('[name=cerrar]')!.click();
    const peticion = http.expectOne(`${API}/periodos`);
    expect(peticion.request.body).toEqual({ anio: 2024, mes: 2 });
    peticion.flush({
      id: 1,
      anio: 2024,
      mes: 2,
      fecha: '2024-02-29',
      cerrado_por: 2,
      cerrado_en: '2024-03-03T15:00:00Z',
      balance: { filas: [{}, {}], total_debe: '1000.000000', total_haber: '1000.000000' },
    });
    await fixture.whenStable();

    const cierre = el.querySelector('#cierre')!.textContent!;
    expect(cierre).toContain('Cerrado el 2024-03-03 por el usuario 2');
    expect(cierre).toContain('2 cuentas');
    expect(el.querySelector('[name=cerrar]')).toBeNull();
  });
});
