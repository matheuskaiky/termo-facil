import { Component, HostListener, OnInit, OnDestroy, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeHtml, SafeResourceUrl } from '@angular/platform-browser';
import { environment } from '../../../environments/environment';
import { PipelineStepperComponent } from '../shared/pipeline-stepper/pipeline-stepper.component';
import { SignatureModalComponent } from '../shared/signature-modal/signature-modal.component';
import { KpiCardComponent } from '../shared/kpi-card/kpi-card.component';

export interface Segment {
  start: number;
  end: number;
  text: string;
  speaker: string;
  speaker_nome?: string | null;
  confianca?: number | null;
}

const DRAFT_KEY = (id: string) => `rascunho_${id}`;
const AUTOSAVE_DELAY_MS = 1500;

const STAGE_MAP: Record<string, number> = {
  'Nenhum':         0,
  'Sem Upload':     0,
  'Pendente':       0,
  'Transcrevendo':  1,
  'Extraindo Dados':2,
  'Gerando Resumo': 3,
  'Concluído':      4,
  'Processando':    1,
  'Erro':           1,
};

@Component({
  selector: 'app-auditoria',
  standalone: true,
  imports: [CommonModule, FormsModule, PipelineStepperComponent, SignatureModalComponent, KpiCardComponent],
  templateUrl: './auditoria.component.html',
  styleUrls: ['./auditoria.component.css']
})
export class AuditoriaComponent implements OnInit, OnDestroy {
  @ViewChild('audioPlayer') audioPlayerRef!: ElementRef<HTMLAudioElement>;
  @ViewChild('fileInputNative') fileInputNativeRef!: ElementRef<HTMLInputElement>;

  file: File | null = null;
  fileName: string | null = null;
  jobId: string | null = null;

  // Audio player state
  isPlaying = false;
  audioCurrentTime = 0;
  audioDuration = 0;
  playbackRate: number = 1.0;
  status: string = 'Nenhum';
  isUploading: boolean = false;

  transcricao: string = '';
  resumo: string = '';
  segmentos: Segment[] = [];
  nerEntities: Record<string, string[]> = {};
  audioUrl: string | null = null;

  // Identificação / confiança
  nomeDepoente: string = '';
  numProcedimento: string = '';
  assinado: boolean = false;
  confiancaAsr: number | null = null;
  confiancaNer: number | null = null;
  nerEntidades: { tipo: string; texto: string; score: number }[] = [];

  // Tempos de execução do pipeline (ms) — só populados em jobs novos.
  tempoAsrMs: number | null = null;
  tempoNerMs: number | null = null;
  tempoLlmMs: number | null = null;
  tempoTotalMs: number | null = null;

  // Identificação manual de falantes (ouvir amostra + rotular)
  speakers: { label: string; role: string; nome: string; sampleStart: number; count: number }[] = [];
  isApplyingSpeakers = false;
  isReprocessing = false;

  // Active segment sync
  activeSegmentIndex: number = -1;

  // Responsibility acceptance (RN-03)
  revisaoAceita: boolean = false;

  // Speaker role identification
  speakerSampleFile: File | null = null;
  speakerReclassifyStatus: 'idle' | 'loading' | 'done' | 'error' = 'idle';
  speakerReclassifyMessage: string = '';

  // Auto-save state (RNF-04)
  autoSaveLabel: string = '';
  private autoSaveTimer: any = null;

  // RBAC and PDF States
  permissions: string[] = [];
  pdfHash: string | null = null;
  pdfUrl: string | null = null;
  safePdfUrl: SafeResourceUrl | null = null;
  pdfGenerationDate: Date | null = null;
  pdfErrorMessage: string = '';
  isGeneratingPdf: boolean = false;

  // Signature modal
  showSignModal: boolean = false;

  private intervalId: any;
  private pollDelay = 2000;
  idDepoimento: string | null = null;
  isDescartando = false;

