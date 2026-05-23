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
| **Fila de Tarefas** | Celery + Redis | ✅ Funcional (mock) |
| **Armazenamento de Mídias** | MinIO (S3-compatível) | ✅ Funcional |
| **Frontend** | Angular 17 (standalone) | ✅ Funcional |
| **RBAC** | Permissões por Cargo (dinâmicas) | ✅ Funcional |
| **Pipeline de IA** | ASR (Whisper) + NER + LLM (Ollama) | 🟡 ASR e LLM reais, NER ainda mock |
| **Geração de PDF** | ReportLab + MinIO Presigned URLs | ✅ Funcional |
| **Autenticação** | Simulador por header | 🟡 Desenvolvimento |

---
---

## 🔬 Fase 9 — Pipeline de IA Real (Celery + Whisper + LLM)

### Objetivo
Substituir os mocks de texto em `process_audio.py` por chamadas reais aos modelos de IA: **Whisper** para transcrição de áudio (ASR) e um **LLM** local (via vLLM ou Ollama) para síntese jurídica do depoimento.

### Contexto técnico importante
O task Celery em `backend/app/tasks/process_audio.py` já está estruturado com os 5 passos corretos do pipeline (ASR → NER → LLM → Salvar → Concluir). O que precisa mudar é a implementação de cada passo, de `time.sleep(N)` para chamadas reais aos modelos.

---

### Issue #10 — Backend: Integração com Whisper (ASR Real)

**Responsável:** Humano (Backend)

**O que fazer:**

Substituir o `mock_asr` no task Celery pela chamada real ao modelo Whisper.

**Por que `openai-whisper` e não a API da OpenAI?**
- O sistema roda em ambiente de segurança pública. Áudios de depoimentos são **dados sensíveis e sigilosos** — não podem ser enviados para servidores externos.
- O HPC Mandu da UFPI tem GPUs locais disponíveis. O `openai-whisper` roda 100% localmente.
- A biblioteca `openai-whisper` é open-source (licença MIT) e pode ser usada sem custo operacional.

**Modelo recomendado:** `whisper-large-v3` para português com alta precisão. Em desenvolvimento, usar `whisper-base` para velocidade.

**Tarefas:**
- [x] Instalar `openai-whisper` no ambiente (`ffmpeg` é dependência de sistema — instalar no Docker/host)
- [x] Criar `backend/app/services/asr_service.py` com `ASRModel` Protocol e `WhisperASRModel` (modelo cacheado no startup do worker)
- [x] Download do áudio delegado ao `audio_storage.download_as_local_file()` — ASR desacoplado do storage
- [x] Atualizar `process_audio_task` para chamar `asr_model.transcribe()` no passo 3
- [x] Parametrizar via `WHISPER_MODEL_SIZE` (default: `base`)
- [x] Criar `backend/app/services/storage_service.py` com `FileStorage` Protocol, `MinioStorage` e instâncias `audio_storage`/`pdf_storage`

---

### Issue #11 — Backend: Integração com LLM para Síntese Jurídica

**Responsável:** Humano (Backend)

**O que fazer:**

Substituir o `mock_llm` pela chamada a um LLM local via **Ollama** (desenvolvimento) ou **vLLM** (produção no HPC Mandu).

**Por que Ollama para desenvolvimento e vLLM para produção?**
- **Ollama** é uma ferramenta de linha de comando que gerencia modelos LLM locais com uma API REST simples (`http://localhost:11434`). É ideal para desenvolvimento local porque é trivial de instalar no Windows/Mac/Linux.
- **vLLM** é um servidor de inferência de alta performance para GPUs NVIDIA. Ele usa PagedAttention para maximizar o throughput e é o padrão para produção em servidores HPC como o Mandu.
- Abstrair a chamada num `llm_service.py` permite trocar de Ollama para vLLM sem mudar o código do task Celery.

**Prompt jurídico base a usar:**
```
Sistema: Você é um escrivão policial brasileiro especializado em redigir Termos de Depoimento.
Converta a transcrição literal abaixo para o formato formal de inquérito policial,
na terceira pessoa, sem alterar os fatos. Seja preciso, conciso e jurídico.

Transcrição: {texto_asr}
```

**Tarefas:**
- [x] Criar `backend/app/services/llm_service.py` com `LLMModel` Protocol e `OllamaLLM`
- [x] Chamar `{LLM_BASE_URL}/api/generate` com `stream: false` e `temperature: 0.0`
- [x] Configurável via `LLM_BASE_URL` (default: `http://localhost:11434`) e `LLM_MODEL_NAME` (default: `llama3`)
- [x] Atualizar `process_audio_task` para chamar `llm_model.synthesize(transcript)` no passo 5
- [x] Documentar instalação do Ollama e variáveis de ambiente no README

---

### Issue #12 — Backend: Integração com LeNER-Br para NER Jurídico

**Responsável:** Humano (Backend)

**O que fazer:**

Substituir o `mock_ner` pela extração real de entidades nomeadas usando o modelo **LeNER-Br** (BERT fine-tuned para textos legais brasileiros).

**Por que LeNER-Br?**
- É o modelo de NER estado-da-arte para **português jurídico brasileiro**, treinado especificamente em textos do Diário Oficial, STF e processos judiciais.
- Identifica corretamente entidades como nomes de pessoas, organizações policiais, locais de crime, datas e números de documentos — categorias que modelos genéricos de NER erram com frequência.
- Está disponível no HuggingFace (`alfaneo/lener_br`) e pode ser carregado com `transformers`.

