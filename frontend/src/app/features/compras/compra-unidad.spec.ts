import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CompraUnidadPantalla } from './compra-unidad';

const URL = '/api/v1/compras/compras-unidades';
const URL_PROVEEDORES = '/api/v1/compras/proveedores';
const URL_CATALOGOS = '/api/v1/unidades/catalogos';
const VIN = '1HGCM82633A004352';

const CATALOGOS = {
  estados: ['en_transito', 'en_aduana'],
  tipos_vehiculo: ['sedan', 'suv'],
  lineas_negocio: ['alquiler', 'venta'],
};

const SUBASTA = {
  id: 1,
  tipo: 'exterior',
  nombre: 'Copart Inc.',
  nit: null,
  nit_formateado: null,
  identificacion_fiscal: '94-2867490',
  pais: 'US',
  regimen: null,
  rubro: 'subasta',
  moneda_habitual: 'USD',
  dias_credito: 30,
  banco: null,
  cuenta_bancaria: null,
  creado_en: '2026-11-05T10:00:00Z',
};

const COMPRA = {
  id: 5,
  vin: VIN,
  proveedor: { id: 1, nombre: 'Copart Inc.', tipo: 'exterior' },
  fecha: '2026-10-20',
  documento: 'LOT-44871203',
  precio_usd: '8500.000000',
  comision_usd: '350.000000',
  documentacion_usd: '75.000000',
  arrastre_usd: '150.000000',
  total_usd: '9075.000000',
  tipo_cambio: '7.75000000',
  total_gtq: '70331.250000',
  partida_id: 12,
  cuenta_por_pagar: {
    id: 9,
    fecha: '2026-10-20',
    fecha_vencimiento: '2026-11-19',
    moneda: 'USD',
    monto: '9075.000000',
    saldo: '9075.000000',
  },
  creado_en: '2026-11-06T10:00:00Z',
};

describe('CompraUnidadPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [CompraUnidadPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(compras: unknown[] = []): Promise<ComponentFixture<CompraUnidadPantalla>> {
    const fixture = TestBed.createComponent(CompraUnidadPantalla);
    http.expectOne(URL_CATALOGOS).flush(CATALOGOS);
    const proveedores = http.expectOne((r) => r.url === URL_PROVEEDORES);
    expect(proveedores.request.params.get('tipo')).toBe('exterior');
    proveedores.flush([SUBASTA]);
    http.expectOne((r) => r.url === URL && r.method === 'GET').flush(compras);
    await fixture.whenStable();
    return fixture;
  }

  function elemento(fixture: ComponentFixture<CompraUnidadPantalla>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  function llenar(el: HTMLElement): void {
    const proveedor = el.querySelector<HTMLSelectElement>('select[name=proveedor_id]')!;
    proveedor.selectedIndex = 1; // la opción 0 es el texto de ayuda
    proveedor.dispatchEvent(new Event('change'));
    escribir(el, 'fecha', '2026-10-20');
    escribir(el, 'documento', ' LOT-44871203 ');
    escribir(el, 'vin', '1hgcm82633a004352');
    escribir(el, 'marca', 'Honda');
    escribir(el, 'linea', 'Accord');
    escribir(el, 'modelo', '2007');
    escribir(el, 'color', 'Gris');
    escribir(el, 'tipo_vehiculo', 'sedan');
    escribir(el, 'precio_usd', '8500.00');
    escribir(el, 'comision_usd', '350.00');
  }

  it('lista las compras con su total en dólares, en quetzales y la cuenta por pagar', async () => {
    const fixture = await crear([COMPRA]);
    const tabla = elemento(fixture).querySelector('tbody')!.textContent ?? '';

    expect(tabla).toContain(VIN);
    expect(tabla).toContain('Copart Inc.');
    expect(tabla).toContain('LOT-44871203');
    expect(tabla).toContain('9,075.00');
    expect(tabla).toContain('70,331.25');
    expect(tabla).toContain('TC 7.75000000');
    expect(tabla).toContain('vence 2026-11-19');
  });

  it('registra la compra y muestra la unidad, la cuenta por pagar y la partida', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    llenar(el);
    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL });
    // Los montos van como texto; los cargos vacíos van en cero y la suma la hace el servidor.
    expect(envio.request.body).toEqual({
      proveedor_id: 1,
      fecha: '2026-10-20',
      documento: 'LOT-44871203',
      vin: VIN,
      marca: 'Honda',
      linea: 'Accord',
      modelo: 2007,
      color: 'Gris',
      tipo_vehiculo: 'sedan',
      precio_usd: '8500.00',
      comision_usd: '350.00',
      documentacion_usd: '0',
      arrastre_usd: '0',
    });
    envio.flush(COMPRA);
    http.expectOne((r) => r.url === URL && r.method === 'GET').flush([COMPRA]);
    await fixture.whenStable();

    const resultado = el.querySelector('[role=status]')!.textContent ?? '';
    expect(resultado).toContain(`Unidad ${VIN} comprada a Copart Inc.`);
    expect(resultado).toContain('queda en tránsito');
    expect(resultado).toContain('70,331.25');
    expect(resultado).toContain('vencimiento 2026-11-19');
    expect(resultado).toContain('Partida contable 12 generada');
  });

  it('muestra el error del servidor cuando la compra no se puede registrar', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    llenar(el);
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: `Ya existe una unidad con el VIN ${VIN}` },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(el.querySelector('[role=alert]')!.textContent).toContain(
      `Ya existe una unidad con el VIN ${VIN}`,
    );
    expect(el.querySelector('[role=status]')).toBeNull();
  });

  it('no envía la compra con campos inválidos', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'vin', 'CORTO');
    escribir(el, 'precio_usd', '-5');
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    expect(el.textContent).toContain('Revisa los campos marcados');
    expect(el.textContent).toContain('17 caracteres, sin I, O ni Q');
    expect(el.textContent).toContain('Número positivo');
    http.expectNone({ method: 'POST', url: URL });
  });
});
