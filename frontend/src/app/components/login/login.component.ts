import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
})
export class LoginComponent {
  matricula = '';
  senha = '';
  erro = '';
  carregando = false;

  constructor(private auth: AuthService, private router: Router) {}

  async onSubmit() {
    if (!this.matricula || !this.senha) return;
    this.carregando = true;
    this.erro = '';
    try {
      await this.auth.login(this.matricula, this.senha);
      this.router.navigate(['/processos']);
    } catch (e: any) {
      this.erro = e?.response?.data?.detail ?? 'Erro ao conectar com o servidor.';
    } finally {
      this.carregando = false;
    }
  }
}
