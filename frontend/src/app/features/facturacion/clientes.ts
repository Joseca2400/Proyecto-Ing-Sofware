import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  Cliente,
  ClienteEntrada,
  FacturacionService,
  TipoIdentificacion,
} from './facturacion.service';

// HU-6.01 (Sprint 2): alta y consulta de clientes con NIT, CUI o pasaporte.
// El verificador del NIT y los duplicados los decide el servidor.
// Diferido: nombre registrado en la SAT (HU-6.02) y estado de cuenta integrado (Sprint 3).
@Component({
  selector: 'app-clientes',
  imports: [ReactiveFormsModule],
  templateUrl: './clientes.html',
})
export class ClientesPantalla {
  private readonly servicio = inject(FacturacionService);
  private readonly fb = inject(FormBuilder).nonNullable;

  protected readonly clientes = signal<Cliente[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = this.fb.group({
    tipo: ['individual' as 'individual' | 'empresa'],
    nombre: ['', Validators.required],
    tipo_identificacion: ['nit' as TipoIdentificacion],
    identificacion: ['', Validators.required],
    pais: [''],
    direccion: [''],
    telefono: [''],
    correo: ['', Validators.email],
    agente_retencion_iva: [false],
    agente_retencion_isr: [false],
  });

  protected readonly filtro = this.fb.group({ buscar: [''] });

  protected readonly tipo = toSignal(this.formulario.controls.tipo.valueChanges, {
    initialValue: this.formulario.controls.tipo.value,
  });
  protected readonly tipoIdentificacion = toSignal(
    this.formulario.controls.tipo_identificacion.valueChanges,
    { initialValue: this.formulario.controls.tipo_identificacion.value },
  );

  constructor() {
    // Una empresa solo se identifica con NIT.
    this.formulario.controls.tipo.valueChanges.subscribe((tipo) => {
      if (tipo === 'empresa') this.formulario.controls.tipo_identificacion.setValue('nit');
    });
    this.cargar();
  }

  protected cargar(): void {
    this.servicio.clientes(this.filtro.controls.buscar.value.trim() || undefined).subscribe({
      next: (lista) => this.clientes.set(lista),
      error: () => this.error.set('No se pudo consultar los clientes'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    const v = this.formulario.getRawValue();
    const opcional = (texto: string) => texto.trim() || undefined;
    const entrada: ClienteEntrada = {
      tipo: v.tipo,
      nombre: v.nombre.trim(),
      tipo_identificacion: v.tipo_identificacion,
      identificacion: v.identificacion.trim(),
      pais: v.tipo_identificacion === 'pasaporte' ? opcional(v.pais)?.toUpperCase() : undefined,
      direccion: opcional(v.direccion),
      telefono: opcional(v.telefono),
      correo: opcional(v.correo),
      agente_retencion_iva: v.agente_retencion_iva,
      agente_retencion_isr: v.agente_retencion_isr,
    };

    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.registrarCliente(entrada).subscribe({
      next: (cliente) => {
        this.guardando.set(false);
        this.aviso.set(`Cliente ${cliente.nombre} registrado`);
        this.formulario.reset({ tipo: v.tipo, tipo_identificacion: v.tipo_identificacion });
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
