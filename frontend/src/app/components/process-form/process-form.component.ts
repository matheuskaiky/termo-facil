import { Component, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ComponentCanDeactivate } from '../../services/pending-changes.guard';

interface ProcessFormData {
  num_procedimento: string;
  tipo_procedimento: string;
  natureza_feito: string;
  data_registro: string;
  nome_depoente: string;
  tipo_depoente: string;
  cpf: string;
  // Endereço opcional (ViaCEP), nos moldes da delegacia.
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  municipio: string;
  uf: string;
  cod_ibge: string;
  observacoes: string;
}

type CpfState = 'empty' | 'invalid' | 'checking' | 'found' | 'new';
type CepState = 'idle' | 'loading' | 'ok' | 'partial' | 'notfound' | 'error';
type AutoField = 'logradouro' | 'bairro' | 'municipio' | 'uf';

@Component({
  selector: 'app-process-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './process-form.component.html',
  styleUrls: ['./process-form.component.css']
})
export class ProcessFormComponent implements OnInit, ComponentCanDeactivate {
  isEditMode = false;
  idProcesso: string | null = null;
  isSubmitting = false;
  errorMessage = '';

  // Wizard: avanço controlado (só vai à frente validando; volta só ao que já passou).
  currentStep = 0;
  furthest = 0;

  // CPF
  cpfState: CpfState = 'empty';
  cpfMessage = '';
  private cpfDebounceTimer: any;

  // CEP / endereço
  cepState: CepState = 'idle';
  cepMessage = '';
  locked: Record<AutoField, boolean> = { logradouro: false, bairro: false, municipio: false, uf: false };
  manualAddr = false;
  private cepDebounceTimer: any;

  private savedSnapshot = '';
  private saved = false;

  formData: ProcessFormData = {
    num_procedimento: '',
    tipo_procedimento: 'Inquérito Policial',
    natureza_feito: '',
    data_registro: new Date().toISOString().slice(0, 10),
    nome_depoente: '',
    tipo_depoente: 'Testemunha',
    cpf: '',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    municipio: '',
    uf: 'PI',
    cod_ibge: '',
    observacoes: '',
  };

  sections = [
    { key: 'inquerito', label: 'Identificação do procedimento' },
    { key: 'depoente',  label: 'Dados do depoente' },
    { key: 'obs',       label: 'Observações' },
  ];

