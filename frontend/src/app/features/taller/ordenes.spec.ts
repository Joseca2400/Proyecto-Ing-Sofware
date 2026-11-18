import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { OrdenesTallerPantalla } from './ordenes';

const URL = '/api/v1/taller/ordenes';
const VIN = '1HGCM82633A004352';

const ORDEN = {
  id: 1,
  numero: 'OT-00001',
  vin: VIN,
  tipo: 'reacondicionamiento',
  estado: 'abierta',
  fecha_apertura: '2026-11-10',
  kilometraje: 84500,
  descripcion: 'Pintura y frenos',
  responsable: 'Taller central',
  dias: 8,
  costo_acumulado: '0.000000',
  fecha_cierre: null,
  justificacion: null,
  partida_id: null,
};

describe('OrdenesTallerPantalla', () => {
  let http: HttpTestingController;
  let fixture: ComponentFixture<OrdenesTallerPantalla>;

  beforeEach(async () => {
    TestBed.configureTestingModule({
      imports: [OrdenesTallerPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(OrdenesTallerPantalla);
    http.expectOne(URL).flush([ORDEN]);
    await fixture.whenStable();
  });

  afterEach(() => http.verify());

  const elemento = () => fixture.nativeElement as HTMLElement;
  const texto = () => elemento().textContent ?? '';

  function escribir(selector: string, valor: string): void {
    const input = elemento().querySelector<HTMLInputElement>(selector)!;
    input.value = valor;
    input.dispatchEvent(new Event('input'));
  }

  function llenarYEnviar(vin: string): void {
    escribir('input[formControlName=vin]', vin);
    escribir('input[formControlName=kilometraje]', '84500');
    escribir('input[formControlName=responsable]', 'Taller central');
    escribir('input[formControlName=descripcion]', 'Pintura y frenos');
    elemento().querySelector('form')!.dispatchEvent(new Event('submit'));
  }

  it('lista las órdenes con su estado, antigüedad y costo acumulado', () => {
    expect(texto()).toContain('OT-00001');
    expect(texto()).toContain('Abierta');
    expect(texto()).toContain('8');
    expect(texto()).toContain('Q');
  });

  it('abre una orden de reacondicionamiento y recarga la lista', async () => {
    llenarYEnviar(VIN.toLowerCase());
    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toMatchObject({
      vin: VIN,
      tipo: 'reacondicionamiento',
      kilometraje: 84500,
      responsable: 'Taller central',
    });
    envio.flush(ORDEN);
    http.expectOne(URL).flush([ORDEN]);
    await fixture.whenStable();

    expect(texto()).toContain('Orden OT-00001 abierta');
    expect(texto()).toContain('Pintura y frenos');
  });

  it('muestra el mensaje del backend cuando rechaza la apertura', async () => {
    llenarYEnviar(VIN);
    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'La unidad ya tiene una orden de trabajo abierta' },
        { status: 409, statusText: 'Conflict' },
      );
    await fixture.whenStable();

    expect(texto()).toContain('ya tiene una orden de trabajo abierta');
  });

  it('no envía un VIN inválido', async () => {
    llenarYEnviar('ABC');
    http.expectNone({ method: 'POST', url: URL });
    await fixture.whenStable();

    expect(texto()).toContain('17 caracteres');
  });
});
