import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
export class AdminComponent implements OnInit {
  users: any[] = [];
  cargos: any[] = [];
  permissions: any[] = [];
  
  // Create Cargo state
  newCargoName: string = '';
  selectedPermissionIds: { [key: string]: boolean } = {};
  
  activeTab: 'users' | 'roles' = 'users';
  
  // Feedback messages
  successMessage: string = '';
  errorMessage: string = '';

  constructor(private api: ApiService) {}

  async ngOnInit() {
    await this.loadData();
  }

  async loadData() {
    try {
      const usersRes = await this.api.get('/admin/users');
      this.users = usersRes.data;

      const cargosRes = await this.api.get('/admin/cargos');
      this.cargos = cargosRes.data;

      const permRes = await this.api.get('/admin/permissions');
      this.permissions = permRes.data;
      
      // Initialize checkboxes
      this.permissions.forEach(p => {
        this.selectedPermissionIds[p.id_permissao] = false;
      });
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao carregar dados do servidor.');
    }
  }

  async onRoleChange(userId: string, newCargoId: string) {
    this.clearAlerts();
    try {
      await this.api.put(`/admin/users/${userId}/cargo`, { id_cargo: newCargoId });
      this.showSuccess('Cargo do usuário atualizado com sucesso!');
      await this.loadData();
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao atualizar cargo do usuário.');
    }
  }

  async onCreateCargo() {
    this.clearAlerts();
    
    if (!this.newCargoName.trim()) {
      this.showError('O nome do cargo é obrigatório.');
      return;
    }

    const permissionIds = Object.keys(this.selectedPermissionIds).filter(
      id => this.selectedPermissionIds[id]
    );

    if (permissionIds.length === 0) {
      this.showError('Selecione pelo menos uma permissão para o novo cargo.');
      return;
    }

    try {
      await this.api.post('/admin/cargos', {
        nome_cargo: this.newCargoName.trim(),
        permissoes_ids: permissionIds
      });

      this.showSuccess(`Cargo "${this.newCargoName}" criado com sucesso!`);
      this.newCargoName = '';
      
      // Reset checkboxes
      this.permissions.forEach(p => {
        this.selectedPermissionIds[p.id_permissao] = false;
      });

      await this.loadData();
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao criar o cargo.');
    }
  }

  togglePermission(permId: string) {
    this.selectedPermissionIds[permId] = !this.selectedPermissionIds[permId];
  }

  showSuccess(msg: string) {
    this.successMessage = msg;
    setTimeout(() => this.successMessage = '', 4000);
  }

  showError(msg: string) {
    this.errorMessage = msg;
    setTimeout(() => this.errorMessage = '', 5000);
  }

  clearAlerts() {
    this.successMessage = '';
    this.errorMessage = '';
  }
}
