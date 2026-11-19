import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FacturasPantalla } from './facturas';

const URL = '/api/v1/facturacion/facturas';
const URL_CLIENTES = '/api/v1/facturacion/clientes';

const CERTIFICADA = {
  id: 1,
  cliente_id: 3,
  fecha: '2026-10-20',
  moneda: 'GTQ',
  tipo_cambio: null,
  origen_tipo: null,
  origen_id: null,
  dias_credito: 30,
  emisor_nit: '12345679',
  emisor_nombre: 'Kilómetro Cero, S. A.',
  receptor_id: '576937K',
  receptor_nombre: 'Transportes del Norte',
  base: '1000.000000',
  iva: '120.000000',
  total: '1120.000000',
  total_gtq: '1120.000000',
  estado: 'certificada',
  serie: 'A1B2C3D4',
  numero: '123456789',
  autorizacion: 'A1B2C3D4-1234-5678-9ABC-DEF012345678',
  certificada_en: '2026-10-20T15:00:00Z',
  xml: '<DTE Tipo="FACT" />',
  motivo_rechazo: null,
  partida_id: 9,
  lineas: [],
  cuenta_por_cobrar: {
    id: 1,
    fecha: '2026-10-20',
    fecha_vencimiento: '2026-11-19',
    moneda: 'GTQ',
    monto: '1120.000000',
    saldo: '1120.000000',
  },
};
const RECHAZADA = {
  ...CERTIFICADA,
  id: 2,
  estado: 'rechazada',
  serie: null,
  numero: null,
  autorizacion: null,
  certificada_en: null,
  xml: null,
  partida_id: null,
  cuenta_por_cobrar: null,
  motivo_rechazo: 'receptor inactivo',
};

describe('FacturasPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [FacturasPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(lista: unknown[] = []): Promise<ComponentFixture<FacturasPantalla>> {
    const fixture = TestBed.createComponent(FacturasPantalla);
    http.expectOne(URL_CLIENTES).flush([]);
    http.expectOne(URL).flush(lista);
    await fixture.whenStable();
    return fixture;
  }

  const elemento = (f: ComponentFixture<FacturasPantalla>) => f.nativeElement as HTMLElement;

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  function enviar(el: HTMLElement): void {
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
  }

  function llenar(el: HTMLElement): void {
    escribir(el, 'fecha', '2026-10-20');
    escribir(el, 'descripcion0', ' Alquiler semanal ');
    escribir(el, 'precio_unitario0', '1120.00');
    escribir(el, 'vin0', '1hgcm82633a004352');
  }

  it('lista las facturas con su estado y muestra el detalle', async () => {
    const fixture = await crear([CERTIFICADA, RECHAZADA]);
    const el = elemento(fixture);

    const filas = el.querySelectorAll('tbody tr');
    expect(filas[0].textContent).toContain('certificada');
    expect(filas[1].textContent).toContain('rechazada');

    filas[1].querySelector('button')!.click();
    await fixture.whenStable();
    expect(el.querySelector('.detalle')!.textContent).toContain(
      'El certificador rechazó la factura: receptor inactivo',
    );
  });

  it('emite a Consumidor Final y muestra la certificación y el XML', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    llenar(el);
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      cliente_id: null,
      fecha: '2026-10-20',
      moneda: 'GTQ',
      dias_credito: 0,
      lineas: [
        {
          descripcion: 'Alquiler semanal',
          cantidad: '1',
          precio_unitario: '1120.00',
          linea_negocio: 'alquiler',
          vin: '1HGCM82633A004352',
        },
      ],
    });
    envio.flush(CERTIFICADA);
    http.expectOne(URL).flush([CERTIFICADA]);
    await fixture.whenStable();

    const detalle = el.querySelector('.detalle')!.textContent;
    expect(detalle).toContain('Factura A1B2C3D4-123456789 certificada a Transportes del Norte');
    expect(detalle).toContain('A1B2C3D4-1234-5678-9ABC-DEF012345678');
    expect(detalle).toContain('<DTE Tipo="FACT" />');
  });

  it('muestra el error del servidor', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    llenar(el);
    enviar(el);
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'No existe tipo de cambio para el 20/10/2026' },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(el.textContent).toContain('No existe tipo de cambio para el 20/10/2026');
  });

  it('no envía sin fecha ni precio', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    enviar(el);
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('Revisa los campos marcados');
  });
});
