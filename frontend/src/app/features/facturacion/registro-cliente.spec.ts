import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RegistroClientePantalla } from './registro-cliente';

const URL = '/api/v1/facturacion/clientes';

const INDIVIDUAL = {
  id: 1,
  tipo: 'individual',
  nombre: 'María Fernanda López',
  nit: '12345679',
  nit_formateado: '1234567-9',
  cui: '2584123450101',
  pasaporte: null,
  pais: null,
  direccion: null,
  telefono: '5555-1234',
  correo: 'maria@correo.com',
  agente_retencion_iva: false,
  agente_retencion_isr: false,
  exento_iva: false,
  motivo_exencion: null,
  creado_en: '2026-11-18T10:00:00Z',
};

const EMPRESA = {
  ...INDIVIDUAL,
  id: 2,
  tipo: 'empresa',
  nombre: 'Distribuidora La Ceiba, S.A.',
  nit: '576937K',
  nit_formateado: '576937-K',
  cui: null,
  telefono: null,
  correo: null,
  agente_retencion_iva: true,
};

const EXTRANJERO = {
  ...INDIVIDUAL,
  id: 3,
  nombre: 'John Smith',
  nit: null,
  nit_formateado: null,
  cui: null,
  pasaporte: 'X1234567',
  pais: 'US',
};

describe('RegistroClientePantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RegistroClientePantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(lista: unknown[] = []): Promise<ComponentFixture<RegistroClientePantalla>> {
    const fixture = TestBed.createComponent(RegistroClientePantalla);
    http.expectOne(URL).flush(lista);
    await fixture.whenStable();
    return fixture;
  }

  function elemento(fixture: ComponentFixture<RegistroClientePantalla>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  function enviar(el: HTMLElement): void {
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));
  }

  it('lista los clientes con su identificación y retenciones', async () => {
    const fixture = await crear([EMPRESA, EXTRANJERO, INDIVIDUAL]);
    const texto = elemento(fixture).querySelector('tbody')!.textContent ?? '';

    expect(texto).toContain('NIT 576937-K');
    expect(texto).toContain('IVA');
    expect(texto).toContain('Pasaporte X1234567 · US');
    expect(texto).toMatch(/NIT 1234567-9\s+· CUI 2584123450101/);
    expect(texto).toContain('maria@correo.com');
  });

  it('registra una persona guatemalteca con su CUI', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'nombre', ' María Fernanda López ');
    escribir(el, 'cui', '2584 12345 0101');
    escribir(el, 'telefono', '5555-1234');
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      tipo: 'individual',
      nombre: 'María Fernanda López',
      cui: '2584 12345 0101',
      telefono: '5555-1234',
      agente_retencion_iva: false,
      agente_retencion_isr: false,
    });
    envio.flush(INDIVIDUAL);
    http.expectOne(URL).flush([INDIVIDUAL]);
    await fixture.whenStable();

    expect(el.textContent).toContain('Cliente María Fernanda López registrado');
  });

  it('registra una empresa agente de retención con su NIT', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    el.querySelector<HTMLInputElement>('input[value=empresa]')!.click();
    await fixture.whenStable();
    expect(el.querySelector('[name=cui]')).toBeNull();
    expect(el.querySelector('input[value=extranjero]')).toBeNull();

    escribir(el, 'nombre', 'Distribuidora La Ceiba, S.A.');
    escribir(el, 'nit', '576937-k');
    el.querySelector<HTMLInputElement>('[name=agente_retencion_iva]')!.click();
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      tipo: 'empresa',
      nombre: 'Distribuidora La Ceiba, S.A.',
      nit: '576937-k',
      agente_retencion_iva: true,
      agente_retencion_isr: false,
    });
    envio.flush(EMPRESA);
    http.expectOne(URL).flush([EMPRESA]);
    await fixture.whenStable();
  });

  it('registra un cliente exento de IVA con su motivo', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    el.querySelector<HTMLInputElement>('input[value=empresa]')!.click();
    escribir(el, 'nombre', 'Embajada de Ejemplo');
    escribir(el, 'nit', '576937-k');
    el.querySelector<HTMLInputElement>('[name=exento_iva]')!.click();
    await fixture.whenStable();

    enviar(el);
    await fixture.whenStable();
    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('Indique el motivo de la exención de IVA');

    escribir(el, 'motivo_exencion', 'diplomatico');
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body.exento_iva).toBe(true);
    expect(envio.request.body.motivo_exencion).toBe('diplomatico');
    const exento = { ...EMPRESA, exento_iva: true, motivo_exencion: 'diplomatico' };
    envio.flush(exento);
    http.expectOne(URL).flush([exento]);
    await fixture.whenStable();

    expect(el.querySelector('tbody')!.textContent).toContain('Exento · Diplomático');
  });

  it('pide pasaporte y país a un extranjero', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    el.querySelector<HTMLInputElement>('input[value=extranjero]')!.click();
    await fixture.whenStable();
    expect(el.querySelector('[name=cui]')).toBeNull();

    escribir(el, 'nombre', 'John Smith');
    escribir(el, 'pasaporte', 'X1234567');
    escribir(el, 'pais', 'us');
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      tipo: 'individual',
      nombre: 'John Smith',
      pasaporte: 'X1234567',
      pais: 'US',
      agente_retencion_iva: false,
      agente_retencion_isr: false,
    });
    envio.flush(EXTRANJERO);
    http.expectOne(URL).flush([EXTRANJERO]);
    await fixture.whenStable();
  });

  it('no envía una persona sin CUI ni NIT', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'nombre', 'Sin identificación');
    enviar(el);
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('Indique el CUI o el NIT del cliente');
  });

  it('muestra el rechazo del servidor por cliente duplicado', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'nombre', 'Otra María');
    escribir(el, 'cui', '2584123450101');
    enviar(el);
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'Ya existe un cliente con el CUI 2584123450101' },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(el.textContent).toContain('Ya existe un cliente con el CUI 2584123450101');
  });

  it('consulta con los filtros de búsqueda y tipo', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'buscar', 'ceiba');
    escribir(el, 'filtro_tipo', 'empresa');
    el.querySelector('form.filtros')!.dispatchEvent(new Event('submit'));

    const consulta = http.expectOne((r) => r.url === URL);
    expect(consulta.request.params.get('buscar')).toBe('ceiba');
    expect(consulta.request.params.get('tipo')).toBe('empresa');
    consulta.flush([EMPRESA]);
  });
});
