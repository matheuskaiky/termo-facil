import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../services/api.service';

interface UserFormData {
  cpf: string;
  matricula: string;
  nome: string;
  email: string;
  id_delegacia: string;
  id_cargo: string;
}

type CheckState = 'idle' | 'checking' | 'available' | 'taken';

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './user-form.component.html',
  styleUrls: ['./user-form.component.css']
})
export class UserFormComponent implements OnInit {
  isEditMode = false;
  userId: string | null = null;
  isSubmitting = false;

  formData: UserFormData = {
    cpf: '',
    matricula: '',
    nome: '',
    email: '',
    id_delegacia: '',
    id_cargo: '',
  };

  delegacias: any[] = [];
  cargos: any[] = [];
  selectedCargoPermissions: any[] = [];

  cpfCheckState: CheckState = 'idle';
  cpfCheckMessage = '';
  matriculaCheckState: CheckState = 'idle';
  matriculaCheckMessage = '';

  userActivity: any = null;
  userHistory: any[] = [];

  tempPasswordModal: { senha: string; nome: string; matricula: string } | null = null;
  errorMessage = '';
  successMessage = '';

  private cpfDebounce: any;
  private matriculaDebounce: any;

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
  }

  async loadUser() {
    try {
      const res = await this.api.get(`/admin/users/${this.userId}`);
      const u = res.data;
      this.formData = {
        cpf: u.cpf ?? '',
        matricula: u.matricula ?? '',
        nome: u.nome ?? '',
        email: u.email ?? '',
        id_delegacia: u.id_delegacia ?? u.delegacia?.id_delegacia ?? '',
        id_cargo: u.id_cargo ?? u.cargo?.id_cargo ?? '',
      };
      if (this.formData.id_cargo) this.updateCargoPermissions(this.formData.id_cargo);
      this.userActivity = u.atividade ?? null;
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

  onCpfChange() {
    if (this.isEditMode) return;
    clearTimeout(this.cpfDebounce);
    const raw = this.formData.cpf.replace(/\D/g, '');
    this.formData.cpf = this.maskCpf(raw);
    if (raw.length < 11) { this.cpfCheckState = 'idle'; this.cpfCheckMessage = ''; return; }
    this.cpfCheckState = 'checking';
    this.cpfCheckMessage = '';
    this.cpfDebounce = setTimeout(() => this.checkCpf(raw), 600);
  }

  private async checkCpf(raw: string) {
    try {
      const res = await this.api.get(`/admin/users/check-cpf?cpf=${encodeURIComponent(raw)}`);
      if (res.data.available) {
        this.cpfCheckState = 'available';
        this.cpfCheckMessage = 'Disponível';
      } else {
        this.cpfCheckState = 'taken';
        this.cpfCheckMessage = `Em uso: ${res.data.nome ?? ''}`;
      }
    } catch {
      this.cpfCheckState = 'idle';
    }
  }

  onMatriculaChange() {
    clearTimeout(this.matriculaDebounce);
    if (!this.formData.matricula.trim()) { this.matriculaCheckState = 'idle'; return; }
    this.matriculaCheckState = 'checking';
    this.matriculaDebounce = setTimeout(() => this.checkMatricula(), 600);
  }

  private async checkMatricula() {
    try {
      const res = await this.api.get(`/admin/users/check-matricula?matricula=${encodeURIComponent(this.formData.matricula)}`);
      if (res.data.available) {
        this.matriculaCheckState = 'available';
        this.matriculaCheckMessage = 'Disponível';
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

  private maskCpf(digits: string): string {
    const d = digits.slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return `${d.slice(0,3)}.${d.slice(3)}`;
    if (d.length <= 9) return `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6)}`;
    return `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6,9)}-${d.slice(9)}`;
  }

  get validationChecks(): { label: string; ok: boolean | null }[] {
    return [
      { label: 'CPF único', ok: this.cpfCheckState === 'available' ? true : this.cpfCheckState === 'taken' ? false : null },
      { label: 'Matrícula única', ok: this.matriculaCheckState === 'available' ? true : this.matriculaCheckState === 'taken' ? false : null },
      { label: 'Nome preenchido', ok: this.formData.nome.trim().length >= 3 || null },
      { label: 'Delegacia selecionada', ok: !!this.formData.id_delegacia || null },
      { label: 'Cargo selecionado', ok: !!this.formData.id_cargo || null },
    ];
  }

  async salvar() {
    this.errorMessage = '';
    if (!this.formData.matricula.trim()) { this.errorMessage = 'Matrícula obrigatória.'; return; }
    if (!this.formData.nome.trim()) { this.errorMessage = 'Nome obrigatório.'; return; }
    if (!this.formData.id_delegacia) { this.errorMessage = 'Delegacia obrigatória.'; return; }
    if (!this.formData.id_cargo) { this.errorMessage = 'Cargo obrigatório.'; return; }

    this.isSubmitting = true;
    try {
      const payload: any = {
        matricula: this.formData.matricula.trim(),
        nome: this.formData.nome.trim(),
        id_delegacia: this.formData.id_delegacia,
        id_cargo: this.formData.id_cargo,
      };
      if (this.formData.cpf) payload.cpf = this.formData.cpf.replace(/\D/g, '');
      if (this.formData.email) payload.email = this.formData.email.trim();

      if (this.isEditMode) {
        await this.api.put(`/admin/users/${this.userId}`, payload);
        this.successMessage = 'Servidor atualizado.';
        setTimeout(() => this.router.navigate(['/admin']), 1200);
      } else {
        const res = await this.api.post('/admin/users', payload);
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
    this.router.navigate(['/admin']);
  }

  cancelar() {
    this.router.navigate(['/admin']);
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    try { return new Date(dateStr).toLocaleDateString('pt-BR'); } catch { return dateStr; }
  }
}
