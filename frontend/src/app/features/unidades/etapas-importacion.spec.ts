import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EtapasImportacionPantalla } from './etapas-importacion';

const URL = '/api/v1/unidades';
const URL_ETAPAS = `${URL}/etapas-importacion`;
const VIN = '1HGCM82633A004352';
const OTRO_VIN = '1FTFW1ET9DFC10312';

const HONDA = {
  vin: VIN,
  marca: 'Honda',
  linea: 'Accord',
  modelo: 2007,
  color: 'Gris',
  estado: 'en_transito',
  desde: '2026-11-05T10:00:00Z',
  dias_en_etapa: 12,
  costo_total_gtq: '65500.000000',
  siguiente_etapa: 'en_aduana',
};

const FORD = {
  ...HONDA,
  vin: OTRO_VIN,
  marca: 'Ford',
  linea: 'F-150',
  estado: 'lista',
  dias_en_etapa: 3,
  costo_total_gtq: '98000.500000',
  siguiente_etapa: null,
};

const ETAPAS = {
  etapas: [
    { estado: 'en_transito', unidades: 1, costo_total_gtq: '65500.000000' },
    { estado: 'en_aduana', unidades: 0, costo_total_gtq: '0.000000' },
    { estado: 'en_taller', unidades: 0, costo_total_gtq: '0.000000' },
    { estado: 'lista', unidades: 1, costo_total_gtq: '98000.500000' },
  ],
  unidades: [HONDA, FORD],
};

describe('EtapasImportacionPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [EtapasImportacionPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(): Promise<ComponentFixture<EtapasImportacionPantalla>> {
    const fixture = TestBed.createComponent(EtapasImportacionPantalla);
    http.expectOne(URL_ETAPAS).flush(ETAPAS);
    await fixture.whenStable();
    return fixture;
  }

  function elemento(fixture: ComponentFixture<EtapasImportacionPantalla>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function filas(el: HTMLElement): string[] {
    return [...el.querySelectorAll('tbody tr')].map((f) => f.textContent ?? '');
  }

  it('muestra las unidades con su etapa, días y costo, y el total de cada etapa', async () => {
    const el = elemento(await crear());

    const [honda, ford] = filas(el);
    expect(honda).toContain(VIN);
    expect(honda).toContain('Honda Accord 2007');
    expect(honda).toContain('En tránsito');
    expect(honda).toContain('12');
    expect(honda).toContain('65,500.00');
    expect(honda).toContain('Pasar a En aduana');
    expect(ford).toContain('Lista para la flota');

    const tarjetas = [...el.querySelectorAll('.etapa')].map((t) => t.textContent ?? '');
    expect(tarjetas).toHaveLength(5);
    expect(tarjetas[0]).toContain('Todas');
    expect(tarjetas[4]).toContain('Lista');
    expect(tarjetas[4]).toContain('98,000.50');
  });

  it('filtra la tabla por etapa sin volver a consultar', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    el.querySelector<HTMLButtonElement>('.etapa[data-estado=lista]')!.click();
    await fixture.whenStable();
    expect(filas(el)).toHaveLength(1);
    expect(filas(el)[0]).toContain(OTRO_VIN);

    el.querySelector<HTMLButtonElement>('.etapa[data-estado=en_aduana]')!.click();
    await fixture.whenStable();
    expect(filas(el)[0]).toContain('No hay unidades en esta etapa');

    el.querySelector<HTMLButtonElement>('.etapa:not([data-estado])')!.click();
    await fixture.whenStable();
    expect(filas(el)).toHaveLength(2);
  });

  it('pasa la unidad a la etapa siguiente con su documento y recarga', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    el.querySelector<HTMLButtonElement>('td.accion button')!.click();
    await fixture.whenStable();
    const documento = el.querySelector<HTMLInputElement>('[name=documento]')!;
    documento.value = ' BL MSCU1234567 ';
    documento.dispatchEvent(new Event('input'));
    el.querySelector('form.avance')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: `${URL}/${VIN}/estado` });
    expect(envio.request.body).toEqual({ estado: 'en_aduana', documento: 'BL MSCU1234567' });
    envio.flush({ vin: VIN, estado: 'en_aduana' });
    http.expectOne(URL_ETAPAS).flush(ETAPAS);
    await fixture.whenStable();

    expect(el.querySelector('[role=status]')!.textContent).toContain('pasó a En aduana');
    expect(el.querySelector('form.avance')).toBeNull();
  });

  it('exige el documento y muestra el rechazo del servidor', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    el.querySelector<HTMLButtonElement>('td.accion button')!.click();
    await fixture.whenStable();
    el.querySelector('form.avance')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();
    expect(el.querySelector('form.avance')!.textContent).toContain('Indica el documento');

    const documento = el.querySelector<HTMLInputElement>('[name=documento]')!;
    documento.value = 'BL 1';
    documento.dispatchEvent(new Event('input'));
    el.querySelector('form.avance')!.dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: `${URL}/${VIN}/estado` })
      .flush(
        { detail: 'una unidad en tránsito solo puede pasar a en aduana' },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();

    expect(el.querySelector('[role=alert]')!.textContent).toContain('solo puede pasar a en aduana');
  });
});
