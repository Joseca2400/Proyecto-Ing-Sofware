import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PartidasPantalla } from './partidas';

const URL = '/api/v1/contabilidad/partidas';
const BASE = { es_detalle: true, nivel: 2, padre_id: 1, tipo: 'activo', naturaleza: 'deudora' };
const CUENTAS = [
  { ...BASE, id: 11, codigo: '1.1', nombre: 'Caja', monetaria_usd: false },
  { ...BASE, id: 12, codigo: '1.2', nombre: 'Bancos USD', monetaria_usd: true },
];
const LINEA = {
  moneda: 'GTQ',
  monto_usd: null,
  tipo_cambio: null,
  linea_negocio: null,
  vin: null,
};
const PARTIDA = {
  id: 7,
  numero: null,
  fecha: '2026-11-02',
  concepto: 'Aporte',
  documento_soporte: null,
  estado: 'en_revision',
  origen: 'manual',
  documento_tipo: null,
  documento_id: null,
  comentario: null,
  creado_por: 1,
  contabilizada_por: null,
  contabilizada_en: null,
  total_debe: '77.000000',
  total_haber: '77.000000',
  lineas: [
    {
      ...LINEA,
      numero_linea: 1,
      cuenta_id: 12,
      debe: '77.000000',
      haber: '0.000000',
      moneda: 'USD',
      monto_usd: '10.000000',
      tipo_cambio: '7.70000000',
    },
    { ...LINEA, numero_linea: 2, cuenta_id: 11, debe: '0.000000', haber: '77.000000' },
  ],
};

