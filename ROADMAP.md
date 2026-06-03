# Roadmap Técnico — Termo Fácil (SSP-PI)

> Este documento é o **mapa de evolução oficial do projeto**. Cada fase representa um bloco coeso de funcionalidades que transforma o sistema de um MVP simulado em uma plataforma de produção real. As fases devem ser executadas em ordem, pois há dependências entre elas.
>
> **Como manter este documento:** Ao finalizar uma fase, mova-a para a seção `## ✅ Fases Concluídas` no fim do arquivo e registre a data de conclusão. Ao iniciar uma nova fase, abra as issues correspondentes no GitHub seguindo o padrão de `PADROES_CONTRIBUICAO.md`.

---

## 📦 Estado Atual do Sistema

| Camada | Tecnologia | Status |
|---|---|---|
| **API** | FastAPI + Uvicorn | ✅ Funcional |
| **Banco de Dados** | PostgreSQL 15 + SQLAlchemy | ✅ Funcional |
| **Fila de Tarefas** | Celery + Redis | ✅ Funcional |
| **Armazenamento de Mídias** | MinIO (S3-compatível) | ✅ Funcional |
| **Frontend** | Angular 17 (standalone) | ✅ Funcional |
| **RBAC** | Permissões por Cargo (dinâmicas) | ✅ Funcional |
| **Pipeline de IA** | Whisper + LeNER-Br + Ollama | ✅ Código completo; modelos testados (NCAD UFPI como ambiente paliativo de luxo enquanto Mandu não está disponível) |
| **Geração de PDF** | ReportLab + MinIO Presigned URLs | ✅ Funcional |
| **Autenticação** | JWT (bcrypt + HS256) | ✅ Funcional |
| **Gestão de Senhas** | Reset com senha temporária + troca obrigatória | ✅ Funcional |
| **Revisão Human-in-the-Loop** | Split-screen + auto-save + aceite de responsabilidade | ✅ Funcional |
| **Ancoragem Factual LLM** | NER injeta entidades no prompt, top_p=0.1 | ✅ Funcional |
| **Diarização / Timestamps** | Segmentos Whisper + heurística de locutor + player sincronizado | ✅ Funcional (heurística; PyAnnote planejado para HPC) |
| **PDF Híbrido (Anexo + Disclaimer)** | Resumo + transcrição literal anexa + rodapé RN-02 | ✅ Funcional |
| **Dashboard de Métricas (ROI)** | Volumetria sem dados sigilosos | ✅ Funcional |
| **Expurgo LGPD (Retenção Volátil)** | Apagar áudio/rascunhos após exportação | ✅ Funcional (imediato + Celery Beat fallback) |

### ⚠️ Notas de Configuração dos Modelos de IA

O pipeline de IA está **implementado no código** mas depende de serviços externos para funcionar de ponta a ponta:

| Componente | Configuração `.env` | Pré-requisito para funcionar |
|---|---|---|
| **ASR (Whisper)** | `WHISPER_MODEL_SIZE=base` | `openai-whisper` instalado no venv; download automático do modelo `base` (~140MB) no primeiro `transcribe()` |
| **NER (LeNER-Br)** | `NER_MODEL_NAME=alfaneo/lener_br` | `transformers` + `torch` instalados; download automático do HuggingFace (~1.3GB) no primeiro `extract_entities()` |
| **LLM (Ollama)** | `LLM_BASE_URL=http://localhost:11434` / `LLM_MODEL_NAME=llama3` | Ollama precisa estar rodando (`ollama serve`) com o modelo baixado (`ollama pull llama3`) |

---

## 🗺️ Fases Planejadas (Backlog Técnico)

> As fases abaixo derivam diretamente dos requisitos em `arquivos-projeto/` (ERSW e Backlog). **Importante:** abrir as issues no GitHub somente ao **iniciar** a fase correspondente — não converter este planejamento em issues antecipadamente.

### Redesign Frontend v2 — UI/UX Profissional
> **Nota:** Esta fase é um grande refactoring que ocorreu durante a Fase 21 e a interrompeu. Focou em elevar a maturidade visual e usabilidade do sistema para o padrão institucional esperado na SSP-PI.

**Issues #55–#68**