  // Meta info for sub-header
  startedAt: Date | null = null;

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private sanitizer: DomSanitizer,
    private route: ActivatedRoute,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  async ngOnInit() {
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
    const draft = this.idDepoimento ? sessionStorage.getItem(DRAFT_KEY(this.idDepoimento)) : null;

    const [termoRes, audioRes] = await Promise.allSettled([
      this.api.get(`/termos/${this.idDepoimento}`),
      this.api.get(`/audio/${this.idDepoimento}`),
    ]);

    if (termoRes.status === 'fulfilled') {
      const termo = termoRes.value.data;
      this.applyTermo(termo);
      if (termo.txt_literal_asr) {
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

    // Recupera o job desta sessão p/ habilitar Reprocessar quando deu Erro.
    if (this.idDepoimento && this.status !== 'Concluído') {
      const storedJob = sessionStorage.getItem('job_' + this.idDepoimento);
      if (storedJob) {
        this.jobId = storedJob;
        try {
          const jr = await this.api.get(`/jobs/${storedJob}`);
          this.status = jr.data.status;
          if (this.isProcessing) this.startPolling();
        } catch { /* job sumiu */ }
      }
    }
  }

  /** Aplica os campos do termo (transcrição, NER, confiança, nome, falantes). */
  private applyTermo(termo: any) {
    if (termo.txt_literal_asr) this.transcricao = termo.txt_literal_asr;
    this.segmentos = termo.segmentos_asr ?? this.segmentos;
    this.nerEntities = termo.dicionario_ner ?? this.nerEntities;
    this.nerEntidades = termo.ner_entidades ?? [];
    this.confiancaAsr = termo.confianca_asr ?? null;
    this.confiancaNer = termo.confianca_ner ?? null;
    this.tempoAsrMs = termo.tempo_asr_ms ?? null;
    this.tempoNerMs = termo.tempo_ner_ms ?? null;
    this.tempoLlmMs = termo.tempo_llm_ms ?? null;
    this.tempoTotalMs = termo.tempo_total_ms ?? null;
    this.nomeDepoente = termo.nome_depoente ?? this.nomeDepoente;
    this.numProcedimento = termo.num_procedimento ?? this.numProcedimento;
    this.assinado = !!termo.assinado;
    this.buildSpeakers();
  }

  /** Deriva os falantes distintos dos segmentos, com um trecho-amostra de cada. */
  private buildSpeakers() {
    const map = new Map<string, { count: number; sampleStart: number; sampleDur: number; nome: string }>();
    for (const s of this.segmentos) {
      const label = s.speaker ?? 'Desconhecido';
      const dur = (s.end ?? 0) - (s.start ?? 0);
      const cur = map.get(label);
      if (!cur) {
        map.set(label, { count: 1, sampleStart: s.start ?? 0, sampleDur: dur, nome: (s as any).speaker_nome ?? '' });
      } else {
        cur.count++;
        if (dur > cur.sampleDur) { cur.sampleDur = dur; cur.sampleStart = s.start ?? 0; }
        if (!cur.nome && (s as any).speaker_nome) cur.nome = (s as any).speaker_nome;
      }
    }
    const roles = ['Depoente', 'Inquiridor'];
    this.speakers = [...map.entries()].map(([label, v]) => ({
      label,
      role: roles.includes(label) ? label : 'Depoente',
      nome: v.nome,
      sampleStart: v.sampleStart,
      count: v.count,
    }));
  }

  /**
   * Ticket 1: ao trocar o áudio, zera imediatamente a transcrição/termo antigos
   * na tela (o backend já apaga os dados; aqui evitamos exibir conteúdo obsoleto
   * enquanto o novo áudio é processado).
   */
  private resetWorkspaceState() {
    this.transcricao = '';
    this.resumo = '';
    this.segmentos = [];
    this.nerEntities = {};
    this.nerEntidades = [];
    this.speakers = [];
    this.confiancaAsr = null;
    this.confiancaNer = null;
    this.tempoAsrMs = null;
    this.tempoNerMs = null;
    this.tempoLlmMs = null;
    this.tempoTotalMs = null;
    this.activeSegmentIndex = -1;
    this.revisaoAceita = false;
    this.pdfHash = null;
    this.pdfUrl = null;
    this.safePdfUrl = null;
    this.autoSaveLabel = '';
    if (this.idDepoimento) sessionStorage.removeItem(DRAFT_KEY(this.idDepoimento));
  }

  /** Tempo de execução formatado (ms → "x,x s") ou "—" quando ausente. */
  formatMs(ms: number | null): string {
    if (ms === null || ms === undefined) return '—';
    return `${(ms / 1000).toFixed(1).replace('.', ',')} s`;
  }

  get hasTimingMetrics(): boolean {
    return this.tempoTotalMs !== null && this.tempoTotalMs !== undefined;
  }

  /** Confiança de um segmento (0–100, 1 casa) ou null. */
  confiancaSegmento(seg: any): number | null {
    return seg && typeof seg.confianca === 'number' ? seg.confianca : null;
  }

  /** Score (%) de uma entidade pelo texto, vindo de ner_entidades. */
  entityScore(label: string): number | null {
    const hit = this.nerEntidades.find(e => e.texto === label);
    return hit && typeof hit.score === 'number' ? hit.score : null;
  }

  get isProcessing(): boolean {
    return !['Concluído', 'Erro', 'Nenhum'].includes(this.status);
  }

  getStageIndex(): number {
    return STAGE_MAP[this.status] ?? 0;
  }

  get inquerito(): string {
    return this.idDepoimento ? `DEP-${this.idDepoimento.slice(-6).toUpperCase()}` : '';
  }

  // ─── Audio player ───────────────────────────────
  seekTo(seconds: number) {
    const player = this.audioPlayerRef?.nativeElement;
    if (!player) return;
    player.currentTime = seconds;
    player.play().catch(() => {});
  }

  togglePlayPause() {
    const player = this.audioPlayerRef?.nativeElement;
    if (!player) return;
    if (this.isPlaying) {
      player.pause();
    } else {
      player.play().catch(() => {});
    }
  }

  onAudioLoaded() {
    const player = this.audioPlayerRef?.nativeElement;
    if (player) this.audioDuration = player.duration || 0;
  }

  onAudioTimeUpdate() {
    const player = this.audioPlayerRef?.nativeElement;
    if (player) {
      this.audioCurrentTime = player.currentTime;
      this.isPlaying = !player.paused;
      this.syncActiveSegment(player.currentTime);
    }
  }

  private syncActiveSegment(time: number) {
    if (!this.segmentos.length) return;
    const idx = this.segmentos.findIndex(s => time >= s.start && time < s.end);
    if (idx !== this.activeSegmentIndex) {
      this.activeSegmentIndex = idx;
      this.cdr.markForCheck();
      // auto-scroll active segment into view
      setTimeout(() => {
        document.querySelector('.seg-row.active')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }, 50);
    }
  }

  onAudioEnded() {
    this.isPlaying = false;
    this.audioCurrentTime = 0;
    this.activeSegmentIndex = -1;
  }

  onProgressChange(event: Event) {
    const input = event.target as HTMLInputElement;
    const player = this.audioPlayerRef?.nativeElement;
    if (player) {
      player.currentTime = parseFloat(input.value);
    }
  }

  setPlaybackRate(rate: number) {
    this.playbackRate = rate;
    const player = this.audioPlayerRef?.nativeElement;
    if (player) player.playbackRate = rate;
  }

  triggerFileInput() {
    this.fileInputNativeRef?.nativeElement.click();
  }

  formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  formatElapsed(): string {
    if (!this.startedAt) return '';
    const secs = (Date.now() - this.startedAt.getTime()) / 1000;
    return this.formatTime(secs);
  }

  // ─── RBAC ───────────────────────────────────────
  get hasUploadPermission(): boolean {
    return this.permissions.includes('UPLOAD_AUDIO');
  }

  get hasEditPermission(): boolean {
    return this.permissions.includes('EDITAR_TERMO');
  }

  get hasPdfPermission(): boolean {
    return this.permissions.includes('GERAR_PDF');
  }

  // ─── Auto-save ──────────────────────────────────
  onResumoChange() {
    if (!this.idDepoimento) return;
    clearTimeout(this.autoSaveTimer);
    this.autoSaveLabel = 'Salvando rascunho...';
    this.autoSaveTimer = setTimeout(() => {
      sessionStorage.setItem(DRAFT_KEY(this.idDepoimento!), this.resumo);
      this.autoSaveLabel = 'Rascunho salvo localmente';
    }, AUTOSAVE_DELAY_MS);
  }

  // ─── PDF generation ─────────────────────────────
  async onGeneratePDF() {
    this.pdfErrorMessage = '';
    this.isGeneratingPdf = true;
    this.pdfUrl = null;
    this.safePdfUrl = null;
    this.pdfGenerationDate = null;

    try {
      await this.api.put(`/termos/${this.idDepoimento}`, {
        txt_editado_humano: this.resumo
      });

      const response = await this.api.post('/pdf/gerar', {
        id_depoimento: this.idDepoimento
      });
      this.pdfHash = response.data.hash_pdf;
      this.pdfUrl = response.data.pdf_url;
      if (this.pdfUrl) {
        this.safePdfUrl = this.isTrustedMinioUrl(this.pdfUrl)
          ? this.sanitizer.bypassSecurityTrustResourceUrl(this.pdfUrl)
          : null;
      }
      this.pdfGenerationDate = new Date();

      if (this.idDepoimento) {
        sessionStorage.removeItem(DRAFT_KEY(this.idDepoimento));
        this.autoSaveLabel = '';
      }

      // Show signature modal instead of success-panel
      this.showSignModal = true;
    } catch (error: any) {
      console.error('Erro ao gerar PDF', error);
      this.pdfErrorMessage = error.response?.data?.detail || 'Erro ao comunicar com o servidor para geração de PDF.';
    } finally {
      this.isGeneratingPdf = false;
    }
  }

  // ─── Upload & polling ───────────────────────────
  ngOnDestroy() {
    this.stopPolling();
    clearTimeout(this.autoSaveTimer);
  }

  onFileSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.file = event.target.files[0];
      this.fileName = this.file!.name;
    }
  }

