import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { FilterChipComponent } from '../shared/filter-chip/filter-chip.component';

const IN_PROGRESS_STATUSES = new Set(['Transcrevendo', 'Extraindo Dados', 'Gerando Resumo', 'Processando', 'Pendente']);

@Component({
  selector: 'app-process-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, FilterChipComponent],
  templateUrl: './process-list.component.html',
  styleUrls: ['./process-list.component.css']
})
export class ProcessListComponent implements OnInit {
  processos: any[] = [];
  filteredProcessos: any[] = [];

  activeUser: any = null;

  // Filtros
  searchTerm: string = '';
  activeChip: string = '';

  // Paginação
  totalProcessos: number = 0;
  currentPage: number = 0;
  readonly pageSize: number = 50;

  isLoading: boolean = true;

  constructor(private api: ApiService, private auth: AuthService, private router: Router) {}

  async ngOnInit() {
    await this.fetchActiveUser();
    await this.fetchProcessos();
  }

  async fetchActiveUser() {
    try {
      const response = await this.api.get('/auth/me');
      this.activeUser = response.data;
    } catch {
      // fallback to JWT data
      this.activeUser = this.auth.getCurrentUser();
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
    } catch {
      this.processos = [];
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

  get currentMonthYear(): string {
    return new Date().toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
      .replace(' de ', '/');
  }

  get kpiCounts() {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    return {
      emProcessamento: this.processos.filter(p => IN_PROGRESS_STATUSES.has(p.status_job)).length,
      aguardandoRevisao: this.processos.filter(p => p.status_job === 'Concluído' && !p.pdf_gerado).length,
      comErro: this.processos.filter(p => p.status_job === 'Erro').length,
      concluidosNoMes: this.processos.filter(p => {
        if (p.status_job !== 'Concluído') return false;
        const d = new Date(p.data_hora_reg);
        return d >= startOfMonth;
      }).length,
    };
  }

  setChip(chip: string) {
    this.activeChip = this.activeChip === chip ? '' : chip;
    this.applyFilters();
  }

  applyFilters() {
    const user = this.activeUser;
    this.filteredProcessos = this.processos.filter(p => {
      const matchSearch = !this.searchTerm ||
        (p.nome_depoente?.toLowerCase().includes(this.searchTerm.toLowerCase())) ||
        (p.num_procedimento?.toLowerCase().includes(this.searchTerm.toLowerCase())) ||
        (p.cpf_depoente?.includes(this.searchTerm));

      let matchChip = true;
      if (this.activeChip === 'meus') {
        const userName = user?.nome || user?.sub || '';
        matchChip = p.escrivao === userName;
      } else if (this.activeChip === 'aguardando') {
        matchChip = p.status_job === 'Concluído' && !p.pdf_gerado;
      } else if (this.activeChip === 'processando') {
        matchChip = IN_PROGRESS_STATUSES.has(p.status_job);
      } else if (this.activeChip === 'erro') {
        matchChip = p.status_job === 'Erro';
      } else if (this.activeChip === 'concluidos') {
        matchChip = p.status_job === 'Concluído';
      }

      return matchSearch && matchChip;
    });
  }

  novoProcesso() {
    this.router.navigate(['/processos/novo']);
  }

  goToAuditoria(id: string) {
    this.router.navigate(['/auditoria', id]);
  }

  get canCreateProcess(): boolean {
    if (!this.activeUser?.cargo) return false;
    const permissions = this.activeUser.cargo.permissoes || [];
    return permissions.some((p: any) => p.nome_permissao === 'UPLOAD_AUDIO');
  }

  getStageIndex(status: string): number {
    const map: Record<string, number> = {
      'Pendente': 0, 'Transcrevendo': 1, 'Extraindo Dados': 2, 'Gerando Resumo': 3, 'Concluído': 4,
      'Processando': 1, 'Sem Upload': 0, 'Erro': 1,
    };
    return map[status] ?? 0;
  }

  getStageLabel(p: any): string {
    const s = p.status_job;
    if (s === 'Erro') return 'Erro no processamento';
    if (s === 'Concluído') return 'Pronto para revisão';
    if (s === 'Sem Upload' || !s) return 'Aguardando upload';
    return s;
  }

  isInProgress(status: string): boolean {
    return IN_PROGRESS_STATUSES.has(status) && status !== 'Pendente';
  }

  getStatusDotColor(p: any): string {
    const s = p.status_job;
    if (s === 'Erro') return 'var(--color-accent)';
    if (s === 'Concluído') return 'var(--color-success)';
    if (IN_PROGRESS_STATUSES.has(s)) return 'var(--color-primary)';
    return 'var(--color-text-subtle)';
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString('pt-BR', {
      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
    });
  }
}
