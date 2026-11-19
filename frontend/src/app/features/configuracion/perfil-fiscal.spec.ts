import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PerfilFiscalPantalla } from './perfil-fiscal';

const URL = '/api/v1/configuracion/perfil-fiscal';
const URL_TASAS = '/api/v1/configuracion/tasas-impositivas';

const PERFIL = {
  id: 1,
  vigente_desde: '2026-01-01',
  razon_social: 'Kilómetro Cero, S.A.',
  nombre_comercial: 'Kilómetro Cero',
  nit: '12345679',
  nit_formateado: '1234567-9',
  direccion_fiscal: 'Calzada Roosevelt 22-43 zona 11',
  establecimiento_sat: 1,
  regimen_isr: 'sobre_utilidades',
  agente_retencion_iva: true,
  agente_retencion_isr: false,
  tasas_del_regimen: ['IVA_GENERAL', 'ISR_UTILIDADES', 'ISO', 'UMBRAL_CF'],
  creado_en: '2026-01-01T10:00:00Z',
};

const tasa = (id: number, tipo: string, porcentaje: string | null, monto: string | null) => ({
  id,
  tipo,
  tasa: null,
  porcentaje,
  monto_limite: monto,
  vigente_desde: '2015-01-01',
});

const TASAS = [
  tasa(1, 'IVA_GENERAL', '12', null),
  tasa(2, 'ISO', '1', null),
  tasa(3, 'ISR_SIMPLIFICADO_1', '5', '30000.000000'),
  tasa(4, 'UMBRAL_CF', null, '2500.000000'),
];

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

  async function crear(
    versiones: unknown[] = [],
    tasas: unknown[] = TASAS,
  ): Promise<ComponentFixture<PerfilFiscalPantalla>> {
    const fixture = TestBed.createComponent(PerfilFiscalPantalla);
    http.expectOne(URL).flush(versiones);
    http.expectOne(URL_TASAS).flush(tasas);
    await fixture.whenStable();
    return fixture;
  }

  function elemento(fixture: ComponentFixture<PerfilFiscalPantalla>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  it('sin perfil invita a registrarlo', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    expect(el.textContent).toContain('Todavía no hay un perfil fiscal vigente');
    expect(el.querySelector('form.formulario button')!.textContent).toContain('Registrar perfil');
  });

  it('registra el perfil fiscal con su régimen y vigencia', async () => {
    const fixture = await crear();
    const el = elemento(fixture);

    escribir(el, 'razon_social', ' Kilómetro Cero, S.A. ');
    escribir(el, 'nombre_comercial', 'Kilómetro Cero');
    escribir(el, 'nit', '1234567-9');
    escribir(el, 'direccion_fiscal', 'Calzada Roosevelt 22-43 zona 11');
    escribir(el, 'regimen_isr', 'opcional_simplificado');
    escribir(el, 'vigente_desde', '2026-01-01');
    el.querySelector<HTMLInputElement>('[name=agente_retencion_iva]')!.click();
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      vigente_desde: '2026-01-01',
      razon_social: 'Kilómetro Cero, S.A.',
      nombre_comercial: 'Kilómetro Cero',
      nit: '1234567-9',
      direccion_fiscal: 'Calzada Roosevelt 22-43 zona 11',
      establecimiento_sat: 1,
      regimen_isr: 'opcional_simplificado',
      agente_retencion_iva: true,
      agente_retencion_isr: false,
    });
    envio.flush(PERFIL);
    http.expectOne(URL).flush([PERFIL]);
    http.expectOne(URL_TASAS).flush(TASAS);
    await fixture.whenStable();

    expect(el.textContent).toContain('Perfil fiscal guardado, vigente desde el 2026-01-01');
  });

  it('muestra el perfil vigente, parte de él para un cambio y resalta sus tasas', async () => {
    const fixture = await crear([PERFIL]);
    const el = elemento(fixture);

    expect(el.querySelector('.resumen')!.textContent).toContain('NIT 1234567-9');
    expect(el.querySelector('.resumen')!.textContent).toContain('Agente de retención de IVA');
    expect(el.querySelector<HTMLInputElement>('[name=razon_social]')!.value).toBe(
      'Kilómetro Cero, S.A.',
    );
    expect(el.querySelector('form.formulario button')!.textContent).toContain('Guardar cambio');

    const filas = [...el.querySelectorAll('tbody.tasas tr')].map((f) => f.textContent ?? '');
    expect(filas[0]).toContain('12 %');
    expect(filas[0]).toContain('Aplica a la empresa');
    expect(filas[1]).toContain('Aplica a la empresa'); // ISO, régimen sobre utilidades
    expect(filas[2]).toMatch(/5 %\s*hasta\s*Q\s?30,000\.00/);
    expect(filas[2]).not.toContain('Aplica a la empresa');
    expect(filas[3]).toContain('2,500.00');
  });

  it('muestra el rechazo del servidor a una vigencia ya cubierta', async () => {
    const fixture = await crear([PERFIL]);
    const el = elemento(fixture);

    escribir(el, 'vigente_desde', '2025-12-31');
    el.querySelector('form.formulario')!.dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'La vigencia debe ser posterior a la del perfil actual (01/01/2026)' },
        { status: 400, statusText: 'Bad Request' },
      );
    await fixture.whenStable();

    expect(el.textContent).toContain('posterior a la del perfil actual');
  });

  it('agrega una tasa nueva con su vigencia', async () => {
    const fixture = await crear([PERFIL]);
    const el = elemento(fixture);
    const formulario = el.querySelectorAll('form.formulario')[1];

    escribir(el, 'tasa_porcentaje', '12.5');
    escribir(el, 'tasa_vigente_desde', '2027-01-01');
    formulario.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL_TASAS });
    expect(envio.request.body).toEqual({
      tipo: 'IVA_GENERAL',
      vigente_desde: '2027-01-01',
      porcentaje: '12.5',
    });
    envio.flush({ ...tasa(9, 'IVA_GENERAL', '12.5', null), vigente_desde: '2027-01-01' });
    http.expectOne(URL_TASAS).flush(TASAS);
    await fixture.whenStable();

    expect(el.textContent).toContain('IVA general registrada, vigente desde el 2027-01-01');
  });

  it('el umbral de Consumidor Final pide monto y no porcentaje', async () => {
    const fixture = await crear([PERFIL]);
    const el = elemento(fixture);

    escribir(el, 'tasa_tipo', 'UMBRAL_CF');
    await fixture.whenStable();
    expect(el.querySelector('[name=tasa_porcentaje]')).toBeNull();

    el.querySelectorAll('form.formulario')[1].dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL_TASAS });
    expect(el.textContent).toContain('Indique el monto límite');
  });
});
