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
| **Pipeline de IA** | Whisper + LeNER-Br + Ollama | ✅ Pipeline completo implementado |
| **Geração de PDF** | ReportLab + MinIO Presigned URLs | ✅ Funcional |
| **Autenticação** | JWT (bcrypt + HS256) | ✅ Funcional |
| **Gestão de Senhas** | Reset com senha temporária + troca obrigatória | ✅ Funcional |
| **Revisão Human-in-the-Loop** | Split-screen (transcrição + editor) | 🟡 Parcial — edição não é persistida |
| **Diarização / Timestamps** | Separação de locutores + marcação de tempo | ❌ Não implementado |
| **PDF Híbrido (Anexo + Disclaimer)** | Resumo + transcrição literal anexa | ❌ Apenas resumo (sem anexo/disclaimer) |
| **Dashboard de Métricas (ROI)** | Volumetria sem dados sigilosos | ❌ Não implementado |
| **Expurgo LGPD (Retenção Volátil)** | Apagar áudio/rascunhos após exportação | ❌ Não implementado |

---

## 🗺️ Fases Planejadas (Backlog Técnico)

> As fases abaixo derivam diretamente dos requisitos em `arquivos-projeto/` (ERSW e Backlog). A ordem prioriza primeiro fechar o ciclo de valor *Human-in-the-Loop* (hoje quebrado), depois a ancoragem factual, a auditabilidade do documento e, por fim, a governança de dados (LGPD). Cada `RF-XX` / `RN-XX` referencia o requisito de origem para rastreabilidade.
>
> **Importante:** abrir as issues no GitHub somente ao **iniciar** a fase correspondente — não converter este planejamento em issues antecipadamente.

### 🐞 Correções Críticas (pré-requisito — bloqueiam o fluxo atual)

Identificadas na análise de código de Maio/2026. Devem ser corrigidas antes (ou como parte) da Fase 12, pois quebram o ciclo principal:

1. **Edição humana não é persistida** — o botão "Aprovar e Gerar PDF" chama `/pdf/gerar` direto; o texto editado em `AuditoriaComponent` (`resumo`) nunca é enviado ao backend. `txt_editado_humano` permanece `NULL` e o PDF usa o texto bruto da IA. *Anula o propósito do RF-05.*
2. **`NameError` na geração de PDF** — `pdf_service.py` usa `colors.gray` (linha ~130) sem `from reportlab.lib import colors`. Deve quebrar a geração em runtime; precisa verificação + correção.
3. **NER não alimenta o LLM** — o pipeline extrai entidades (`ner_model.extract_entities`) mas `llm_model.synthesize(transcript)` ignora o dicionário. A "blindagem factológica" (RF-04) está incompleta.

---

### 🔁 Fase 12 — Fechamento do Loop Humano (RF-05, RN-03, RNF-04)

**Objetivo:** tornar a revisão *Human-in-the-Loop* real — persistir a edição do escrivão, exigir aceite explícito de responsabilidade e proteger o rascunho contra quedas de rede.

**Tarefas (Backend):**
- [ ] Endpoint `PUT /jobs/{job_id}/resultado` (ou `/termos/{id_depoimento}`) que salva `txt_editado_humano` (requer `EDITAR_TERMO`)
- [ ] Corrigir bug do `colors` em `pdf_service.py`
- [ ] Garantir que `gerar_pdf` use `txt_editado_humano` quando presente (já lê — depende do save acima)

**Tarefas (Frontend):**
- [ ] Salvar `resumo` editado antes de gerar o PDF (ou auto-save ao editar)
- [ ] Checkbox obrigatório **"Declaro que revisei o conteúdo"** antes de habilitar "Aprovar e Gerar Documento" (RN-03)
- [ ] Auto-save do rascunho no `localStorage` durante a edição, com restauração ao reabrir (RNF-04)
- [ ] Remover dependências legadas do `AuditoriaComponent`: troca `/auth/me` por leitura do JWT local e remove `mock_ids.json`

---

