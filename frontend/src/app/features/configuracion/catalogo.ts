import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  ConfiguracionService,
  Cuenta,
  CuentaEntrada,
  ETIQUETAS_LINEA,
} from './configuracion.service';

// HU-1.02 y HU-1.04 (Sprint 1): consulta jerárquica, alta mínima y dimensiones por cuenta.
// El servidor valida padre, tipo y código único. Diferido: máscara de niveles e inactivación.
@Component({
  selector: 'app-catalogo',
  imports: [ReactiveFormsModule],
  templateUrl: './catalogo.html',
  styleUrl: './catalogo.css',
})
export class CatalogoPantalla {
  private readonly servicio = inject(ConfiguracionService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly etiquetasLinea = ETIQUETAS_LINEA;
  protected readonly tipos = ['activo', 'pasivo', 'patrimonio', 'ingreso', 'costo', 'gasto'];
  protected readonly cuentas = signal<Cuenta[]>([]);
  protected readonly lineas = signal<string[]>([]);
  protected readonly padres = computed(() => this.cuentas().filter((c) => !c.es_detalle));
  protected readonly seleccionada = signal<Cuenta | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    codigo: ['', Validators.required],
    nombre: ['', Validators.required],
    tipo: ['activo' as Cuenta['tipo']],
    naturaleza: ['deudora' as Cuenta['naturaleza']],
    padre_id: [0],
    es_detalle: [true],
    monetaria_usd: [false],
    linea_obligatoria: [false],
    vin: ['no_aplica' as Cuenta['vin']],
    linea_defecto: ['' as Cuenta['linea_defecto'] | ''],
  });

  protected readonly dimensiones = this.fb.group({
    linea_obligatoria: [false],
    vin: ['no_aplica' as Cuenta['vin']],
    linea_defecto: ['' as Cuenta['linea_defecto'] | ''],
  });

  constructor() {
    this.servicio.lineasNegocio().subscribe({
      next: (lista) => this.lineas.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar las líneas de negocio'),
    });
    this.cargar();
  }

  private cargar(): void {
    this.servicio.cuentas().subscribe({
      next: (lista) => this.cuentas.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar el catálogo'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    const v = this.formulario.getRawValue();
    const entrada: CuentaEntrada = {
      codigo: v.codigo.trim(),
      nombre: v.nombre.trim(),
      tipo: v.tipo,
      naturaleza: v.naturaleza,
      padre_id: v.padre_id || null,
      es_detalle: v.es_detalle,
      monetaria_usd: v.monetaria_usd,
      // Las cuentas de agrupación no llevan dimensiones.
      linea_obligatoria: v.es_detalle && v.linea_obligatoria,
      vin: v.es_detalle ? v.vin : 'no_aplica',
      linea_defecto: (v.es_detalle && v.linea_defecto) || null,
    };
    this.iniciar();
    this.servicio.crearCuenta(entrada).subscribe({
      next: (cuenta) => {
        this.guardando.set(false);
        this.aviso.set(`Cuenta ${cuenta.codigo} creada`);
        this.formulario.reset();
        this.cargar();
      },
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo crear la cuenta'),
    });
  }

  protected editar(cuenta: Cuenta): void {
    this.seleccionada.set(cuenta);
    this.dimensiones.setValue({
      linea_obligatoria: cuenta.linea_obligatoria,
      vin: cuenta.vin,
      linea_defecto: cuenta.linea_defecto ?? '',
    });
  }

  protected guardarDimensiones(): void {
    const cuenta = this.seleccionada();
    if (!cuenta) return;
    const v = this.dimensiones.getRawValue();
    this.iniciar();
    this.servicio
      .definirDimensiones(cuenta.id, {
        linea_obligatoria: v.linea_obligatoria,
        vin: v.vin,
        linea_defecto: v.linea_defecto || null,
      })
      .subscribe({
        next: (actualizada) => {
          this.guardando.set(false);
          this.aviso.set(`Dimensiones de ${actualizada.codigo} guardadas`);
          this.seleccionada.set(null);
          this.cargar();
        },
        error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo guardar las dimensiones'),
      });
  }

  private iniciar(): void {
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    this.guardando.set(false);
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
