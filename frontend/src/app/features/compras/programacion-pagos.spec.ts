import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { AuthService } from '../../core/auth/auth.service';
import { ProgramacionPagosPantalla } from './programacion-pagos';

const API = '/api/v1';
const URL = `${API}/compras/programaciones-pago`;

const BANCOS = [
  {
    id: 1,
    banco: 'Banco Industrial',
    numero: '000-GTQ',
    tipo: 'monetaria',
    moneda: 'GTQ',
    cuenta_id: 3,
    siguiente_cheque: 101,
    activa: true,
  },
  {
    id: 2,
    banco: 'Banco Industrial',
    numero: '000-USD',
    tipo: 'monetaria',
    moneda: 'USD',
    cuenta_id: 4,
    siguiente_cheque: null,
    activa: true,
  },
];

const CUENTA = {
  id: 5,
  proveedor_id: 1,
  proveedor: 'Seaboard Marine Ltd.',
  origen: 'gasto_importacion',
  documento: 'Flete BL-778812',
  vin: '1HGCM82633A004352',
  fecha: '2026-11-10',
  fecha_vencimiento: '2026-11-10',
  dias_vencida: 9,
  moneda: 'USD',
  monto: '1000.000000',
  saldo: '1000.000000',
  programado: '0.000000',
};

const PROGRAMACION = {
  id: 7,
  fecha: '2026-11-20',
  descripcion: 'Pagos de la semana',
  propuesta_por: 1,
  creado_en: '2026-11-19T15:00:00Z',
  estado: 'pendiente',
  pagos: [
    {
      id: 11,
      cuenta_por_pagar_id: 5,
      proveedor_id: 1,
      proveedor: 'Seaboard Marine Ltd.',
      documento: 'Flete BL-778812',
      vin: '1HGCM82633A004352',
      fecha_vencimiento: '2026-11-10',
      moneda: 'USD',
      saldo: '1000.000000',
      cuenta_bancaria_id: 2,
      banco: 'Banco Industrial 000-USD',
      moneda_banco: 'USD',
      monto_propuesto: '1000.000000',
      monto: '1000.000000',
      monto_banco: '1000.000000',
      estado: 'propuesto',
      decidido_por: null,
      decidido_en: null,
      comentario: null,
    },
  ],
  totales: { GTQ: '0.000000', USD: '1000.000000' },
  tipo_cambio_estimado: '7.75000000',
  bancos: [
    {
      cuenta_bancaria_id: 2,
      banco: 'Banco Industrial 000-USD',
      moneda: 'USD',
      saldo_libros: '500.000000',
      comprometido: '0.000000',
      disponible: '500.000000',
      programado: '1000.000000',
      alcanza: false,
    },
  ],
};

function preparar(usuario: { id: number; rol: string }) {
  TestBed.configureTestingModule({
    imports: [ProgramacionPagosPantalla],
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      {
        provide: AuthService,
        useValue: {
          usuario: signal({ ...usuario, correo: 'x@empresa.gt', nombre: 'X' }),
          tieneRol: (roles?: readonly string[]) => !roles?.length || roles.includes(usuario.rol),
        },
      },
    ],
  });
  const http = TestBed.inject(HttpTestingController);
  const fixture = TestBed.createComponent(ProgramacionPagosPantalla);
  http.expectOne(`${API}/configuracion/cuentas-bancarias`).flush(BANCOS);
  http.expectOne(`${API}/compras/cuentas-por-pagar`).flush([CUENTA]);
  http.expectOne(URL).flush([PROGRAMACION]);
  return { http, fixture, el: fixture.nativeElement as HTMLElement };
}

describe('ProgramacionPagosPantalla', () => {
  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('propone el pago elegido con su monto y la cuenta bancaria en su moneda', async () => {
    const { http, fixture, el } = preparar({ id: 1, rol: 'auxiliar_contable' });
    await fixture.whenStable();
    expect(el.textContent).toContain('Vencida hace 9 días');

    const casilla = el.querySelector<HTMLInputElement>('input[type=checkbox]')!;
    casilla.checked = true;
    casilla.dispatchEvent(new Event('change'));
    await fixture.whenStable();
    const monto = el.querySelector<HTMLInputElement>(
      'input[aria-label="Monto de Flete BL-778812"]',
    )!;
    monto.value = '400.00';
    monto.dispatchEvent(new Event('input'));
    el.querySelector<HTMLButtonElement>('.formulario button')!.click();

    const peticion = http.expectOne((r) => r.method === 'POST' && r.url === URL);
    expect(peticion.request.body.pagos).toEqual([
      { cuenta_por_pagar_id: 5, cuenta_bancaria_id: 2, monto: '400.00' },
    ]);
    peticion.flush(PROGRAMACION);
    http.expectOne(`${API}/compras/cuentas-por-pagar`).flush([]);
    http.expectOne(URL).flush([PROGRAMACION]);
    await fixture.whenStable();
    expect(el.textContent).toContain('Programación 7 propuesta');
    expect(el.textContent).not.toContain('Decisión'); // el auxiliar no decide
  });

  it('muestra los totales y el saldo disponible que calcula el servidor', async () => {
    const { fixture, el } = preparar({ id: 1, rol: 'auxiliar_contable' });
    await fixture.whenStable();
    expect(el.querySelector('tfoot')!.textContent).toMatch(/1,000\.00/);
    expect(el.textContent).toContain('No alcanza');
  });

  it('el gerente aprueba con otro monto y solo envía lo que cambió', async () => {
    const { http, fixture, el } = preparar({ id: 2, rol: 'gerente_financiero' });
    await fixture.whenStable();
    const monto = el.querySelector<HTMLInputElement>(
      'input[aria-label="Monto a aprobar de Flete BL-778812"]',
    )!;
    monto.value = '600.00';
    monto.dispatchEvent(new Event('input'));
    const aprobar = [...el.querySelectorAll<HTMLButtonElement>('.decision button')].find(
      (b) => b.textContent?.trim() === 'Aprobar',
    )!;
    aprobar.click();

    const peticion = http.expectOne(`${URL}/7/pagos/11/decision`);
    expect(peticion.request.body).toEqual({ accion: 'aprobar', monto: '600.00' });
    peticion.flush({
      ...PROGRAMACION,
      estado: 'revisada',
      pagos: [
        { ...PROGRAMACION.pagos[0], estado: 'aprobado', monto: '600.000000', decidido_por: 2 },
      ],
    });
    http.expectOne(`${API}/compras/cuentas-por-pagar`).flush([]);
    await fixture.whenStable();
    expect(el.textContent).toContain('Aprobado');
    expect(el.textContent).toContain('Propuesto');
  });

  it('rechazar exige un motivo antes de llamar al servidor', async () => {
    const { fixture, el } = preparar({ id: 2, rol: 'gerente_financiero' });
    await fixture.whenStable();
    const rechazar = [...el.querySelectorAll<HTMLButtonElement>('.decision button')].find(
      (b) => b.textContent?.trim() === 'Rechazar',
    )!;
    rechazar.click();
    await fixture.whenStable();
    expect(el.textContent).toContain('Escribe el motivo del rechazo');
  });

  it('quien propuso la programación no ve los botones para decidir', async () => {
    const { fixture, el } = preparar({ id: 1, rol: 'gerente_financiero' });
    await fixture.whenStable();
    expect(el.textContent).toContain('La propusiste tú');
    expect(el.querySelector('.decision')).toBeNull();
  });
});
