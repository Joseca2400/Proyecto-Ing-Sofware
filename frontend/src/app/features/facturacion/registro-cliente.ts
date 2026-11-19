import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Cliente, ClienteEntrada, FacturacionService, TipoCliente } from './facturacion.service';

type Origen = 'nacional' | 'extranjero';

// HU-6.01 (Sprint 1): alta y consulta de clientes individuales o empresas.
// La empresa se identifica con NIT; la persona guatemalteca con CUI o NIT; la extranjera con
// pasaporte y país. El dígito verificador del NIT y los duplicados los valida el servidor.
// Diferido: consulta del nombre en la SAT y estado de cuenta integrado (Sprint 3).
@Component({
  selector: 'app-registro-cliente',
  imports: [ReactiveFormsModule],
  templateUrl: './registro-cliente.html',
  styleUrl: './registro-cliente.css',
})
export class RegistroClientePantalla {
  private readonly servicio = inject(FacturacionService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly clientes = signal<Cliente[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    tipo: ['individual' as TipoCliente],
    origen: ['nacional' as Origen],
    nombre: ['', Validators.required],
    nit: ['', Validators.pattern(/^\s*\d[\d\s]*-?\s*[\dkK]\s*$/)],
    cui: ['', Validators.pattern(/^\s*(\d[\s-]*){13}$/)],
    pasaporte: [''],
    pais: ['', Validators.pattern(/^[A-Za-z]{2}$/)],
    direccion: [''],
    telefono: [''],
    correo: ['', Validators.email],
    agente_retencion_iva: [false],
    agente_retencion_isr: [false],
  });

  protected readonly filtro = this.fb.group({
    buscar: [''],
    tipo: ['' as TipoCliente | ''],
  });

  protected readonly tipo = toSignal(this.formulario.controls.tipo.valueChanges, {
    initialValue: this.formulario.controls.tipo.value,
  });

  protected readonly origen = toSignal(this.formulario.controls.origen.valueChanges, {
    initialValue: this.formulario.controls.origen.value,
  });

  constructor() {
    this.cargar();
  }

  protected cargar(): void {
    const { buscar, tipo } = this.filtro.getRawValue();
    this.servicio
      .clientes({ buscar: buscar.trim() || undefined, tipo: tipo || undefined })
      .subscribe({
        next: (lista) => this.clientes.set(lista),
        error: () => this.error.set('No se pudo consultar los clientes'),
      });
  }

  protected guardar(): void {
    const valores = this.formulario.getRawValue();
    const empresa = valores.tipo === 'empresa';
    const extranjero = !empresa && valores.origen === 'extranjero';
    let faltante: string | false;
    if (empresa) {
      faltante = !valores.nit.trim() && 'Una empresa se identifica con su NIT';
    } else if (extranjero) {
      faltante =
        (!valores.pasaporte.trim() || !valores.pais.trim()) &&
        'Un cliente extranjero requiere pasaporte y país';
    } else {
      faltante =
        !valores.cui.trim() && !valores.nit.trim() && 'Indique el CUI o el NIT del cliente';
    }

    if (this.formulario.invalid || faltante) {
      this.formulario.markAllAsTouched();
      this.error.set(faltante || null);
      return;
    }

    const opcional = (texto: string) => texto.trim() || undefined;
    const entrada: ClienteEntrada = {
      tipo: valores.tipo,
      nombre: valores.nombre.trim(),
      nit: opcional(valores.nit),
      ...(empresa
        ? {}
        : extranjero
          ? { pasaporte: valores.pasaporte.trim(), pais: valores.pais.trim().toUpperCase() }
          : { cui: opcional(valores.cui) }),
      direccion: opcional(valores.direccion),
      telefono: opcional(valores.telefono),
      correo: opcional(valores.correo),
      agente_retencion_iva: valores.agente_retencion_iva,
      agente_retencion_isr: valores.agente_retencion_isr,
    };
    // Sin claves vacías: el servidor recibe solo lo que se capturó.
    for (const clave of Object.keys(entrada) as (keyof ClienteEntrada)[]) {
      if (entrada[clave] === undefined) delete entrada[clave];
    }

    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.registrarCliente(entrada).subscribe({
      next: (cliente) => {
        this.guardando.set(false);
        this.aviso.set(`Cliente ${cliente.nombre} registrado`);
        this.formulario.reset({ tipo: valores.tipo, origen: valores.origen });
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo registrar el cliente');
      },
    });
  }
}
