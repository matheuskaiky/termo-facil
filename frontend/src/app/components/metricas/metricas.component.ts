import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

interface MetricasData {
  total_depoimentos: number;
  total_termos_gerados: number;
  total_pdfs_exportados: number;
  jobs_por_status: Record<string, number>;
  taxa_sucesso_pct: number;
  horas_economizadas_estimadas: number;
}

const PERIOD_LABELS = ['7 dias', '30 dias', '90 dias', '12 meses'];

@Component({
  selector: 'app-metricas',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './metricas.component.html',
  styleUrls: ['./metricas.component.css'],
})
export class MetricasComponent implements OnInit {
  metricas: MetricasData | null = null;
  isLoading = true;
  hasPermission = false;
  errorMessage = '';

  activePeriod = '30 dias';
  periodLabels = PERIOD_LABELS;

  activeSegment: 'geral' | 'por-delegacia' | 'por-escrivao' | 'erros' = 'geral';
  delegaciaSegments: any[] = [];

  constructor(private api: ApiService, private auth: AuthService, private router: Router) {}

  async ngOnInit() {
    const user = this.auth.getCurrentUser();
    this.hasPermission = user?.permissoes?.includes('VER_METRICAS') ?? false;
    if (!this.hasPermission) { this.isLoading = false; return; }
    await this.loadMetricas();
    this.loadDelegaciaSegments();
  }

  async loadMetricas() {
    this.isLoading = true;
    try {
      const res = await this.api.get('/metricas');
      this.metricas = res.data;
    } catch (err: any) {
      this.errorMessage = err.response?.data?.detail || 'Erro ao carregar métricas.';
    } finally {
      this.isLoading = false;
    }
  }

  async loadDelegaciaSegments() {
    try {
      const res = await this.api.get('/metricas/por-delegacia');
      this.delegaciaSegments = res.data ?? [];
    } catch {
      this.delegaciaSegments = [];
    }
  }

  get maxDelegaciaTotal(): number {
    if (!this.delegaciaSegments.length) return 1;
    return Math.max(...this.delegaciaSegments.map((d: any) => d.total ?? 0), 1);
  }

  navigateToDelegacia(id: string) {
    this.router.navigate(['/dashboard/delegacias', id]);
  }

  navigateToErros() {
    this.router.navigate(['/dashboard/erros']);
  }

  setPeriod(p: string) {
    this.activePeriod = p;
    this.loadMetricas();
  }

  jobStatuses(): { label: string; value: number; color: string }[] {
    if (!this.metricas) return [];
    const colorMap: Record<string, string> = {
      'Concluído': 'var(--color-success)',
      'Erro': 'var(--color-accent)',
      'Processando': '#D69E2E',
      'Pendente': 'var(--color-text-subtle)',
    };
    return Object.entries(this.metricas.jobs_por_status).map(([label, value]) => ({
      label,
      value,
      color: colorMap[label] ?? 'var(--color-primary)',
    }));
  }

  get totalJobs(): number {
    return this.jobStatuses().reduce((a, b) => a + b.value, 0);
  }

  jobBarWidth(value: number): number {
    return this.totalJobs > 0 ? Math.round((value / this.totalJobs) * 100) : 0;
  }

  get topEscrivaes(): { nome: string; total: number }[] {
    return [];
  }

  // Inline SVG area chart data (simple placeholder path)
  areaChartPath(w: number, h: number): string {
    const points = [0.2, 0.5, 0.35, 0.7, 0.55, 0.8, 0.65, 0.9, 0.75, 0.6];
    const coords = points.map((v, i) => `${(i / (points.length - 1)) * w},${h - v * h}`).join(' L ');
    return `M ${coords} L ${w},${h} L 0,${h} Z`;
  }

  sparklinePath(w: number, h: number): string {
    const pts = [0.4, 0.6, 0.5, 0.7, 0.8, 0.65, 0.9];
    return pts.map((v, i) => `${(i / (pts.length - 1)) * w},${h - v * h}`).join(' ');
  }

  donutSegments(): { color: string; dash: number; offset: number }[] {
    const statuses = this.jobStatuses();
    const total = statuses.reduce((a, b) => a + b.value, 0) || 1;
    const circumference = 2 * Math.PI * 50;
    let offset = 0;
    return statuses.map(s => {
      const dash = (s.value / total) * circumference;
      const seg = { color: s.color, dash, offset };
      offset += dash;
      return seg;
    });
  }
}
