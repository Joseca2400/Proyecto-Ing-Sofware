import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { DepreciacionPantalla } from './depreciacion';

const URL = '/api/v1/unidades/depreciacion/tipos';
const PICKUP = {
  tipo_vehiculo: 'pickup',
  vida_util_meses: 60,
  porcentaje_residual: '10.00',
  porcentaje_fiscal: '20.00',
};

describe('DepreciacionPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [DepreciacionPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lista los valores por tipo y guarda el editado', async () => {
    const fixture = TestBed.createComponent(DepreciacionPantalla);
    http.expectOne(URL).flush([PICKUP]);
    await fixture.whenStable();
    const elemento = fixture.nativeElement as HTMLElement;
    expect(elemento.textContent).toContain('Pickup');
    expect(elemento.textContent).toContain('20.00 %');

    elemento.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
    const envio = http.expectOne({ method: 'PUT', url: `${URL}/pickup` });
    expect(envio.request.body).toEqual({
      vida_util_meses: 60,
      porcentaje_residual: '10.00',
      porcentaje_fiscal: '20.00',
    });
    envio.flush(PICKUP);
    http.expectOne(URL).flush([PICKUP]);
    await fixture.whenStable();
    expect(elemento.textContent).toContain('guardados');
  });

  it('no envía un formulario incompleto y muestra el error del servidor', async () => {
    const fixture = TestBed.createComponent(DepreciacionPantalla);
    http.expectOne(URL).flush([PICKUP]);
    await fixture.whenStable();
    const elemento = fixture.nativeElement as HTMLElement;
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
    http.expectNone({ method: 'PUT' });

    elemento.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'PUT', url: `${URL}/pickup` })
      .flush({ detail: 'Sin permiso' }, { status: 403, statusText: 'x' });
    await fixture.whenStable();
    expect(elemento.textContent).toContain('Sin permiso');
  });
});
