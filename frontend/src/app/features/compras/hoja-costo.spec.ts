import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { HojaCosto } from './compras.service';
import { HojaCostoPantalla } from './hoja-costo';

const VIN = '1HGCM82633A004352';
const URL = `/api/v1/compras/hoja-costo/${VIN}`;

const HOJA: HojaCosto = {
  vin: VIN,
  marca: 'Honda',
  linea: 'Accord',
  modelo: 2007,
  estado: 'lista',
  compra: {
    fecha: '2026-10-20',
    documento: 'LOT-1',
    proveedor: 'Copart Inc.',
    total_usd: '9075.000000',
    tipo_cambio: '7.75000000',
    total_gtq: '70331.250000',
  },
  importacion: [
    {
      concepto: 'iva_importacion',
      nombre: 'IVA de importación',
      fecha: '2026-10-20',
      documento: 'DUCA',
      moneda: 'GTQ',
      monto: '5000.000000',
      tipo_cambio: null,
      monto_gtq: '5000.000000',
      suma_al_costo: false,
    },
  ],
  mano_obra: [{ numero: 'OT-00001', fecha_cierre: '2026-11-18', costo_gtq: '112.500000' }],
  repuestos: [],
  compra_gtq: '70331.250000',
  importacion_gtq: '0.000000',
  credito_fiscal_gtq: '5000.000000',
  reacondicionamiento_gtq: '112.500000',
  total_gtq: '70443.750000',
  saldo_mayor_gtq: '70443.750000',
  costo_alta_gtq: null,
  diferencia_gtq: '0.000000',
  cuadra: true,
};

describe('HojaCostoPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HojaCostoPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function consultar() {
    const fixture = TestBed.createComponent(HojaCostoPantalla);
    http.expectOne('/api/v1/unidades').flush([]);
    await fixture.whenStable();
    const elemento = fixture.nativeElement as HTMLElement;
    const input = elemento.querySelector<HTMLInputElement>('input')!;
    input.value = VIN.toLowerCase();
    input.dispatchEvent(new Event('input'));
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
    return { fixture, elemento };
  }

  it('muestra la hoja agrupada, el IVA aparte y que cuadra', async () => {
    const { fixture, elemento } = await consultar();
    http.expectOne(URL).flush(HOJA);
    await fixture.whenStable();

    const texto = elemento.textContent ?? '';
    expect(texto).toContain('Cuadra con el mayor');
    expect(texto).toContain('Copart Inc.');
    expect(texto).toContain('7.75000000');
    expect(texto).toContain('crédito fiscal, no suma');
    expect(texto).toContain('OT-00001');
    expect(texto).toContain('70,443.75');
  });

  it('destaca la diferencia cuando no cuadra e imprime', async () => {
    const { fixture, elemento } = await consultar();
    http.expectOne(URL).flush({
      ...HOJA,
      saldo_mayor_gtq: '70493.750000',
      diferencia_gtq: '-50.000000',
      cuadra: false,
    });
    await fixture.whenStable();

    expect(elemento.querySelector('[role=alert]')?.textContent).toContain('No cuadra');
    const imprimir = vi.spyOn(window, 'print').mockImplementation(() => undefined);
    elemento.querySelector<HTMLButtonElement>('button.secundario')!.click();
    expect(imprimir).toHaveBeenCalled();
  });

  it('muestra el mensaje del servidor', async () => {
    const { fixture, elemento } = await consultar();
    http
      .expectOne(URL)
      .flush({ detail: `No existe la unidad con VIN ${VIN}` }, { status: 404, statusText: 'x' });
    await fixture.whenStable();
    expect(elemento.textContent).toContain('No existe la unidad');
  });
});
