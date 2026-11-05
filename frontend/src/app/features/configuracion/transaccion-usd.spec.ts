import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { TransaccionUSDPantalla } from './transaccion-usd';

const URL = '/api/v1/configuracion/transacciones-usd';

const TX_STUB = {
  id: 1,
  fecha: '2026-11-02',
  monto_usd: '8500.000000',
  tipo_cambio_aplicado: '7.75000000',
  monto_gtq: '65875.000000',
  justificacion: null,
};

describe('TransaccionUSDPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TransaccionUSDPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function texto(fixture: { nativeElement: unknown }): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  function llenar(
    el: HTMLElement,
    fecha: string,
    monto: string,
    tipoPers = '',
    justificacion = '',
  ): void {
    const inputs = el.querySelectorAll<HTMLInputElement>('input[type=text], input[type=date]');
    // fecha es el primer input (type=date), monto el segundo, tipoPers el tercero
    const fechaInput = el.querySelector<HTMLInputElement>('input[type=date]')!;
    const montoInput = el.querySelectorAll<HTMLInputElement>('input[type=text]')[0]!;
    const tipoInput = el.querySelectorAll<HTMLInputElement>('input[type=text]')[1]!;

    fechaInput.value = fecha;
    fechaInput.dispatchEvent(new Event('input'));
    montoInput.value = monto;
    montoInput.dispatchEvent(new Event('input'));

    if (tipoPers) {
      tipoInput.value = tipoPers;
      tipoInput.dispatchEvent(new Event('input'));
    }

    if (justificacion) {
      const textarea = el.querySelector<HTMLTextAreaElement>('textarea');
      if (textarea) {
        textarea.value = justificacion;
        textarea.dispatchEvent(new Event('input'));
      }
    }

    el.querySelector('form')!.dispatchEvent(new Event('submit'));
  }

  it('lista las transacciones registradas', async () => {
    const fixture = TestBed.createComponent(TransaccionUSDPantalla);
    http.expectOne(URL).flush([TX_STUB]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('2026-11-02');
    expect(texto(fixture)).toContain('Banguat');
  });

  it('envía monto como texto y muestra el resultado', async () => {
    const fixture = TestBed.createComponent(TransaccionUSDPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    llenar(fixture.nativeElement as HTMLElement, '2026-11-02', '8500.00');
    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({ fecha: '2026-11-02', monto_usd: '8500.00' });
    envio.flush(TX_STUB);
    http.expectOne(URL).flush([TX_STUB]);
    await fixture.whenStable();

    expect(texto(fixture)).toContain('Resultado');
  });

  it('envía tipo personalizado y justificación cuando se indican', async () => {
    const fixture = TestBed.createComponent(TransaccionUSDPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    const el = fixture.nativeElement as HTMLElement;
    // Llenar tipo personalizado para que aparezca el textarea
    const tipoInput = el.querySelectorAll<HTMLInputElement>('input[type=text]')[1]!;
    tipoInput.value = '7.72';
    tipoInput.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    await fixture.whenStable();

    const montoInput = el.querySelectorAll<HTMLInputElement>('input[type=text]')[0]!;
    montoInput.value = '1000.00';
    montoInput.dispatchEvent(new Event('input'));

    const textarea = el.querySelector<HTMLTextAreaElement>('textarea')!;
    textarea.value = 'El banco lo aplicó';
    textarea.dispatchEvent(new Event('input'));

    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      fecha: jasmine.any(String),
      monto_usd: '1000.00',
      tipo_cambio_personalizado: '7.72',
      justificacion: 'El banco lo aplicó',
    });
    envio.flush({ ...TX_STUB, tipo_cambio_aplicado: '7.72000000', justificacion: 'El banco lo aplicó' });
    http.expectOne(URL).flush([]);
    await fixture.whenStable();
  });

  it('muestra el mensaje del backend cuando rechaza', async () => {
    const fixture = TestBed.createComponent(TransaccionUSDPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    llenar(fixture.nativeElement as HTMLElement, '2026-11-02', '1000.00');
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'No existe tipo de cambio para el 02/11/2026; cárguelo antes' },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(texto(fixture)).toContain('No existe tipo de cambio');
  });

  it('no envía si el monto tiene formato inválido', async () => {
    const fixture = TestBed.createComponent(TransaccionUSDPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    llenar(fixture.nativeElement as HTMLElement, '2026-11-02', '-500');
    http.expectNone({ method: 'POST', url: URL });
    expect(texto(fixture)).toContain('Número positivo');
  });

  it('no envía si falta la justificación para el tipo personalizado', async () => {
    const fixture = TestBed.createComponent(TransaccionUSDPantalla);
    http.expectOne(URL).flush([]);
    await fixture.whenStable();

    const el = fixture.nativeElement as HTMLElement;
    // Llenar tipo personalizado sin justificación
    const montoInput = el.querySelectorAll<HTMLInputElement>('input[type=text]')[0]!;
    montoInput.value = '1000.00';
    montoInput.dispatchEvent(new Event('input'));
    const tipoInput = el.querySelectorAll<HTMLInputElement>('input[type=text]')[1]!;
    tipoInput.value = '7.72';
    tipoInput.dispatchEvent(new Event('input'));

    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    http.expectNone({ method: 'POST', url: URL });
    await fixture.whenStable();

    expect(texto(fixture)).toContain('justificación');
  });
});
