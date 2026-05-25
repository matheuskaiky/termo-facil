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
| **Pipeline de IA** | Whisper + LeNER-Br + Ollama | ⚠️ Código completo; modelos configurados no `.env` mas dependem de Ollama rodando localmente e download do LeNER-Br no primeiro uso |
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

**Importante:** o `seed_db.py` insere os modelos no banco como `"Whisper Turbo (Mock)"` e `"vLLM Llama 3 (Mock)"` — estes são nomes de exibição para rastreabilidade no PDF, não os modelos efetivamente utilizados. Os modelos reais são definidos via variáveis de ambiente.

---

## 🗺️ Fases Planejadas (Backlog Técnico)

> As fases abaixo derivam diretamente dos requisitos em `arquivos-projeto/` (ERSW e Backlog). **Importante:** abrir as issues no GitHub somente ao **iniciar** a fase correspondente — não converter este planejamento em issues antecipadamente.

---

## 📋 Planejamento de Issues para GitHub

| Issue | Fase | Tipo | Prioridade | Dependência |
|---|---|---|---|---|
| #25 | 19 | FEATURE | 🔴 Alta | — |
| #26 | 19 | DOCS | 🔴 Alta | — |
| #27 | 19 | FIX | 🟡 Média | — |
| #28 | 20 | RESEARCH | 🟡 Média | Áudios de teste |
| #29 | 20 | RESEARCH | 🟡 Média | Dataset NER anotado |
| #30 | 20 | RESEARCH | 🟡 Média | Acesso a GPU |
| #31 | 21 | FIX | 🔴 Alta | — |
| #32 | 21 | FIX | 🔴 Alta | — |
| #33 | 21 | FIX | 🔴 Alta | — |
| #34 | 21 | FEATURE | 🔵 Baixa | HPC Mandu |
| #35 | 21 | TEST | 🟡 Média | #25 |

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
| **Fase 19** | Formulário Real de Processo: `POST /processos/novo` com validação CPF e upsert, modal frontend, sincronização do modelo BD | Maio/2026 |
| **Fase 20** | Benchmarking Científico: WER para Whisper (`benchmark_wer.py`), F1-Score para LeNER-Br (`benchmark_ner.py`), comparativo de LLMs (`benchmark_llm.py`) | Maio/2026 |
| **Fase 21** | Polimento Pré-Deploy: remover `GET /auth/users`, garantir buckets MinIO, validar JWT em produção, testes integrados do pipeline | Maio/2026 |

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
  - *Heurística de locutor:* função `_assign_speakers` alterna entre "Inquiridor" e "Depoente" sempre que a pausa entre segmentos consecutivos ultrapassa 1,0s. É um placeholder — substituir por PyAnnote quando o HPC Mandu estiver disponível.
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

### ⚠️ Verificação de Maio/2026 — Gaps identificados na auditoria de código

Auditoria realizada em 25/05/2026 sobre o código das Fases 6–18. Os itens abaixo foram corrigidos ou planejados:

1. **`storage_path_pdf` — coluna ausente no banco** → Migration adicionada e aplicada (corrigido em 25/05/2026)
2. **`POST /processos/novo` ainda mock** → Corrigido em Fase 19, Issue #25 ✅
3. **`modelo_bd.sql` desatualizado** → Corrigido em Fase 19, Issue #26 ✅
4. **Modelos de IA no seed com nomes "(Mock)"** → Corrigido em Fase 19, Issue #27 ✅
5. **`GET /auth/users` sem RBAC** → Corrigido em Fase 21, Issue #31 ✅
6. **Bucket `termos-finais` não auto-criado** → Corrigido em Fase 21, Issue #32 ✅
7. **JWT_SECRET_KEY padrão inseguro aceito em produção** → Corrigido em Fase 21, Issue #33 ✅
8. **Ausência de benchmarks WER e F1** → Corrigido em Fase 20, Issues #28–#30 ✅
9. **Diarização heurística (pendência assumida)** → Planejado como Fase 21, Issue #34 (aguardando HPC Mandu)

---

## 📝 Notas de Pesquisa (PIBITI/CNPq)

Extraídas para [`NOTAS_PIBITI.md`](NOTAS_PIBITI.md) para facilitar a citação no relatório de IC.
