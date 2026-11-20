import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CotizadorPantalla } from './cotizador';

const URL = '/api/v1/alquileres';

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

const MULTA = {
  ...GPS,
  id: 6,
  nombre: 'Reintegro de multa de tránsito',
  naturaleza: 'reintegro',
  aplica_iva: false,
  es_ingreso_acumulable: false,
  precio_sugerido: null,
  moneda: null,
};

const linea = (
  descripcion: string,
  naturaleza: string,
  total: string,
  base = total,
  iva = '0.00',
) => ({
  descripcion,
  naturaleza,
  aplica_iva: iva !== '0.00',
  cantidad: '1',
  precio_unitario: total,
  total,
  base,
  iva,
});

const COTIZACION = {
  moneda: 'USD',
  tarifa: {
    id: 1,
    tipo_vehiculo: 'sedan',
    vin: null,
    temporada: null,
    modalidad: 'diaria',
    moneda: 'GTQ',
    monto: '300.000000',
    km_incluido: null,
    costo_km_adicional: null,
    vigente_desde: '2026-01-01',
    creado_en: '2026-01-01T10:00:00Z',
  },
  periodos: 3,
  dias: 3,
  tipo_cambio: '7.75000000',
  tasa_iva: '0.120000',
  lineas: [
    linea('Alquiler diaria · sedan (por día)', 'ingreso', '116.13', '103.69', '12.44'),
    linea('Reintegro de multa de tránsito', 'reintegro', '20.00'),
  ],
  total_ingresos: '116.13',
  total_base: '103.69',
  total_iva: '12.44',
  total_depositos: '0.00',
  total_reintegros: '20.00',
  total_a_pagar: '136.13',
};

describe('CotizadorPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [CotizadorPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(): Promise<ComponentFixture<CotizadorPantalla>> {
    const fixture = TestBed.createComponent(CotizadorPantalla);
    http.expectOne(`${URL}/conceptos?solo_activos=true`).flush([GPS, MULTA]);
    await fixture.whenStable();
    return fixture;
  }

  function escribir(raiz: HTMLElement, nombre: string, valor: string): void {
    const campo = raiz.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  it('envía la cotización con sus cargos y muestra el desglose del servidor', async () => {
    const fixture = await crear();
    const raiz = fixture.nativeElement as HTMLElement;

    escribir(raiz, 'moneda', 'USD');
    escribir(raiz, 'fecha_salida', '2026-03-02');
    escribir(raiz, 'fecha_devolucion', '2026-03-05');
    raiz.querySelector<HTMLInputElement>('[name=incluir_6]')!.click();
    await fixture.whenStable();
    escribir(raiz, 'precio_6', '20.00');
    raiz.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: `${URL}/cotizaciones` });
    expect(envio.request.body).toEqual({
      tipo_vehiculo: 'sedan',
      modalidad: 'diaria',
      moneda: 'USD',
      fecha_salida: '2026-03-02',
      fecha_devolucion: '2026-03-05',
      cargos: [{ concepto_id: 6, cantidad: 1, precio: '20.00' }],
    });
    envio.flush(COTIZACION);
    await fixture.whenStable();

    const texto = raiz.textContent!;
    expect(texto).toContain('Convertido de GTQ');
    expect(texto).toContain('Reintegros de terceros');
    expect(raiz.querySelector('.resumen strong')!.textContent).toContain('136.13');
    expect(raiz.querySelector('tbody.lineas')!.textContent).toContain('12.44');
  });

  it('pide el monto de un cargo que no tiene precio en el tarifario', async () => {
    const fixture = await crear();
    const raiz = fixture.nativeElement as HTMLElement;

    raiz.querySelector<HTMLInputElement>('[name=incluir_6]')!.click();
    await fixture.whenStable();
    raiz.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: `${URL}/cotizaciones` });
    expect(raiz.textContent).toContain('Indique el monto de Reintegro de multa de tránsito');
  });

  it('muestra el rechazo del servidor cuando falta el tipo de cambio', async () => {
    const fixture = await crear();
    const raiz = fixture.nativeElement as HTMLElement;

    escribir(raiz, 'moneda', 'USD');
    raiz.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: `${URL}/cotizaciones` })
      .flush(
        { detail: 'No hay tipo de cambio del 02/03/2026 para convertir la tarifa a USD' },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(raiz.textContent).toContain('No hay tipo de cambio');
  });
});
