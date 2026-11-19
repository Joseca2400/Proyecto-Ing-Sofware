import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GastosImportacionPantalla } from './gastos-importacion';

const URL = '/api/v1/compras/gastos-importacion';
const URL_PROVEEDORES = '/api/v1/compras/proveedores';
const VIN = '1HGCM82633A004352';

const CONCEPTOS = [
  {
    codigo: 'flete',
    nombre: 'Flete',
    cuenta: '1.1.04.01',
    tratamiento: 'costo',
    suma_al_costo: true,
  },
  { codigo: 'dai', nombre: 'DAI', cuenta: '1.1.04.01', tratamiento: 'costo', suma_al_costo: true },
  {
    codigo: 'iva_importacion',
    nombre: 'IVA de importación',
    cuenta: '1.1.03.02',
    tratamiento: 'credito_fiscal',
    suma_al_costo: false,
  },
];

const NAVIERA = {
  id: 1,
  tipo: 'exterior',
  nombre: 'Seaboard Marine Ltd.',
  nit: null,
  nit_formateado: null,
  identificacion_fiscal: '59-1182372',
  pais: 'US',
  regimen: null,
  rubro: 'naviera',
  moneda_habitual: 'USD',
  dias_credito: 15,
  banco: null,
  cuenta_bancaria: null,
  creado_en: '2026-11-05T10:00:00Z',
};

const SAT = {
  ...NAVIERA,
  id: 2,
  tipo: 'local',
  nombre: 'Superintendencia de Administración Tributaria',
  nit: '16693949',
  nit_formateado: '1669394-9',
  identificacion_fiscal: null,
  pais: null,
  regimen: 'general',
  rubro: 'otros',
  moneda_habitual: 'GTQ',
  dias_credito: 0,
};

const FLETE_USD = {
  id: 10,
  vin: VIN,
  concepto: 'flete',
  concepto_nombre: 'Flete',
  proveedor: { id: 1, nombre: 'Seaboard Marine Ltd.', tipo: 'exterior' },
  fecha: '2026-10-20',
  documento: 'BL-778812',
  descripcion: 'Miami - Santo Tomás',
  moneda: 'USD',
  monto: '1250.500000',
  tipo_cambio: '7.75000000',
  monto_gtq: '9691.375000',
  cuenta: '1.1.04.01',
  tratamiento: 'costo',
  suma_al_costo: true,
  cuenta_por_pagar: {
    id: 7,
    fecha: '2026-10-20',
    fecha_vencimiento: '2026-11-04',
    moneda: 'USD',
    monto: '1250.500000',
    saldo: '1250.500000',
  },
  creado_en: '2026-11-06T10:00:00Z',
};

const IVA = {
  ...FLETE_USD,
  id: 11,
  concepto: 'iva_importacion',
  concepto_nombre: 'IVA de importación',
  proveedor: { id: 2, nombre: 'Superintendencia de Administración Tributaria', tipo: 'local' },
  documento: 'DUCA 26-001',
  descripcion: null,
  moneda: 'GTQ',
  monto: '1020.000000',
  tipo_cambio: null,
  monto_gtq: '1020.000000',
  cuenta: '1.1.03.02',
  tratamiento: 'credito_fiscal',
  suma_al_costo: false,
  cuenta_por_pagar: {
    ...FLETE_USD.cuenta_por_pagar,
    id: 8,
    fecha_vencimiento: '2026-10-20',
    moneda: 'GTQ',
    monto: '1020.000000',
    saldo: '1020.000000',
  },
};

const RESUMEN = {
  vin: VIN,
  gastos: 2,
  total_costo_gtq: '9691.375000',
  total_credito_fiscal_gtq: '1020.000000',
};

