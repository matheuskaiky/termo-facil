import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './change-password.component.html',
})
export class ChangePasswordComponent {
  novaSenha = '';
  confirmar = '';
  erro = '';
  carregando = false;

  constructor(private auth: AuthService, private router: Router) {}

  get senhasNaoConferem(): boolean {
    return this.confirmar.length > 0 && this.novaSenha !== this.confirmar;
  }

  get podeSalvar(): boolean {
    return this.novaSenha.length >= 8 && this.novaSenha === this.confirmar && !this.carregando;
  }

  async onSubmit() {
    if (!this.podeSalvar) return;
    this.carregando = true;
    this.erro = '';
    try {
      await this.auth.changePassword(this.novaSenha);
      this.router.navigate(['/processos']);
    } catch (e: any) {
      this.erro = e?.response?.data?.detail ?? 'Erro ao alterar senha.';
    } finally {
      this.carregando = false;
    }
  }
}
