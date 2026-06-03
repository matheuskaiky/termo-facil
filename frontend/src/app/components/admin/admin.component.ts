import { Component, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../services/api.service';

type AdminTab = 'users' | 'roles' | 'matrix' | 'delegacias';
const ADMIN_TABS: AdminTab[] = ['users', 'roles', 'matrix', 'delegacias'];

const PERM_CATEGORIES: Record<string, string[]> = {
  'Processamento': ['UPLOAD_AUDIO', 'EDITAR_TERMO', 'GERAR_PDF', 'CRIAR_TERMO'],
  'Administração': ['GERENCIAR_USUARIOS', 'VER_METRICAS', 'REDEFINIR_SENHA', 'VER_TODOS_TERMOS', 'ACESSAR_DEV_DEBUG'],
};

// O cargo Admin é imutável e onipotente — a UI o trata como somente-leitura
// (o backend rejeita qualquer alteração com 403).
const ADMIN_CARGO = 'Admin';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
export class AdminComponent implements OnInit {
  users: any[] = [];
  cargos: any[] = [];
  permissions: any[] = [];

  activeTab: AdminTab = 'users';
  filtroChip: string = 'Todos';
  searchAdmin: string = '';
  selectedUser: any = null;
  drawerCargo: string = '';

  newCargoName: string = '';
  selectedPermissionIds: Record<string, boolean> = {};
  editingCargoId: string | null = null;
  editingCargoNameValue: string = '';
  editingPermissionIds: Record<string, boolean> = {};

  tempPasswordModal: { senha: string; nome: string; matricula: string } | null = null;

  successMessage = '';
  errorMessage = '';

  chipOptions = ['Todos', 'Escrivão', 'Delegado', 'Administrador', 'Auditor', 'Supervisor', 'Inativo'];
  permCategories = Object.entries(PERM_CATEGORIES);

  // Delegacias tab
  delegacias: any[] = [];
  delegaciaFilter: 'todas' | 'ativas' | 'inativas' = 'todas';
  searchDelegacia: string = '';

  constructor(private api: ApiService, private router: Router, private route: ActivatedRoute) {}

  async ngOnInit() {
    // Restore the active tab from the URL fragment (e.g. /admin#delegacias),
    // so returning from a sub-screen lands on the tab the user was on.
    const frag = this.route.snapshot.fragment as AdminTab | null;
    if (frag && ADMIN_TABS.includes(frag)) {
      this.activeTab = frag;
    }
    await this.loadData();
  }

  setTab(tab: AdminTab) {
    this.activeTab = tab;
    this.router.navigate([], { fragment: tab, replaceUrl: true });
  }

  async loadData() {
    try {
      const [usersRes, cargosRes, permRes] = await Promise.all([
        this.api.get('/admin/users'),
        this.api.get('/admin/cargos'),
        this.api.get('/admin/permissions'),
      ]);
      this.users = usersRes.data.items ?? usersRes.data;
      this.cargos = cargosRes.data;
      this.permissions = permRes.data;
      this.permissions.forEach(p => { this.selectedPermissionIds[p.id_permissao] = false; });
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao carregar dados.');
    }
    this.loadDelegacias();
  }

  async loadDelegacias() {
    try {
      const res = await this.api.get('/admin/delegacias');
      this.delegacias = res.data ?? [];
    } catch {
      this.delegacias = [];
    }
  }

  get filteredDelegacias(): any[] {
    let list = this.delegacias;
    if (this.delegaciaFilter === 'ativas') list = list.filter(d => d.ativo !== false);
    if (this.delegaciaFilter === 'inativas') list = list.filter(d => d.ativo === false);
    if (this.searchDelegacia.trim()) {
      const q = this.searchDelegacia.toLowerCase();
      list = list.filter(d =>
        d.nome_unidade?.toLowerCase().includes(q) ||
        d.sigla?.toLowerCase().includes(q) ||
        d.municipio?.toLowerCase().includes(q)
      );
    }
    return list;
  }

  permDescricao(nome: string): string {
    return this.permissions.find(p => p.nome_permissao === nome)?.descricao_permissao ?? '';
  }

  get filteredUsers(): any[] {
    let list = this.users;
    if (this.filtroChip && this.filtroChip !== 'Todos') {
      list = list.filter(u => u.cargo?.nome_cargo === this.filtroChip ||
        (this.filtroChip === 'Inativo' && !u.ativo));
    }
    if (this.searchAdmin.trim()) {
      const q = this.searchAdmin.toLowerCase();
      list = list.filter(u =>
        u.nome?.toLowerCase().includes(q) ||
        u.matricula?.toLowerCase().includes(q) ||
        u.email?.toLowerCase().includes(q)
      );
    }
    return list;
  }

  getUserInitials(nome: string): string {
    return (nome ?? '').split(' ').slice(0, 2).map((s: string) => s[0]).join('').toUpperCase();
  }

  selectUser(user: any) {
    this.selectedUser = user;
    this.drawerCargo = user.cargo?.id_cargo ?? '';
  }

  closeDrawer() {
    this.selectedUser = null;
  }

  @HostListener('document:keydown.escape')
  onEscape() {
    this.closeDrawer();
  }

  async saveDrawer() {
    if (!this.selectedUser) return;
    this.clearAlerts();
    try {
      await this.api.put(`/admin/users/${this.selectedUser.id_usuario}/cargo`, { id_cargo: this.drawerCargo });
      this.showSuccess('Cargo atualizado.');
      await this.loadData();
      this.selectedUser = this.users.find(u => u.id_usuario === this.selectedUser?.id_usuario) ?? null;
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao salvar.');
    }
  }

  async toggleUserStatus(user: any) {
    if (!user) return;
    this.clearAlerts();
    const novo = !user.ativo;
    try {
      await this.api.put(`/admin/users/${user.id_usuario}/status`, { ativo: novo });
      this.showSuccess(novo ? 'Usuário ativado.' : 'Usuário desativado.');
      await this.loadData();
      this.selectedUser = this.users.find(u => u.id_usuario === user.id_usuario) ?? null;
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao alterar status.');
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

  async onCreateCargo() {
    this.clearAlerts();
    if (!this.newCargoName.trim()) { this.showError('Nome obrigatório.'); return; }
    const ids = Object.keys(this.selectedPermissionIds).filter(id => this.selectedPermissionIds[id]);
    if (!ids.length) { this.showError('Selecione ao menos uma permissão.'); return; }
    try {
      await this.api.post('/admin/cargos', { nome_cargo: this.newCargoName.trim(), permissoes_ids: ids });
      this.showSuccess(`Cargo "${this.newCargoName}" criado.`);
      this.newCargoName = '';
      this.permissions.forEach(p => { this.selectedPermissionIds[p.id_permissao] = false; });
      await this.loadData();
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao criar cargo.');
    }
  }

  /** O cargo Admin nunca pode ser editado (imutável). */
  isAdminCargo(cargo: any): boolean {
    return cargo?.nome_cargo === ADMIN_CARGO;
  }

  startEditCargo(cargo: any) {
    if (this.isAdminCargo(cargo)) return;
    this.editingCargoId = cargo.id_cargo;
    this.editingCargoNameValue = cargo.nome_cargo;
    this.editingPermissionIds = {};
    const current = new Set((cargo.permissoes ?? []).map((p: any) => p.id_permissao));
    this.permissions.forEach(p => { this.editingPermissionIds[p.id_permissao] = current.has(p.id_permissao); });
  }

  cancelEditCargo() { this.editingCargoId = null; }

  async saveCargo(cargoId: string) {
    this.clearAlerts();
    const ids = Object.keys(this.editingPermissionIds).filter(id => this.editingPermissionIds[id]);
    if (!this.editingCargoNameValue.trim()) { this.showError('Nome do cargo é obrigatório.'); return; }
    if (!ids.length) { this.showError('Selecione ao menos uma permissão.'); return; }
    try {
      await this.api.put(`/admin/cargos/${cargoId}`, { nome_cargo: this.editingCargoNameValue.trim() });
      await this.api.put(`/admin/cargos/${cargoId}/permissions`, { permissoes_ids: ids });
      this.showSuccess('Cargo atualizado.');
      this.cancelEditCargo();
      await this.loadData();
    } catch (err: any) {
      this.showError(err.response?.data?.detail || 'Erro ao atualizar cargo.');
    }
  }

  toggleMatrixPerm(cargoId: string, permName: string) {
    const cargo = this.cargos.find(c => c.id_cargo === cargoId);
    if (!cargo) return;
    if (this.isAdminCargo(cargo)) return;  // Admin é imutável
    const has = this.cargoHasPerm(cargoId, permName);
    const perm = this.permissions.find(p => p.nome_permissao === permName);
    if (!perm) return;
    const existing: string[] = (cargo.permissoes ?? []).map((p: any) => p.id_permissao);
    const updated = has ? existing.filter(id => id !== perm.id_permissao) : [...existing, perm.id_permissao];
    this.api.put(`/admin/cargos/${cargoId}/permissions`, { permissoes_ids: updated })
      .then(() => this.loadData())
      .catch((err: any) => this.showError(err.response?.data?.detail || 'Erro.'));
  }

  cargoHasPerm(cargoId: string, permName: string): boolean {
    const cargo = this.cargos.find(c => c.id_cargo === cargoId);
    return (cargo?.permissoes ?? []).some((p: any) => p.nome_permissao === permName);
  }

  allPermNames(): string[] {
    return this.permissions.map(p => p.nome_permissao);
  }

  permCategoryKeys(): string[] { return Object.keys(PERM_CATEGORIES); }

  permsForCategory(cat: string): string[] { return PERM_CATEGORIES[cat] ?? []; }

  showSuccess(msg: string) {
    this.successMessage = msg;
    setTimeout(() => { this.successMessage = ''; }, 4000);
  }

  showError(msg: string) {
    this.errorMessage = msg;
    setTimeout(() => { this.errorMessage = ''; }, 5000);
  }

  clearAlerts() { this.successMessage = ''; this.errorMessage = ''; }
}
