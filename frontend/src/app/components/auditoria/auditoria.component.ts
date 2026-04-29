import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
// @ts-ignore
import * as mockIdsData from '../../../mock_ids.json';

@Component({
  selector: 'app-auditoria',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auditoria.component.html'
})
export class AuditoriaComponent implements OnInit, OnDestroy {
  file: File | null = null;
  jobId: string | null = null;
  status: string = 'Nenhum';
  isUploading: boolean = false;
  
  transcricao: string = '';
  resumo: string = '';
  
  private intervalId: any;
  private mockIds: any = mockIdsData;

  constructor(private api: ApiService) {
    if (this.mockIds && this.mockIds.default) {
      this.mockIds = this.mockIds.default;
    }
  }

  ngOnInit() {}

  ngOnDestroy() {
    this.stopPolling();
  }

  onFileSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.file = event.target.files[0];
    }
  }

  async onUpload() {
    if (!this.file) {
      alert('Selecione um arquivo de áudio primeiro!');
      return;
    }

    this.isUploading = true;
    const formData = new FormData();
    formData.append('file', this.file);
    formData.append('id_depoimento', this.mockIds.id_depoimento);
    formData.append('id_modelo_asr', this.mockIds.id_modelo_asr);
    formData.append('id_modelo_llm', this.mockIds.id_modelo_llm);

    try {
      const response = await this.api.post('/upload/audio', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      this.jobId = response.data.id_job;
      this.status = response.data.status;
      this.startPolling();
    } catch (error) {
      console.error('Erro no upload', error);
      alert('Erro ao enviar o arquivo.');
    } finally {
      this.isUploading = false;
    }
  }

  startPolling() {
    this.intervalId = setInterval(async () => {
      if (!this.jobId) return;
      
      try {
        const response = await this.api.get(`/jobs/${this.jobId}`);
        this.status = response.data.status;
        
        if (this.status === 'Concluído') {
          this.stopPolling();
          await this.fetchResult();
        } else if (this.status === 'Erro') {
          this.stopPolling();
        }
      } catch (error) {
        console.error('Erro ao buscar status', error);
      }
    }, 2000);
  }

  stopPolling() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  async fetchResult() {
    try {
      const response = await this.api.get(`/jobs/${this.jobId}/resultado`);
      // Alimentando os atributos com o resultado da IA
      this.transcricao = response.data.txt_literal_asr || 'Sem transcrição.';
      this.resumo = response.data.txt_original_ia || 'Sem resumo gerado.';
    } catch (error) {
      console.error('Erro ao buscar resultado final', error);
      alert('Erro ao buscar a transcrição final do banco de dados.');
    }
  }

  getStatusColor(): string {
    switch (this.status) {
      case 'Concluído': return 'var(--color-success)';
      case 'Erro': return 'var(--color-accent)';
      case 'Processando': return '#D69E2E';
      default: return 'var(--color-secondary)';
    }
  }
}
