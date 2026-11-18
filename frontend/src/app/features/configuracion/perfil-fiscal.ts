import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ConfiguracionService, ETIQUETAS_REGIMEN_ISR, PerfilFiscal } from './configuracion.service';

// HU-1.01 (Sprint 2): perfil fiscal con vigencia por cambio. Diferido: confirmar con el contador el
// régimen de ISR exacto y la calidad de agente de retención.
@Component({
  selector: 'app-perfil-fiscal',
  imports: [ReactiveFormsModule],
  templateUrl: './perfil-fiscal.html',
})
export class PerfilFiscalPantalla {
  private readonly servicio = inject(ConfiguracionService);

  protected readonly regimenes = ETIQUETAS_REGIMEN_ISR;
  protected readonly vigente = signal<PerfilFiscal | null>(null);
  protected readonly historial = signal<PerfilFiscal[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly guardando = signal(false);

  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    vigente_desde: [new Date().toLocaleDateString('en-CA'), Validators.required],
    razon_social: ['', Validators.required],
    nombre_comercial: ['', Validators.required],
    nit: ['', Validators.required],
    direccion_fiscal: ['', Validators.required],
    establecimiento: ['', Validators.required],
    regimen_isr: ['utilidades' as 'utilidades' | 'simplificado', Validators.required],
    agente_retencion_iva: false,
    agente_retencion_isr: false,
  });

  constructor() {
    this.cargar();
  }

  protected cargar(): void {
    // Sin perfil el backend responde 404: la pantalla muestra el aviso de "sin registrar".
    this.servicio.perfilFiscal().subscribe({
      next: (perfil) => this.vigente.set(perfil),
      error: () => this.vigente.set(null),
    });
    this.servicio.historialPerfilFiscal().subscribe({
      next: (perfiles) => this.historial.set(perfiles),
      error: () => this.error.set('No se pudo consultar el perfil fiscal'),
    });
  }

  protected guardar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    this.guardando.set(true);
    this.error.set(null);
    this.aviso.set(null);
    this.servicio.registrarPerfilFiscal(this.formulario.getRawValue()).subscribe({
      next: (perfil) => {
        this.guardando.set(false);
        this.aviso.set(`Perfil fiscal vigente desde el ${perfil.vigente_desde} guardado`);
        this.cargar();
      },
      error: (respuesta: HttpErrorResponse) => {
        this.guardando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(
          typeof detalle === 'string' ? detalle : 'No se pudo guardar el perfil fiscal',
        );
      },
    });
  }
}
