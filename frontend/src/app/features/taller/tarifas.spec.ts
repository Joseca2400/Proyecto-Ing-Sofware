import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { TarifasTallerPantalla } from './tarifas';

const URL = '/api/v1/taller/tarifas';

describe('TarifasTallerPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TarifasTallerPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function texto(fixture: { nativeElement: unknown }): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  function llenar(elemento: HTMLElement, tarifa: string): void {
    const input = elemento.querySelector<HTMLInputElement>('input[type=text]')!;
    input.value = tarifa;
    input.dispatchEvent(new Event('input'));
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
  }

  it('lista las tarifas con su vigencia', async () => {
    const fixture = TestBed.createComponent(TarifasTallerPantalla);
    http
      .expectOne(URL)
      .flush([{ id: 1, tarifa_hora: '45.000000', vigente_desde: '2026-11-01', creado_en: 'x' }]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('2026-11-01');
    expect(texto(fixture)).toContain('45.00');
  });

  it('envía la tarifa como texto y recarga la lista', async () => {
    const fixture = TestBed.createComponent(TarifasTallerPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    llenar(fixture.nativeElement as HTMLElement, '52.50');
    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body.tarifa_hora).toBe('52.50');
    envio.flush({ id: 2, tarifa_hora: '52.500000', vigente_desde: '2026-12-01', creado_en: 'x' });
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('guardada');
  });

  it('muestra el mensaje del backend y no envía un valor inválido', async () => {
    const fixture = TestBed.createComponent(TarifasTallerPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    llenar(fixture.nativeElement as HTMLElement, '-3');
    http.expectNone({ method: 'POST', url: URL });
    await fixture.whenStable();
    expect(texto(fixture)).toContain('Número positivo');

    llenar(fixture.nativeElement as HTMLElement, '50');
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'Ya existe una tarifa vigente desde el 2026-11-18' },
        { status: 409, statusText: 'x' },
      );
    await fixture.whenStable();
    expect(texto(fixture)).toContain('Ya existe una tarifa');
  });
});
