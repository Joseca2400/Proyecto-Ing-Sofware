import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { UsuariosPantalla } from './usuarios';

const URL = '/api/v1/seguridad/usuarios';
const USUARIO = {
  id: 7,
  correo: 'ana@empresa.gt',
  nombre: 'Ana',
  rol: 'contador',
  estado: 'activo',
  creado_en: '2026-11-10T15:30:00Z',
};

describe('UsuariosPantalla (HU-1.09)', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lista los usuarios con su estado', () => {
    const pantalla = TestBed.createComponent(UsuariosPantalla);
    http.expectOne(URL).flush([USUARIO]);
    pantalla.detectChanges();
    const texto = pantalla.nativeElement.textContent;
    expect(texto).toContain('ana@empresa.gt');
    expect(texto).toContain('activo');
    expect(texto).toContain('Suspender');
  });

  it('suspende a un usuario y refleja el nuevo estado', () => {
    const pantalla = TestBed.createComponent(UsuariosPantalla);
    http.expectOne(URL).flush([USUARIO]);
    pantalla.detectChanges();

    pantalla.nativeElement.querySelector('tbody button').click();
    http.expectOne(`${URL}/7/suspender`).flush({ ...USUARIO, estado: 'suspendido' });
    pantalla.detectChanges();
    expect(pantalla.nativeElement.textContent).toContain('Reactivar');
  });

  it('muestra el error del servidor al crear un usuario', () => {
    const pantalla = TestBed.createComponent(UsuariosPantalla);
    http.expectOne(URL).flush([]);
    pantalla.detectChanges();

    const el: HTMLElement = pantalla.nativeElement;
    const llenar = (nombre: string, valor: string) => {
      const campo = el.querySelector<HTMLInputElement>(`[formControlName="${nombre}"]`)!;
      campo.value = valor;
      campo.dispatchEvent(new Event('input'));
    };
    llenar('correo', 'nuevo@empresa.gt');
    llenar('nombre', 'Nuevo');
    llenar('clave', 'debil');
    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    http
      .expectOne({ method: 'POST', url: URL })
      .flush(
        { detail: 'La contraseña debe tener al menos 12 caracteres' },
        { status: 400, statusText: '' },
      );
    pantalla.detectChanges();
    expect(el.textContent).toContain('al menos 12 caracteres');
  });
});
