import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ClientesPantalla } from './clientes';

const URL = '/api/v1/facturacion/clientes';

const EMPRESA = {
  id: 1,
  tipo: 'empresa',
  nombre: 'Transportes del Norte, S.A.',
  tipo_identificacion: 'nit',
  identificacion: '12345679',
  identificacion_formateada: '1234567-9',
  pais: null,
  direccion: null,
  telefono: '2222-3333',
  correo: 'compras@transportes.gt',
  agente_retencion_iva: true,
  agente_retencion_isr: false,
  creado_en: '2026-11-18T10:00:00Z',
};

describe('ClientesPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [ClientesPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(lista: unknown[] = []): Promise<ComponentFixture<ClientesPantalla>> {
    const fixture = TestBed.createComponent(ClientesPantalla);
    http.expectOne(URL).flush(lista);
    await fixture.whenStable();
    return fixture;
  }

  const elemento = (f: ComponentFixture<ClientesPantalla>) => f.nativeElement as HTMLElement;

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  function enviar(el: HTMLElement): void {
    el.querySelector('form.tarjeta')!.dispatchEvent(new Event('submit'));
  }

  it('lista los clientes con su identificación y retenciones', async () => {
    const el = elemento(await crear([EMPRESA]));
    const fila = el.querySelector('tbody')!.textContent;

    expect(fila).toContain('NIT 1234567-9');
    expect(fila).toContain('IVA');
    expect(fila).not.toContain('ISR');
  });

  it('registra una empresa con su NIT', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'tipo', 'empresa');
    escribir(el, 'nombre', ' Transportes del Norte, S.A. ');
    escribir(el, 'identificacion', '1234567-9');
    el.querySelector<HTMLInputElement>('[name=agente_retencion_iva]')!.click();
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toMatchObject({
      tipo: 'empresa',
      nombre: 'Transportes del Norte, S.A.',
      tipo_identificacion: 'nit',
      identificacion: '1234567-9',
      agente_retencion_iva: true,
      agente_retencion_isr: false,
    });
    envio.flush(EMPRESA);
    http.expectOne(URL).flush([EMPRESA]);
    await fixture.whenStable();

    expect(el.textContent).toContain('Cliente Transportes del Norte, S.A. registrado');
  });

  it('pide el país cuando se identifica con pasaporte', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    expect(el.querySelector('[name=pais]')).toBeNull();
    escribir(el, 'tipo_identificacion', 'pasaporte');
    await fixture.whenStable();
    expect(el.querySelector('[name=pais]')).not.toBeNull();

    escribir(el, 'nombre', 'John Smith');
    escribir(el, 'identificacion', 'X1234567');
    escribir(el, 'pais', 'us');
    enviar(el);

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toMatchObject({ tipo_identificacion: 'pasaporte', pais: 'US' });
    envio.flush({ ...EMPRESA, tipo: 'individual', tipo_identificacion: 'pasaporte' });
    http.expectOne(URL).flush([]);
  });

  it('no envía sin nombre ni identificación', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    enviar(el);
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('El nombre es obligatorio');
  });

  it('muestra el rechazo por cliente duplicado', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'nombre', 'Repetido');
    escribir(el, 'identificacion', '1234567-9');
    enviar(el);
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'Ya existe un cliente con el NIT 1234567-9' },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(el.textContent).toContain('Ya existe un cliente con el NIT 1234567-9');
  });

  it('consulta con el texto de búsqueda', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'buscar', 'norte');
    el.querySelectorAll('form')[1].dispatchEvent(new Event('submit'));

    http.expectOne(`${URL}?buscar=norte`).flush([EMPRESA]);
    await fixture.whenStable();
    expect(el.querySelector('tbody')!.textContent).toContain('Transportes del Norte');
  });
});
