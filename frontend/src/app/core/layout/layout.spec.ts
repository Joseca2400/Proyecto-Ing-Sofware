import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { CLAVE_TEMA } from '../tema/tema.service';
import { Layout } from './layout';

/** Simula la preferencia de color del sistema (jsdom no trae matchMedia). */
function sistemaEnOscuro(oscuro: boolean): void {
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: (consulta: string) => ({
      matches: oscuro && consulta === '(prefers-color-scheme: dark)',
      media: consulta,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
    }),
  });
}

function crearLayout() {
  TestBed.configureTestingModule({
    providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
  });
  const fixture = TestBed.createComponent(Layout);
  fixture.detectChanges();
  const boton = (): HTMLButtonElement => fixture.nativeElement.querySelector('button.tema');
  return { fixture, boton };
}

describe('Botón de modo claro/oscuro', () => {
  const html = document.documentElement;

  beforeEach(() => {
    localStorage.clear();
    delete html.dataset['tema'];
  });

  afterEach(() => {
    delete (window as { matchMedia?: unknown }).matchMedia;
    localStorage.clear();
  });

  it('la primera vez sigue al sistema y al pulsarlo cambia de modo y lo recuerda', () => {
    sistemaEnOscuro(true);
    const { fixture, boton } = crearLayout();

    expect(html.dataset['tema']).toBe('oscuro');
    expect(boton().getAttribute('aria-label')).toBe('Activar modo claro');
    expect(localStorage.getItem(CLAVE_TEMA)).toBeNull();

    boton().click();
    fixture.detectChanges();

    expect(html.dataset['tema']).toBe('claro');
    expect(boton().getAttribute('aria-label')).toBe('Activar modo oscuro');
    expect(localStorage.getItem(CLAVE_TEMA)).toBe('claro');

    boton().click();
    fixture.detectChanges();

    expect(html.dataset['tema']).toBe('oscuro');
    expect(localStorage.getItem(CLAVE_TEMA)).toBe('oscuro');
  });

  it('lo que eligió el usuario gana sobre la preferencia del sistema', () => {
    sistemaEnOscuro(false);
    localStorage.setItem(CLAVE_TEMA, 'oscuro');
    const { boton } = crearLayout();

    expect(html.dataset['tema']).toBe('oscuro');
    expect(boton().getAttribute('aria-label')).toBe('Activar modo claro');
  });

  it('sin localStorage ni matchMedia arranca en claro y el botón sigue funcionando', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('bloqueado');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('bloqueado');
    });
    const { fixture, boton } = crearLayout();

    expect(html.dataset['tema']).toBe('claro');
    boton().click();
    fixture.detectChanges();
    expect(html.dataset['tema']).toBe('oscuro');

    vi.restoreAllMocks();
  });
});
