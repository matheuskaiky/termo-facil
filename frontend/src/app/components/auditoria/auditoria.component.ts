import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

export interface Segment {
  start: number;
  end: number;
  text: string;
  speaker: string;
}

const DRAFT_KEY = (id: string) => `rascunho_${id}`;
const AUTOSAVE_DELAY_MS = 1500;

@Component({
  selector: 'app-auditoria',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auditoria.component.html'
})
export class AuditoriaComponent implements OnInit, OnDestroy {
  @ViewChild('audioPlayer') audioPlayerRef!: ElementRef<HTMLAudioElement>;

  file: File | null = null;
  jobId: string | null = null;
  status: string = 'Nenhum';
  isUploading: boolean = false;

  transcricao: string = '';
  resumo: string = '';
  segmentos: Segment[] = [];
  audioUrl: string | null = null;

  // Responsibility acceptance (RN-03)
  revisaoAceita: boolean = false;

  // Auto-save state (RNF-04)
  autoSaveLabel: string = '';
  private autoSaveTimer: any = null;

  // RBAC and PDF States
  permissions: string[] = [];
  pdfHash: string | null = null;
  pdfUrl: string | null = null;
  safePdfUrl: SafeResourceUrl | null = null;
  pdfGenerationDate: Date | null = null;
  pdfSuccessMessage: string = '';
  pdfErrorMessage: string = '';
  isGeneratingPdf: boolean = false;

  private intervalId: any;
  idDepoimento: string | null = null;

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private sanitizer: DomSanitizer,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  async ngOnInit() {
    // Load permissions from local JWT — no extra HTTP call needed
    const user = this.auth.getCurrentUser();
    this.permissions = user?.permissoes ?? [];

    this.route.paramMap.subscribe(async params => {
      this.idDepoimento = params.get('id');
      if (this.idDepoimento) {
        await this.loadExistingTermo();
      }
    });
  }

  async loadExistingTermo() {
    const draft = this.idDepoimento ? localStorage.getItem(DRAFT_KEY(this.idDepoimento)) : null;

    const [termoRes, audioRes] = await Promise.allSettled([
      this.api.get(`/termos/${this.idDepoimento}`),
      this.api.get(`/audio/${this.idDepoimento}`),
    ]);

    if (termoRes.status === 'fulfilled') {
      const termo = termoRes.value.data;
      if (termo.txt_literal_asr) {
        this.transcricao = termo.txt_literal_asr;
        this.segmentos = termo.segmentos_asr ?? [];
        // Draft > server edit > original AI output
        this.resumo = draft ?? termo.txt_editado_humano ?? termo.txt_original_ia ?? '';
        this.status = 'Concluído';
        if (draft) this.autoSaveLabel = 'Rascunho local restaurado';
      }
    } else if (draft) {
      this.resumo = draft;
      this.autoSaveLabel = 'Rascunho local restaurado';
    }

    if (audioRes.status === 'fulfilled') {
      this.audioUrl = audioRes.value.data.audio_url;
    }
  }

  seekTo(seconds: number) {
    const player = this.audioPlayerRef?.nativeElement;
    if (!player) return;
    player.currentTime = seconds;
    player.play();
  }

  formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
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

  onResumoChange() {
    if (!this.idDepoimento) return;
    clearTimeout(this.autoSaveTimer);
    this.autoSaveLabel = 'Salvando rascunho...';
    this.autoSaveTimer = setTimeout(() => {
      localStorage.setItem(DRAFT_KEY(this.idDepoimento!), this.resumo);
      this.autoSaveLabel = 'Rascunho salvo localmente';
    }, AUTOSAVE_DELAY_MS);
  }

  async onGeneratePDF() {
    this.pdfSuccessMessage = '';
    this.pdfErrorMessage = '';
    this.isGeneratingPdf = true;
    this.pdfUrl = null;
    this.safePdfUrl = null;
    this.pdfGenerationDate = null;

    try {
      // Persist human edits before PDF generation so the PDF uses the reviewed text
      await this.api.put(`/termos/${this.idDepoimento}`, {
        txt_editado_humano: this.resumo
      });

      const response = await this.api.post('/pdf/gerar', {
        id_depoimento: this.idDepoimento
      });
      this.pdfHash = response.data.hash_pdf;
      this.pdfUrl = response.data.pdf_url;
      if (this.pdfUrl) {
        this.safePdfUrl = this.sanitizer.bypassSecurityTrustResourceUrl(this.pdfUrl);
      }
      this.pdfGenerationDate = new Date();
      this.pdfSuccessMessage = response.data.message;

      // Clear local draft after successful export
      if (this.idDepoimento) {
        localStorage.removeItem(DRAFT_KEY(this.idDepoimento));
        this.autoSaveLabel = '';
      }
    } catch (error: any) {
      console.error('Erro ao gerar PDF', error);
      this.pdfErrorMessage = error.response?.data?.detail || 'Erro ao comunicar com o servidor para geração de PDF.';
    } finally {
      this.isGeneratingPdf = false;
    }
  }

  ngOnDestroy() {
    this.stopPolling();
    clearTimeout(this.autoSaveTimer);
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
    if (this.idDepoimento) {
      formData.append('id_depoimento', this.idDepoimento);
    }
    // Model IDs are now optional — backend resolves defaults from DB

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
      const [resultRes, audioRes] = await Promise.allSettled([
        this.api.get(`/jobs/${this.jobId}/resultado`),
        this.api.get(`/audio/${this.idDepoimento}`),
      ]);

      if (resultRes.status === 'fulfilled') {
        const data = resultRes.value.data;
        this.transcricao = data.txt_literal_asr || 'Sem transcrição.';
        const draft = this.idDepoimento ? localStorage.getItem(DRAFT_KEY(this.idDepoimento)) : null;
        this.resumo = draft ?? data.txt_editado_humano ?? data.txt_original_ia ?? 'Sem resumo gerado.';
        if (draft) this.autoSaveLabel = 'Rascunho local restaurado';
      }

      // Load segments via the full termo endpoint (job resultado doesn't carry segments yet)
      if (this.idDepoimento) {
        try {
          const termoRes = await this.api.get(`/termos/${this.idDepoimento}`);
          this.segmentos = termoRes.data.segmentos_asr ?? [];
        } catch { /* segments unavailable */ }
      }

      if (audioRes.status === 'fulfilled') {
        this.audioUrl = audioRes.value.data.audio_url;
      }
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

  voltar() {
    this.router.navigate(['/processos']);
  }
}
