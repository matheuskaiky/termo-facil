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
| **Autenticação** | Simulador por header | 🟡 Em desenvolvimento (Fase 10) |

---

## 🔐 Fase 10 — Autenticação Real com JWT

### Objetivo
Substituir o simulador de perfis por um sistema de autenticação real baseado em **JWT (JSON Web Tokens)**, com tela de login, proteção de rotas no frontend e validação segura no backend. Essa fase torna o sistema apto para implantação em um ambiente piloto real na SSP-PI.

### Por que JWT e não sessões com cookie?
- O sistema é uma SPA (Single Page Application) com Angular consumindo uma API REST. O modelo stateless de JWT é o padrão para este tipo de arquitetura.
- JWT permite que múltiplas instâncias da API validem tokens sem compartilhar estado (sem banco de sessões), facilitando a escalabilidade horizontal.
- Tokens JWT podem incluir os `claims` de permissões do usuário diretamente no payload, eliminando a necessidade de buscar o cargo no banco a cada requisição.

---

### Issue #14 — Backend: Endpoint de Login e Emissão de JWT

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

### Issue #15 — Frontend: Tela de Login e Gerenciamento de Token JWT (Angular)

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
| **Fase 9** | Pipeline de IA Real: Whisper (ASR) + LeNER-Br (NER) + Ollama (LLM) + Abstração de Storage | Maio/2026 |

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
