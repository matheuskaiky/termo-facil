import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../../services/api.service';

type TipoErro = 'ASR' | 'NER' | 'LLM';
type FiltroErro = 'Todas' | TipoErro;

interface ErroItem {
  id_job: string;
  num_procedimento: string;
  nome_depoente: string;
  delegacia: string;
  etapa: string;
  detalhe: string;
  quando: string;
  tipo_erro: TipoErro;
}

interface ErrosData {
  total_erros: number;
  erros_asr: number;
  erros_ner: number;
  erros_llm: number;
  erros: ErroItem[];
}

@Component({
  selector: 'app-dashboard-erros',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './dashboard-erros.component.html',
  styleUrls: ['./dashboard-erros.component.css']
})
export class DashboardErrosComponent implements OnInit {
  data: ErrosData | null = null;
  isLoading = true;
  errorMessage = '';

  filtro: FiltroErro = 'Todas';
  filtros: FiltroErro[] = ['Todas', 'ASR', 'NER', 'LLM'];

  isRetrying: Record<string, boolean> = {};

  constructor(private api: ApiService) {}

  async ngOnInit() {
    await this.loadData();
  }

  async loadData() {
    this.isLoading = true;
    try {
      const res = await this.api.get('/metricas/erros?periodo=30d');
      this.data = res.data;
    } catch {
      this.errorMessage = 'Erro ao carregar dados. O endpoint ainda pode não estar disponível.';
    } finally {
      this.isLoading = false;
    }
  }

  get filteredErros(): ErroItem[] {
    if (!this.data?.erros) return [];
    if (this.filtro === 'Todas') return this.data.erros;
    return this.data.erros.filter(e => e.tipo_erro === this.filtro);
  }

  async reprocessar(jobId: string) {
    this.isRetrying[jobId] = true;
    try {
      await this.api.post(`/jobs/${jobId}/retry`, {});
      await this.loadData();
    } catch {
      // Endpoint can be unavailable — fail silently, the button just re-enables
    } finally {
      this.isRetrying[jobId] = false;
    }
  }

  tipoColor(tipo: TipoErro): string {
    switch (tipo) {
      case 'ASR': return 'asr';
      case 'NER': return 'ner';
      case 'LLM': return 'llm';
      default: return '';
    }
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    try { return new Date(dateStr).toLocaleDateString('pt-BR'); } catch { return dateStr; }
  }
}
