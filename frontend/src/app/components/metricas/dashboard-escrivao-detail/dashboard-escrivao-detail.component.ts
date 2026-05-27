import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../services/api.service';

interface EscrivaoDetailData {
  nome: string;
  matricula: string;
  delegacia_nome: string;
  total_depoimentos: number;
  termos_editados: number;
  pdfs_assinados: number;
  taxa_sucesso_pct: number;
  tempo_medio_min: number;
  producao_diaria: number[];
  tipos_depoente: { tipo: string; count: number }[];
  pontos_atencao: { nivel: 'warning' | 'info' | 'success'; texto: string }[];
}

@Component({
  selector: 'app-dashboard-escrivao-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard-escrivao-detail.component.html',
  styleUrls: ['./dashboard-escrivao-detail.component.css']
})
export class DashboardEscrivaoDetailComponent implements OnInit {
  escrivaoId: string | null = null;
  data: EscrivaoDetailData | null = null;
  isLoading = true;
  errorMessage = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) {}

  async ngOnInit() {
    this.escrivaoId = this.route.snapshot.paramMap.get('id');
    await this.loadData();
  }

  async loadData() {
    this.isLoading = true;
    try {
      const res = await this.api.get(`/metricas/escrivaes/${this.escrivaoId}?periodo=30d`);
      this.data = res.data;
    } catch {
      this.errorMessage = 'Erro ao carregar dados. O endpoint ainda pode não estar disponível.';
    } finally {
      this.isLoading = false;
    }
  }

  get maxProducao(): number {
    if (!this.data?.producao_diaria?.length) return 1;
    return Math.max(...this.data.producao_diaria, 1);
  }

  get maxTipoCount(): number {
    if (!this.data?.tipos_depoente?.length) return 1;
    return Math.max(...this.data.tipos_depoente.map(t => t.count));
  }

  getInitials(nome: string): string {
    return (nome ?? '').split(' ').slice(0, 2).map(s => s[0]).join('').toUpperCase();
  }

  voltar() {
    this.router.navigate(['/metricas']);
  }
}
