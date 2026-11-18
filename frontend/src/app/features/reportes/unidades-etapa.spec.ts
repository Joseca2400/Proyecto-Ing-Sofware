import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ReporteUnidadesEtapa } from './reportes.service';
import { UnidadesEtapaPantalla } from './unidades-etapa';

const URL = '/api/v1/reportes/unidades-por-etapa';

const UNIDAD = {
  marca: 'Honda',
  linea: 'Accord',
  modelo: 2007,
  desde: '2026-10-01T10:00:00Z',
};

const REPORTE: ReporteUnidadesEtapa = {
  limite_dias: 30,
  valor_total: '137196.850000',
  estados: [
    { estado: 'lista', unidades: 1, valor: '77196.850000', dias_promedio: 40, excedidas: 1 },
    { estado: 'en_flota', unidades: 1, valor: '60000.000000', dias_promedio: 5, excedidas: 0 },
    { estado: 'vendida', unidades: 0, valor: '0.000000', dias_promedio: 0, excedidas: 0 },
  ],
  unidades: [
    {
      ...UNIDAD,
      vin: 'JHMCM56557C404453',
      estado: 'lista',
      dias_en_estado: 40,
      valor: '77196.850000',
      valor_en_libros: false,
      excede: true,
    },
    {
      ...UNIDAD,
      vin: '1HGCM82633A004352',
      estado: 'en_flota',
      dias_en_estado: 5,
      valor: '60000.000000',
      valor_en_libros: true,
      excede: false,
    },
  ],
};

describe('UnidadesEtapaPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [UnidadesEtapaPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('muestra cantidad, valor y días por estado y destaca las que superan el plazo', async () => {
    const fixture = TestBed.createComponent(UnidadesEtapaPantalla);
    http.expectOne(URL).flush(REPORTE);
    await fixture.whenStable();
    const elemento = fixture.nativeElement as HTMLElement;

    expect(elemento.textContent).toContain('137,196.85');
    expect(elemento.textContent).toContain('sobre el plazo');
    expect(elemento.textContent).toContain('en libros');
    expect(elemento.querySelectorAll('table')[1].querySelectorAll('tbody tr').length).toBe(2);

    // Abrir el listado de un estado.
    elemento.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    const filas = elemento.querySelectorAll('table')[1].querySelectorAll('tbody tr');
    expect(filas.length).toBe(1);
    expect(filas[0].textContent).toContain('JHMCM56557C404453');
  });

  it('consulta con el plazo indicado', async () => {
    const fixture = TestBed.createComponent(UnidadesEtapaPantalla);
    http.expectOne(URL).flush(REPORTE);
    await fixture.whenStable();
    const elemento = fixture.nativeElement as HTMLElement;
    const input = elemento.querySelector<HTMLInputElement>('input[name=limite_dias]')!;
    expect(input.value).toBe('30');
    input.value = '60';
    input.dispatchEvent(new Event('input'));
    elemento.querySelector<HTMLButtonElement>('.formulario button')!.click();

    const consulta = http.expectOne((r) => r.url === URL);
    expect(consulta.request.params.get('limite_dias')).toBe('60');
    consulta.flush({ ...REPORTE, limite_dias: 60 });
  });
});
