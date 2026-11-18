import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { CuentasBancariasPantalla } from './cuentas-bancarias';

const URL = '/api/v1/configuracion/cuentas-bancarias';
const CUENTAS = '/api/v1/configuracion/cuentas';
const catalogo = [
  cuenta(1, '1.1.01', 'Caja y bancos', false, false),
  cuenta(2, '1.1.01.02', 'Bancos en quetzales', true, false),
  cuenta(3, '1.1.01.03', 'Bancos en dólares', true, true),
];
const BANCARIA = {
  id: 7,
  banco: 'Banco Industrial',
  numero: '123-4',
  tipo: 'monetaria',
  moneda: 'GTQ',
  cuenta_id: 2,
  siguiente_cheque: 100,
  activa: true,
};

function cuenta(id: number, codigo: string, nombre: string, es_detalle: boolean, usd: boolean) {
  return { id, codigo, nombre, es_detalle, monetaria_usd: usd };
}

describe('CuentasBancariasPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [CuentasBancariasPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function abrir(bancarias: unknown[] = []) {
    const fixture = TestBed.createComponent(CuentasBancariasPantalla);
    http.expectOne(CUENTAS).flush(catalogo);
    http.expectOne(URL).flush(bancarias);
    await fixture.whenStable();
    return fixture;
  }

  function texto(fixture: { nativeElement: unknown }): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  function campo(fixture: { nativeElement: unknown }, nombre: string): HTMLInputElement {
    return (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      `[formControlName=${nombre}]`,
    )!;
  }

  function escribir(elemento: HTMLInputElement, valor: string): void {
    elemento.value = valor;
    elemento.dispatchEvent(new Event(elemento.tagName === 'SELECT' ? 'change' : 'input'));
  }

  it('lista las cuentas con su cuenta contable', async () => {
    const fixture = await abrir([BANCARIA]);

    expect(texto(fixture)).toContain('Banco Industrial');
    expect(texto(fixture)).toContain('1.1.01.02 Bancos en quetzales');
    expect(texto(fixture)).toContain('Activa');
  });

  it('ofrece solo cuentas de detalle y, en USD, solo las monetarias en USD', async () => {
    const fixture = await abrir();
    const opciones = () =>
      Array.from(campo(fixture, 'cuenta_id').querySelectorAll('option')).map((o) => o.textContent);

    expect(opciones().join()).toContain('Bancos en quetzales');
    expect(opciones().join()).not.toContain('Caja y bancos');

    escribir(campo(fixture, 'moneda'), 'USD');
    await fixture.whenStable();
    expect(opciones().join()).not.toContain('Bancos en quetzales');
    expect(opciones().join()).toContain('Bancos en dólares');
  });

  it('crea la cuenta y recarga la lista', async () => {
    const fixture = await abrir();
    escribir(campo(fixture, 'banco'), 'Banco Industrial');
    escribir(campo(fixture, 'numero'), '123-4');
    fixture.componentInstance['formulario'].controls.cuenta_id.setValue(2);
    (fixture.nativeElement as HTMLElement)
      .querySelector('form')!
      .dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toMatchObject({
      banco: 'Banco Industrial',
      numero: '123-4',
      moneda: 'GTQ',
      cuenta_id: 2,
    });
    envio.flush(BANCARIA);
    http.expectOne({ method: 'GET', url: URL }).flush([BANCARIA]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('guardada');
  });

  it('muestra el mensaje del backend cuando rechaza la cuenta', async () => {
    const fixture = await abrir();
    escribir(campo(fixture, 'banco'), 'Banco Industrial');
    escribir(campo(fixture, 'numero'), '123-4');
    fixture.componentInstance['formulario'].controls.cuenta_id.setValue(2);
    (fixture.nativeElement as HTMLElement)
      .querySelector('form')!
      .dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: URL })
      .flush({ detail: 'Ya existe la cuenta 123-4' }, { status: 409, statusText: 'Conflict' });
    await fixture.whenStable();

    expect(texto(fixture)).toContain('Ya existe la cuenta 123-4');
  });

  it('no envía el formulario sin cuenta contable', async () => {
    const fixture = await abrir();
    (fixture.nativeElement as HTMLElement)
      .querySelector('form')!
      .dispatchEvent(new Event('submit'));
    http.expectNone({ method: 'POST', url: URL });
  });

  it('inactiva una cuenta', async () => {
    const fixture = await abrir([BANCARIA]);
    const botones = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLButtonElement>('td button'),
    );
    botones.find((b) => b.textContent?.includes('Inactivar'))!.click();

    http
      .expectOne({ method: 'POST', url: `${URL}/7/inactivar` })
      .flush({ ...BANCARIA, activa: false });
    http.expectOne({ method: 'GET', url: URL }).flush([{ ...BANCARIA, activa: false }]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('Inactiva');
  });

  it('guarda la numeración de cheques', async () => {
    const fixture = await abrir([BANCARIA]);
    const el = fixture.nativeElement as HTMLElement;
    const entrada = el.querySelector<HTMLInputElement>('td input[type=number]')!;
    entrada.value = '250';
    Array.from(el.querySelectorAll<HTMLButtonElement>('td button'))
      .find((b) => b.textContent?.includes('Guardar'))!
      .click();

    const envio = http.expectOne({ method: 'PUT', url: `${URL}/7/cheques` });
    expect(envio.request.body).toEqual({ siguiente_cheque: 250 });
    envio.flush({ ...BANCARIA, siguiente_cheque: 250 });
    http.expectOne({ method: 'GET', url: URL }).flush([{ ...BANCARIA, siguiente_cheque: 250 }]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('Numeración de cheques');
  });
});
