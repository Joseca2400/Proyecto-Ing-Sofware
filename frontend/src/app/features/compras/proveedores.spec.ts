import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ProveedoresPantalla } from './proveedores';

const URL = '/api/v1/compras/proveedores';

const LOCAL = {
  id: 1,
  tipo: 'local',
  nombre: 'Repuestos El Volante, S.A.',
  nit: '12345679',
  nit_formateado: '1234567-9',
  identificacion_fiscal: null,
  pais: null,
  rubro: 'repuestos',
  moneda_habitual: 'GTQ',
  dias_credito: 30,
  banco: 'Banco Industrial',
  cuenta_bancaria: null,
  creado_en: '2026-11-05T10:00:00Z',
};

const EXTERIOR = {
  ...LOCAL,
  id: 2,
  tipo: 'exterior',
  nombre: 'Copart Inc.',
  nit: null,
  nit_formateado: null,
  identificacion_fiscal: '94-2867490',
  pais: 'US',
  rubro: 'subasta',
  moneda_habitual: 'USD',
  dias_credito: 0,
  banco: null,
};

describe('ProveedoresPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ProveedoresPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(lista: unknown[] = []): Promise<ComponentFixture<ProveedoresPantalla>> {
    const fixture = TestBed.createComponent(ProveedoresPantalla);
    http.expectOne(URL).flush(lista);
    await fixture.whenStable();
    return fixture;
  }

  function elemento(fixture: ComponentFixture<ProveedoresPantalla>): HTMLElement {
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

  it('lista los proveedores locales y del exterior', async () => {
    const fixture = await crear([EXTERIOR, LOCAL]);
    const texto = elemento(fixture).textContent ?? '';

    expect(texto).toContain('NIT 1234567-9');
    expect(texto).toContain('94-2867490 · US');
    expect(texto).toContain('Subasta');
    expect(texto).toContain('30 días');
    expect(texto).toContain('Contado');
  });

  it('registra un proveedor local con su NIT', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'nombre', ' Repuestos El Volante, S.A. ');
    escribir(el, 'nit', '1234567-9');
    escribir(el, 'dias_credito', '30');
    escribir(el, 'banco', 'Banco Industrial');
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      tipo: 'local',
      nombre: 'Repuestos El Volante, S.A.',
      nit: '1234567-9',
      rubro: 'repuestos',
      moneda_habitual: 'GTQ',
      dias_credito: 30,
      banco: 'Banco Industrial',
    });
    envio.flush(LOCAL);
    http.expectOne(URL).flush([LOCAL]);
    await fixture.whenStable();

    expect(el.textContent).toContain('Proveedor Repuestos El Volante, S.A. registrado');
  });

  it('pide identificación fiscal y país a un proveedor del exterior', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    el.querySelector<HTMLInputElement>('input[value=exterior]')!.click();
    await fixture.whenStable();
    expect(el.querySelector('[name=nit]')).toBeNull();

    escribir(el, 'nombre', 'Copart Inc.');
    escribir(el, 'identificacion_fiscal', '94-2867490');
    escribir(el, 'pais', 'us');
    escribir(el, 'rubro', 'subasta');
    escribir(el, 'moneda_habitual', 'USD');
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      tipo: 'exterior',
      nombre: 'Copart Inc.',
      identificacion_fiscal: '94-2867490',
      pais: 'US',
      rubro: 'subasta',
      moneda_habitual: 'USD',
      dias_credito: 0,
    });
    envio.flush(EXTERIOR);
    http.expectOne(URL).flush([EXTERIOR]);
    await fixture.whenStable();
  });

  it('no envía un proveedor local sin NIT', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'nombre', 'Sin NIT');
    enviar(el);
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('El NIT es obligatorio');
  });

  it('muestra el rechazo del servidor por dígito verificador', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'nombre', 'Repuestos');
    escribir(el, 'nit', '1234567-8');
    enviar(el);
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'El NIT no es válido: el dígito verificador no corresponde' },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();

    expect(el.textContent).toContain('el dígito verificador no corresponde');
  });

  it('consulta con los filtros de búsqueda, tipo y rubro', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'buscar', 'copart');
    escribir(el, 'filtro_tipo', 'exterior');
    escribir(el, 'filtro_rubro', 'subasta');
    el.querySelector('form.filtros')!.dispatchEvent(new Event('submit'));

    const consulta = http.expectOne((r) => r.url === URL && r.method === 'GET');
    expect(consulta.request.params.get('buscar')).toBe('copart');
    expect(consulta.request.params.get('tipo')).toBe('exterior');
    expect(consulta.request.params.get('rubro')).toBe('subasta');
    consulta.flush([EXTERIOR]);
    await fixture.whenStable();

    expect(el.textContent).toContain('Copart Inc.');
  });
});
