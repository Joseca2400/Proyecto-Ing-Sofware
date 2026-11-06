import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { TipoCambioPantalla } from './tipo-cambio';

const URL = '/api/v1/configuracion/tipos-cambio';

describe('TipoCambioPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TipoCambioPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function texto(fixture: { nativeElement: unknown }): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  function llenar(elemento: HTMLElement, fecha: string, valor: string): void {
    const fechaInput = elemento.querySelector<HTMLInputElement>('input[type=date]')!;
    const valorInput = elemento.querySelector<HTMLInputElement>('input[type=text]')!;
    fechaInput.value = fecha;
    fechaInput.dispatchEvent(new Event('input'));
    valorInput.value = valor;
    valorInput.dispatchEvent(new Event('input'));
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
  }

  it('lista los tipos de cambio cargados', async () => {
    const fixture = TestBed.createComponent(TipoCambioPantalla);
    http
      .expectOne(URL)
      .flush([{ id: 1, fecha: '2026-11-02', valor: '7.75120000', origen: 'manual' }]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('2026-11-02');
    expect(texto(fixture)).toContain('7.75120000');
    expect(texto(fixture)).toContain('Manual');
  });

  it('envía el valor como texto y recarga la lista', async () => {
    const fixture = TestBed.createComponent(TipoCambioPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    llenar(fixture.nativeElement as HTMLElement, '2026-11-02', '7.75');
    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({ fecha: '2026-11-02', valor: '7.75' });
    envio.flush({ id: 1, fecha: '2026-11-02', valor: '7.75000000', origen: 'manual' });
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('guardado');
  });

  it('muestra el mensaje del backend cuando rechaza la carga', async () => {
    const fixture = TestBed.createComponent(TipoCambioPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    llenar(fixture.nativeElement as HTMLElement, '2026-11-02', '7.75');
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'Ya existe el tipo de cambio del 02/11/2026' },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(texto(fixture)).toContain('Ya existe el tipo de cambio del 02/11/2026');
  });

  it('no envía un valor con formato inválido', async () => {
    const fixture = TestBed.createComponent(TipoCambioPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    llenar(fixture.nativeElement as HTMLElement, '2026-11-02', '-7');
    http.expectNone({ method: 'POST', url: URL });
    await fixture.whenStable();
    expect(texto(fixture)).toContain('Número positivo');
  });
});
