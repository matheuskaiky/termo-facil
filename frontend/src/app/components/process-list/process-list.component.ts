import { Component, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';

interface ProcessoForm {
  num_procedimento: string;
  data_instauracao: string;
  nome_depoente: string;
  cpf_depoente: string;
  tipo_depoente: string;
}

interface FormErrors {
  [key: string]: string;
}

@Component({
  selector: 'app-process-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './process-list.component.html',
  styleUrls: ['./process-list.component.css']
})
export class ProcessListComponent implements OnInit {
  processos: any[] = [];
  filteredProcessos: any[] = [];

  activeUser: any = null;

  // Filtros
  searchTerm: string = '';
  statusFilter: string = '';
  escrivaoFilter: string = '';

  // Paginação
  totalProcessos: number = 0;
  currentPage: number = 0;
  readonly pageSize: number = 50;

  isLoading: boolean = true;
  isCreating: boolean = false;

  // Modal
  showModal: boolean = false;
  formData: ProcessoForm = {
    num_procedimento: '',
    data_instauracao: '',
    nome_depoente: '',
    cpf_depoente: '',
    tipo_depoente: 'Testemunha'
  };
  formErrors: FormErrors = {};
  isSubmitting: boolean = false;

  tiposDepoente = ['Testemunha', 'Vítima', 'Suspeito', 'Informante'];

  constructor(private api: ApiService, private router: Router) {}

  async ngOnInit() {
    await this.fetchActiveUser();
    await this.fetchProcessos();
  }

  async fetchActiveUser() {
    try {
      const response = await this.api.get('/auth/me');
      this.activeUser = response.data;
    } catch (error) {
      console.error('Erro ao buscar usuário logado', error);
    }
  }

  async fetchProcessos(page: number = this.currentPage) {
    this.isLoading = true;
    const offset = page * this.pageSize;
    try {
      const response = await this.api.get(`/processos/?limit=${this.pageSize}&offset=${offset}`);
      this.totalProcessos = response.data.total;
      this.processos = response.data.items;
      this.currentPage = page;
      this.applyFilters();
    } catch (error) {
      console.error('Erro ao buscar processos', error);
    } finally {
      this.isLoading = false;
    }
  }

  get totalPages(): number {
    return Math.ceil(this.totalProcessos / this.pageSize);
  }

  goToPage(page: number) {
    if (page < 0 || page >= this.totalPages) return;
    this.fetchProcessos(page);
  }

  applyFilters() {
    this.filteredProcessos = this.processos.filter(p => {
      const matchSearch = this.searchTerm === '' ||
        (p.nome_depoente && p.nome_depoente.toLowerCase().includes(this.searchTerm.toLowerCase())) ||
        (p.num_procedimento && p.num_procedimento.toLowerCase().includes(this.searchTerm.toLowerCase()));

      const matchStatus = this.statusFilter === '' || p.status_job === this.statusFilter;

      const matchEscrivao = this.escrivaoFilter === '' ||
        (p.escrivao && p.escrivao.toLowerCase().includes(this.escrivaoFilter.toLowerCase()));

      return matchSearch && matchStatus && matchEscrivao;
    });
  }

  abrirModal() {
    this.showModal = true;
    this.formData = {
      num_procedimento: '',
      data_instauracao: '',
      nome_depoente: '',
      cpf_depoente: '',
      tipo_depoente: 'Testemunha'
    };
    this.formErrors = {};
  }

  fecharModal() {
    this.showModal = false;
    this.formErrors = {};
  }

  formatarCpf(cpf: string): string {
    const clean = cpf.replace(/\D/g, '');
    if (clean.length <= 3) return clean;
    if (clean.length <= 6) return `${clean.slice(0, 3)}.${clean.slice(3)}`;
    if (clean.length <= 9) return `${clean.slice(0, 3)}.${clean.slice(3, 6)}.${clean.slice(6)}`;
    return `${clean.slice(0, 3)}.${clean.slice(3, 6)}.${clean.slice(6, 9)}-${clean.slice(9, 11)}`;
  }

  onCpfInput(event: any) {
    const value = event.target.value;
    this.formData.cpf_depoente = this.formatarCpf(value);
  }

  validarCpf(cpf: string): boolean {
    const clean = cpf.replace(/\D/g, '');

    if (clean.length !== 11 || /^(\d)\1{10}$/.test(clean)) {
      return false;
    }

    const calcDigit = (s: string, multiplier: number): number => {
      let total = 0;
      for (let i = 0; i < s.length; i++) {
        total += parseInt(s[i]) * (multiplier - i);
      }
      const remainder = total % 11;
      return remainder < 2 ? 0 : 11 - remainder;
    };

    const d1 = calcDigit(clean.slice(0, 9), 10);
    const d2 = calcDigit(clean.slice(0, 9) + d1, 11);

    return clean[9] === d1.toString() && clean[10] === d2.toString();
  }

  validarFormulario(): boolean {
    this.formErrors = {};

    if (!this.formData.num_procedimento.trim()) {
      this.formErrors['num_procedimento'] = 'Nº Procedimento é obrigatório';
    }

    if (!this.formData.data_instauracao) {
      this.formErrors['data_instauracao'] = 'Data de Instauração é obrigatória';
    }

    if (!this.formData.nome_depoente.trim()) {
      this.formErrors['nome_depoente'] = 'Nome do Depoente é obrigatório';
    }

    if (!this.formData.cpf_depoente.trim()) {
      this.formErrors['cpf_depoente'] = 'CPF é obrigatório';
    } else if (!this.validarCpf(this.formData.cpf_depoente)) {
      this.formErrors['cpf_depoente'] = 'CPF inválido';
    }

    return Object.keys(this.formErrors).length === 0;
  }

  async submeterFormulario() {
    if (!this.validarFormulario() || this.isSubmitting) return;

    this.isSubmitting = true;
    try {
      const payload = {
        num_procedimento: this.formData.num_procedimento.trim(),
        data_instauracao: this.formData.data_instauracao,
        nome_depoente: this.formData.nome_depoente.trim(),
        cpf_depoente: this.formData.cpf_depoente.replace(/\D/g, ''),
        tipo_depoente: this.formData.tipo_depoente
      };

      const response = await this.api.post('/processos/novo', payload);
      const novoId = response.data.id_depoimento;

      this.fecharModal();
      await this.fetchProcessos();
      this.router.navigate(['/auditoria', novoId]);
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Erro ao criar processo';
      this.formErrors['submit'] = errorMsg;
    } finally {
      this.isSubmitting = false;
    }
  }

  @HostListener('document:keydown.escape')
  onEscapeKey() {
    if (this.showModal) {
      this.fecharModal();
    }
  }

  goToAuditoria(id: string) {
    this.router.navigate(['/auditoria', id]);
  }

  get canSeeEscrivaoFilter(): boolean {
    return this.activeUser?.cargo?.nome_cargo === 'Delegado' || this.activeUser?.cargo?.nome_cargo === 'Admin';
  }

  get canCreateProcess(): boolean {
    if (!this.activeUser || !this.activeUser.cargo) return false;
    const permissions = this.activeUser.cargo.permissoes || [];
    return permissions.some((p: any) => p.nome_permissao === 'UPLOAD_AUDIO');
  }

  getStatusClass(status: string): string {
    const map: Record<string, string> = {
      'Sem Upload':      'status-sem-upload',
      'Pendente':        'status-pendente',
      'Processando':     'status-processando',
      'Transcrevendo':   'status-processando',
      'Extraindo Dados': 'status-processando',
      'Gerando Resumo':  'status-processando',
      'Concluído':       'status-concluido',
      'Erro':            'status-erro',
    };
    return map[status] ?? 'status-sem-upload';
  }
}