### 🧬 Fase 13 — Ancoragem Factual Real no LLM (RF-04, RN-01)

**Objetivo:** garantir determinismo e impedir alucinação injetando as entidades NER na síntese.

**Tarefas:**
- [ ] Injetar o dicionário NER (`{PESSOAS, LOCAIS, DATAS, LEGISLACAO}`) no `_SYSTEM_PROMPT` do `llm_service`, instruindo uso exclusivo desses fatos
- [ ] Adicionar `top_p: 0.1` às `options` do Ollama (RF-04 exige Top-P = 0.1)
- [ ] Instruir o modelo a escrever `[(Trecho Ininteligível)]` em vez de adivinhar (RN-01)
- [ ] Passar `entities` para `llm_model.synthesize(...)` na task `process_audio`

---

### 🎙️ Fase 14 — Diarização e Timestamps Sincronizados (RF-02, RF-05)

**Objetivo:** separar locutores e permitir navegação do áudio pelos timestamps.

**Tarefas (Backend):**
- [ ] `asr_service` passa a retornar segmentos (`start`, `end`, `text`) — Whisper já os fornece em `result["segments"]`
- [ ] Diarização de locutores (ex: PyAnnote) marcando "Inquiridor"/"Depoente"
- [ ] Persistir segmentos estruturados (nova coluna JSONB em `TermosFinais` ou `MidiaBruta`)

**Tarefas (Frontend):**
- [ ] Player de áudio na coluna esquerda do `AuditoriaComponent`
- [ ] Renderizar transcrição como blocos com timestamp; clicar no timestamp posiciona o player no segundo correspondente

---

### 📑 Fase 15 — PDF Híbrido Auditável (RF-06, RN-02)

**Objetivo:** transformar o PDF de resumo em documento de prova com anexo e rastreabilidade.

**Tarefas:**
- [ ] Anexar a transcrição literal com timestamps como páginas anexas (Parte 2)
- [ ] Rodapé em todas as páginas: *"Documento gerado com assistência de Inteligência Artificial e revisado por autoridade policial"* (RN-02)
- [ ] Metadados/watermark de rastreabilidade do modelo gerador (modelo ASR/LLM, versão)

---

### 📊 Fase 16 — Dashboard de Métricas / ROI (RF-07)

**Objetivo:** dar visibilidade de eficiência ao Gestor Estratégico sem expor conteúdo sigiloso.

**Tarefas:**
- [ ] Endpoint de métricas: nº de termos gerados, tempo médio de áudio processado, horas estimadas economizadas — **sem** texto/áudio sigiloso
- [ ] Nova permissão `VER_METRICAS` + cargo "Gestor Estratégico" no seed
- [ ] Componente Angular de dashboard (cards de volumetria), protegido por `permissionGuard`

---

### 🔐 Fase 17 — Governança de Dados: Expurgo LGPD (RN-04)

**Objetivo:** cumprir a Política de Retenção Volátil — o sistema processa, não custodia.

**Tarefas:**
- [ ] Registrar timestamp de exportação do PDF em `TermosFinais`
- [ ] Task agendada (Celery Beat) que expurga áudio bruto, dicionário JSON e rascunhos > 24h após exportação bem-sucedida
- [ ] Log de auditoria dos expurgos (o que foi apagado e quando)

---

### 🛡️ Fase 18 — Hardening de Produção & Polimentos

**Objetivo:** preparar para o piloto.

**Tarefas:**
- [ ] Upload: aceitar `.opus` e validar tamanho máximo (200MB) — hoje só `.wav/.mp3/.m4a`, sem limite
- [ ] Status granular do Job: "Transcrevendo", "Extraindo Dados", "Gerando Resumo" (RF-01)
- [ ] Desabilitar fallbacks de dev (`X-User-Id`, "primeiro usuário") via `APP_ENV=production` em `deps.py`
- [ ] *(Could Have)* Upload resiliente a quedas de rede (retomada automática — US-01/RNF-04)

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

### 📝 Notas de Desenvolvimento (Intercorrências)
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