describe('GastosImportacionPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [GastosImportacionPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(
    gastos: unknown[] = [],
  ): Promise<ComponentFixture<GastosImportacionPantalla>> {
    const fixture = TestBed.createComponent(GastosImportacionPantalla);
    http.expectOne(`${URL}/conceptos`).flush(CONCEPTOS);
    http.expectOne((r) => r.url === URL_PROVEEDORES).flush([NAVIERA, SAT]);
    http.expectOne((r) => r.url === URL && r.method === 'GET').flush(gastos);
    await fixture.whenStable();
    return fixture;
  }

  function elemento(fixture: ComponentFixture<GastosImportacionPantalla>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  function elegir(el: HTMLElement, nombre: string, indice: number): void {
    const campo = el.querySelector<HTMLSelectElement>(`select[name=${nombre}]`)!;
    campo.selectedIndex = indice;
    campo.dispatchEvent(new Event('change'));
  }

  it('lista los gastos con su tratamiento, equivalente en quetzales y cuenta por pagar', async () => {
    const fixture = await crear([IVA, FLETE_USD]);
    const tabla = elemento(fixture).querySelector('tbody')!.textContent ?? '';

    expect(tabla).toContain(VIN);
    expect(tabla).toContain('Suma al costo');
    expect(tabla).toContain('Crédito fiscal');
    expect(tabla).toContain('1,250.50');
    expect(tabla).toContain('9,691.38');
    expect(tabla).toContain('TC 7.75000000');
    expect(tabla).toContain('vence 2026-11-04');
    expect(tabla).toContain('Miami - Santo Tomás');
  });

  it('ofrece el catálogo de conceptos y avisa cuál no suma al costo', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    const opciones = [...el.querySelectorAll('select[name=concepto] option')].map((o) =>
      o.textContent?.trim(),
    );
    expect(opciones).toEqual([
      'Selecciona',
      'Flete · 1.1.04.01',
      'DAI · 1.1.04.01',
      'IVA de importación · 1.1.03.02',
    ]);

    escribir(el, 'concepto', 'iva_importacion');
    await fixture.whenStable();
    expect(el.textContent).toContain('Crédito fiscal: no suma al costo');
  });

  it('registra un gasto en dólares y muestra lo que calculó el servidor', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'vin', '1hgcm82633a004352');
    escribir(el, 'concepto', 'flete');
    elegir(el, 'proveedor_id', 1); // la opción 0 es el texto de ayuda
    escribir(el, 'fecha', '2026-10-20');
    escribir(el, 'documento', ' BL-778812 ');
    escribir(el, 'moneda', 'USD');
    escribir(el, 'monto', '1250.50');
    escribir(el, 'descripcion', 'Miami - Santo Tomás');
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      vin: VIN,
      concepto: 'flete',
      proveedor_id: 1,
      fecha: '2026-10-20',
      documento: 'BL-778812',
      descripcion: 'Miami - Santo Tomás',
      moneda: 'USD',
      monto: '1250.50',
    });
    envio.flush(FLETE_USD);

    // Tras registrar, la lista queda filtrada por la unidad con su total.
    const consulta = http.expectOne((r) => r.url === URL && r.method === 'GET');
    expect(consulta.request.params.get('vin')).toBe(VIN);
    consulta.flush([FLETE_USD]);
    http
      .expectOne(`${URL}/unidad/${VIN}`)
      .flush({ ...RESUMEN, gastos: 1, total_credito_fiscal_gtq: '0.000000' });
    await fixture.whenStable();

    const resultado = el.querySelector('.resultado')!.textContent ?? '';
    expect(resultado).toContain(`Flete de la unidad ${VIN} registrado`);
    expect(resultado).toContain('Seaboard Marine Ltd.');
    expect(resultado).toContain('1,250.50');
    expect(resultado).toContain('vencimiento 2026-11-04');
    expect(resultado).toContain('9,691.38');
    expect(resultado).toContain('tipo de cambio 7.75000000');
    // Se conservan la unidad y el proveedor para el siguiente gasto; el monto queda vacío.
    expect(el.querySelector<HTMLInputElement>('[name=vin]')!.value).toBe('1hgcm82633a004352');
    expect(el.querySelector<HTMLInputElement>('[name=monto]')!.value).toBe('');
  });

  it('muestra el total por VIN que calcula el servidor, sin el IVA de importación', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'filtro_vin', '1hgcm82633a004352');
    el.querySelector('form.filtros')!.dispatchEvent(new Event('submit'));
    const consulta = http.expectOne((r) => r.url === URL && r.method === 'GET');
    expect(consulta.request.params.get('vin')).toBe(VIN);
    consulta.flush([IVA, FLETE_USD]);
    http.expectOne(`${URL}/unidad/${VIN}`).flush(RESUMEN);
    await fixture.whenStable();

    const resumen = el.querySelector('.resumen')!.textContent ?? '';
    expect(resumen).toMatch(/Suma al costo de 1HGCM82633A004352\s*\D*9,691\.38/);
    expect(resumen).toMatch(/crédito fiscal\)\s*\D*1,020\.00/);
  });

  it('no envía el gasto con datos incompletos o mal escritos', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'vin', '1HGCM82633A0O4352');
    escribir(el, 'monto', '1,000');
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL });
    const texto = el.textContent ?? '';
    expect(texto).toContain('Revisa los campos marcados');
    expect(texto).toContain('sin I, O ni Q');
    expect(texto).toContain('Elige el concepto');
    expect(texto).toContain('Elige el proveedor');
    expect(texto).toContain('Número positivo');
  });

  it('muestra el rechazo del servidor cuando falta el tipo de cambio', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'vin', VIN);
    escribir(el, 'concepto', 'flete');
    elegir(el, 'proveedor_id', 1);
    escribir(el, 'fecha', '2026-10-21');
    escribir(el, 'documento', 'BL-1');
    escribir(el, 'moneda', 'USD');
    escribir(el, 'monto', '100');
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));
    const detalle = 'No existe tipo de cambio para el 21/10/2026; cárguelo antes';
    http
      .expectOne({ method: 'POST', url: URL })
      .flush({ detail: detalle }, { status: 409, statusText: 'Conflict' });
    await fixture.whenStable();

    expect(el.querySelector('[role=alert]')!.textContent).toContain('No existe tipo de cambio');
  });
});
