import { Component, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../services/api.service';
import { ComponentCanDeactivate } from '../../../services/pending-changes.guard';

interface UserFormData {
  matricula: string;
  nome: string;
  id_delegacia: string;
  id_cargo: string;
  ativo: boolean;
}

type CheckState = 'idle' | 'checking' | 'available' | 'taken';

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './user-form.component.html',
  styleUrls: ['./user-form.component.css']
})
export class UserFormComponent implements OnInit, ComponentCanDeactivate {
  isEditMode = false;
  userId: string | null = null;
  isSubmitting = false;

  formData: UserFormData = {
    matricula: '',
    nome: '',
    id_delegacia: '',
    id_cargo: '',
    ativo: true,
  };

  delegacias: any[] = [];
  cargos: any[] = [];
  selectedCargoPermissions: any[] = [];

  matriculaCheckState: CheckState = 'idle';
  matriculaCheckMessage = '';

  userHistory: any[] = [];

  tempPasswordModal: { senha: string; nome: string; matricula: string } | null = null;
  errorMessage = '';
  successMessage = '';

  private matriculaDebounce: any;
  private savedSnapshot = '';
  private saved = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {}

  async ngOnInit() {
    this.userId = this.route.snapshot.paramMap.get('id');
    this.isEditMode = !!this.userId;

    const [delegRes, cargosRes] = await Promise.allSettled([
      this.api.get('/admin/delegacias'),
      this.api.get('/admin/cargos'),
    ]);
    if (delegRes.status === 'fulfilled') this.delegacias = delegRes.value.data ?? [];
    if (cargosRes.status === 'fulfilled') this.cargos = cargosRes.value.data ?? [];

    if (this.isEditMode && this.userId) {
      await this.loadUser();
    }
    this.savedSnapshot = JSON.stringify(this.formData);
  }

  async loadUser() {
    try {
      const res = await this.api.get(`/admin/users/${this.userId}`);
      const u = res.data;
      this.formData = {
        matricula: u.matricula ?? '',
        nome: u.nome ?? '',
        id_delegacia: u.id_delegacia ?? u.delegacia?.id_delegacia ?? '',
        id_cargo: u.id_cargo ?? u.cargo?.id_cargo ?? '',
        ativo: u.ativo !== false,
      };
      if (this.formData.id_cargo) this.updateCargoPermissions(this.formData.id_cargo);
    } catch {
      this.errorMessage = 'Erro ao carregar dados do usuário.';
    }

    try {
      const histRes = await this.api.get(`/admin/users/${this.userId}/history`);
      this.userHistory = histRes.data ?? [];
    } catch {
      this.userHistory = [];
    }
  }

  // ── Unsaved-changes guard ─────────────────────────────────────────────────
  canDeactivate(): boolean {
    return this.saved || JSON.stringify(this.formData) === this.savedSnapshot;
  }

  @HostListener('window:beforeunload', ['$event'])
  onBeforeUnload(event: BeforeUnloadEvent) {
    if (!this.canDeactivate()) {
      event.preventDefault();
      event.returnValue = '';
    }
  }

  onMatriculaChange() {
    clearTimeout(this.matriculaDebounce);
    if (!this.formData.matricula.trim()) { this.matriculaCheckState = 'idle'; this.matriculaCheckMessage = ''; return; }
    this.matriculaCheckState = 'checking';
    this.matriculaDebounce = setTimeout(() => this.checkMatricula(), 500);
  }

  private async checkMatricula() {
    try {
      const res = await this.api.get(`/admin/users/check-matricula?matricula=${encodeURIComponent(this.formData.matricula.trim())}`);
      if (res.data.available) {
        this.matriculaCheckState = 'available';
        this.matriculaCheckMessage = 'Matrícula disponível';
      } else {
        this.matriculaCheckState = 'taken';
        this.matriculaCheckMessage = 'Matrícula já cadastrada';
      }
    } catch {
      this.matriculaCheckState = 'idle';
    }
  }

