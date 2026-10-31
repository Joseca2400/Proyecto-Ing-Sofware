import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Inicio } from './inicio';

describe('Inicio', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [Inicio],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('muestra el mensaje de la API y el estado de la base', async () => {
    const fixture = TestBed.createComponent(Inicio);
    http.expectOne('/api/v1/sistema/estado').flush({
      aplicacion: 'Sistema administrativo y financiero',
      version: '0.1.0',
      mensaje: 'Hola, mundo: la API responde',
      base_datos: { conectada: true, motor: 'postgresql', revision_esquema: '0001' },
    });
    await fixture.whenStable();

    const texto = (fixture.nativeElement as HTMLElement).textContent;
    expect(texto).toContain('Hola, mundo: la API responde');
    expect(texto).toContain('Conectada (postgresql)');
    expect(texto).toContain('0001');
  });

  it('avisa si la API no responde', async () => {
    const fixture = TestBed.createComponent(Inicio);
    http.expectOne('/api/v1/sistema/estado').error(new ProgressEvent('error'));
    await fixture.whenStable();

    const texto = (fixture.nativeElement as HTMLElement).textContent;
    expect(texto).toContain('Sin respuesta');
    expect(texto).toContain('Reintentar');
  });
});
