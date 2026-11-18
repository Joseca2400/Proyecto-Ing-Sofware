import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

// HU-1.09: inicio de sesión. El servidor responde igual si el correo no existe o la clave es errónea.
@Component({
  selector: 'app-entrar',
  imports: [ReactiveFormsModule],
  templateUrl: './entrar.html',
  styleUrl: './entrar.css',
})
export class Entrar {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly error = signal<string | null>(null);
  protected readonly entrando = signal(false);
  protected readonly formulario = inject(FormBuilder).nonNullable.group({
    correo: ['', [Validators.required, Validators.email]],
    clave: ['', Validators.required],
  });

  protected entrar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    this.entrando.set(true);
    this.error.set(null);
    const { correo, clave } = this.formulario.getRawValue();
    this.auth.entrar(correo, clave).subscribe({
      next: () => void this.router.navigate(['/inicio']),
      error: (respuesta: HttpErrorResponse) => {
        this.entrando.set(false);
        const detalle = respuesta.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo iniciar sesión');
      },
    });
  }
}
