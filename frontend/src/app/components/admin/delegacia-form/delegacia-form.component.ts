import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../services/api.service';

interface DelegaciaFormData {
  nome_unidade: string;
  cod_sinesp: string;
  tipo: string;
  sigla: string;
  municipio: string;
  uf: string;
  cep: string;
  endereco: string;
  telefone: string;
  email: string;
  ativo: boolean;
}

type SinespState = 'idle' | 'checking' | 'available' | 'taken';

@Component({
  selector: 'app-delegacia-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './delegacia-form.component.html',
  styleUrls: ['./delegacia-form.component.css']
})
export class DelegaciaFormComponent implements OnInit {
  isEditMode = false;
  delegaciaId: string | null = null;
  isSubmitting = false;
  isDesativando = false;

  formData: DelegaciaFormData = {
    nome_unidade: '',
    cod_sinesp: '',
    tipo: '',
    sigla: '',
    municipio: '',
    uf: 'PI',
    cep: '',
    endereco: '',
    telefone: '',
    email: '',
    ativo: true,
  };

  sinespState: SinespState = 'idle';
  sinespMessage = '';

  servidoresCount = 0;
  errorMessage = '';
  successMessage = '';

  tiposDelegacia = [
    'Delegacia Territorial',
    'Delegacia Especializada',
    'Delegacia Central',
    'Posto Policial',
    'Delegacia Seccional',
  ];

  ufs = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO'];

  private sinespDebounce: any;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {}

  async ngOnInit() {
    this.delegaciaId = this.route.snapshot.paramMap.get('id');
    this.isEditMode = !!this.delegaciaId;

    if (this.isEditMode) {
      await this.loadDelegacia();
    }
  }

  async loadDelegacia() {
    try {
      const res = await this.api.get(`/admin/delegacias/${this.delegaciaId}`);
      const d = res.data;
      this.formData = {
        nome_unidade: d.nome_unidade ?? '',
        cod_sinesp: d.cod_sinesp ?? '',
        tipo: d.tipo ?? '',
        sigla: d.sigla ?? '',
        municipio: d.municipio ?? '',
        uf: d.uf ?? 'PI',
        cep: d.cep ?? '',
        endereco: d.endereco ?? '',
        telefone: d.telefone ?? '',
        email: d.email ?? '',
        ativo: d.ativo !== false,
      };
      this.servidoresCount = d.servidores_count ?? 0;
    } catch {
      this.errorMessage = 'Erro ao carregar dados da delegacia.';
    }
  }

  onSinespInput() {
    clearTimeout(this.sinespDebounce);
    const val = this.formData.cod_sinesp.trim();
    if (!val) { this.sinespState = 'idle'; this.sinespMessage = ''; return; }
    this.sinespState = 'checking';
    this.sinespMessage = '';
    this.sinespDebounce = setTimeout(() => this.checkSinesp(val), 600);
  }

  private async checkSinesp(val: string) {
    try {
      const res = await this.api.get(`/admin/delegacias/check-sinesp?sinesp=${encodeURIComponent(val)}`);
      if (res.data.available) {
        this.sinespState = 'available';
        this.sinespMessage = 'Código disponível';
      } else {
        this.sinespState = 'taken';
        this.sinespMessage = `Já cadastrado: ${res.data.nome ?? ''}`;
      }
    } catch {
      this.sinespState = 'idle';
    }
  }

  formatCep(event: Event) {
    const input = event.target as HTMLInputElement;
    const digits = input.value.replace(/\D/g, '').slice(0, 8);
    this.formData.cep = digits.length > 5 ? `${digits.slice(0,5)}-${digits.slice(5)}` : digits;
  }

  get validationChecks(): { label: string; ok: boolean | null }[] {
    return [
      { label: 'SINESP único', ok: this.sinespState === 'available' ? true : this.sinespState === 'taken' ? false : null },
      { label: 'Nome preenchido', ok: this.formData.nome_unidade.trim().length >= 3 || null },
      { label: 'Município preenchido', ok: !!this.formData.municipio.trim() || null },
      { label: 'Tipo selecionado', ok: !!this.formData.tipo || null },
    ];
  }

  async salvar() {
    this.errorMessage = '';
    if (!this.formData.nome_unidade.trim()) { this.errorMessage = 'Nome da unidade obrigatório.'; return; }
    if (!this.formData.cod_sinesp.trim()) { this.errorMessage = 'Código SINESP obrigatório.'; return; }

    this.isSubmitting = true;
    try {
      const payload: any = { ...this.formData };

      if (this.isEditMode) {
        await this.api.put(`/admin/delegacias/${this.delegaciaId}`, payload);
        this.successMessage = 'Delegacia atualizada.';
        setTimeout(() => this.router.navigate(['/admin'], { fragment: 'delegacias' }), 1200);
      } else {
        await this.api.post('/admin/delegacias', payload);
        this.successMessage = 'Delegacia cadastrada.';
        setTimeout(() => this.router.navigate(['/admin'], { fragment: 'delegacias' }), 1200);
      }
    } catch (err: any) {
      this.errorMessage = err.response?.data?.detail || 'Erro ao salvar.';
    } finally {
      this.isSubmitting = false;
    }
  }

  async desativar() {
    if (!this.delegaciaId) return;
    this.isDesativando = true;
    try {
      await this.api.put(`/admin/delegacias/${this.delegaciaId}/desativar`, {});
      this.formData.ativo = false;
      this.successMessage = 'Delegacia desativada.';
    } catch (err: any) {
      this.errorMessage = err.response?.data?.detail || 'Erro ao desativar.';
    } finally {
      this.isDesativando = false;
    }
  }

  cancelar() {
    this.router.navigate(['/admin']);
  }
}