  async onUpload() {
    if (!this.file) {
      alert('Selecione um arquivo de áudio primeiro!');
      return;
    }

    this.isUploading = true;
    this.resetWorkspaceState();
    const formData = new FormData();
    formData.append('file', this.file);
    if (this.idDepoimento) {
      formData.append('id_depoimento', this.idDepoimento);
    }

    try {
      const response = await this.api.post('/upload/audio', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      this.jobId = response.data.id_job;
      if (this.idDepoimento && this.jobId) sessionStorage.setItem('job_' + this.idDepoimento, this.jobId);
      this.status = response.data.status;
      this.startedAt = new Date();
      this.startPolling();
    } catch (error) {
      console.error('Erro no upload', error);
      alert('Erro ao enviar o arquivo.');
    } finally {
      this.isUploading = false;
    }
  }

  startPolling() {
    this.pollDelay = 2000;
    this.scheduleNextPoll();
  }

  private scheduleNextPoll() {
    this.intervalId = setTimeout(async () => {
      if (!this.jobId) return;
      try {
        const response = await this.api.get(`/jobs/${this.jobId}`);
        this.status = response.data.status;
        if (this.status === 'Concluído') {
          this.stopPolling();
          await this.fetchResult();
          return;
        } else if (this.status === 'Erro') {
          this.stopPolling();
          return;
        }
      } catch (error) {
        console.error('Erro ao buscar status', error);
      }
      this.pollDelay = Math.min(this.pollDelay * 2, 30000);
      this.scheduleNextPoll();
    }, this.pollDelay);
  }

  stopPolling() {
    if (this.intervalId) {
      clearTimeout(this.intervalId);
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
        const draft = this.idDepoimento ? sessionStorage.getItem(DRAFT_KEY(this.idDepoimento)) : null;
        this.resumo = draft ?? data.txt_editado_humano ?? data.txt_original_ia ?? 'Sem resumo gerado.';
        if (draft) this.autoSaveLabel = 'Rascunho local restaurado';
      }

      if (this.idDepoimento) {
        try {
          const termoRes = await this.api.get(`/termos/${this.idDepoimento}`);
          this.applyTermo(termoRes.data);
        } catch { /* segments unavailable */ }
      }

      if (audioRes.status === 'fulfilled') {
        this.audioUrl = audioRes.value.data.audio_url;
      }
    } catch (error) {
      console.error('Erro ao buscar resultado final', error);
    }
  }