  tiposDepoente = ['Testemunha', 'Vítima', 'Indiciado', 'Perito', 'Informante'];
  tiposProcedimento = ['Inquérito Policial', 'Termo Circunstanciado', 'Auto de Prisão em Flagrante', 'Boletim de Ocorrência'];
  ufs = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO'];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService,
    private auth: AuthService
  ) {}

  ngOnInit() {
    this.route.paramMap.subscribe(async params => {
      this.idProcesso = params.get('id');
      this.isEditMode = !!this.idProcesso;
      if (this.isEditMode) {
        await this.loadProcesso();
      }
      this.savedSnapshot = JSON.stringify(this.formData);
    });
  }

  async loadProcesso() {
    try {
      const res = await this.api.get(`/processos/${this.idProcesso}`);
      const d = res.data;
      this.formData = { ...this.formData, ...d };
      this.cpfState = this.cpfValido(this.formData.cpf) ? 'new' : 'empty';
    } catch {
      this.errorMessage = 'Erro ao carregar processo.';
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

  // ── CPF ───────────────────────────────────────────────────────────────────
  get cpfDigits(): string {
    return (this.formData.cpf || '').replace(/\D/g, '');
  }

  cpfValido(cpf: string): boolean {
    const c = (cpf || '').replace(/\D/g, '');
    if (c.length !== 11 || /^(\d)\1{10}$/.test(c)) return false;
    const dig = (base: string, start: number) => {
      let soma = 0;
      for (let i = 0; i < base.length; i++) soma += parseInt(base[i], 10) * (start - i);
      const resto = (soma * 10) % 11;
      return resto === 10 ? 0 : resto;
    };
    return c[9] === String(dig(c.slice(0, 9), 10)) && c[10] === String(dig(c.slice(0, 10), 11));
  }

  onCpfInput(event: any) {
    let v = event.target.value.replace(/\D/g, '').slice(0, 11);
    if (v.length > 9) v = v.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    else if (v.length > 6) v = v.replace(/(\d{3})(\d{3})(\d{0,3})/, '$1.$2.$3');
    else if (v.length > 3) v = v.replace(/(\d{3})(\d{0,3})/, '$1.$2');
    this.formData.cpf = v;

    clearTimeout(this.cpfDebounceTimer);
    const digits = this.cpfDigits;
    if (digits.length < 11) { this.cpfState = 'empty'; this.cpfMessage = ''; return; }
    if (!this.cpfValido(digits)) { this.cpfState = 'invalid'; this.cpfMessage = 'CPF inválido — confira os dígitos.'; return; }
    this.cpfState = 'checking';
    this.cpfMessage = '';
    this.cpfDebounceTimer = setTimeout(() => this.checkCpf(digits), 500);
  }

  private async checkCpf(digits: string) {
    try {
      const res = await this.api.get(`/processos/check-cpf?cpf=${encodeURIComponent(digits)}`);
      if (res.data.existe) {
        if (res.data.nome_depoente && !this.formData.nome_depoente) {
          this.formData.nome_depoente = res.data.nome_depoente;
        }
        this.cpfState = 'found';
        this.cpfMessage = `Depoente já cadastrado: ${res.data.nome_depoente ?? ''}`;
      } else {
        this.cpfState = 'new';
        this.cpfMessage = 'CPF válido — novo depoente.';
      }
    } catch {
      this.cpfState = this.cpfValido(digits) ? 'new' : 'invalid';
    }
  }

  // ── CEP → ViaCEP (opcional) ──────────────────────────────────────────────
  get cepDigits(): string { return (this.formData.cep || '').replace(/\D/g, ''); }

  onCepInput(event: Event) {
    const input = event.target as HTMLInputElement;
    const digits = input.value.replace(/\D/g, '').slice(0, 8);
    this.formData.cep = digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : digits;
    clearTimeout(this.cepDebounceTimer);
    if (digits.length === 8) this.cepDebounceTimer = setTimeout(() => this.lookupCep(digits), 450);
    else { this.cepState = 'idle'; this.cepMessage = ''; }
  }

  private async lookupCep(cep8: string) {
    this.cepState = 'loading'; this.cepMessage = '';
    try {
      const resp = await fetch(`https://viacep.com.br/ws/${cep8}/json/`);
      const data = await resp.json();
      if (data?.erro) { this.cepState = 'notfound'; this.cepMessage = 'CEP não encontrado.'; return; }
      const logradouro = (data.logradouro ?? '').trim();
      const bairro = (data.bairro ?? '').trim();
      this.formData.logradouro = logradouro;
      this.formData.bairro = bairro;
      this.formData.municipio = (data.localidade ?? '').trim();
      this.formData.uf = (data.uf ?? this.formData.uf).trim();
      this.formData.cod_ibge = (data.ibge ?? '').trim();
      this.locked = { municipio: true, uf: true, logradouro: !!logradouro, bairro: !!bairro };
      this.manualAddr = false;
      this.cepState = logradouro ? 'ok' : 'partial';
      this.cepMessage = logradouro
        ? `${this.formData.municipio} – ${this.formData.uf}`
        : `CEP municipal (${this.formData.municipio}/${this.formData.uf}). Informe rua e bairro.`;
    } catch {
      this.cepState = 'error';
      this.cepMessage = 'Não foi possível consultar o CEP. Preencha manualmente.';
      this.enableManualAddr();
    }
  }

  enableManualAddr() {
    this.manualAddr = true;
    this.locked = { logradouro: false, bairro: false, municipio: false, uf: false };
  }

  isAddrLocked(field: AutoField): boolean {
    return !this.manualAddr && this.locked[field];
  }

  // ── Wizard ────────────────────────────────────────────────────────────────
  get currentKey(): string { return this.sections[this.currentStep].key; }
  get isLastStep(): boolean { return this.currentStep === this.sections.length - 1; }

  isStepComplete(key: string): boolean {
    if (key === 'inquerito') return !!this.formData.num_procedimento.trim() && !!this.formData.data_registro;
    if (key === 'depoente') return !!this.formData.nome_depoente.trim() && this.cpfValido(this.formData.cpf);
    return true; // 'obs' não tem campos obrigatórios
  }

  canReach(index: number): boolean {
    return index <= this.furthest;
  }

  goToStep(index: number) {
    if (this.canReach(index)) this.currentStep = index;
  }

  avancar() {
    if (!this.isStepComplete(this.currentKey)) {
      this.errorMessage = 'Preencha os campos obrigatórios desta etapa para avançar.';
      return;
    }
    this.errorMessage = '';
    if (!this.isLastStep) {
      this.currentStep++;
      this.furthest = Math.max(this.furthest, this.currentStep);
    }
  }

  voltar() {
    if (this.currentStep > 0) this.currentStep--;
  }

  getDeponenteInitials(): string {
    return (this.formData.nome_depoente ?? '').split(' ').slice(0, 2).map(s => s[0]).join('').toUpperCase();
  }

  // ── Persistência ──────────────────────────────────────────────────────────
  async criar() {
    if (!this.isStepComplete('inquerito') || !this.isStepComplete('depoente')) {
      this.errorMessage = 'Há etapas obrigatórias incompletas.';
      return;
    }
    this.isSubmitting = true;
    this.errorMessage = '';
    try {
      const f = this.formData;
      const payload: any = {
        num_procedimento: f.num_procedimento.trim(),
        data_instauracao: f.data_registro,
        nome_depoente: f.nome_depoente.trim(),
        cpf_depoente: this.cpfDigits,
        tipo_depoente: f.tipo_depoente,
        cep: f.cep || null,
        logradouro: f.logradouro.trim() || null,
        numero: f.numero.trim() || null,
        complemento: f.complemento.trim() || null,
        bairro: f.bairro.trim() || null,
        municipio: f.municipio.trim() || null,
        uf: f.uf || null,
        cod_ibge: f.cod_ibge || null,
      };
      const res = await this.api.post('/processos/novo', payload);
      this.saved = true;
      this.router.navigate(['/auditoria', res.data.id_depoimento]);
    } catch (err: any) {
      this.errorMessage = err.response?.data?.detail || 'Erro ao criar o processo.';
    } finally {
      this.isSubmitting = false;
    }
  }

  descartar() {
    const ok = confirm(
      'Descartar este cadastro?\n\n' +
      'Todos os dados preenchidos neste formulário serão perdidos e nenhum processo será criado. ' +
      'Esta ação não pode ser desfeita. Deseja continuar?'
    );
    if (!ok) return;
    this.saved = true; // evita o segundo aviso do guard ao navegar
    this.router.navigate(['/processos']);
  }
}
