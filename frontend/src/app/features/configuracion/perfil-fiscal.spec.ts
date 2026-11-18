import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { PerfilFiscalPantalla } from './perfil-fiscal';

const URL = '/api/v1/configuracion/perfil-fiscal';
const PERFIL = {
  id: 1,
  vigente_desde: '2026-01-01',
  razon_social: 'Kilómetro Cero, S. A.',
  nombre_comercial: 'Kilómetro Cero',
  nit: '1234567-9',
  direccion_fiscal: 'Zona 10',
  establecimiento: '1',
  regimen_isr: 'utilidades',
  agente_retencion_iva: true,
  agente_retencion_isr: false,
};

describe('PerfilFiscalPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [PerfilFiscalPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function texto(fixture: { nativeElement: unknown }): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  function rellenar(elemento: HTMLElement): void {
    const campos: Record<string, string> = {
      razon_social: 'Kilómetro Cero, S. A.',
      nombre_comercial: 'Kilómetro Cero',
      nit: '1234567-9',
      direccion_fiscal: 'Zona 10',
      establecimiento: '1',
    };
    for (const [nombre, valor] of Object.entries(campos)) {
      const input = elemento.querySelector<HTMLInputElement>(`[formControlName=${nombre}]`)!;
      input.value = valor;
      input.dispatchEvent(new Event('input'));
    }
  }

  it('muestra el perfil vigente y el historial', async () => {
    const fixture = TestBed.createComponent(PerfilFiscalPantalla);
    http.expectOne(URL).flush(PERFIL);
    http.expectOne(`${URL}/historial`).flush([PERFIL]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('Kilómetro Cero, S. A.');
    expect(texto(fixture)).toContain('1234567-9');
    expect(texto(fixture)).toContain('Sobre utilidades');
  });

  it('avisa cuando todavía no hay perfil', async () => {
    const fixture = TestBed.createComponent(PerfilFiscalPantalla);
    http.expectOne(URL).flush({ detail: 'sin perfil' }, { status: 404, statusText: 'Not Found' });
    http.expectOne(`${URL}/historial`).flush([]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('Todavía no hay un perfil fiscal registrado');
  });

  it('registra un cambio y recarga', async () => {
    const fixture = TestBed.createComponent(PerfilFiscalPantalla);
    http.expectOne(URL).flush({}, { status: 404, statusText: 'Not Found' });
    http.expectOne(`${URL}/historial`).flush([]);
    await fixture.whenStable();

    const elemento = fixture.nativeElement as HTMLElement;
    rellenar(elemento);
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toMatchObject({
      nit: '1234567-9',
      regimen_isr: 'utilidades',
      agente_retencion_iva: false,
    });
    envio.flush(PERFIL);
    http.expectOne({ method: 'GET', url: URL }).flush(PERFIL);
    http.expectOne(`${URL}/historial`).flush([PERFIL]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('guardado');
  });

  it('muestra el mensaje del backend cuando rechaza el NIT', async () => {
    const fixture = TestBed.createComponent(PerfilFiscalPantalla);
    http.expectOne(URL).flush({}, { status: 404, statusText: 'Not Found' });
    http.expectOne(`${URL}/historial`).flush([]);
    await fixture.whenStable();

    const elemento = fixture.nativeElement as HTMLElement;
    rellenar(elemento);
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'El NIT no es válido: el dígito verificador no corresponde' },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();

    expect(texto(fixture)).toContain('dígito verificador');
  });

  it('no envía el formulario incompleto', async () => {
    const fixture = TestBed.createComponent(PerfilFiscalPantalla);
    http.expectOne(URL).flush({}, { status: 404, statusText: 'Not Found' });
    http.expectOne(`${URL}/historial`).flush([]);
    await fixture.whenStable();

    (fixture.nativeElement as HTMLElement)
      .querySelector('form')!
      .dispatchEvent(new Event('submit'));
    http.expectNone({ method: 'POST', url: URL });
  });
});
