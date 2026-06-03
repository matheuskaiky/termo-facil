import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

interface ModelOption { id: string; label: string; tipo: string | null; recurso: string | null; available?: boolean; motivo?: string; }
interface Catalogo { asr: ModelOption[]; ner: ModelOption[]; llm: ModelOption[]; diarizacao: ModelOption[]; }

const RUNNING = ['Pendente', 'Transcrevendo', 'Extraindo Dados', 'Gerando Resumo', 'Processando'];

@Component({
  selector: 'app-dev-debug',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dev-debug.component.html',
  styleUrls: ['./dev-debug.component.css'],
})
export class DevDebugComponent implements OnInit, OnDestroy {
  testes: any[] = [];
  catalogo: Catalogo | null = null;
  health: any = null;

  // criar teste
  novoNome = '';
  novoFile: File | null = null;
  isCriandoTeste = false;

  // teste selecionado
  selected: any = null;
  processamentos: any[] = [];

  // form de processamento
  form = { asr_model: 'whisper-base', ner_model: 'lener-br', llm_model: 'skip', diarizacao: 'heuristic' };
  isCriandoProc = false;

  mensagem = '';
  erro = '';
  private pollTimer: any = null;

  constructor(private api: ApiService, private router: Router) {}

  async ngOnInit() {
    await Promise.all([this.loadTestes(), this.loadCatalogo()]);
  }

  ngOnDestroy() { clearTimeout(this.pollTimer); }

  async loadCatalogo() {
    try {
      const res = await this.api.get('/models/available');
      this.catalogo = res.data.catalogo;
      this.health = res.data.health;
      // default do LLM = primeiro disponível (ou skip)
      const llm = this.catalogo?.llm?.find(o => o.id !== 'skip');
      if (llm) this.form.llm_model = llm.id;
    } catch (e: any) {
      this.erro = e.response?.data?.detail || 'Erro ao carregar modelos.';
    }
  }

  async loadTestes() {
    try {
      this.testes = (await this.api.get('/debug/testes')).data ?? [];
    } catch { this.testes = []; }
  }

  onFileSelected(event: any) {
    this.novoFile = event.target.files?.[0] ?? null;
  }

  async criarTeste() {
    if (!this.novoNome.trim() || !this.novoFile) { this.erro = 'Informe nome e áudio.'; return; }
    this.isCriandoTeste = true; this.erro = '';
    try {
      const fd = new FormData();
      fd.append('nome', this.novoNome.trim());
      fd.append('file', this.novoFile);
      const res = await this.api.post('/debug/testes', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      this.novoNome = ''; this.novoFile = null;
      this.mensagem = 'Teste criado.';
      await this.loadTestes();
      await this.selectTeste(res.data.id_teste);
    } catch (e: any) {
      this.erro = e.response?.data?.detail || 'Erro ao criar teste.';
    } finally { this.isCriandoTeste = false; }
  }

  async selectTeste(id: string) {
    try {
      const res = await this.api.get(`/debug/testes/${id}`);
      this.selected = res.data;
      this.processamentos = res.data.processamentos ?? [];
      this.schedulePollIfRunning();
    } catch (e: any) {
      this.erro = e.response?.data?.detail || 'Erro ao carregar teste.';
    }
  }

  async criarProcessamento() {
    if (!this.selected) return;
    this.isCriandoProc = true; this.erro = '';
    try {
      await this.api.post(`/debug/testes/${this.selected.id_teste}/processamentos`, this.form);
      this.mensagem = 'Processamento enfileirado.';
      await this.selectTeste(this.selected.id_teste);
    } catch (e: any) {
      this.erro = e.response?.data?.detail || 'Erro ao criar processamento.';
    } finally { this.isCriandoProc = false; }
  }

  private schedulePollIfRunning() {
    clearTimeout(this.pollTimer);
    if (this.processamentos.some(p => RUNNING.includes(p.status))) {
      this.pollTimer = setTimeout(() => this.selected && this.selectTeste(this.selected.id_teste), 3000);
    }
  }

  abrirDetalhe(proc: any) {
    if (proc.status !== 'Concluído') return;
    this.router.navigate(['/dev-debug/processamento', proc.id_processamento]);
  }

  async exportarCsv() {
    if (!this.selected) return;
    try {
      const res = await this.api.get(`/debug/testes/${this.selected.id_teste}/export.csv`);
      const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `teste_${this.selected.nome || 'debug'}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      this.erro = e.response?.data?.detail || 'Erro ao exportar CSV.';
    }
  }

  fmtMs(ms: number | null): string {
    if (ms === null || ms === undefined) return '—';
    return `${(ms / 1000).toFixed(1).replace('.', ',')} s`;
  }

  fmtPct(v: number | null): string {
    return (v === null || v === undefined) ? '—' : `${v.toFixed(1)}%`;
  }

  statusClass(status: string): string {
    if (status === 'Concluído') return 'st-ok';
    if (status === 'Erro') return 'st-err';
    return 'st-run';
  }
}
