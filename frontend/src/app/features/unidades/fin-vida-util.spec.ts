import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { FinVidaUtilPantalla } from './fin-vida-util';
import { FinVidaUtil } from './unidades.service';

const URL = '/api/v1/unidades/fin-vida-util';

const DATOS: FinVidaUtil = {
  regla: {
    kilometraje_limite: 100000,
    meses_limite: 24,
    porcentaje_aviso: '90.00',
    actualizado_por: 2,
    actualizado_en: '2026-11-18T10:00:00Z',
  },
  unidades: [
    {
      vin: '1HGCM82633A004352',
      marca: 'Honda',
      linea: 'Accord',
      modelo: 2007,
      estado: 'en_flota',
      fecha_alta: '2024-01-10',
      kilometraje: null,
      meses_en_flota: 34,
      situacion: 'alcanzado',
      valor_libros_financiero: '45000.000000',
      valor_libros_fiscal: '20000.000000',
    },
    {
      vin: 'JHMCM56557C404453',
      marca: 'Honda',
      linea: 'Fit',
      modelo: 2010,
      estado: 'alquilada',
      fecha_alta: '2026-11-18',
      kilometraje: 95000,
      meses_en_flota: 0,
      situacion: 'por_alcanzar',
      valor_libros_financiero: '77196.850000',
      valor_libros_fiscal: '77196.850000',
    },
  ],
};

describe('FinVidaUtilPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [FinVidaUtilPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lista las unidades que alcanzaron o están por alcanzar el límite con su valor en libros', async () => {
    const fixture = TestBed.createComponent(FinVidaUtilPantalla);
    http.expectOne(URL).flush(DATOS);
    await fixture.whenStable();
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Alcanzó el límite');
    expect(texto).toContain('Por alcanzarlo');
    expect(texto).toContain('45,000.00');
    const input = (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      'input[name=meses_limite]',
    )!;
    expect(input.value).toBe('24');
  });

  it('guarda la regla y exige al menos un límite', async () => {
    const fixture = TestBed.createComponent(FinVidaUtilPantalla);
    http.expectOne(URL).flush({ regla: null, unidades: [] });
    await fixture.whenStable();
    const elemento = fixture.nativeElement as HTMLElement;
    expect(elemento.textContent).toContain('no hay una regla');

    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
    http.expectNone({ method: 'PUT' });
    await fixture.whenStable();
    expect(elemento.textContent).toContain('Indica el límite');

    const meses = elemento.querySelector<HTMLInputElement>('input[name=meses_limite]')!;
    meses.value = '60';
    meses.dispatchEvent(new Event('input'));
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
    const envio = http.expectOne({ method: 'PUT', url: `${URL}/regla` });
    expect(envio.request.body).toEqual({
      kilometraje_limite: null,
      meses_limite: 60,
      porcentaje_aviso: '90',
    });
    envio.flush(DATOS.regla);
    http.expectOne(URL).flush(DATOS);
    await fixture.whenStable();
    expect(elemento.textContent).toContain('Regla guardada');
  });
});
