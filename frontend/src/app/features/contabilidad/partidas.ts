import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Observable } from 'rxjs';
import { MontoPipe } from '../../shared/pipes/monto.pipe';
import { ETIQUETAS_LINEA } from '../configuracion/configuracion.service';
import { ContabilidadService, Cuenta, Partida, PartidaEntrada } from './contabilidad.service';

// El front solo revisa la forma; cuadre, totales, equivalente en quetzales y dimensiones los
// calcula y valida el servidor.
const MONTO = /^\s*\d+(\.\d{1,6})?\s*$/;
const VIN = /^\s*[A-HJ-NPR-Za-hj-npr-z0-9]{17}\s*$/;
const CERO = '0.000000';

// HU-2.01, HU-2.02 y HU-1.10 (Sprint 1): captura de la partida manual, bandeja de revisión y
// separación de funciones (la decide el servidor). Diferido: adjuntos, lotes y límites de aprobación.
@Component({
  selector: 'app-partidas',
  imports: [ReactiveFormsModule, MontoPipe],
  templateUrl: './partidas.html',
  styleUrls: ['../configuracion/catalogo.css', './partidas.css'],
})
export class PartidasPantalla {
  private readonly servicio = inject(ContabilidadService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly CERO = CERO;
  protected readonly etiquetasLinea = ETIQUETAS_LINEA;
  protected readonly estados: Record<string, string> = {
    borrador: 'Borrador',
    en_revision: 'En revisión',
    contabilizada: 'Contabilizada',
    devuelta: 'Devuelta',
  };
  protected readonly claves = Object.keys(this.estados);
  protected readonly cuentas = signal<Cuenta[]>([]);
  protected readonly lineasNegocio = signal<string[]>([]);
  protected readonly partidas = signal<Partida[]>([]);
  protected readonly seleccionada = signal<Partida | null>(null);
  protected readonly editando = signal<number | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    fecha: ['', Validators.required],
    concepto: ['', Validators.required],
    documento_soporte: [''],
    lineas: this.fb.array([this.nuevaLinea(), this.nuevaLinea()]),
  });
  protected readonly filtro = this.fb.control('en_revision');
  protected readonly comentario = this.fb.control('', Validators.required);

  constructor() {
    this.servicio.cuentas().subscribe({
      next: (lista) => this.cuentas.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar las cuentas'),
    });
    this.servicio.lineasNegocio().subscribe({
      next: (lista) => this.lineasNegocio.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar las líneas de negocio'),
    });
    this.cargar();
  }

  protected get lineas() {
    return this.formulario.controls.lineas;
  }

  private nuevaLinea() {
    return this.fb.group({
      cuenta_id: [0, Validators.min(1)],
      lado: ['debe' as 'debe' | 'haber'],
      moneda: ['GTQ' as 'GTQ' | 'USD'],
      monto: ['', [Validators.required, Validators.pattern(MONTO)]],
      linea_negocio: [''],
      vin: ['', Validators.pattern(VIN)],
    });
  }

  protected agregarLinea(): void {
    this.lineas.push(this.nuevaLinea());
  }

  protected quitarLinea(indice: number): void {
    if (this.lineas.length > 2) this.lineas.removeAt(indice);
  }

  protected cuenta(id: number): string {
    const cuenta = this.cuentas().find((c) => c.id === id);
    return cuenta ? `${cuenta.codigo} · ${cuenta.nombre}` : `${id}`;
  }

  protected cargar(): void {
    this.servicio.partidas(this.filtro.value || undefined).subscribe({
      next: (lista) => this.partidas.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar las partidas'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    const v = this.formulario.getRawValue();
    const datos: PartidaEntrada = {
      fecha: v.fecha,
      concepto: v.concepto.trim(),
      documento_soporte: v.documento_soporte.trim() || null,
      lineas: v.lineas.map((l) => ({
        cuenta_id: l.cuenta_id,
        lado: l.lado,
        moneda: l.moneda,
        monto: l.monto.trim(),
        linea_negocio: l.linea_negocio || null,
        vin: l.vin.trim().toUpperCase() || null,
      })),
    };
    const id = this.editando();
    this.ejecutar(
      id === null ? this.servicio.registrar(datos) : this.servicio.corregir(id, datos),
      (p) => `Partida ${p.id} guardada en borrador`,
      () => this.limpiar(),
    );
  }

  protected editar(p: Partida): void {
    this.editando.set(p.id);
    this.lineas.clear();
    p.lineas.forEach(() => this.lineas.push(this.nuevaLinea()));
    this.formulario.setValue({
      fecha: p.fecha,
      concepto: p.concepto,
      documento_soporte: p.documento_soporte ?? '',
      lineas: p.lineas.map((l) => {
        const lado = l.debe !== CERO ? 'debe' : 'haber';
        return {
          cuenta_id: l.cuenta_id,
          lado,
          moneda: l.moneda as 'GTQ' | 'USD',
          monto: (l.moneda === 'USD' ? l.monto_usd : l[lado]) ?? '',
          linea_negocio: l.linea_negocio ?? '',
          vin: l.vin ?? '',
        };
      }),
    });
  }

  protected limpiar(): void {
    this.editando.set(null);
    this.formulario.reset();
    while (this.lineas.length > 2) this.lineas.removeAt(2);
  }

  protected ver(p: Partida): void {
    this.seleccionada.set(p);
    this.comentario.reset();
  }

  protected enviar(p: Partida): void {
    this.ejecutar(this.servicio.enviarARevision(p.id), (r) => `Partida ${r.id} enviada a revisión`);
  }

  protected contabilizar(p: Partida): void {
    this.ejecutar(
      this.servicio.contabilizar(p.id),
      (r) => `Partida contabilizada con el número ${r.numero}`,
    );
  }

  protected devolver(p: Partida): void {
    if (this.comentario.invalid || !this.comentario.value.trim()) {
      this.comentario.markAsTouched();
      return;
    }
    this.ejecutar(
      this.servicio.devolver(p.id, this.comentario.value.trim()),
      (r) => `Partida ${r.id} devuelta`,
    );
  }

  private ejecutar(
    accion: Observable<Partida>,
    aviso: (p: Partida) => string,
    despues?: () => void,
  ): void {
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    accion.subscribe({
      next: (p) => {
        this.guardando.set(false);
        this.aviso.set(aviso(p));
        despues?.();
        this.ver(p);
        this.cargar();
      },
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo completar la operación'),
    });
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    this.guardando.set(false);
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