**Tarefas:**
- [ ] Instalar `transformers` e `torch` no ambiente
- [ ] Criar `backend/app/services/ner_service.py` com função `extrair_entidades(texto: str) -> dict`
- [ ] O retorno deve ser um dicionário estruturado compatível com o campo `dicionario_ner` do modelo `TermosFinais`
- [ ] Atualizar `process_audio_task` para chamar `ner_service.extrair_entidades()` no passo 4

---

## 🔐 Fase 10 — Autenticação Real com JWT

### Objetivo
Substituir o simulador de perfis por um sistema de autenticação real baseado em **JWT (JSON Web Tokens)**, com tela de login, proteção de rotas no frontend e validação segura no backend. Essa fase torna o sistema apto para implantação em um ambiente piloto real na SSP-PI.

### Por que JWT e não sessões com cookie?
- O sistema é uma SPA (Single Page Application) com Angular consumindo uma API REST. O modelo stateless de JWT é o padrão para este tipo de arquitetura.
- JWT permite que múltiplas instâncias da API validem tokens sem compartilhar estado (sem banco de sessões), facilitando a escalabilidade horizontal.
- Tokens JWT podem incluir os `claims` de permissões do usuário diretamente no payload, eliminando a necessidade de buscar o cargo no banco a cada requisição.

---

### Issue #13 — Backend: Endpoint de Login e Emissão de JWT

**Responsável:** Humano (Backend)

**O que fazer:**

Criar o endpoint `POST /auth/login` que recebe matrícula e senha, valida as credenciais no banco e retorna um JWT assinado.

**Bibliotecas:**
- `python-jose[cryptography]`: Biblioteca padrão para criação e validação de JWT em Python. Mais leve e segura que `PyJWT` para este caso de uso.
- `passlib[bcrypt]`: Para hashing de senha. Bcrypt é o algoritmo recomendado pelo OWASP para senhas de sistemas governamentais.

**Tarefas:**
- [ ] Instalar `python-jose[cryptography]` e `passlib[bcrypt]`
- [ ] Adicionar campo `senha_hash` ao model `Usuario` em `models.py`
- [ ] Criar `backend/app/core/security.py` com funções `criar_token(data)` e `verificar_token(token)`
- [ ] Criar endpoint `POST /auth/login` recebendo `{ matricula, senha }` e retornando `{ access_token, token_type }`
- [ ] O payload do JWT deve incluir: `sub` (id_usuario), `cargo` (nome_cargo), `permissoes` (lista), `exp` (expiração em 8h)
- [ ] Atualizar `get_current_user` em `deps.py` para aceitar o JWT no header `Authorization: Bearer <token>` além do mock `X-User-Id`
- [ ] Atualizar o `seed_db.py` para gerar senhas hasheadas para os usuários de teste

---

### Issue #14 — Frontend: Tela de Login e Gerenciamento de Token JWT (Angular)

**Responsável:** IA (Frontend)

**O que fazer:**

Criar a tela de login, armazenar o JWT no `localStorage` e atualizar o Axios interceptor para enviar o token em todas as requisições.

**Tarefas:**
- [ ] Criar `LoginComponent` com formulário de matrícula e senha, com design GovTech
- [ ] Criar `auth.service.ts` com métodos `login(matricula, senha)`, `logout()`, `getToken()`, `isAuthenticated()`
- [ ] Atualizar o Axios interceptor em `api.service.ts` para enviar `Authorization: Bearer <token>` ao invés do `X-User-Id`
- [ ] Criar `authGuard` para redirecionar rotas protegidas para `/login` se não houver token válido
- [ ] Criar rota `/login` e remover o simulador de perfis do cabeçalho (agora substituído pelo login real)
- [ ] Decodificar o payload do JWT no frontend para exibir nome, cargo e permissões sem request adicional ao backend

---

## ✅ Fases Concluídas

| Fase | Descrição | Concluída em |
|---|---|---|
| **Fase 6** | Split-screen UI + polling de Jobs + gravação de resultados da IA | Abril/2026 |
| **Fase 7** | RBAC dinâmico (Cargo/Permissão) + Middleware de Autorização + Painel Admin Angular | Maio/2026 |
| **Fase 8** | Geração Real de PDF (ReportLab), Upload no MinIO, Presigned URLs e Preview | Maio/2026 |

### 📝 Notas de Desenvolvimento (Intercorrências)
- **Fase 8:** 
  - *Backend:* Conflito de Chave Primária (`IntegrityError`) ao tentar fazer upload de múltiplos áudios para o mesmo `id_depoimento`. Resolvido implementando lógica de upsert (Update se existe, Insert se não existe) na tabela `midia_bruta`.
  - *Frontend:* Bloqueio de segurança do Angular (XSS) ao tentar injetar a Presigned URL do MinIO dinamicamente no `<iframe>`. Resolvido injetando e utilizando o serviço `DomSanitizer` (`bypassSecurityTrustResourceUrl`).
- **Fase 9 (Issues #10 e #11):**
  - *Refactor:* Introduzida camada de abstração `FileStorage` (`storage_service.py`) com instâncias dedicadas `audio_storage` e `pdf_storage`. Endpoints (`upload.py`, `pdf.py`) e a task Celery passaram a depender da abstração, não do `MinioService` diretamente. O `storage_path` no banco passou a armazenar apenas a chave lógica do objeto (sem prefixo `s3://`), eliminando acoplamento do provider nos dados persistidos.
  - *Arquitetura ASR:* `asr_service.py` implementado com `ASRModel` Protocol e `WhisperASRModel`. Modelo Whisper cacheado por `model_size` no startup do worker Celery via `_model_cache`, evitando recarga a cada job.
  - *Arquitetura LLM:* `llm_service.py` implementado com `LLMModel` Protocol e `OllamaLLM`. Temperatura `0.0` para saída determinística. Troca de Ollama para vLLM em produção requer apenas mudança em `LLM_BASE_URL`.
