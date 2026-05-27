import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

interface ProcessFormData {
  num_procedimento: string;
  tipo_procedimento: string;
  natureza_feito: string;
  data_registro: string;
  nome_depoente: string;
  tipo_depoente: string;
  cpf: string;
  rg: string;
  data_nascimento: string;
  telefone: string;
  profissao: string;
  endereco: string;
  municipio: string;
  uf: string;
  id_delegacia: string;
  id_inquerito: string;
  observacoes: string;
}

type DeponenteState = 'empty' | 'checking' | 'not-found' | 'found' | 'found-modified';

@Component({
  selector: 'app-process-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './process-form.component.html',
  styleUrls: ['./process-form.component.css']
})
export class ProcessFormComponent implements OnInit {
  isEditMode = false;
  idProcesso: string | null = null;
  isSubmitting = false;
  activeSection = 'inquerito';
  errorMessage = '';

  // CPF-first state machine (Issue #68)
  deponenteState: DeponenteState = 'empty';
  foundDepoente: any = null;
  modifiedFields: Set<string> = new Set();
  private cpfDebounceTimer: any;

  formData: ProcessFormData = {
    num_procedimento: '',
    tipo_procedimento: 'Inquérito Policial',
    natureza_feito: '',
    data_registro: new Date().toISOString().slice(0, 10),
    nome_depoente: '',
    tipo_depoente: 'Testemunha',
    cpf: '',
    rg: '',
    data_nascimento: '',
    telefone: '',
    profissao: '',
    endereco: '',
    municipio: '',
    uf: 'PI',
    id_delegacia: '',
    id_inquerito: '',
    observacoes: '',
  };

  historico: { descricao: string; data: string }[] = [];

  sections = [
    { key: 'inquerito',  label: 'Identificação do procedimento' },
    { key: 'depoente',   label: 'Dados do depoente' },
    { key: 'vinculacao', label: 'Vinculação institucional' },
    { key: 'obs',        label: 'Observações' },
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
    });
  }

  async loadProcesso() {
    try {
      const res = await this.api.get(`/processos/${this.idProcesso}`);
      const d = res.data;
      this.formData.num_procedimento = d.num_procedimento ?? '';
      this.formData.tipo_procedimento = d.tipo_procedimento ?? 'Inquérito Policial';
      this.formData.natureza_feito = d.natureza_feito ?? '';
      this.formData.data_registro = d.data_registro?.slice(0, 10) ?? '';
      this.formData.nome_depoente = d.nome_depoente ?? '';
      this.formData.tipo_depoente = d.tipo_depoente ?? 'Testemunha';
      this.formData.cpf = d.cpf ?? '';
      this.formData.rg = d.rg ?? '';
      this.formData.data_nascimento = d.data_nascimento?.slice(0, 10) ?? '';
      this.formData.telefone = d.telefone ?? '';
      this.formData.profissao = d.profissao ?? '';
      this.formData.endereco = d.endereco ?? '';
      this.formData.municipio = d.municipio ?? '';
      this.formData.uf = d.uf ?? 'PI';
      this.formData.observacoes = d.observacoes ?? '';
      this.historico = d.historico ?? [];
    } catch {
      this.errorMessage = 'Erro ao carregar processo.';
    }
  }

  onCpfInput(event: any) {
    let v = event.target.value.replace(/\D/g, '').slice(0, 11);
    if (v.length > 9) v = v.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    else if (v.length > 6) v = v.replace(/(\d{3})(\d{3})(\d{0,3})/, '$1.$2.$3');
    else if (v.length > 3) v = v.replace(/(\d{3})(\d{0,3})/, '$1.$2');
    this.formData.cpf = v;

    clearTimeout(this.cpfDebounceTimer);
    const digits = v.replace(/\D/g, '');
    if (digits.length < 11) {
      if (this.deponenteState !== 'empty') {
        this.deponenteState = 'empty';
        this.foundDepoente = null;
        this.modifiedFields.clear();
      }
      return;
    }
    this.deponenteState = 'checking';
    this.cpfDebounceTimer = setTimeout(() => this.checkCpf(digits), 600);
  }

  private async checkCpf(digits: string) {
    try {
      const res = await this.api.get(`/depoentes/check-cpf?cpf=${encodeURIComponent(digits)}`);
      if (res.data.found) {
        this.foundDepoente = res.data.depoente;
        this.prefillDepoente(res.data.depoente);
        this.deponenteState = 'found';
        this.modifiedFields.clear();
      } else {
        this.foundDepoente = null;
        this.deponenteState = 'not-found';
      }
    } catch {
      this.foundDepoente = null;
      this.deponenteState = 'not-found';
    }
  }

  private prefillDepoente(dep: any) {
    if (dep.nome_depoente) this.formData.nome_depoente = dep.nome_depoente;
  }

  onDeponenteFieldChange(field: string) {
    if (!this.foundDepoente) return;
    const val = (this.formData as any)[field];
    const orig = this.foundDepoente[field] ?? this.foundDepoente['nome_depoente'];
    if (val !== orig) {
      this.modifiedFields.add(field);
    } else {
      this.modifiedFields.delete(field);
    }
    this.deponenteState = this.modifiedFields.size > 0 ? 'found-modified' : 'found';
  }

  get deponenteFieldsLocked(): boolean {
    return this.deponenteState === 'empty';
  }

  getDeponenteInitials(): string {
    return (this.formData.nome_depoente ?? '').split(' ').slice(0, 2).map(s => s[0]).join('').toUpperCase();
  }

  async salvar() {
    if (!this.formData.nome_depoente || !this.formData.num_procedimento) {
      this.errorMessage = 'Preencha os campos obrigatórios: número do procedimento e nome do depoente.';
      return;
    }
    this.isSubmitting = true;
    this.errorMessage = '';
    try {
      let id: string;
      if (this.isEditMode) {
        await this.api.put(`/processos/${this.idProcesso}`, this.formData);
        id = this.idProcesso!;
      } else {
        const payload: any = { ...this.formData };
      if (this.foundDepoente?.id_depoente) payload.id_depoente = this.foundDepoente.id_depoente;
      const res = await this.api.post('/processos', payload);
        id = res.data.id;
      }
      this.router.navigate(['/auditoria', id]);
    } catch (err: any) {
      this.errorMessage = err.response?.data?.detail || 'Erro ao salvar o processo.';
    } finally {
      this.isSubmitting = false;
    }
  }

  descartar() {
    this.router.navigate(['/processos']);
  }

  setSection(key: string) {
    this.activeSection = key;
  }

  sectionDone(key: string): boolean {
    const order = this.sections.map(s => s.key);
    return order.indexOf(key) < order.indexOf(this.activeSection);
  }
}