- `[FEATURE]` ✅ Tokens de design e componentes base compartilhados (Pipeline Stepper, KPI Card, Chips)
- `[FEATURE]` ✅ Redesign da tela de auditoria: remoção de overlay bloqueante e sidebar de entidades NER
- `[FEATURE]` ✅ Redesenho da lista de processos: substituição da tabela densa por linhas-cartão, KPIs e chips de filtro
- `[FEATURE]` ✅ Tela dedicada para cadastro e edição de processo com layout em 3 colunas
- `[FEATURE]` ✅ Redesign do painel admin de RBAC: drawer de detalhes e matriz cruzada de permissões
- `[FEATURE]` ✅ Redesign da tela de métricas para Dashboard completo com gráficos
- `[FEATURE]` ✅ Modal de assinatura digital para o PDF híbrido com apelo jurídico (SHA-256)
- `[FEATURE]` ✅ Redesign institucional em split-screen para a tela de login
- `[FEATURE]` ✅ Player de áudio persistente no rodapé da página e polimentos no header
- `[FEATURE]` ✅ Gerenciamento e CRUD de Delegacias — frontend completo (`DelegaciaFormComponent`); backend pendente (IC-1: migration de campos extras necessária)
- `[FEATURE]` ✅ Cadastro e Edição de Servidor com validações assíncronas — frontend completo (`UserFormComponent`); backend pendente (IC-2/IC-5: `POST /admin/users`, `check-cpf`, `check-matricula`, campos `email`/`cpf`/`ativo`)
- `[FEATURE]` ✅ Cadastro de depoente com fluxo CPF-first — frontend completo (state machine `empty→checking→found/not-found`); backend pendente (IC-3/IC-4: `GET /depoentes/check-cpf`, `id_depoente` em `processos/novo`)
- `[FEATURE]` ✅ Dashboard segmentado e drill-downs por delegacia/escrivão/erros — frontend completo (3 novos componentes + seletor de segmento); backend pendente (`/metricas/por-delegacia`, `/metricas/delegacias/:id`, `/metricas/escrivaes/:id`, `/metricas/erros`, `/jobs/:id/retry`)
- `[FEATURE]` ✅ Descrições humanas nas permissões de RBAC — `permDescricao()` no admin, `adm-matrix-perm-desc`, `adm-cb-desc`, chips com hint no drawer


---

### Pendências Isoladas (Pós-Fase 23)

**Issue #36 — `[FEATURE]` Diarização real via PyAnnote (quando HPC Mandu ou cluster NCAD UFPI estiver disponível)**
- Substituir heurística de pausa > 1.0s por PyAnnote speaker diarization
- Manter a heurística como fallback quando PyAnnote não está disponível (`PYANNOTE_ENABLED=false` no `.env`)
- Estratégia de integração: PyAnnote identifica segmentos de speaker no áudio; word-level alignment com timestamps do Whisper associa cada palavra ao speaker (pipeline semelhante ao `whisperx`)
- Criar `PyAnnoteDiarizer` como serviço separado, desacoplado do `WhisperASRModel` — `_assign_speakers` em `asr_service.py` permanece como fallback
- Pré-requisito: token HuggingFace (pyannote/speaker-diarization-3.1 requer aceitação de licença); `pyannote.audio` + `torch` CUDA no ambiente HPC
- Depende do acesso ao HPC Mandu (opção primária) ou à fatia de processamento nas GPUs NVIDIA L4 do cluster NCAD da UFPI (alternativa de luxo)

**Issue #37 — `[FEATURE]` Migração de Ollama para vLLM em produção (HPC Mandu)**
- ADR-002 já documenta vLLM como servidor preferido de produção — Ollama permanece para desenvolvimento local
- Criar `VllmLLM` implementando o Protocol `LLMModel` em `llm_service.py`, apontando para `/v1/completions` (API OpenAI-compatível do vLLM) — sem alterar a interface da task Celery
- Configurar container vLLM com CUDA alinhado ao driver da GPU A100 do HPC Mandu
- Baixar modelo de produção escolhido pós-benchmarks da Fase 20 (candidatos: Llama3 8B/70B, Mistral, Qwen)
- Ativar com `LLM_BASE_URL` apontando para o vLLM e `LLM_PROVIDER=vllm` no `.env`
- Depende de: acesso ao HPC Mandu ou cluster NCAD UFPI

**Issue #38 — `[FEATURE]` Modelo ASR de alta precisão: Whisper Large-v3-Turbo ou Parakeet TDT (HPC)**
- Whisper `base` (~74 M params) foi usado por restrição de recursos em dev; GPU A100 do HPC Mandu permite modelos maiores
- Candidatos: `whisper-large-v3-turbo` (~800 M params, ~5× melhor WER que `base` com latência aceitável) e NVIDIA Parakeet TDT (modelo nativo PT-BR, competitivo em WER para português)
- Criar `ParakeetASRModel` implementando o Protocol `ASRModel` — troca é transparente ao pipeline (`asr_model` em `process_audio.py` não muda)
- Ativar com `WHISPER_MODEL_SIZE=large-v3-turbo` ou `ASR_PROVIDER=parakeet` no `.env`
- Depende de: acesso HPC Mandu / NCAD UFPI e benchmarks WER comparativos (Fase 20 fornece baseline)

---

## 📋 Planejamento de Issues para GitHub

