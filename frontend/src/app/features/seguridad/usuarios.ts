import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { NOMBRE_ROL, Rol } from '../../core/auth/auth.service';
import { SeguridadService, UsuarioAdmin } from './seguridad.service';

// HU-1.09: alta, suspensión, reactivación y baja de usuarios; solo el gerente financiero (lo decide
// el servidor). Diferido: cambio de rol y de contraseña.
@Component({
  selector: 'app-usuarios',
  imports: [ReactiveFormsModule, DatePipe],
  templateUrl: './usuarios.html',
})
export class UsuariosPantalla {
  private readonly servicio = inject(SeguridadService);

  protected readonly nombres: Record<string, string> = NOMBRE_ROL;
  protected readonly roles = Object.keys(NOMBRE_ROL) as Rol[];
  protected readonly usuarios = signal<UsuarioAdmin[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    correo: ['', Validators.required],
    nombre: ['', Validators.required],
    rol: ['contador', Validators.required],
    clave: ['', Validators.required],
  });

  constructor() {
    this.cargar();
  }

  protected crear(): void {
    this.iniciar();
    this.servicio.altaUsuario(this.formulario.getRawValue()).subscribe({
      next: (usuario) => {
        this.aviso.set(`Usuario ${usuario.correo} creado`);
        this.formulario.patchValue({ correo: '', nombre: '', clave: '' });
        this.cargar();
      },
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo crear el usuario'),
    });
  }

  protected cambiar(usuario: UsuarioAdmin, accion: 'suspender' | 'reactivar' | 'baja'): void {
    if (accion === 'baja' && !confirm(`¿Dar de baja a ${usuario.correo}? No se puede deshacer.`)) {
      return;
    }
    this.iniciar();
    this.servicio.cambiarEstado(usuario.id, accion).subscribe({
      next: (nuevo) => {
        this.usuarios.update((lista) => lista.map((u) => (u.id === nuevo.id ? nuevo : u)));
        this.aviso.set(`${nuevo.correo}: ${nuevo.estado}`);
      },
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo cambiar el estado'),
    });
  }

  private cargar(): void {
    this.servicio.usuarios().subscribe({
      next: (lista) => this.usuarios.set(lista),
      error: (r: HttpErrorResponse) => this.fallo(r, 'No se pudo consultar los usuarios'),
    });
  }

  private iniciar(): void {
    this.error.set(null);
    this.aviso.set(null);
  }

  private fallo(respuesta: HttpErrorResponse, mensaje: string): void {
    const detalle = respuesta.error?.detail;
    this.error.set(typeof detalle === 'string' ? detalle : mensaje);
  }
}
