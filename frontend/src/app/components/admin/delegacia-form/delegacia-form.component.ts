import { Component, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../services/api.service';
import { ComponentCanDeactivate } from '../../../services/pending-changes.guard';

interface DelegaciaFormData {
  nome_unidade: string;
  tipo: string;
  sigla: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  municipio: string;
  uf: string;
  cod_ibge: string;
  telefone: string;
  email: string;
  ativo: boolean;
}

type CepState = 'idle' | 'loading' | 'ok' | 'partial' | 'notfound' | 'error';
type AutoField = 'logradouro' | 'bairro' | 'municipio' | 'uf';

@Component({
  selector: 'app-delegacia-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './delegacia-form.component.html',
  styleUrls: ['./delegacia-form.component.css']
})
export class DelegaciaFormComponent implements OnInit, ComponentCanDeactivate {
  isEditMode = false;
  private savedSnapshot = '';
  private saved = false;
  delegaciaId: string | null = null;
  isSubmitting = false;
  isDesativando = false;
  submitted = false;

  formData: DelegaciaFormData = {
    nome_unidade: '',
    tipo: '',
    sigla: '',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    municipio: '',
    uf: 'PI',
    cod_ibge: '',
    telefone: '',
    email: '',
    ativo: true,
  };

  cepState: CepState = 'idle';
  cepMessage = '';
  // Fields auto-filled by ViaCEP are locked; cleared on manual override.
  locked: Record<AutoField, boolean> = { logradouro: false, bairro: false, municipio: false, uf: false };
  manualMode = false;

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

  private cepDebounce: any;

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
    this.savedSnapshot = JSON.stringify(this.formData);
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

  async loadDelegacia() {
    try {
      const res = await this.api.get(`/admin/delegacias/${this.delegaciaId}`);
      const d = res.data;
      this.formData = {
        nome_unidade: (d.nome_unidade ?? '').toUpperCase(),
        tipo: d.tipo ?? '',
        sigla: d.sigla ?? '',
        cep: d.cep ?? '',
        logradouro: d.logradouro ?? '',
        numero: d.numero ?? '',
        complemento: d.complemento ?? '',
        bairro: d.bairro ?? '',
        municipio: d.municipio ?? '',
        uf: d.uf ?? 'PI',
        cod_ibge: d.cod_ibge ?? '',
        telefone: d.telefone ?? '',
        email: d.email ?? '',
        ativo: d.ativo !== false,
      };
      this.servidoresCount = d.servidores_count ?? 0;
      // Existing record: fields already filled → allow free editing.
      this.manualMode = true;
      if (this.cepDigits.length === 8) this.cepState = 'ok';
    } catch {
      this.errorMessage = 'Erro ao carregar dados da delegacia.';
    }
  }

  // ── Nome e sigla: sempre MAIÚSCULOS ───────────────────────────────────────
  onNomeInput() {
    this.formData.nome_unidade = (this.formData.nome_unidade || '').toUpperCase();
  }

  onSiglaInput() {
    this.formData.sigla = (this.formData.sigla || '').toUpperCase();
  }

  // ── CEP → ViaCEP ──────────────────────────────────────────────────────────
  get cepDigits(): string {
    return (this.formData.cep || '').replace(/\D/g, '');
  }

  onCepInput(event: Event) {
    const input = event.target as HTMLInputElement;
    const digits = input.value.replace(/\D/g, '').slice(0, 8);
    this.formData.cep = digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : digits;

    clearTimeout(this.cepDebounce);
    if (digits.length === 8) {
      this.cepDebounce = setTimeout(() => this.lookupCep(digits), 450);
    } else {
      this.cepState = 'idle';
      this.cepMessage = '';
    }
  }

  private async lookupCep(cep8: string) {
    this.cepState = 'loading';
    this.cepMessage = '';
    try {
      const resp = await fetch(`https://viacep.com.br/ws/${cep8}/json/`);
      const data = await resp.json();

      if (data?.erro) {
        this.cepState = 'notfound';
        this.cepMessage = 'CEP não encontrado. Confira o número ou preencha manualmente.';
        return;
      }

      // ViaCEP devolve string vazia (não null) quando o campo não se aplica.
      const logradouro = (data.logradouro ?? '').trim();
      const bairro = (data.bairro ?? '').trim();

      this.formData.logradouro = logradouro;
      this.formData.bairro = bairro;
      this.formData.municipio = (data.localidade ?? '').trim();
      this.formData.uf = (data.uf ?? this.formData.uf).trim();
      this.formData.cod_ibge = (data.ibge ?? '').trim();

      // Cidade/UF sempre travam. Logradouro/bairro travam só se vieram preenchidos
      // (CEP único de cidade inteira retorna vazio → deixa livre p/ digitar).
      this.locked = {
        municipio: true,
        uf: true,
        logradouro: !!logradouro,
        bairro: !!bairro,
      };
      this.manualMode = false;

      if (logradouro) {
        this.cepState = 'ok';
        this.cepMessage = `${this.formData.municipio} – ${this.formData.uf} · IBGE ${this.formData.cod_ibge || '—'}`;
      } else {
        this.cepState = 'partial';
        this.cepMessage = `CEP de abrangência municipal (${this.formData.municipio}/${this.formData.uf}). Informe o logradouro e o bairro.`;
      }
    } catch {
      this.cepState = 'error';
      this.cepMessage = 'Não foi possível consultar o CEP agora. Você pode preencher o endereço manualmente.';
      this.enableManual();
    }
  }

  enableManual() {
    this.manualMode = true;
    this.locked = { logradouro: false, bairro: false, municipio: false, uf: false };
  }

  isLocked(field: AutoField): boolean {
    return !this.manualMode && this.locked[field];
  }

  // ── Validação ──────────────────────────────────────────────────────────────
  get validationChecks(): { label: string; ok: boolean | null }[] {
    return [
      { label: 'Nome (mín. 3 caracteres)', ok: this.formData.nome_unidade.trim().length >= 3 || null },
      { label: 'CEP válido (8 dígitos)', ok: this.cepDigits.length === 8 || null },
      { label: 'Logradouro', ok: !!this.formData.logradouro.trim() || null },
      { label: 'Número', ok: !!this.formData.numero.trim() || null },
      { label: 'Município e UF', ok: (!!this.formData.municipio.trim() && !!this.formData.uf) || null },
    ];
  }

  private validate(): string | null {
    if (this.formData.nome_unidade.trim().length < 3) return 'Nome da unidade obrigatório (mínimo 3 caracteres).';
    if (this.cepDigits.length !== 8) return 'CEP obrigatório (8 dígitos).';
    if (!this.formData.logradouro.trim()) return 'Logradouro obrigatório.';
    if (!this.formData.numero.trim()) return 'Número obrigatório.';
    if (!this.formData.municipio.trim()) return 'Município obrigatório.';
    if (!this.formData.uf) return 'UF obrigatória.';
    return null;
  }

  async salvar() {
    this.submitted = true;
    this.errorMessage = '';
    this.formData.nome_unidade = this.formData.nome_unidade.toUpperCase();

    const err = this.validate();
    if (err) { this.errorMessage = err; return; }

    this.isSubmitting = true;
    try {
      const f = this.formData;
      const payload: any = {
        nome_unidade: f.nome_unidade,
        tipo: f.tipo || null,
        sigla: f.sigla ? f.sigla.toUpperCase() : null,
        cep: f.cep,
        logradouro: f.logradouro.trim(),
        numero: f.numero.trim(),
        complemento: f.complemento.trim() || null,
        bairro: f.bairro.trim() || null,
        municipio: f.municipio.trim(),
        uf: f.uf,
        cod_ibge: f.cod_ibge || null,
        telefone: f.telefone.trim() || null,
        email: f.email.trim() || null,
        ativo: f.ativo,
      };

      if (this.isEditMode) {
        await this.api.put(`/admin/delegacias/${this.delegaciaId}`, payload);
        this.successMessage = 'Delegacia atualizada.';
      } else {
        await this.api.post('/admin/delegacias', payload);
        this.successMessage = 'Delegacia cadastrada.';
      }
      this.saved = true;
      setTimeout(() => this.router.navigate(['/admin'], { fragment: 'delegacias' }), 1100);
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
    this.router.navigate(['/admin'], { fragment: 'delegacias' });
  }
}
