import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './header.component.html'
})
export class HeaderComponent implements OnInit {
  title = 'Termo Fácil';
  activeUser: any = null;
  allUsers: any[] = [];
  selectedSimUserId: string = '';

  constructor(private api: ApiService, private router: Router) {}

  async ngOnInit() {
    await this.fetchActiveUser();
    await this.fetchAllUsers();
  }

  async fetchActiveUser() {
    try {
      const response = await this.api.get('/auth/me');
      this.activeUser = response.data;
      this.selectedSimUserId = this.activeUser?.id_usuario || '';
      if (!localStorage.getItem('simulated_user_id') && this.selectedSimUserId) {
        localStorage.setItem('simulated_user_id', this.selectedSimUserId);
      }
    } catch (error) {
      console.error('Erro ao buscar perfil atual:', error);
    }
  }

  async fetchAllUsers() {
    try {
      const response = await this.api.get('/auth/users');
      this.allUsers = response.data;
    } catch (error) {
      console.error('Erro ao buscar lista de usuários para simulação:', error);
    }
  }

  async onUserSimChange() {
    if (this.selectedSimUserId) {
      localStorage.setItem('simulated_user_id', this.selectedSimUserId);
      window.location.reload();
    }
  }

  get canManageUsers(): boolean {
    if (!this.activeUser || !this.activeUser.cargo) return false;
    const permissions = this.activeUser.cargo.permissoes || [];
    return permissions.some((p: any) => p.nome_permissao === 'GERENCIAR_USUARIOS');
  }

  get userInitials(): string {
    if (!this.activeUser || !this.activeUser.nome) return 'TF';
    const names = this.activeUser.nome.replace(' (Escrivão)', '').replace(' (Delegado)', '').replace(' (Admin)', '').split(' ');
    if (names.length >= 2) {
      return (names[0][0] + names[1][0]).toUpperCase();
    }
    return names[0][0].toUpperCase();
  }
}
