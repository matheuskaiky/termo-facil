import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
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
  
  // RBAC and PDF States
  activeUser: any = null;
  permissions: string[] = [];
  pdfHash: string | null = null;
  pdfUrl: string | null = null;
  safePdfUrl: SafeResourceUrl | null = null;
  pdfGenerationDate: Date | null = null;
  pdfSuccessMessage: string = '';
  pdfErrorMessage: string = '';
  isGeneratingPdf: boolean = false;
  
  private intervalId: any;
  private mockIds: any = mockIdsData;

  constructor(private api: ApiService, private sanitizer: DomSanitizer) {
    if (this.mockIds && this.mockIds.default) {
      this.mockIds = this.mockIds.default;
    }
  }

  async ngOnInit() {
    await this.fetchUserProfile();
  }

  async fetchUserProfile() {
    try {
      const response = await this.api.get('/auth/me');
      this.activeUser = response.data;
      this.permissions = this.activeUser?.cargo?.permissoes?.map((p: any) => p.nome_permissao) || [];
    } catch (error) {
      console.error('Erro ao buscar perfil atual na Auditoria:', error);
    }
  }

  get hasUploadPermission(): boolean {
    return this.permissions.includes('UPLOAD_AUDIO');
  }

  get hasEditPermission(): boolean {
    return this.permissions.includes('EDITAR_TERMO');
  }

  get hasPdfPermission(): boolean {
    return this.permissions.includes('GERAR_PDF');
  }

  async onGeneratePDF() {
    this.pdfSuccessMessage = '';
    this.pdfErrorMessage = '';
    this.isGeneratingPdf = true;
    this.pdfUrl = null;
    this.safePdfUrl = null;
    this.pdfGenerationDate = null;

    try {
      const response = await this.api.post('/pdf/gerar', {
        id_depoimento: this.mockIds.id_depoimento
      });
      this.pdfHash = response.data.hash_pdf;
      this.pdfUrl = response.data.pdf_url;
      if (this.pdfUrl) {
        this.safePdfUrl = this.sanitizer.bypassSecurityTrustResourceUrl(this.pdfUrl);
      }
      this.pdfGenerationDate = new Date();
      this.pdfSuccessMessage = response.data.message;
    } catch (error: any) {
      console.error('Erro ao gerar PDF', error);
      this.pdfErrorMessage = error.response?.data?.detail || 'Erro ao comunicar com o servidor para geração de PDF.';
    } finally {
      this.isGeneratingPdf = false;
    }
  }

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
