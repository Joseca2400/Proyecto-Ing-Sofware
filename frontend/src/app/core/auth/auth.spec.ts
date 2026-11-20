import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { routes } from '../../app.routes';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';

const sesion = (rol: string) => ({
  token: 'abc',
  usuario: { id: 1, correo: 'u@empresa.gt', nombre: 'Usuaria', rol },
});

describe('Sesión (HU-1.09)', () => {
  let http: HttpTestingController;
  let auth: AuthService;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthService);
  });

  function entrarComo(rol: string): void {
    auth.entrar('u@empresa.gt', 'clave').subscribe();
    http.expectOne('/api/v1/seguridad/login').flush(sesion(rol));
  }

  it('al entrar guarda la sesión y manda el token en las llamadas a la API', () => {
    entrarComo('contador');
    expect(auth.usuario()?.rol).toBe('contador');
    expect(sessionStorage.getItem('km0.sesion')).toContain('abc');

    TestBed.inject(HttpClient).get('/api/v1/unidades').subscribe();
    const peticion = http.expectOne('/api/v1/unidades');
    expect(peticion.request.headers.get('Authorization')).toBe('Bearer abc');
  });

  it('un 401 olvida la sesión y lleva a la pantalla de entrada', async () => {
    entrarComo('contador');
    const navegar = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);

    TestBed.inject(HttpClient)
      .get('/api/v1/unidades')
      .subscribe({ error: () => undefined });
    http
      .expectOne('/api/v1/unidades')
      .flush({ detail: 'La sesión expiró' }, { status: 401, statusText: '' });

    expect(auth.usuario()).toBeNull();
    expect(sessionStorage.getItem('km0.sesion')).toBeNull();
    expect(navegar).toHaveBeenCalledWith(['/entrar']);
  });

  it('sin sesión cualquier pantalla lleva a entrar', async () => {
    await RouterTestingHarness.create('/unidades');
    expect(TestBed.inject(Router).url).toBe('/entrar');
  });

  it('el menú y las rutas ocultan lo que el rol no puede ver', async () => {
    entrarComo('auxiliar_contable');
    const arnes = await RouterTestingHarness.create('/unidades/etapas-importacion');
    http.match(() => true); // lo que pida la pantalla de inicio no importa aquí
    arnes.detectChanges();

    expect(TestBed.inject(Router).url).toBe('/inicio');
    const menu =
      arnes.routeNativeElement?.closest('body')?.textContent ?? document.body.textContent;
    expect(menu).toContain('Unidades');
    expect(menu).not.toContain('Etapas de importación');
    const sesion = document.querySelector('.sesion .quien')?.textContent ?? '';
    expect(sesion).toContain('Usuaria');
    expect(sesion).toContain('Auxiliar contable');
  });

  it('cerrar sesión avisa al servidor con el token y olvida la sesión', () => {
    entrarComo('gerencia');
    auth.salir();
    const cierre = http.expectOne('/api/v1/seguridad/logout');
    expect(cierre.request.headers.get('Authorization')).toBe('Bearer abc');
    expect(auth.usuario()).toBeNull();
  });
});
