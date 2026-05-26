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
  tempPasswordModal: { senha: string; nome: string; matricula: string } | null = null;
  editingCargoId: string | null = null;
  editingPermissionIds: { [key: string]: boolean } = {};

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
      this.users = usersRes.data.items ?? usersRes.data;

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

  startEditCargo(cargo: any) {
    this.editingCargoId = cargo.id_cargo;
    this.editingPermissionIds = {};
    const current = new Set((cargo.permissoes || []).map((p: any) => p.id_permissao));
    this.permissions.forEach(p => {
      this.editingPermissionIds[p.id_permissao] = current.has(p.id_permissao);
    });
  }

  cancelEditCargo() {
    this.editingCargoId = null;
    this.editingPermissionIds = {};
  }

  async saveCargoPermissions(cargoId: string) {
    this.clearAlerts();
    const ids = Object.keys(this.editingPermissionIds).filter(id => this.editingPermissionIds[id]);
    if (ids.length === 0) {
      this.showError('Selecione pelo menos uma permissão.');
      return;
    }
    try {
      await this.api.put(`/admin/cargos/${cargoId}/permissions`, { permissoes_ids: ids });
      this.showSuccess('Permissões do cargo atualizadas com sucesso!');
      this.cancelEditCargo();
      await this.loadData();
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao atualizar permissões.');
    }
  }

  async onResetPassword(user: any) {
    this.clearAlerts();
    try {
      const res = await this.api.post(`/admin/users/${user.id_usuario}/reset-password`, {});
      this.tempPasswordModal = { senha: res.data.temp_password, nome: user.nome, matricula: user.matricula };
      await this.loadData();
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao gerar senha temporária.');
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
