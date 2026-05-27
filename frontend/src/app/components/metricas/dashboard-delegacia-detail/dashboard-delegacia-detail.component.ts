import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../services/api.service';

interface DelegaciaDetailData {
  nome_unidade: string;
  cod_sinesp: string;
  total_depoimentos: number;
  servidores_ativos: number;
  taxa_sucesso_pct: number;
  tempo_medio_min: number;
  escrivaes: { id_usuario: string; nome: string; total: number; taxa: number }[];
  tipos_depoente: { tipo: string; count: number }[];
  atividade_recente: { id_depoimento: string; num_procedimento: string; nome_depoente: string; escrivao: string; status: string; quando: string }[];
}

@Component({
  selector: 'app-dashboard-delegacia-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard-delegacia-detail.component.html',
  styleUrls: ['./dashboard-delegacia-detail.component.css']
})
export class DashboardDelegaciaDetailComponent implements OnInit {
  delegaciaId: string | null = null;
  data: DelegaciaDetailData | null = null;
  isLoading = true;
  errorMessage = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {}

  async ngOnInit() {
    this.delegaciaId = this.route.snapshot.paramMap.get('id');
    await this.loadData();
  }

  async loadData() {
    this.isLoading = true;
    try {
      const res = await this.api.get(`/metricas/delegacias/${this.delegaciaId}?periodo=30d`);
      this.data = res.data;
    } catch {
      this.errorMessage = 'Erro ao carregar dados. O endpoint ainda pode não estar disponível.';
    } finally {
      this.isLoading = false;
    }
  }

  get maxEscrivaoTotal(): number {
    if (!this.data?.escrivaes?.length) return 1;
    return Math.max(...this.data.escrivaes.map(e => e.total));
  }

  get maxTipoCount(): number {
    if (!this.data?.tipos_depoente?.length) return 1;
    return Math.max(...this.data.tipos_depoente.map(t => t.count));
  }

  navigateToEscrivao(id: string) {
    this.router.navigate(['/dashboard/escrivaes', id]);
  }

  voltar() {
    this.router.navigate(['/metricas']);
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    try { return new Date(dateStr).toLocaleDateString('pt-BR'); } catch { return dateStr; }
  }
}
