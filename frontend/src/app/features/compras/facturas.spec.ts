import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FacturasComprasPantalla } from './facturas';

const URL = '/api/v1/compras/facturas';
const URL_PROVEEDORES = '/api/v1/compras/proveedores';
const AUTORIZACION = '1A2B3C4D-1234-4ABC-9DEF-0123456789AB';

const GENERAL = {
  id: 1,
  tipo: 'local',
  nombre: 'Repuestos El Volante, S.A.',
  nit: '12345679',
  nit_formateado: '1234567-9',
  identificacion_fiscal: null,
  pais: null,
  regimen: 'general',
  rubro: 'repuestos',
  moneda_habitual: 'GTQ',
  dias_credito: 30,
  banco: null,
  cuenta_bancaria: null,
  creado_en: '2026-11-05T10:00:00Z',
};

const PEQUENO = {
  ...GENERAL,
  id: 2,
  nombre: 'Taller Don Chepe',
  nit: '576937K',
  nit_formateado: '576937-K',
  regimen: 'pequeno_contribuyente',
  dias_credito: 0,
};

const FACTURA = {
  id: 10,
  proveedor: {
    id: 1,
    nombre: 'Repuestos El Volante, S.A.',
    nit: '12345679',
    nit_formateado: '1234567-9',
    regimen: 'general',
  },
  serie: '1A2B3C4D',
  numero: '305419896',
  autorizacion: AUTORIZACION,
  fecha: '2026-10-15',
  regimen_proveedor: 'general',
  genera_credito_fiscal: true,
  total_base: '1250.500000',
  total_iva: '150.060000',
  credito_fiscal: '150.060000',
  total: '1400.560000',
  lineas: [
    {
      numero_linea: 1,
      descripcion: 'Pastillas de freno',
      cuenta: '5.1.02',
      linea_negocio: 'taller',
      vin: '1HGCM82633A004352',
      base: '1250.500000',
      iva: '150.060000',
    },
  ],
  cuenta_por_pagar: {
    id: 7,
    fecha: '2026-10-15',
    fecha_vencimiento: '2026-11-14',
    moneda: 'GTQ',
    monto: '1400.560000',
    saldo: '1400.560000',
  },
  creado_en: '2026-11-05T10:00:00Z',
};

const FACTURA_PEQUENO = {
  ...FACTURA,
  id: 11,
  proveedor: {
    ...FACTURA.proveedor,
    id: 2,
    nombre: 'Taller Don Chepe',
    regimen: 'pequeno_contribuyente',
  },
  regimen_proveedor: 'pequeno_contribuyente',
  genera_credito_fiscal: false,
  credito_fiscal: '0.000000',
};

