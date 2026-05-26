import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
})
export class LoginComponent implements OnInit {
  matricula = '';
  senha = '';
  erro = '';
  carregando = false;
  sessaoExpirada = false;

  constructor(private auth: AuthService, private router: Router, private route: ActivatedRoute) {}

  ngOnInit() {
    this.sessaoExpirada = this.route.snapshot.queryParamMap.get('expired') === '1';
  }

  async onSubmit() {
    if (!this.matricula || !this.senha) return;
    this.carregando = true;
    this.erro = '';
    this.sessaoExpirada = false;
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
