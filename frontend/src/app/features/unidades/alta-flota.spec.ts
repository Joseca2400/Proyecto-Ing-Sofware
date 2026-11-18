import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AltaFlotaPantalla } from './alta-flota';
import { CandidataAltaFlota } from './unidades.service';

const URL = '/api/v1/unidades/alta-flota/candidatas';
const VIN = '1HGCM82633A004352';

const CANDIDATA: CandidataAltaFlota = {
  vin: VIN,
  marca: 'Honda',
  linea: 'Accord',
  modelo: 2007,
  tipo_vehiculo: 'sedan',
  costo: '77196.850000',
  cuadra: true,
  diferencia: '0.000000',
  orden_abierta: false,
  vida_util_meses: 60,
  valor_residual: '7719.690000',
  porcentaje_fiscal: '20.00',
};

describe('AltaFlotaPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [AltaFlotaPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function abrir(candidatas: CandidataAltaFlota[]) {
    const fixture = TestBed.createComponent(AltaFlotaPantalla);
    http.expectOne(URL).flush(candidatas);
    await fixture.whenStable();
    return { fixture, elemento: fixture.nativeElement as HTMLElement };
  }

  it('lista las unidades listas y no deja dar de alta una que no cuadra', async () => {
    const { elemento } = await abrir([
      CANDIDATA,
      { ...CANDIDATA, vin: 'JHMCM56557C404453', cuadra: false, diferencia: '-50.000000' },
    ]);
    expect(elemento.textContent).toContain('77,196.85');
    expect(elemento.textContent).toContain('Diferencia');
    const botones = elemento.querySelectorAll<HTMLButtonElement>('tbody button');
    expect(botones[0].disabled).toBe(false);
    expect(botones[1].disabled).toBe(true);
  });

  it('confirma el alta con su fecha y recarga', async () => {
    const { fixture, elemento } = await abrir([CANDIDATA]);
    elemento.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: `/api/v1/unidades/${VIN}/alta-flota` });
    expect(envio.request.body.fecha).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(envio.request.body.vida_util_meses).toBe(60);
    expect(envio.request.body.valor_residual).toBe('7719.690000');
    expect(envio.request.body.porcentaje_fiscal).toBe('20.00');
    envio.flush({ id: 1, vin: VIN, fecha: '2026-11-18', costo: '77196.850000', partida_id: 9 });
    http.expectOne(URL).flush([]);
    await fixture.whenStable();
    expect(elemento.textContent).toContain('dada de alta en la flota');
  });

  it('muestra el rechazo del servidor', async () => {
    const { fixture, elemento } = await abrir([CANDIDATA]);
    elemento.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    elemento.querySelector('form')!.dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: `/api/v1/unidades/${VIN}/alta-flota` })
      .flush({ detail: 'La hoja de costo no cuadra' }, { status: 409, statusText: 'x' });
    await fixture.whenStable();
    expect(elemento.querySelector('[role=alert]')?.textContent).toContain('no cuadra');
  });
});