  // ─── NER highlight ──────────────────────────────
  highlightEntitiesInText(text: string): SafeHtml {
    const allEntities = Object.values(this.nerEntities).flat().filter(e => e && e.trim().length > 1);
    if (!allEntities.length) {
      return this.sanitizer.bypassSecurityTrustHtml(this.escapeHtml(text));
    }
    const sorted = [...allEntities].sort((a, b) => b.length - a.length);
    let result = this.escapeHtml(text);
    for (const entity of sorted) {
      const escapedEntity = this.escapeHtml(entity);
      const pattern = escapedEntity.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      result = result.replace(new RegExp('\\b' + pattern + '\\b', 'gi'), '<mark class="ner-highlight">$&</mark>');
    }
    return this.sanitizer.bypassSecurityTrustHtml(result);
  }

  private isTrustedMinioUrl(url: string): boolean {
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') return false;
      return environment.minioAllowedHosts.includes(parsed.host);
    } catch {
      return false;
    }
  }

  private escapeHtml(s: string): string {
    return s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ─── Speaker role reclassification ─────────────
  onSpeakerSampleSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    this.speakerSampleFile = input.files?.[0] ?? null;
  }

  async onReclassifySpeakers() {
    if (!this.idDepoimento) return;
    this.speakerReclassifyStatus = 'loading';
    this.speakerReclassifyMessage = '';
    try {
      const formData = new FormData();
      if (this.speakerSampleFile) {
        formData.append('file', this.speakerSampleFile);
      }
      const res = await this.api.post(
        `/termos/${this.idDepoimento}/reclassify-speakers`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      this.segmentos = res.data.segmentos_asr ?? this.segmentos;
      this.speakerReclassifyStatus = 'done';
      this.speakerReclassifyMessage = 'Falantes reclassificados com sucesso.';
    } catch (err: any) {
      this.speakerReclassifyStatus = 'error';
      this.speakerReclassifyMessage = err.response?.data?.detail ?? 'Erro ao reclassificar falantes.';
    }
  }

  get hasUnknownSpeakers(): boolean {
    return this.segmentos.some(s => s.speaker === 'Desconhecido');
  }

  // ─── Identificação manual de falantes (ouvir amostra + rotular) ──
  playSpeakerSample(label: string) {
    const sp = this.speakers.find(s => s.label === label);
    if (sp) this.seekTo(sp.sampleStart);
  }

  async applySpeakers() {
    if (!this.idDepoimento || this.assinado) return;
    this.isApplyingSpeakers = true;
    try {
      const mapping: Record<string, { role: string; nome: string | null }> = {};
      for (const s of this.speakers) {
        mapping[s.label] = { role: s.role, nome: s.nome?.trim() || null };
      }
      const res = await this.api.post(`/termos/${this.idDepoimento}/speakers`, { mapping });
      this.applyTermo(res.data);
      this.speakerReclassifyStatus = 'done';
      this.speakerReclassifyMessage = 'Falantes identificados e aplicados.';
    } catch (err: any) {
      this.speakerReclassifyStatus = 'error';
      this.speakerReclassifyMessage = err.response?.data?.detail ?? 'Erro ao aplicar identificação.';
    } finally {
      this.isApplyingSpeakers = false;
    }
  }

  // ─── Reprocessar (somente em Erro) ──────────────
  async reprocessar() {
    if (!this.jobId || this.status !== 'Erro' || this.assinado) return;
    this.isReprocessing = true;
    try {
      const res = await this.api.post(`/jobs/${this.jobId}/reprocessar`, {});
      this.status = res.data.status;
      this.startedAt = new Date();
      this.startPolling();
    } catch (err: any) {
      alert(err.response?.data?.detail ?? 'Erro ao reprocessar.');
    } finally {
      this.isReprocessing = false;
    }
  }

  // ─── NER entity list for sidebar ────────────────
  get entityList(): { type: string; label: string; low: boolean }[] {
    const result: { type: string; label: string; low: boolean }[] = [];
    for (const [type, labels] of Object.entries(this.nerEntities)) {
      for (const label of labels) {
        result.push({ type, label, low: false });
      }
    }
    return result;
  }

  // ─── Keyboard shortcut ──────────────────────────
  @HostListener('document:keydown.control.enter')
  async onCtrlEnter() {
    if (this.revisaoAceita && this.hasPdfPermission && this.status === 'Concluído' && !this.isGeneratingPdf) {
      await this.onGeneratePDF();
    }
  }

  getStatusColor(): string {
    switch (this.status) {
      case 'Concluído': return 'var(--color-success)';
      case 'Erro': return 'var(--color-accent)';
      case 'Transcrevendo':
      case 'Extraindo Dados':
      case 'Gerando Resumo':
      case 'Processando': return '#D69E2E';
      default: return 'var(--color-secondary)';
    }
  }

  voltar() {
    this.router.navigate(['/processos']);
  }

  async descartarProcesso() {
    if (!this.idDepoimento) return;
    const ok = confirm(
      'Descartar este processo?\n\n' +
      'O processo NÃO será apagado — ele permanece no registro, apenas marcado como ' +
      'descartado e oculto da lista padrão. Deseja continuar?'
    );
    if (!ok) return;
    this.isDescartando = true;
    try {
      await this.api.put(`/processos/${this.idDepoimento}/descartar`, {});
      this.router.navigate(['/processos']);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Erro ao descartar o processo.');
    } finally {
      this.isDescartando = false;
    }
  }

  get permissionWarnings(): string[] {
    const w: string[] = [];
    if (!this.hasUploadPermission) w.push('Upload de Áudio (UPLOAD_AUDIO)');
    if (!this.hasEditPermission)   w.push('Edição do Termo (EDITAR_TERMO)');
    if (!this.hasPdfPermission)    w.push('Geração de PDF (GERAR_PDF)');
    return w;
  }
}
