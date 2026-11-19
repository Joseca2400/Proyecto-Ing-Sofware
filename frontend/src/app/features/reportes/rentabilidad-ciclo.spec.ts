import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { RentabilidadCicloPantalla } from './rentabilidad-ciclo';
import { ReporteRentabilidadCiclo } from './reportes.service';

const URL = '/api/v1/reportes/rentabilidad/ciclo';

const MONTOS = {
  compra: '70331.250000',
  importacion: '5633.100000',
  reacondicionamiento: '1232.500000',
  costo_total: '77196.850000',
  ingreso_alquiler: '1272.320000',
  mantenimiento: '500.000000',
  seguro: null,
  marchamo: null,
  depreciacion: '1608.270000',
  resultado: '-835.950000',
  rentabilidad: '-1.08',
};

const REPORTE: ReporteRentabilidadCiclo = {
  orden: 'resultado',
  unidades: [
    {
      ...MONTOS,
      vin: '1HGCM82633A004352',
      marca: 'Honda',
      linea: 'Accord',
      modelo: 2007,
      estado: 'en_flota',
      proveedor: 'Copart Inc.',
      fecha_compra: '2026-10-20',
      fecha_alta: '2024-01-10',
      dias_en_flota: 1044,
      dias_alquilados: 3,
      ocupacion: '0.29',
    },
    {
      ...MONTOS,
      compra: '0.000000',
      importacion: '0.000000',
      reacondicionamiento: '0.000000',
      costo_total: '0.000000',
      resultado: '0.000000',
      rentabilidad: null,
      vin: 'JHMCM56557C404454',
      marca: 'Toyota',
      linea: 'Yaris',
      modelo: 2015,
      estado: 'en_transito',
      proveedor: null,
      fecha_compra: null,
      fecha_alta: null,
      dias_en_flota: null,
      dias_alquilados: 0,
      ocupacion: null,
    },
  ],
  totales: MONTOS,
  filtros: {
    marcas: ['Honda', 'Toyota'],
    lineas: ['Accord', 'Yaris'],
    anios_compra: [2026],
    proveedores: [{ id: 1, nombre: 'Copart Inc.' }],
  },
  pendientes: ['Seguro: pendiente; asigne una cuenta a la regla «rentabilidad · seguro».'],
};

describe('RentabilidadCicloPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RentabilidadCicloPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function abrir() {
    const fixture = TestBed.createComponent(RentabilidadCicloPantalla);
    const consulta = http.expectOne((r) => r.url === URL);
    expect(consulta.request.params.keys()).toEqual(['orden']);
    consulta.flush(REPORTE);
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  it('muestra costo, resultado, rentabilidad, días en flota y ocupación por VIN', async () => {
    const elemento = await abrir();
    const filas = elemento.querySelectorAll('tbody tr');
    expect(filas.length).toBe(2);
    expect(filas[0].textContent).toContain('77,196.85');
    expect(filas[0].textContent).toContain('-1.08 %');
    expect(filas[0].textContent).toContain('1044');
    expect(filas[0].textContent).toContain('0.29 %');
    expect(filas[0].textContent).toContain('pendiente');
    expect(filas[0].querySelector('.falla')?.textContent).toContain('835.95');
    expect(filas[1].textContent).toContain('—');
    expect(elemento.textContent).toContain('rentabilidad · seguro');
    // Las opciones de los filtros vienen del servidor.
    const proveedores = elemento.querySelector<HTMLSelectElement>('select[name=proveedor_id]')!;
    expect(proveedores.options.length).toBe(2);
  });

  it('consulta con los filtros y el orden elegidos', async () => {
    const elemento = await abrir();
    const elegir = (nombre: string, valor: string) => {
      const select = elemento.querySelector<HTMLSelectElement>(`select[name=${nombre}]`)!;
      select.value = valor;
      select.dispatchEvent(new Event('change'));
    };
    elegir('marca', 'Honda');
    elegir('proveedor_id', '1');
    elegir('anio_compra', '2026');
    elegir('orden', 'rentabilidad');
    elemento.querySelector<HTMLButtonElement>('form button')!.click();

    const consulta = http.expectOne((r) => r.url === URL);
    const params = consulta.request.params;
    expect(params.get('marca')).toBe('Honda');
    expect(params.get('proveedor_id')).toBe('1');
    expect(params.get('anio_compra')).toBe('2026');
    expect(params.get('orden')).toBe('rentabilidad');
    expect(params.has('estado')).toBe(false);
    consulta.flush({ ...REPORTE, orden: 'rentabilidad' });
  });
});
