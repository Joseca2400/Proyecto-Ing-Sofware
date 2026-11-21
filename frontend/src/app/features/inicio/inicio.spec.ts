import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { routes } from '../../app.routes';
import { AuthService } from '../../core/auth/auth.service';
import { Inicio } from './inicio';

const API = '/api/v1';

const ESTADO = {
  aplicacion: 'Sistema administrativo y financiero',
  version: '0.1.0',
  mensaje: 'La API responde',
  base_datos: { conectada: true, motor: 'postgresql', revision_esquema: '0034' },
};

function crear(rol: string) {
  TestBed.configureTestingModule({
    imports: [Inicio],
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      provideRouter(routes),
      {
        provide: AuthService,
        useValue: {
          usuario: signal({ id: 1, rol, correo: 'x@empresa.gt', nombre: 'Ana López' }),
          tieneRol: (roles?: readonly string[]) => !roles?.length || roles.includes(rol),
        },
      },
    ],
  });
  const http = TestBed.inject(HttpTestingController);
  const fixture = TestBed.createComponent(Inicio);
  return { http, fixture };
}

/** Responde todas las consultas pendientes cuyo URL empiece con `ruta`. */
function responder(http: HttpTestingController, ruta: string, cuerpo: object) {
  http.match((r) => r.url === `${API}${ruta}`).forEach((r) => r.flush(cuerpo));
}

/** Responde lo que quede pendiente con datos vacíos de la forma de cada endpoint. */
function vaciar(http: HttpTestingController) {
  const objetos: Record<string, object> = {
    [`${API}/sistema/estado`]: ESTADO,
    [`${API}/alquileres/depositos`]: { depositos: [], totales: {}, cuadra: true },
    [`${API}/reportes/unidades-por-etapa`]: {
      limite_dias: 60,
      valor_total: '0.000000',
      unidades: [],
    },
  };
  http.match(() => true).forEach((r) => r.flush(objetos[r.request.url] ?? []));
}

describe('Inicio', () => {
  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('al contador le muestra los números clave con los montos que da el servidor', async () => {
    const { http, fixture } = crear('contador');

    responder(http, '/sistema/estado', ESTADO);
    responder(http, '/unidades', [
      { id: 1, estado: 'en_flota' },
      { id: 2, estado: 'alquilada' },
      { id: 3, estado: 'en_flota' },
    ]);
    responder(http, '/alquileres/contratos', [{ id: 1 }]);
    responder(http, '/taller/ordenes', [{ id: 1 }, { id: 2 }]);
    responder(http, '/compras/cuentas-por-pagar', [
      { id: 1, dias_vencida: 3 },
      { id: 2, dias_vencida: 0 },
    ]);
    responder(http, '/compras/pagos-por-ejecutar', []);
    http
      .match((r) => r.url === `${API}/contabilidad/partidas`)
      .forEach((r) => r.flush(r.request.params.get('estado') === 'devuelta' ? [{ id: 9 }] : []));
    responder(http, '/configuracion/tipos-cambio', [
      { fecha: '2026-11-20', valor: '7.71234000', origen: 'manual' },
      { fecha: '2026-11-19', valor: '7.70000000', origen: 'manual' },
    ]);
    responder(http, '/alquileres/depositos', {
      depositos: [],
      totales: { GTQ: '1500.000000', USD: '200.000000' },
      cuadra: true,
    });
    responder(http, '/reportes/unidades-por-etapa', {
      limite_dias: 60,
      valor_total: '250000.000000',
      unidades: [{ excede: true }, { excede: false }],
    });
    await fixture.whenStable();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Hola, Ana');
    expect(texto).toContain('Unidades registradas');
    expect(texto).toContain('1 vencida');
    expect(texto).toContain('1 devuelta');
    expect(texto).toContain('Q 7.71234000');
    expect(texto).toContain('20/11/2026');
    expect(texto).toContain('cuadra con el mayor');
    expect(texto).toContain('Superan 60 días');
    expect(texto).toContain('La API responde');
    expect(texto).toContain('revisión 0034');
    // Los totales los da el servidor; el front solo les da formato.
    expect(texto).toMatch(/Q\s?1,500\.00/);
    expect(texto).toMatch(/Q\s?250,000\.00/);
    const chips = fixture.nativeElement.querySelectorAll('.estados .chip');
    expect([...chips].map((c) => (c as HTMLElement).dataset['estado'])).toEqual([
      'en_flota',
      'alquilada',
    ]);
  });

  it('a gerencia no le consulta ni muestra lo que su rol no abre', async () => {
    const { http, fixture } = crear('gerencia');

    // Gerencia no tiene programación de pagos, pagos ni configuración del tipo de cambio...
    http.expectNone(`${API}/compras/cuentas-por-pagar`);
    http.expectNone(`${API}/compras/pagos-por-ejecutar`);
    // ...pero sí el reporte de unidades por etapa.
    vaciar(http);
    await fixture.whenStable();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).not.toContain('Cuentas por pagar');
    expect(texto).not.toContain('Pagos por ejecutar');
    expect(texto).toContain('Inventario por etapa');
  });

  it('al auxiliar contable no le muestra el reporte de gerencia', async () => {
    const { http, fixture } = crear('auxiliar_contable');

    http.expectNone(`${API}/reportes/unidades-por-etapa`);
    vaciar(http);
    await fixture.whenStable();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Pagos por ejecutar');
    expect(texto).not.toContain('Inventario por etapa');
  });

  it('avisa si la API no responde y permite reintentar', async () => {
    const { http, fixture } = crear('contador');

    http.match(() => true).forEach((r) => r.error(new ProgressEvent('error')));
    await fixture.whenStable();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Sin respuesta de la API');
    expect(texto).toContain('No disponible');

    (fixture.nativeElement.querySelector('.sistema button') as HTMLButtonElement).click();
    http.expectOne(`${API}/sistema/estado`).flush(ESTADO);
    await fixture.whenStable();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('La API responde');
  });
});
