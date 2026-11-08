import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CatalogoPantalla } from './catalogo';

const URL = '/api/v1/configuracion/cuentas';
const BASE = {
  tipo: 'activo',
  naturaleza: 'deudora',
  monetaria_usd: false,
  linea_obligatoria: false,
  vin: 'no_aplica',
  linea_defecto: null,
};
const GRUPO = {
  ...BASE,
  id: 1,
  codigo: '1',
  nombre: 'Activo',
  nivel: 1,
  padre_id: null,
  es_detalle: false,
};
const CAJA = {
  ...BASE,
  id: 2,
  codigo: '1.1',
  nombre: 'Caja',
  nivel: 2,
  padre_id: 1,
  es_detalle: true,
};

describe('CatalogoPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [CatalogoPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function crear(): Promise<ComponentFixture<CatalogoPantalla>> {
    const fixture = TestBed.createComponent(CatalogoPantalla);
    http.expectOne('/api/v1/configuracion/lineas-negocio').flush(['alquiler', 'administracion']);
    http.expectOne(URL).flush([GRUPO, CAJA]);
    await fixture.whenStable();
    return fixture;
  }

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  it('muestra el árbol sangrado por nivel y solo ofrece dimensiones en cuentas de detalle', async () => {
    const el = (await crear()).nativeElement as HTMLElement;
    const filas = el.querySelectorAll<HTMLElement>('tbody tr');

    expect(filas[0].classList).toContain('agrupacion');
    expect(filas[0].querySelector('button')).toBeNull();
    expect(filas[1].querySelector('td')!.style.paddingLeft).toBe('36px');
    expect(filas[1].querySelector('button')!.textContent).toContain('Dimensiones');
  });

  it('crea una cuenta bajo su padre, con el orden de los campos que espera la API', async () => {
    const fixture = await crear();
    const el = fixture.nativeElement as HTMLElement;

    escribir(el, 'codigo', ' 1.2 ');
    escribir(el, 'nombre', 'Bancos');
    el.querySelector<HTMLSelectElement>('[name=padre_id]')!.selectedIndex = 1;
    el.querySelector('[name=padre_id]')!.dispatchEvent(new Event('change'));
    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      codigo: '1.2',
      nombre: 'Bancos',
      tipo: 'activo',
      naturaleza: 'deudora',
      padre_id: 1,
      es_detalle: true,
      monetaria_usd: false,
      linea_obligatoria: false,
      vin: 'no_aplica',
      linea_defecto: null,
    });
    envio.flush({ ...CAJA, id: 3, codigo: '1.2' });
    http.expectOne(URL).flush([GRUPO, CAJA]);
    await fixture.whenStable();
    expect(el.textContent).toContain('Cuenta 1.2 creada');
  });

  it('define las dimensiones de una cuenta', async () => {
    const fixture = await crear();
    const el = fixture.nativeElement as HTMLElement;

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    escribir(el, 'dim_vin', 'obligatorio');
    escribir(el, 'dim_linea_defecto', 'alquiler');
    el.querySelector('form.dimensiones')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'PUT', url: `${URL}/2/dimensiones` });
    expect(envio.request.body).toEqual({
      linea_obligatoria: false,
      vin: 'obligatorio',
      linea_defecto: 'alquiler',
    });
    envio.flush({ ...CAJA, vin: 'obligatorio' });
    http.expectOne(URL).flush([GRUPO, CAJA]);
    await fixture.whenStable();
    expect(el.textContent).toContain('Dimensiones de 1.1 guardadas');
  });

  it('muestra el rechazo del servidor', async () => {
    const fixture = await crear();
    const el = fixture.nativeElement as HTMLElement;

    escribir(el, 'codigo', '1.1');
    escribir(el, 'nombre', 'Otra');
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    http
      .expectOne({ method: 'POST', url: URL })
      .flush({ detail: 'Ya existe la cuenta 1.1' }, { status: 409, statusText: 'Conflict' });
    await fixture.whenStable();
    expect(el.querySelector('[role=alert]')!.textContent).toContain('Ya existe la cuenta 1.1');
  });
});
