import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { AuthService } from '../../core/auth/auth.service';
import { PagosPantalla } from './pagos';

const API = '/api/v1';
const URL = `${API}/compras/pagos`;

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
];

function aprobado(id: number, proveedor_id: number, documento: string) {
  return {
    id,
    programacion_id: 7,
    cuenta_por_pagar_id: id + 10,
    proveedor_id,
    proveedor: proveedor_id === 1 ? 'Agencia Aduanal del Pacífico' : 'Seaboard Marine Ltd.',
    documento,
    vin: '1HGCM82633A004352',
    fecha_vencimiento: '2026-11-10',
    moneda: 'GTQ',
    saldo: '3500.000000',
    cuenta_bancaria_id: 1,
    banco: 'Banco Industrial 000-GTQ',
    moneda_banco: 'GTQ',
    monto_propuesto: '3500.000000',
    monto: '3500.000000',
    monto_banco: '3500.000000',
    estado: 'aprobado',
    decidido_por: 3,
    decidido_en: '2026-11-19T15:00:00Z',
    comentario: null,
  };
}

const PAGO = {
  id: 4,
  proveedor_id: 1,
  proveedor: 'Agencia Aduanal del Pacífico',
  cuenta_bancaria_id: 1,
  banco: 'Banco Industrial 000-GTQ',
  moneda: 'GTQ',
  forma_pago: 'cheque',
  referencia: '101',
  fecha: '2026-11-19',
  tipo_cambio: null,
  monto: '3500.000000',
  diferencial: '0.000000',
  estado: 'registrado',
  usuario_id: 1,
  anulado_por: null,
  fecha_anulacion: null,
  motivo_anulacion: null,
  partida_numero: 31,
  reversion_numero: null,
  creado_en: '2026-11-19T15:00:00Z',
  aplicaciones: [
    {
      cuenta_por_pagar_id: 11,
      documento: 'Agente aduanal F-1',
      vin: '1HGCM82633A004352',
      moneda_documento: 'GTQ',
      monto_documento: '3500.000000',
      monto_pago: '3500.000000',
      tipo_cambio_libros: null,
      diferencial: '0.000000',
      saldo_documento: '0.000000',
    },
  ],
};

function preparar(
  rol: string,
  porEjecutar = [aprobado(1, 1, 'Agente aduanal F-1')],
  pagos: unknown[] = [],
) {
  TestBed.configureTestingModule({
    imports: [PagosPantalla],
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      {
        provide: AuthService,
        useValue: {
          usuario: signal({ id: 1, rol, correo: 'x@empresa.gt', nombre: 'X' }),
          tieneRol: (roles?: readonly string[]) => !roles?.length || roles.includes(rol),
        },
      },
    ],
  });
  const http = TestBed.inject(HttpTestingController);
  const fixture = TestBed.createComponent(PagosPantalla);
  http.expectOne(`${API}/configuracion/cuentas-bancarias`).flush(BANCOS);
  http.expectOne(`${API}/compras/pagos-por-ejecutar`).flush(porEjecutar);
  http.expectOne(URL).flush(pagos);
  return { http, fixture, el: fixture.nativeElement as HTMLElement };
}

function marcar(el: HTMLElement, etiqueta: string): HTMLInputElement {
  const casilla = el.querySelector<HTMLInputElement>(`input[aria-label="Pagar ${etiqueta}"]`)!;
  casilla.checked = true;
  casilla.dispatchEvent(new Event('change'));
  return casilla;
}

describe('PagosPantalla', () => {
  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('registra el pago aprobado con el siguiente cheque de la cuenta y muestra el comprobante', async () => {
    const { http, fixture, el } = preparar('auxiliar_contable');
    await fixture.whenStable();
    marcar(el, 'Agente aduanal F-1');
    await fixture.whenStable();
    expect(el.querySelector<HTMLInputElement>('input[name=referencia]')!.value).toBe('101');

    el.querySelector<HTMLButtonElement>('.formulario button')!.click();
    const peticion = http.expectOne((r) => r.method === 'POST' && r.url === URL);
    expect(peticion.request.body).toEqual(
      expect.objectContaining({
        cuenta_bancaria_id: 1,
        forma_pago: 'cheque',
        referencia: '101',
        pagos_programados: [1],
      }),
    );
    peticion.flush(PAGO);
    http.expectOne(`${API}/compras/pagos-por-ejecutar`).flush([]);
    http.expectOne(URL).flush([PAGO]);
    await fixture.whenStable();

    expect(el.textContent).toContain('partida No. 31');
    const comprobante = el.querySelector('.comprobante')!.textContent ?? '';
    expect(comprobante).toContain('Cheque No. 101');
    expect(comprobante).toContain('Agente aduanal F-1');
    expect(el.querySelector('.anular')).toBeNull(); // el auxiliar no anula
  });

  it('no deja combinar pagos de otro proveedor', async () => {
    const { fixture, el } = preparar('contador', [
      aprobado(1, 1, 'Agente aduanal F-1'),
      aprobado(2, 2, 'Flete BL-1'),
    ]);
    await fixture.whenStable();
    marcar(el, 'Agente aduanal F-1');
    await fixture.whenStable();
    expect(
      el.querySelector<HTMLInputElement>('input[aria-label="Pagar Flete BL-1"]')!.disabled,
    ).toBe(true);
  });

  it('anular exige motivo y envía la fecha y el motivo', async () => {
    const { http, fixture, el } = preparar('contador', [], [PAGO]);
    await fixture.whenStable();
    el.querySelector<HTMLButtonElement>('tbody button')!.click();
    await fixture.whenStable();

    const anular = el.querySelector<HTMLButtonElement>('.anular button')!;
    anular.click();
    await fixture.whenStable();
    expect(el.textContent).toContain('Escribe el motivo de la anulación');

    const motivo = el.querySelector<HTMLInputElement>('input[name=motivo]')!;
    motivo.value = 'Cheque dañado';
    motivo.dispatchEvent(new Event('input'));
    anular.click();
    const peticion = http.expectOne(`${URL}/4/anulacion`);
    expect(peticion.request.body.motivo).toBe('Cheque dañado');
    peticion.flush({ ...PAGO, estado: 'anulado', reversion_numero: 32 });
    http.expectOne(`${API}/compras/pagos-por-ejecutar`).flush([]);
    http.expectOne(URL).flush([{ ...PAGO, estado: 'anulado', reversion_numero: 32 }]);
    await fixture.whenStable();
    expect(el.textContent).toContain('revirtió con la No. 32');
  });

  it('el gerente financiero no ve el registro de pagos', async () => {
    const { fixture, el } = preparar('gerente_financiero');
    await fixture.whenStable();
    expect(el.textContent).not.toContain('Pagos aprobados por ejecutar');
  });
});