| Issue | Fase | Tipo | Prioridade | Status |
|---|---|---|---|---|
| #55–#68 | Redesign v2 | FEATURE | 🔴 Alta | ✅ Fechadas |
| #39–#47 | Fase 22 | FIX | 🔴 Alta | ✅ Fechadas (resolvidas na Fase 24) |
| #49–#53 | Fase 23 | FIX/FEATURE | 🟡 Média | ✅ Fechadas (resolvidas na Fase 24) |
| #48, #54 | Épicos Fase 22/23 | — | — | ⏳ Abertos (todos os filhos concluídos; fechar) |
| #36 | Pendência | FEATURE | 🔵 Baixa | ⏳ Aberta — depende de HPC Mandu / NCAD UFPI |
| #37 | Pendência | FEATURE | 🟡 Média | ⏳ Aberta — HPC Mandu (pós-benchmarks Fase 20) |
| #38 | Pendência | FEATURE | 🟡 Média | ⏳ Aberta — HPC Mandu / NCAD UFPI |

---

## ✅ Fases Concluídas

| Fase | Descrição | Concluída em |
|---|---|---|
| **Fase 6** | Split-screen UI + polling de Jobs + gravação de resultados da IA | Abril/2026 |
| **Fase 7** | RBAC dinâmico (Cargo/Permissão) + Middleware de Autorização + Painel Admin Angular | Maio/2026 |
| **Fase 8** | Geração Real de PDF (ReportLab), Upload no MinIO, Presigned URLs e Preview | Maio/2026 |
| **Fase 9** | Pipeline de IA Real: Whisper (ASR) + LeNER-Br (NER) + Ollama (LLM) + Abstração de Storage | Maio/2026 |
| **Fase 10** | Autenticação Real com JWT: login, authGuard, interceptor Axios, remoção do simulador | Maio/2026 |
| **Fase 11** | Gestão de Senhas: reset com senha temporária (`secrets`), `must_change_password`, troca obrigatória no próximo login | Maio/2026 |
| **Fase 12** | Fechamento do Loop Humano: persistência da edição, checkbox de responsabilidade (RN-03), auto-save no localStorage (RNF-04), remoção de mocks | Maio/2026 |
| **Fase 13** | Ancoragem Factual no LLM: injeção do dicionário NER no prompt, `top_p=0.1`, instrução de `[(Trecho Ininteligível)]` | Maio/2026 |
| **Fase 14** | Diarização e Timestamps: segmentos Whisper com heurística de locutor, coluna `segmentos_asr` JSONB, player de áudio e blocos clicáveis sincronizados | Maio/2026 |
| **Fase 15** | PDF Híbrido Auditável: rodapé RN-02 em todas as páginas, metadados ASR/LLM, Anexo I com transcrição literal + timestamps (Parte 2 de 2) | Maio/2026 |
| **Fase 16** | Dashboard de Métricas / ROI: endpoint `GET /metricas` com `VER_METRICAS`, cargo "Gestor Estratégico", componente Angular de cards de volumetria | Maio/2026 |
| **Fase 17** | Governança de Dados LGPD (RN-04): expurgo imediato pós-PDF (`pdf.py`) + Celery Beat fallback horário (`expurgo_dados_expirados`), timestamp `data_exportacao_pdf` em `TermosFinais`, destaque NER no frontend | Maio/2026 |
| **Fase 18** | Hardening de Produção: `.opus` + limite 200 MB no upload, status granular do Job (RF-01), fallbacks de dev desabilitáveis via `APP_ENV=production` | Maio/2026 |
| **Fase 19** | Formulário Real de Autuação, Sincronização do DER e Ajuste de Metadados de IA no Seed | Maio/2026 |
| **Fase 20** | Validação Científica & Benchmarking (DoD PIBITI): WER, F1-Score e Comparativo LLM | Maio/2026 |
| **Fase 21** | Polimento Final & Testes Integrados: Blindagem de segurança, Resiliência de Infra | Maio/2026 |
| **Fase 22** | Hardening de Segurança e RBAC: ✅ concluída (frontend #42–#47; backend #39–#41 resolvido na Fase 24) | Maio/2026 |
| **Fase 23** | Paginação e Resiliência: ✅ concluída (frontend #49; backend #50–#53 resolvido na Fase 24) | Maio/2026 |
| **Extra** | Edição de nome do cargo no painel admin (feature adicional) | Maio/2026 |
| **Extra** | Auditoria de Segurança & Hardening: Correção de 8 vulnerabilidades críticas e altas (C-1 a C-6, A-1 a A-8) | Maio/2026 |
| **Fase 24** | Hardening Completo — LGPD + SOLID: C-4, A-9, M-1 a M-16, B-2 a B-8 (must_change_password server-side, audit log LGPD Art. 37, minimização NER/ASR, CPF masking, rate limiting, decomposição pdf_service, Protocols em ports.py, lazy loading IA, Pydantic v2 config) | Maio/2026 |
| **Extra** | PixIT Speech Separation + Identificação Automática de Falantes: substituição do diarizador simples pelo `pyannote/speech-separation-ami-1.0` para resolução de Overlapped Speech; `SpeakerRoleResolver` (`TextBasedRoleResolver` + `AudioBasedRoleResolver`); mitigação de alucinação Whisper via `avg_logprob` + `compression_ratio`; endpoint `POST /termos/{id}/reclassify-speakers`; `DIARIZATION_PROVIDER` e `LLM_PROVIDER` configuráveis | Maio/2026 |
| **Fase 25** | Suíte de Testes Abrangente + Benchmarks Reais + CI/CD: 125 testes pytest (82% cobertura), modo real-vs-mock (`TEST_AI_MODE`), specs Angular (guards/AuthService), GitHub Actions (`.github/workflows/ci.yml`); benchmarks da Fase 20 reescritos e **executados de verdade** (WER/RTF Whisper, F1 LeNER 90,9%); **2 bugs reais corrigidos** (upload `async for` quebrado, expurgo LGPD com coluna `NOT NULL`). Ver [`TESTES.md`](TESTES.md) | Junho/2026 |
| **Fase 26** | Correções de Auditoria + RBAC: instrumentação de tempos do pipeline (ASR/NER/LLM/total ms) persistidos em `TermosFinais` e expostos em `/termos` + `/metricas`; auditoria com KPIs de tempo, limpeza de estado no re-upload e transcrição em largura cheia; **cargo Admin imutável e onipotente** (anti-lockout por construção); permissão `ACESSAR_DEV_DEBUG`; documentação de ativação do PixIT | Junho/2026 |
| **Fase 27** | Módulo Dev/Debug (benchmark de modelos): catálogo separado + health-check (`debug_models.py`), tabelas dedicadas `TesteIA`/`ProcessamentoTeste`, pipeline parametrizado via `run_pipeline` + factories `build_asr/ner/llm` + task `run_debug_processing` (Skip por etapa), endpoints `/debug/*` e `/models/available` (gate `ACESSAR_DEV_DEBUG`), export CSV, reuso da auditoria read-only. 167 testes. Ver [`TESTES.md`](TESTES.md) | Junho/2026 |

### 📝 Notas de Desenvolvimento (Intercorrências)
- **Fase 15 (RF-06, RN-02):**
  - *Rodapé RN-02:* implementado via callback `_build_footer_drawer()` passado como `onFirstPage`/`onLaterPages` ao `doc.build()` do Platypus. Desenha o texto *"Documento gerado com assistência de Inteligência Artificial e revisado por autoridade policial"* centralizado e número de página à direita em cada folha.
  - *Rastreabilidade:* duas novas linhas na tabela de metadados do PDF — "Modelos IA (ASR / LLM)" (lidos de `job.modelo_asr.nome_modelo` / `job.modelo_llm.nome_modelo`) e "Documento gerado em" (datetime de geração).
  - *Anexo I (Parte 2):* `PageBreak` após as assinaturas inicia a segunda parte. Se `segmentos_asr` estiver preenchido, cada segmento é renderizado como `[MM:SS] Speaker: texto` com `html.escape()` para evitar erros de XML no Platypus. Fallback para `txt_literal_asr` plano quando não há segmentos.
  - *Frontend:* a constraint "PDF oculto até clicar em Gerar" mantida — o `safePdfUrl` permanece `null` no carregamento da página e só é preenchido em `onGeneratePDF()`. Badge informativo e label de download atualizados para refletir o formato híbrido.
- **Fase 8:**
  - *Backend:* Conflito de Chave Primária (`IntegrityError`) ao tentar fazer upload de múltiplos áudios para o mesmo `id_depoimento`. Resolvido implementando lógica de upsert (Update se existe, Insert se não existe) na tabela `midia_bruta`.
  - *Frontend:* Bloqueio de segurança do Angular (XSS) ao tentar injetar a Presigned URL do MinIO dinamicamente no `<iframe>`. Resolvido injetando e utilizando o serviço `DomSanitizer` (`bypassSecurityTrustResourceUrl`).
- **Fase 9 (Issues #10 e #11):**
  - *Refactor:* Introduzida camada de abstração `FileStorage` (`storage_service.py`) com instâncias dedicadas `audio_storage` e `pdf_storage`. Endpoints (`upload.py`, `pdf.py`) e a task Celery passaram a depender da abstração, não do `MinioService` diretamente. O `storage_path` no banco passou a armazenar apenas a chave lógica do objeto (sem prefixo `s3://`), eliminando acoplamento do provider nos dados persistidos.
  - *Arquitetura ASR:* `asr_service.py` implementado com `ASRModel` Protocol e `WhisperASRModel`. Modelo Whisper cacheado por `model_size` no startup do worker Celery via `_model_cache`, evitando recarga a cada job.
  - *Arquitetura LLM:* `llm_service.py` implementado com `LLMModel` Protocol e `OllamaLLM`. Temperatura `0.0` para saída determinística. Troca de Ollama para vLLM em produção requer apenas mudança em `LLM_BASE_URL`.
- **Fase 9 (Issue #12):**
  - *Arquitetura NER:* `ner_service.py` implementado com `NERModel` Protocol e `LeNERModel`. Usa `pipeline("ner", aggregation_strategy="first")` do HuggingFace — `"first"` agrega tokens `##` no nível de palavra antes do agrupamento de entidades, evitando artefatos de subwords que `"simple"` produzia. Texto dividido em chunks por sentença (≤200 palavras) para respeitar o limite de 512 tokens do BERT. Deduplicação por subsunção mantém apenas a forma mais longa de cada entidade.
- **Fase 10 (Issues #14 e #15):**
  - *Schema migration:* `senha_hash` e `data_criacao` adicionados ao banco via `scripts/migrate.py` (idempotente, `ADD COLUMN IF NOT EXISTS`). `seed_db.py` chama `migrate.py` automaticamente.
  - *Timing attack:* `verificar_senha` em `security.py` sempre executa o bcrypt mesmo quando o usuário não existe (`_DUMMY_HASH` gerado no startup), impedindo enumeração de usuários por tempo de resposta (OWASP A07).
  - *JWT payload:* inclui `sub`, `nome`, `matricula`, `cargo`, `permissoes`, `exp` — header Angular decodifica localmente sem roundtrip ao backend.
  - *Fallbacks de dev:* `X-User-Id` e "primeiro usuário do banco" mantidos em `deps.py` durante desenvolvimento. Devem ser desabilitados via env `APP_ENV=production` antes da implantação piloto.
  - *`permission.guard.ts`:* refatorado para ler permissões do JWT local (sem chamada extra a `/auth/me`).
- **Fase 11 (Issues #16 e #17):**
  - *Senha temporária:* gerada com `secrets.choice` (entropia do SO) em `admin.py`, retornada em plaintext **uma única vez** e nunca persistida sem hash. Flag `must_change_password` força a troca no próximo login via `authGuard`.
  - *Bug de path param UUID:* rotas admin (`reset-password`, `cargo`, `permissions`) recebiam `user_id: uuid.UUID` e a query retornava `None`. Corrigido recebendo `str` e convertendo manualmente com `uuid.UUID(...)`, eliminando a coerção implícita do FastAPI/SQLAlchemy.
- **Fases 12 e 13 (Issues #18–#21):**
  - *Loop Humano (Fase 12):* `PUT /termos/{id}` persiste `txt_editado_humano`; `GET /termos/{id}` restaura o estado completo ao reabrir. `AuditoriaComponent` refatorado: `/auth/me` substituído por leitura JWT local (`AuthService`), `mock_ids.json` removido — `upload.py` resolve os modelos pelo DB automaticamente (primeiro ASR/LLM disponível). Checkbox "Declaro que revisei o conteúdo" (RN-03) bloqueia o botão de gerar PDF. Auto-save com debounce de 1,5s no `localStorage` (chave `rascunho_${id}`), com restauração na abertura e limpeza após geração do PDF.
  - *Ancoragem Factual (Fase 13):* `llm_service.synthesize()` aceita `entities: dict | None`; quando presente, serializa o dicionário NER como bloco JSON no prompt com instrução de uso exclusivo dos fatos. `top_p=0.1` adicionado às `options` do Ollama. Instrução de `[(Trecho Ininteligível)]` incluída no `_SYSTEM_PROMPT`. `process_audio.py` passa `entities=entities` ao LLM.
  - *Bug `colors`:* `pdf_service.py` importava `colors` de `reportlab.lib` implicitamente — adicionado `from reportlab.lib import colors` explicitamente. Sem este fix, toda geração de PDF lançava `NameError` em runtime.
- **Fase 14 (Issues #22 e #23):**
  - *ASR Segments:* `asr_service.transcribe()` agora retorna `list[dict]` com `{start, end, text, speaker}` usando `result["segments"]` do Whisper. O texto plano (`" ".join(seg["text"])`) continua sendo passado para NER e LLM.
  - *Heurística de locutor:* função `_assign_speakers` alterna entre "Inquiridor" e "Depoente" sempre que a pausa entre segmentos consecutivos ultrapassa 1,0s. É um placeholder — substituir por PyAnnote quando o HPC Mandu (ou a fatia do NCAD UFPI) estiver disponível.
  - *Persistência:* nova coluna `segmentos_asr JSONB` em `termos_finais` (migration idempotente adicionada a `migrate.py`). `process_audio.py` armazena os segmentos no `TermosFinais`.
  - *Endpoint de áudio:* `GET /audio/{id_depoimento}` retorna presigned URL MinIO de 1h para o arquivo bruto. Novo router registrado em `api.py`.
  - *Frontend:* `AuditoriaComponent` carrega URL de áudio e segmentos em paralelo (`Promise.allSettled`) no `loadExistingTermo` e no `fetchResult`. Player `<audio>` com controles nativos exibido acima da transcrição. Cada segmento renderizado como bloco com botão de timestamp (formato MM:SS) que dispara `seekTo(seg.start)` → `audioElement.currentTime = start; play()`. Fallback para `<pre>` quando os segmentos não estão disponíveis (áudios processados antes desta fase).
- **Fases 16 e 17 (Métricas + Expurgo LGPD):**
  - *Expurgo duplo-camada:* `pdf.py` deleta o áudio do MinIO imediatamente após o `db.commit()` que salva `hash_pdf`. A task `expurgo_dados_expirados` (Celery Beat, `crontab(minute=0)`) verifica a cada hora registros com `data_exportacao_pdf < utcnow() - 24h` que ainda têm `storage_path` preenchido — fallback para falhas transitórias de rede. A coluna `data_exportacao_pdf TIMESTAMP` em `termos_finais` é o elo entre os dois mecanismos.
  - *NER highlight:* `highlightEntitiesInText()` no `AuditoriaComponent` aplica `<mark class="ner-highlight">` (token `#FEEBC8`) às entidades do dicionário NER na transcrição segmentada. Entidades ordenadas da mais longa para a mais curta para evitar sobreposição parcial (e.g. "João Silva" antes de "João"). `escapeHtml()` garante que o texto seja sanitizado antes da injeção via `[innerHTML]`.
  - *Métricas sem conteúdo sigiloso:* `GET /metricas` retorna apenas contagens (`func.count`) e médias; nenhum texto de depoimento ou dado pessoal trafega. A constante `_HORAS_POR_TERMO = 2.5` é a baseline levantada no PIBITI para estimar ROI versus redação manual.
- **Fase 18 (Hardening de Produção):**
  - *Formatos de upload:* `.opus` adicionado aos formatos aceitos (`.wav`, `.mp3`, `.m4a`, `.opus`). Validação de tamanho 200 MB após leitura do conteúdo — `HTTPException 413` se excedido. Upload resiliente (retomada automática, chunked MinIO multipart) deferido para pós-piloto.
  - *Status granular (RF-01):* enum `StatusJob` expandido com `Transcrevendo`, `Extraindo Dados`, `Gerando Resumo`. O valor `Processando` é mantido por compatibilidade com registros legados — o task Celery nunca mais o escreve, mas o banco pode ter registros históricos com este valor. Três `db.commit()` intermediários no `process_audio.py` garantem que o frontend veja cada transição no polling a cada 2s.
  - *Migrations de enum:* `ALTER TYPE status_job_enum ADD VALUE IF NOT EXISTS` para cada novo valor. Compatível com PostgreSQL 15 (suporta `ADD VALUE` em transação desde PG 12).
  - *Fallbacks de dev:* `APP_ENV: str = "development"` adicionado ao `Settings`. Com `APP_ENV=production`, os blocos `X-User-Id` e "primeiro usuário do DB" em `deps.py` levantam HTTP 401 com cabeçalho `WWW-Authenticate: Bearer`. Default `"development"` garante retro-compatibilidade em todos os ambientes existentes sem alteração de `.env`.
- **Fase 19, 20 e 21 (Hardening Final):**
  - Implementação completa do pipeline de criação com formulário e edição de processo de maneira real. Benchmarks devidamente aplicados. Correção das models para uso. Diarização pendente para ativação mediante recurso computacional de hardware em fase subsequente.
- **Redesign Frontend v2 Addon (Issues #64–#68, Maio/2026):**
  - IC-1: `Delegacia` no ORM sem `municipio`, `uf`, `cep`, `telefone`, `tipo`, `ativo` — frontend usa degradação graciosa; backend deve migrar antes da integração real.
  - IC-2: `Usuario` sem `email`, `cpf`, `ativo` — campos opcionais no `UserFormComponent`, payload inclui condicionalmente.
  - IC-3: `Depoente` sem RG, telefone, endereço — CPF-first faz pre-fill parcial de `nome_depoente`; campos extras editáveis.
  - IC-4: `processos/novo` sem suporte a `id_depoente` FK — frontend envia quando disponível; backend deve aceitar opcionalmente.
  - IC-5: Sem `POST /admin/users` — `UserFormComponent` chama o endpoint mas ele ainda não existe; `salvar()` exibirá erro de rede até implementação backend.
  - IC-6: `descricao_permissao` pode estar vazio no DB — frontend renderiza condicionalmente; backend deve popular via seed/UPDATE.
  - Todos os contratos de API gerados estão documentados nos comentários `[BACKEND — advisory]` do plano de implementação.
- **Auditoria de Segurança (Extra, Maio/2026):**
  - *C-1 (Auth bypass prevention):* Inversão de guarda em `deps.py` (linhas 39–40, 54–60): `if settings.APP_ENV not in ("development", "test")` em vez de `== "production"`. Previne bypass acidental em ambientes de staging, homolog, qa ou typos. `X-User-Id` e "primeiro usuário do DB" agora bloqueados com 401 em qualquer ambiente que não seja explicitamente dev/test.
  - *C-2 (Infrastructure hardening):* Docker Compose ports rebindados para `127.0.0.1` (PostgreSQL, Redis, MinIO). Redis adicionado `--requirepass redispassword123` no command. Previne exposição de serviços críticos a redes não-localhost.
  - *C-3 (PDF download auth):* Adicionado `get_current_user` obrigatório em `GET /{job_id}/pdf` (`pdf.py:77`). Verificação de ownership por cargo: Escrivão requer `id_usuario` match, Delegado requer `id_delegacia` match. Sem auth = 403.
  - *C-5 & C-6 (Secrets management):* `JWT_SECRET_KEY` movido para `Settings` (sem default). Removidos defaults de `POSTGRES_PASSWORD`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`. Pydantic-settings agora levanta `ValidationError` no startup se faltarem essas vars — melhor que silenciosamente usar defaults inseguros.
  - *A-1 (IDOR prevention):* Ownership checks adicionados a 4 endpoints: `GET /termos/{id}`, `GET /audio/{id}`, `GET /jobs/{id}`, `POST /pdf/gerar`. Padrão: Escrivão vê apenas seus próprios depoimentos; Delegado vê apenas sua delegacia; Admin vê tudo.
  - *A-2 & A-3 (File upload hardening):* Magic bytes validation (RIFF, ID3, 0xFF 0xFB, OggS) além de extensão. Ownership check no `POST /audio`: Escrivão não pode sobrescrever áudio de outro Escrivão. Valida `Depoimento.id_usuario` (ou `id_delegacia` para Delegado).
  - *A-4 (Permission enforcement):* `POST /processos/novo` adicionado guard `RequirePermission('CRIAR_TERMO')`. Antes, qualquer usuário logado podia criar processo — agora requer permissão explícita.
  - *A-5 (Exception detail leakage):* Removidos `str(e)` de respostas 500 em `pdf.py` (linhas 44, 51, 56) e `processos.py` (linha 132). Substituído por `logger.exception(...)` + genérico "Erro interno. Contate o administrador." Impede vazamento de stack trace, nomes de tabelas, connection strings.
  - *A-7 (Database optimization for security):* Indexes adicionados em `models.py`: `ix_depoimento_id_usuario`, `ix_depoimento_id_inquerito`, `ix_job_id_depoimento`, `ix_termos_id_job`, `ix_termos_data_exportacao`. Unique constraints adicionados em `Cargo.nome_cargo` e `Permissao.nome_permissao` para prevenir race conditions em POST de cargo/permissão.
  - *A-8 (Celery error handling):* `db.rollback()` adicionado antes de `db.commit()` no except de `process_audio.py`. Commit do except agora envolvido em try-except próprio; se falhar, faz segundo `rollback()`. Previne deixar a sessão do pool em estado inválido.
  - *Próximos passos diferidos:* A-6 (requirements.lock via pip freeze — depende de ambiente prod estável), A-9 (MINIO_SECURE=true — depende de cert TLS).
- **Fase 24 — Hardening Completo (Maio/2026):**
  - *C-4 (must_change_password server-side):* `_enforce_password_change()` em `deps.py` bloqueia qualquer endpoint com 403 `password_change_required` quando `must_change_password=True`, exceto `/auth/change-password`. Frontend `api.service.ts` intercepta 403 com esse detail e redireciona para `/change-password`.
  - *A-9 (MinIO HTTPS):* `minio_service.py` agora usa `scheme = "https" if settings.MINIO_SECURE else "http"` eliminando o `http://` hardcoded.
  - *M-9 (CORS lockdown):* `allow_methods` e `allow_headers` substituídos por whitelists explícitas em `main.py`.
  - *M-7 & M-8 (Admin hardening):* `reset_user_password` movido para `reset_router` com `REDEFINIR_SENHA` (permissão agora ativa). Guard de auto-modificação adicionado em `update_user_cargo` e `reset_user_password`.
  - *M-6 (PII fora do JWT):* `nome` e `matricula` removidos do payload JWT. Frontend chama `GET /auth/me` após login e cacheia `user_profile` em sessionStorage separado; `getCurrentUser()` faz merge.
  - *M-5 (Rate limiting):* `slowapi` integrado (`10/min` por IP) em `POST /login`. Limiter extraído para `app/core/rate_limiter.py` evitando circular imports.
  - *M-2 (Audit log LGPD Art. 37):* Model `AuditLog` adicionado; `log_access()` em `app/utils/audit.py` com try-except silencioso. Aplicado em 5 endpoints de dados pessoais.
  - *M-1 (Minimização NER/ASR):* `TermoResumoResponse` (sem NER/ASR) para lista; `TermoDetalheResponse` mantido apenas no endpoint de detalhe.
  - *M-3 (CPF masking):* `mask_cpf()` em `app/utils/formatting.py`. Criptografia at-rest diferida (requer pgcrypto).
  - *M-11 (pdf_service SRP):* Decomposto em `_resolve_metadata()`, `_build_styles()`, `_build_part1_content()`, `_build_part2_transcript()`. HTTPExceptions movidas para endpoint; serviço levanta `DepoimentoNotFoundError`, `TermosNotFoundError`, `TextoAusenteError` (em `app/core/exceptions.py`).
  - *M-12 & B-2:* `apply_depoimento_scope()` em `app/utils/query_scopes.py` centraliza filtro Escrivão/Delegado/Admin. `Permission` class em `app/core/permissions.py` substitui string literals.
  - *M-16:* `datetime.utcnow()` substituído por `datetime.now(timezone.utc)` em `pdf.py` e `expurgo.py`.
  - *B-3:* `CargoUsuario` enum removido. *B-4:* Pydantic v2 `SettingsConfigDict`. *B-5:* Protocols movidos para `app/services/ports.py`. *B-6:* `_LazyWhisperASR` e `_LazyLeNER` diferem carregamento de pesos para o primeiro uso. *B-7:* `Content-Disposition` com aspas em `pdf.py`.
  - *B-8 (Testes):* `test_idor.py` cobre: Escrivão A não acessa termo de Escrivão B (403), acesso ao próprio termo (200), acesso sem auth (401), magic bytes inválidos (415), WAV válido (202), download PDF sem auth (401).
  - *Diferidos:* A-6 (requirements.lock), M-3 encryption at-rest, issues HPC (#36 PyAnnote, #37 vLLM, #38 Whisper Large).
- **PixIT Speech Separation + Identificação Automática de Falantes (Extra, Maio/2026):**
  - *Separação de fontes:* `PyAnnoteSeparationDiarizer` (`diarization_service.py`) carrega `pyannote/speech-separation-ami-1.0` via PixIT; retorna `{"SPEAKER_00": wav, "SPEAKER_01": wav}` — labels neutros, sem mapeamento de papel. A separação física das vozes resolve Overlapped Speech; faixas têm mesma duração do original (silêncio onde o outro locutor fala), preservando timestamps nativamente.
  - *Mitigação de alucinação Whisper:* `transcribe_separated` (`asr_service.py`) filtra segmentos com `avg_logprob < -1.0` ou `compression_ratio > 2.4` antes de incluir no resultado. Três camadas: `no_speech_threshold=0.6` + `avg_logprob` + `compression_ratio`.
  - *Identificação de falantes:* `SpeakerRoleResolver` (`speaker_role_service.py`) atribui papéis após a transcrição. Dois mecanismos: `AudioBasedRoleResolver` (cosine similarity via `pyannote/embedding` com amostras de voz fornecidas pelo usuário) e `TextBasedRoleResolver` (scoring por padrões interrogativos PT-BR, fallback automático). Threshold de confiança: 0.75.
  - *SRP:* o mapeamento `_PYANNOTE_LABEL_MAP` foi removido de `diarize_and_separate` — separação e atribuição de papel são responsabilidades de serviços distintos.
  - *Providers configuráveis:* `DIARIZATION_PROVIDER=heuristic|pyannote` e `LLM_PROVIDER=ollama|vllm` nas variáveis de ambiente.
  - *Endpoint de reclassificação:* `POST /termos/{id}/reclassify-speakers` re-rotula segmentos sem re-executar ASR/NER/LLM; aceita amostra de voz opcional.
- **Auditoria de Sincronização Issues ↔ Código (Junho/2026):**
  - *Intercorrência de tracking:* auditoria do código revelou que as issues #39–#47 (Fase 22) e #49–#53 (Fase 23) permaneciam **abertas** no GitHub e este ROADMAP as marcava como "backend pendente", embora **todas já estivessem implementadas** — o backend foi resolvido pela refatoração da Fase 24 (`apply_depoimento_scope` em `query_scopes.py`, `ALLOWED_ORIGINS` em `config.py:12`, paginação limit/offset+total nos endpoints, `pg_insert().on_conflict_do_update()` em `upload.py`, `server_default=func.now()` em `models.py`, `time_limit`/`soft_time_limit` em `process_audio.py:50`, persistência de erro em `job.parametros_ia['erro']`). As 14 issues foram fechadas com comentário de comprovação (arquivo:linha) para rastreabilidade PIBITI.
  - *Pendência real corrigida (#47):* `isTrustedMinioUrl` (`auditoria.component.ts`) usava *fallbacks* frágeis (regex `host-contains-minio` e pathname `/termos-finais/`) que permitiam bypass da confiança do `DomSanitizer` via host malicioso. Reescrito para whitelist estrita de host via `environment.minioAllowedHosts`.
  - *Lição (gap doc↔código):* concluir a issue no GitHub deve fazer parte do "Definition of Done" de cada fase, não apenas o merge do código — caso contrário o tracker diverge da realidade e induz retrabalho na auditoria.

---

## 📝 Notas de Pesquisa (PIBITI/CNPq)

Extraídas para [`NOTAS_PIBITI.md`](NOTAS_PIBITI.md) para facilitar a citação no relatório de IC.
