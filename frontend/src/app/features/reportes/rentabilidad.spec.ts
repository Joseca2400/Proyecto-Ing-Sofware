import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { RentabilidadPantalla } from './rentabilidad';
import { ReporteRentabilidadContratos, ReporteRentabilidadUnidades } from './reportes.service';

const API = '/api/v1/reportes/rentabilidad';

const CIFRAS = {
  ingreso_alquiler: '1272.320000',
  depreciacion: '1608.270000',
  mantenimiento: '500.000000',
  seguro: null,
  marchamo: null,
  costos: '2108.270000',
  resultado: '-835.950000',
};

const UNIDADES: ReporteRentabilidadUnidades = {
  desde: '2026-01-01',
  hasta: '2026-11-19',
  unidades: [
    {
      ...CIFRAS,
      vin: '1HGCM82633A004352',
      marca: 'Honda',
      linea: 'Accord',
      modelo: 2007,
      estado: 'en_flota',
      fecha_alta: '2024-01-10',
    },
  ],
  totales: CIFRAS,
  pendientes: ['Seguro: pendiente; asigne una cuenta a la regla «rentabilidad · seguro».'],
};

const MONTOS = {
  alquiler: '937.500000',
  cargos_adicionales: '334.820000',
  ingresos: '1272.320000',
  costos_directos: '0.000000',
  resultado: '1272.320000',
};

const CONTRATOS: ReporteRentabilidadContratos = {
  desde: '2026-01-01',
  hasta: '2026-11-19',
  contratos: [
    {
      ...MONTOS,
      contrato_id: 1,
      numero: 1,
      vin: '1HGCM82633A004352',
      cliente: 'María López',
      salida: '2026-11-10T15:00:00Z',
      devolucion: '2026-11-13T15:00:00Z',
      estado: 'cerrado',
      facturas: ['FACE-1'],
    },
  ],
  totales: MONTOS,
  pendientes: ['Costos directos del contrato: pendientes'],
};

describe('RentabilidadPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RentabilidadPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function abrir() {
    const fixture = TestBed.createComponent(RentabilidadPantalla);
    const unidades = http.expectOne((r) => r.url === `${API}/unidades`);
    const contratos = http.expectOne((r) => r.url === `${API}/contratos`);
    expect(unidades.request.params.get('desde')).toMatch(/^\d{4}-01-01$/);
    expect(unidades.request.params.has('vin')).toBe(false);
    unidades.flush(UNIDADES);
    contratos.flush(CONTRATOS);
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  it('muestra las cifras por unidad y por contrato, con los conceptos pendientes', async () => {
    const elemento = await abrir();
    const [porUnidad, porContrato] = Array.from(elemento.querySelectorAll('table'));

    expect(porUnidad.textContent).toContain('1HGCM82633A004352');
    expect(porUnidad.textContent).toContain('1,608.27');
    expect(porUnidad.textContent).toContain('pendiente');
    expect(porUnidad.querySelector('tbody .falla')?.textContent).toContain('835.95');
    expect(elemento.textContent).toContain('rentabilidad · seguro');

    expect(porContrato.textContent).toContain('María López');
    expect(porContrato.textContent).toContain('FACE-1');
    expect(porContrato.textContent).toContain('334.82');
  });

  it('consulta con el período y el VIN indicados', async () => {
    const elemento = await abrir();
    const vin = elemento.querySelector<HTMLInputElement>('input[name=vin]')!;
    vin.value = '1HGCM82633A004352';
    vin.dispatchEvent(new Event('input'));
    elemento.querySelector<HTMLButtonElement>('form button')!.click();

    const consulta = http.expectOne((r) => r.url === `${API}/unidades`);
    expect(consulta.request.params.get('vin')).toBe('1HGCM82633A004352');
    consulta.flush(UNIDADES);
    http.expectOne((r) => r.url === `${API}/contratos`).flush(CONTRATOS);
  });

  it('descarga el CSV que arma el servidor', async () => {
    const elemento = await abrir();
    const crear = vi.fn(() => 'blob:csv');
    const revocar = vi.fn();
    Object.assign(URL, { createObjectURL: crear, revokeObjectURL: revocar });
    const clic = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);

    elemento.querySelector<HTMLButtonElement>('h2 button')!.click();
    const descarga = http.expectOne((r) => r.url === `${API}/unidades/csv`);
    expect(descarga.request.responseType).toBe('blob');
    descarga.flush(new Blob(['VIN']));

    expect(crear).toHaveBeenCalled();
    expect(clic).toHaveBeenCalled();
    expect(revocar).toHaveBeenCalledWith('blob:csv');
    clic.mockRestore();
  });
});
