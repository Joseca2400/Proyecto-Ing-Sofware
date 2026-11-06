import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  ComprasService,
  Proveedor,
  ProveedorEntrada,
  RUBROS,
  RubroProveedor,
  TipoProveedor,
} from './compras.service';

// HU-4.01 (Sprint 1): alta y consulta de proveedores locales o del exterior.
// El dígito verificador del NIT lo valida el servidor; aquí solo se revisa la forma.
// Diferido: régimen y retenciones del proveedor local.
@Component({
  selector: 'app-proveedores',
  imports: [ReactiveFormsModule],
  templateUrl: './proveedores.html',
  styleUrl: './proveedores.css',
})
export class ProveedoresPantalla {
  private readonly servicio = inject(ComprasService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly rubros = RUBROS;
  protected readonly proveedores = signal<Proveedor[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    tipo: ['local' as TipoProveedor],
    nombre: ['', Validators.required],
    nit: ['', Validators.pattern(/^\s*\d[\d\s]*-?\s*[\dkK]\s*$/)],
    identificacion_fiscal: [''],
    pais: ['', Validators.pattern(/^[A-Za-z]{2}$/)],
    rubro: ['repuestos' as RubroProveedor],
    moneda_habitual: ['GTQ' as 'GTQ' | 'USD'],
    dias_credito: [0, [Validators.required, Validators.min(0), Validators.max(365)]],
    banco: [''],
    cuenta_bancaria: [''],
  });

  protected readonly filtro = this.fb.group({
    buscar: [''],
    tipo: ['' as TipoProveedor | ''],
    rubro: ['' as RubroProveedor | ''],
  });

  protected readonly tipo = toSignal(this.formulario.controls.tipo.valueChanges, {
    initialValue: this.formulario.controls.tipo.value,
  });

  constructor() {
    this.cargar();
  }

  protected etiquetaRubro(valor: RubroProveedor): string {
    return this.rubros.find((r) => r.valor === valor)?.etiqueta ?? valor;
  }

  protected cargar(): void {
    const { buscar, tipo, rubro } = this.filtro.getRawValue();
    this.servicio
      .proveedores({
        buscar: buscar.trim() || undefined,
        tipo: tipo || undefined,
        rubro: rubro || undefined,
      })
      .subscribe({
        next: (lista) => this.proveedores.set(lista),
        error: () => this.error.set('No se pudo consultar los proveedores'),
      });
  }

  protected guardar(): void {
    const valores = this.formulario.getRawValue();
    const local = valores.tipo === 'local';
    const faltante = local
      ? !valores.nit.trim() && 'El NIT es obligatorio para un proveedor local'
      : (!valores.identificacion_fiscal.trim() || !valores.pais.trim()) &&
        'Un proveedor del exterior requiere identificación fiscal y país';

    if (this.formulario.invalid || faltante) {
      this.formulario.markAllAsTouched();
      this.error.set(faltante || null);
      return;
    }

    const opcional = (texto: string) => texto.trim() || undefined;
    const entrada: ProveedorEntrada = {
      tipo: valores.tipo,
      nombre: valores.nombre.trim(),
      rubro: valores.rubro,
      moneda_habitual: valores.moneda_habitual,
      dias_credito: valores.dias_credito,
      banco: opcional(valores.banco),
      cuenta_bancaria: opcional(valores.cuenta_bancaria),
      ...(local
        ? { nit: valores.nit.trim() }
        : {
            identificacion_fiscal: valores.identificacion_fiscal.trim(),
            pais: valores.pais.trim().toUpperCase(),
          }),
    };

    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.registrarProveedor(entrada).subscribe({
      next: (proveedor) => {
        this.guardando.set(false);
        this.aviso.set(`Proveedor ${proveedor.nombre} registrado`);
        this.formulario.reset({ tipo: valores.tipo });
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo registrar el proveedor');
      },
    });
  }
}