describe('FacturasComprasPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [FacturasComprasPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(
    facturas: unknown[] = [],
  ): Promise<ComponentFixture<FacturasComprasPantalla>> {
    const fixture = TestBed.createComponent(FacturasComprasPantalla);
    const proveedores = http.expectOne((r) => r.url === URL_PROVEEDORES);
    expect(proveedores.request.params.get('tipo')).toBe('local');
    proveedores.flush([GENERAL, PEQUENO]);
    http.expectOne((r) => r.url === URL && r.method === 'GET').flush(facturas);
    await fixture.whenStable();
    return fixture;
  }

  function elemento(fixture: ComponentFixture<FacturasComprasPantalla>): HTMLElement {
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

  function enviar(el: HTMLElement): void {
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));
  }

  function llenarEncabezado(el: HTMLElement): void {
    elegir(el, 'proveedor_id', 1); // la opción 0 es el texto de ayuda
    escribir(el, 'serie', ' 1a2b3c4d ');
    escribir(el, 'numero', '305419896');
    escribir(el, 'autorizacion', AUTORIZACION.toLowerCase());
    escribir(el, 'fecha', '2026-10-15');
  }

  it('lista las facturas con su crédito fiscal y su cuenta por pagar', async () => {
    const fixture = await crear([FACTURA_PEQUENO, FACTURA]);
    const tabla = elemento(fixture).querySelector('tbody')!.textContent ?? '';

    expect(tabla).toContain('Repuestos El Volante, S.A.');
    expect(tabla).toContain('1A2B3C4D-305419896');
    expect(tabla).toContain('1,400.56');
    expect(tabla).toContain('150.06');
    expect(tabla).toContain('Sin crédito');
    expect(tabla).toContain('vence 2026-11-14');
    expect(tabla).toMatch(/5\.1\.02 · Taller\s+· 1HGCM82633A004352/);
  });

  it('ofrece solo proveedores locales con su régimen', async () => {
    const fixture = await crear();
    const opciones = elemento(fixture).querySelectorAll('select[name=proveedor_id] option');

    expect(opciones).toHaveLength(3);
    expect(opciones[2].textContent).toContain(
      'Taller Don Chepe · NIT 576937-K · Pequeño contribuyente',
    );
  });

  it('registra una factura con varias líneas y muestra los totales del servidor', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    llenarEncabezado(el);
    escribir(el, 'descripcion0', ' Pastillas de freno ');
    escribir(el, 'cuenta0', '5.1.02');
    escribir(el, 'base0', '1000.00');
    escribir(el, 'iva0', '120.00');
    el.querySelector<HTMLButtonElement>('button.agregar')!.click();
    await fixture.whenStable();
    escribir(el, 'descripcion1', 'Pintura');
    escribir(el, 'cuenta1', '5.1.03');
    escribir(el, 'linea_negocio1', 'venta');
    escribir(el, 'vin1', '1hgcm82633a004352');
    escribir(el, 'base1', '250.50');
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      proveedor_id: 1,
      serie: '1A2B3C4D',
      numero: '305419896',
      autorizacion: AUTORIZACION,
      fecha: '2026-10-15',
      lineas: [
        {
          descripcion: 'Pastillas de freno',
          cuenta: '5.1.02',
          linea_negocio: 'taller',
          base: '1000.00',
          iva: '120.00',
        },
        {
          descripcion: 'Pintura',
          cuenta: '5.1.03',
          linea_negocio: 'venta',
          vin: '1HGCM82633A004352',
          base: '250.50',
          iva: '0',
        },
      ],
    });
    envio.flush(FACTURA);
    http.expectOne((r) => r.url === URL && r.method === 'GET').flush([FACTURA]);
    await fixture.whenStable();

    const resultado = el.querySelector('.resultado')!.textContent ?? '';
    expect(resultado).toContain(
      'Factura 1A2B3C4D-305419896 de Repuestos El Volante, S.A. registrada',
    );
    expect(resultado).toContain('vencimiento 2026-11-14');
    expect(resultado).toContain('1,400.56');
    expect(el.querySelectorAll('.linea')).toHaveLength(1);
  });

  it('avisa que el IVA de un pequeño contribuyente no da crédito fiscal', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    llenarEncabezado(el);
    escribir(el, 'descripcion0', 'Servicio');
    escribir(el, 'cuenta0', '5.2.01');
    escribir(el, 'base0', '500');
    enviar(el);
    http.expectOne({ method: 'POST', url: URL }).flush(FACTURA_PEQUENO);
    http.expectOne((r) => r.url === URL && r.method === 'GET').flush([FACTURA_PEQUENO]);
    await fixture.whenStable();

    expect(el.querySelector('.resultado')!.textContent).toContain('no genera crédito fiscal');
  });

  it('no envía la factura con datos incompletos o mal escritos', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'serie', '1A2B3C4D');
    escribir(el, 'numero', '12A');
    escribir(el, 'autorizacion', 'no-es-uuid');
    escribir(el, 'descripcion0', 'Pintura');
    escribir(el, 'cuenta0', 'Gastos');
    escribir(el, 'vin0', '1HGCM82633A0O4352');
    escribir(el, 'base0', '1,000');
    enviar(el);
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL });
    const texto = el.textContent ?? '';
    expect(texto).toContain('Revisa los campos marcados');
    expect(texto).toContain('Elige el proveedor');
    expect(texto).toContain('Solo dígitos');
    expect(texto).toContain('UUID de la SAT');
    expect(texto).toContain('Código, ej. 5.1.02');
    expect(texto).toContain('sin I, O ni Q');
    expect(texto).toContain('Número positivo');
  });

  it('muestra el rechazo del servidor por DTE repetido', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    llenarEncabezado(el);
    escribir(el, 'descripcion0', 'Pastillas');
    escribir(el, 'cuenta0', '5.1.02');
    escribir(el, 'base0', '100');
    enviar(el);
    const detalle = 'El DTE serie 1A2B3C4D número 305419896 de Repuestos ya está registrado';
    http
      .expectOne({ method: 'POST', url: URL })
      .flush({ detail: detalle }, { status: 409, statusText: 'Conflict' });
    await fixture.whenStable();

    expect(el.querySelector('[role=alert]')!.textContent).toContain('ya está registrado');
  });

  it('quita líneas pero deja siempre al menos una', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    el.querySelector<HTMLButtonElement>('button.agregar')!.click();
    await fixture.whenStable();
    expect(el.querySelectorAll('.linea')).toHaveLength(2);

    el.querySelector<HTMLButtonElement>('button.quitar')!.click();
    await fixture.whenStable();
    expect(el.querySelectorAll('.linea')).toHaveLength(1);
    expect(el.querySelector<HTMLButtonElement>('button.quitar')!.disabled).toBe(true);
  });

  it('filtra las facturas por proveedor', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    elegir(el, 'filtro_proveedor', 2);

    const consulta = http.expectOne((r) => r.url === URL && r.method === 'GET');
    expect(consulta.request.params.get('proveedor_id')).toBe('2');
    consulta.flush([FACTURA_PEQUENO]);
    await fixture.whenStable();

    expect(el.querySelector('tbody')!.textContent).toContain('Taller Don Chepe');
  });
});