  onCargoChange() {
    this.updateCargoPermissions(this.formData.id_cargo);
  }

  private updateCargoPermissions(cargoId: string) {
    const cargo = this.cargos.find(c => c.id_cargo === cargoId);
    this.selectedCargoPermissions = cargo?.permissoes ?? [];
  }

  get validationChecks(): { label: string; ok: boolean | null }[] {
    return [
      { label: 'Matrícula preenchida', ok: this.formData.matricula.trim().length >= 2 || null },
      { label: 'Matrícula única', ok: this.isEditMode ? true : (this.matriculaCheckState === 'available' ? true : this.matriculaCheckState === 'taken' ? false : null) },
      { label: 'Nome (mín. 3)', ok: this.formData.nome.trim().length >= 3 || null },
      { label: 'Delegacia selecionada', ok: !!this.formData.id_delegacia || null },
      { label: 'Cargo selecionado', ok: !!this.formData.id_cargo || null },
    ];
  }

  async salvar() {
    this.errorMessage = '';
    if (!this.formData.matricula.trim()) { this.errorMessage = 'Matrícula obrigatória.'; return; }
    if (this.formData.nome.trim().length < 3) { this.errorMessage = 'Nome obrigatório (mínimo 3 caracteres).'; return; }
    if (!this.formData.id_delegacia) { this.errorMessage = 'Delegacia obrigatória.'; return; }
    if (!this.formData.id_cargo) { this.errorMessage = 'Cargo obrigatório.'; return; }

    this.isSubmitting = true;
    try {
      if (this.isEditMode) {
        await this.api.put(`/admin/users/${this.userId}`, {
          nome: this.formData.nome.trim(),
          id_delegacia: this.formData.id_delegacia,
          id_cargo: this.formData.id_cargo,
          ativo: this.formData.ativo,
        });
        this.saved = true;
        this.successMessage = 'Servidor atualizado.';
        setTimeout(() => this.router.navigate(['/admin'], { fragment: 'users' }), 1100);
      } else {
        const res = await this.api.post('/admin/users', {
          matricula: this.formData.matricula.trim(),
          nome: this.formData.nome.trim(),
          id_delegacia: this.formData.id_delegacia,
          id_cargo: this.formData.id_cargo,
        });
        this.saved = true;
        this.tempPasswordModal = {
          senha: res.data.temp_password,
          nome: this.formData.nome,
          matricula: this.formData.matricula,
        };
      }
    } catch (err: any) {
      this.errorMessage = err.response?.data?.detail || 'Erro ao salvar.';
    } finally {
      this.isSubmitting = false;
    }
  }

  async toggleStatus() {
    if (!this.userId) return;
    const novo = !this.formData.ativo;
    try {
      await this.api.put(`/admin/users/${this.userId}/status`, { ativo: novo });
      this.formData.ativo = novo;
      this.savedSnapshot = JSON.stringify(this.formData);
      this.successMessage = novo ? 'Servidor ativado.' : 'Servidor desativado.';
    } catch (err: any) {
      this.errorMessage = err.response?.data?.detail || 'Erro ao alterar status.';
    }
  }

  async onResetPassword() {
    if (!this.userId) return;
    try {
      const res = await this.api.post(`/admin/users/${this.userId}/reset-password`, {});
      this.tempPasswordModal = {
        senha: res.data.temp_password,
        nome: this.formData.nome,
        matricula: this.formData.matricula,
      };
    } catch (err: any) {
      this.errorMessage = err.response?.data?.detail || 'Erro ao gerar senha.';
    }
  }

  closeTempModal() {
    this.tempPasswordModal = null;
    this.router.navigate(['/admin'], { fragment: 'users' });
  }

  cancelar() {
    this.router.navigate(['/admin'], { fragment: 'users' });
  }

  formatDateTime(dateStr: string): string {
    if (!dateStr) return '—';
    try { return new Date(dateStr).toLocaleString('pt-BR'); } catch { return dateStr; }
  }
}
