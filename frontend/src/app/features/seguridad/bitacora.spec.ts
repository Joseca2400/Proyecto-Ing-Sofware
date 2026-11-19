import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { BitacoraPantalla } from './bitacora';

const URL = '/api/v1/seguridad/bitacora';
const REGISTRO = {
  id: 9,
  usuario_id: 2,
  fecha: '2026-11-10T15:30:00Z',
  entidad: 'unidad',
  registro_id: '4',
  accion: 'modificar',
  vin: '1HGCM82633A004352',
  anteriores: { estado: 'en_transito' },
  nuevos: { estado: 'en_aduana' },
};

describe('BitacoraPantalla (HU-1.11)', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  it('muestra los cambios con sus valores anteriores y nuevos', () => {
    const pantalla = TestBed.createComponent(BitacoraPantalla);
    http.expectOne(URL).flush([REGISTRO]);
    pantalla.detectChanges();

    const texto = pantalla.nativeElement.textContent;
    expect(texto).toContain('unidad');
    expect(texto).toContain('1HGCM82633A004352');
    expect(texto).toContain('en_transito');
    expect(texto).toContain('en_aduana');
  });

  it('filtra por usuario, entidad y VIN, y solo envía los filtros con valor', () => {
    const pantalla = TestBed.createComponent(BitacoraPantalla);
    http.expectOne(URL).flush([]);
    pantalla.detectChanges();

    const el: HTMLElement = pantalla.nativeElement;
    const vin = el.querySelector<HTMLInputElement>('input[formControlName="vin"]')!;
    vin.value = '1hgcm82633a004352';
    vin.dispatchEvent(new Event('input'));
    el.querySelector('form')!.dispatchEvent(new Event('submit'));

    const peticion = http.expectOne((p) => p.url === URL);
    expect(peticion.request.params.keys()).toEqual(['vin']);
    expect(peticion.request.params.get('vin')).toBe('1HGCM82633A004352');
    peticion.flush([]);
    pantalla.detectChanges();
    expect(el.textContent).toContain('No hay cambios con esos filtros');
  });

  it('avisa cuando el servidor rechaza la consulta', () => {
    const pantalla = TestBed.createComponent(BitacoraPantalla);
    http
      .expectOne(URL)
      .flush({ detail: 'Tu rol no tiene permiso' }, { status: 403, statusText: '' });
    pantalla.detectChanges();
    expect(pantalla.nativeElement.textContent).toContain('Tu rol no tiene permiso');
  });
});
