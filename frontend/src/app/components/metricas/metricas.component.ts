import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
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

@Component({
  selector: 'app-metricas',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './metricas.component.html',
  styleUrls: ['./metricas.component.css'],
})
export class MetricasComponent implements OnInit {
  metricas: MetricasData | null = null;
  isLoading = true;
  hasPermission = false;
  errorMessage = '';

  constructor(private api: ApiService, private auth: AuthService) {}

  async ngOnInit() {
    const user = this.auth.getCurrentUser();
    this.hasPermission = user?.permissoes?.includes('VER_METRICAS') ?? false;

    if (!this.hasPermission) {
      this.isLoading = false;
      return;
    }

    try {
      const response = await this.api.get('/metricas');
      this.metricas = response.data;
    } catch (err: any) {
      this.errorMessage = err.response?.data?.detail || 'Erro ao carregar métricas.';
    } finally {
      this.isLoading = false;
    }
  }

  jobStatuses(): { label: string; value: number }[] {
    if (!this.metricas) return [];
    return Object.entries(this.metricas.jobs_por_status).map(([label, value]) => ({ label, value }));
  }
}