describe('PartidasPantalla', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [PartidasPantalla],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  const lista = () => http.expectOne((r) => r.url === URL && r.method === 'GET');

  async function crear(partidas: unknown[] = []): Promise<ComponentFixture<PartidasPantalla>> {
    const fixture = TestBed.createComponent(PartidasPantalla);
    http.expectOne((r) => r.url.endsWith('/configuracion/cuentas')).flush(CUENTAS);
    http.expectOne('/api/v1/configuracion/lineas-negocio').flush(['alquiler']);
    const consulta = lista();
    expect(consulta.request.params.get('estado')).toBe('en_revision');
    consulta.flush(partidas);
    await fixture.whenStable();
    return fixture;
  }

  function escribir(el: HTMLElement, nombre: string, valor: string): void {
    const campo = el.querySelector<HTMLInputElement | HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.value = valor;
    campo.dispatchEvent(new Event(campo instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  function elegirCuenta(el: HTMLElement, nombre: string, indice: number): void {
    const campo = el.querySelector<HTMLSelectElement>(`[name=${nombre}]`)!;
    campo.selectedIndex = indice;
    campo.dispatchEvent(new Event('change'));
  }

  function llenar(el: HTMLElement, montoDos = '77.00'): void {
    escribir(el, 'fecha', '2026-11-02');
    escribir(el, 'concepto', ' Aporte ');
    elegirCuenta(el, 'cuenta0', 2);
    escribir(el, 'moneda0', 'USD');
    escribir(el, 'monto0', ' 10.00 ');
    elegirCuenta(el, 'cuenta1', 1);
    escribir(el, 'lado1', 'haber');
    escribir(el, 'monto1', montoDos);
  }

  const boton = (el: HTMLElement, texto: string) =>
    [...el.querySelectorAll('button')].find((b) => b.textContent!.trim() === texto)!;

  it('guarda el borrador con los montos como texto y dimensiones vacías en null', async () => {
    const fixture = await crear();
    const el = fixture.nativeElement as HTMLElement;

    llenar(el);
    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'POST', url: URL });
    expect(envio.request.body).toEqual({
      fecha: '2026-11-02',
      concepto: 'Aporte',
      documento_soporte: null,
      lineas: [
        {
          cuenta_id: 12,
          lado: 'debe',
          moneda: 'USD',
          monto: '10.00',
          linea_negocio: null,
          vin: null,
        },
        {
          cuenta_id: 11,
          lado: 'haber',
          moneda: 'GTQ',
          monto: '77.00',
          linea_negocio: null,
          vin: null,
        },
      ],
    });
    envio.flush({ ...PARTIDA, estado: 'borrador' });
    lista().flush([]);
    await fixture.whenStable();
    expect(el.textContent).toContain('Partida 7 guardada en borrador');
    expect(el.querySelector('.ficha')).not.toBeNull();
  });

  it('no envía un monto mal escrito', async () => {
    const fixture = await crear();
    const el = fixture.nativeElement as HTMLElement;

    llenar(el, '77,00');
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();

    http.expectNone({ method: 'POST', url: URL });
    expect(el.textContent).toContain('Hasta 6 decimales');
  });

  it('muestra original en USD, tipo de cambio, equivalente y totales del servidor', async () => {
    const fixture = await crear([PARTIDA]);
    const el = fixture.nativeElement as HTMLElement;

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    const ficha = el.querySelector('.ficha')!.textContent ?? '';
    expect(ficha).toMatch(/USD\s*10\.00/);
    expect(ficha).toContain('7.70000000');
    expect(ficha).toMatch(/Q\s*77\.00/);
    expect(ficha).toContain('1.2 · Bancos USD');
  });

  it('enseña el motivo cuando el servidor impide contabilizar la partida propia', async () => {
    const fixture = await crear([PARTIDA]);
    const el = fixture.nativeElement as HTMLElement;

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    boton(el, 'Contabilizar').click();
    http
      .expectOne({ method: 'POST', url: `${URL}/7/contabilizar` })
      .flush(
        { detail: 'No puedes contabilizar una partida que registraste tú' },
        { status: 403, statusText: 'Forbidden' },
      );
    await fixture.whenStable();
    expect(el.querySelector('[role=alert]')!.textContent).toContain('registraste tú');
  });

  it('contabiliza y muestra el correlativo', async () => {
    const fixture = await crear([PARTIDA]);
    const el = fixture.nativeElement as HTMLElement;

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    boton(el, 'Contabilizar').click();
    http
      .expectOne({ method: 'POST', url: `${URL}/7/contabilizar` })
      .flush({ ...PARTIDA, estado: 'contabilizada', numero: 15 });
    lista().flush([]);
    await fixture.whenStable();
    expect(el.textContent).toContain('Partida contabilizada con el número 15');
    expect(boton(el, 'Contabilizar')).toBeUndefined();
  });

  it('exige motivo para devolver y lo muestra a quien corrige', async () => {
    const fixture = await crear([PARTIDA]);
    const el = fixture.nativeElement as HTMLElement;

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    boton(el, 'Devolver').click();
    await fixture.whenStable();
    http.expectNone({ method: 'POST', url: `${URL}/7/devolver` });
    expect(el.textContent).toContain('Indica el motivo');

    escribir(el, 'comentario', ' Falta soporte ');
    boton(el, 'Devolver').click();
    const envio = http.expectOne({ method: 'POST', url: `${URL}/7/devolver` });
    expect(envio.request.body).toEqual({ comentario: 'Falta soporte' });
    envio.flush({ ...PARTIDA, estado: 'devuelta', comentario: 'Falta soporte' });
    lista().flush([]);
    await fixture.whenStable();
    expect(el.textContent).toContain('Motivo de la devolución: Falta soporte');
  });

  it('corrige una partida devuelta con sus datos y el monto original en USD', async () => {
    const fixture = await crear([{ ...PARTIDA, estado: 'devuelta', comentario: 'Falta soporte' }]);
    const el = fixture.nativeElement as HTMLElement;

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    boton(el, 'Corregir').click();
    await fixture.whenStable();
    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    const envio = http.expectOne({ method: 'PUT', url: `${URL}/7` });
    expect(envio.request.body.lineas[0]).toMatchObject({
      cuenta_id: 12,
      lado: 'debe',
      moneda: 'USD',
      monto: '10.000000',
    });
    expect(envio.request.body.lineas[1]).toMatchObject({ lado: 'haber', monto: '77.000000' });
    envio.flush(PARTIDA);
    lista().flush([]);
    await fixture.whenStable();
  });

  it('muestra la diferencia que informa el servidor al enviar a revisión', async () => {
    const fixture = await crear([{ ...PARTIDA, estado: 'borrador' }]);
    const el = fixture.nativeElement as HTMLElement;

    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();
    boton(el, 'Enviar a revisión').click();
    http.expectOne({ method: 'POST', url: `${URL}/7/enviar-a-revision` }).flush(
      {
        detail: 'La partida no cuadra: débitos 77.000000, créditos 70.000000, diferencia 7.000000',
      },
      { status: 400, statusText: 'Bad Request' },
    );
    await fixture.whenStable();
    expect(el.querySelector('[role=alert]')!.textContent).toContain('diferencia 7.000000');
  });

  it('filtra la bandeja por estado', async () => {
    const fixture = await crear();
    const el = fixture.nativeElement as HTMLElement;

    escribir(el, 'filtro_estado', 'devuelta');
    const consulta = lista();
    expect(consulta.request.params.get('estado')).toBe('devuelta');
    consulta.flush([]);
    await fixture.whenStable();
    expect(el.textContent).toContain('No hay partidas en este estado');
  });
});
