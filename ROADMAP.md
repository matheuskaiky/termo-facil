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
| **Pipeline de IA** | ASR + NER + LLM | 🟡 Simulado (mock) |
| **Geração de PDF** | Hash SHA256 (mock) | 🟡 Simulado (mock) |
| **Autenticação** | Simulador por header | 🟡 Desenvolvimento |

---

## 🚀 Fase 8 — Geração Real de Documentos PDF (Backend)

### Objetivo
Substituir o mock de hash SHA256 do endpoint `/pdf/gerar` por um PDF juridicamente estruturado, gerado dinamicamente com os dados reais do depoimento (nome do depoente, data, número do inquérito, texto editado pelo escrivão), armazenado no MinIO e retornando uma URL de download autenticada.

### Por que esta fase é prioritária?
O PDF é o **produto final** do sistema — é o documento que será impresso, assinado e arquivado no processo policial. Enquanto ele for um mock, o sistema não tem valor prático para nenhuma delegacia. Esta fase transforma o fluxo completo em algo entregável para um piloto real na SSP-PI.

---

### Issue #7 — Backend: Gerador de PDF com ReportLab

**Responsável:** Humano (Backend)

**O que fazer:**

Criar um serviço `pdf_service.py` dentro de `backend/app/services/` que constrói o PDF usando a biblioteca `reportlab`.

**Por que `reportlab` e não `weasyprint` ou `pdfkit`?**
- `weasyprint` e `pdfkit` convertem HTML → PDF, exigindo um navegador ou engine WebKit instalado. Em um servidor Linux sem interface gráfica (como o HPC Mandu), isso é uma dependência pesada e propensa a falhar.
- `reportlab` gera PDFs nativamente em Python, sem nenhuma dependência de sistema operacional. É a escolha padrão para geração de documentos legais em ambientes governamentais brasileiros (utilizado em sistemas do SERPRO e do TRF).
- É determinístico: o mesmo input sempre gera o mesmo PDF, facilitando a auditoria e a verificação do hash.

**Estrutura do PDF a gerar:**
```
╔══════════════════════════════════════════╗
║     SECRETARIA DE SEGURANÇA PÚBLICA/PI   ║
║         TERMO DE DEPOIMENTO              ║
╠══════════════════════════════════════════╣
║ Nº Inquérito: IP-2026/001                ║
║ Data/Hora:    20/05/2026 às 14h32        ║
║ Depoente:     José Maria da Silva        ║
║ Tipo:         Suspeito                   ║
║ Escrivão:     João Silva — Mat. 123456   ║
╠══════════════════════════════════════════╣
║                                          ║
║   [Texto editado pelo escrivão aqui]     ║
║                                          ║
╠══════════════════════════════════════════╣
║ Assinatura Digital (SHA-256):            ║
║ 3a4f... [hash do conteúdo]               ║
╚══════════════════════════════════════════╝
```

**Tarefas:**
- [ ] Instalar `reportlab` e adicionar ao `requirements.txt`
- [ ] Criar `backend/app/services/pdf_service.py` com função `gerar_pdf_termo(depoimento_data: dict) -> bytes`
- [ ] A função deve receber um dicionário com todos os campos do depoimento e retornar os bytes do PDF gerado
- [ ] Calcular o `hash_sha256` do conteúdo do PDF gerado (não do texto) para garantir integridade
- [ ] Escrever um teste manual simples (`test_pdf.py` na pasta `scripts/`) que gera um PDF de exemplo e o salva em disco para validação visual

**Referência de código (esqueleto):**
```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io, hashlib

def gerar_pdf_termo(dados: dict) -> tuple[bytes, str]:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    # ... montar o conteúdo ...
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    return pdf_bytes, sha256
```

---

### Issue #8 — Backend: Upload do PDF Gerado para o MinIO

**Responsável:** Humano (Backend)

**O que fazer:**

Atualizar o endpoint `/pdf/gerar` em `backend/app/api/endpoints/pdf.py` para chamar o `pdf_service` e depois usar o `minio_service` já existente para fazer upload do PDF gerado.

**Por que armazenar no MinIO e não no disco local?**
- O disco local do servidor da API é **efêmero** em ambientes containerizados (Docker/Kubernetes). Se o container reiniciar, os arquivos se perdem.
- MinIO é S3-compatível, ou seja, o mesmo código funcionará com AWS S3 ou qualquer cloud storage no futuro sem alteração.
- O MinIO já está configurado no `docker-compose.yml` e no `minio_service.py`. O custo de integração é baixo.
- Centralizar os arquivos no MinIO permite que múltiplas instâncias da API (escalabilidade horizontal) acessem o mesmo PDF.

**Tarefas:**
- [ ] Atualizar `backend/app/api/endpoints/pdf.py`:
  - Buscar todos os dados necessários do banco (Depoimento + TermosFinais + Depoente + Inquérito + Usuário)
  - Chamar `pdf_service.gerar_pdf_termo(dados)` → recebe `(pdf_bytes, sha256)`
  - Fazer upload para o MinIO usando `minio_service.upload_file(...)` com o bucket `termos-finais` e key `{id_depoimento}/termo.pdf`
  - Salvar o `hash_sha256` e o `storage_path` (URL do MinIO) no campo correspondente de `TermosFinais`
- [ ] Adicionar o campo `storage_path_pdf` ao model `TermosFinais` em `models.py` (ou reutilizar `hash_pdf` para a URL)
- [ ] O endpoint deve retornar a URL pré-assinada (presigned URL) do MinIO com validade de 1 hora, para que o Angular possa abrir o PDF diretamente no browser

**Fluxo esperado:**
```
[Angular] POST /pdf/gerar
    → [FastAPI] busca dados do DB
    → [pdf_service] gera bytes do PDF
    → [minio_service] faz upload → retorna storage_path
    → [FastAPI] salva hash + path no TermosFinais
    → [minio_service] gera presigned URL (1h)
    → [Angular] recebe URL → abre PDF no browser / botão de download
```

---

### Issue #9 — Frontend: Botão de Download Real do PDF (Angular)

**Responsável:** IA (Frontend)

**O que fazer:**

Atualizar o `AuditoriaComponent` para que, ao receber a resposta do endpoint `/pdf/gerar`, exiba um botão de download funcional apontando para a presigned URL do MinIO.

**Por que presigned URL e não proxy pela API?**
- Fazer o download do PDF passar pelo servidor FastAPI adicionaria carga desnecessária na API para algo que é puramente transferência de arquivo.
- A presigned URL permite que o browser baixe o arquivo diretamente do MinIO, que é um serviço de armazenamento otimizado para isso.
- É o padrão da indústria (AWS S3, GCS, Azure Blob também usam presigned URLs).

**Tarefas:**
- [ ] Atualizar `onGeneratePDF()` no `auditoria.component.ts` para capturar o campo `pdf_url` da resposta da API
- [ ] Substituir o link simulado "📥 Baixar Termo Assinado (.pdf)" por um `<a [href]="pdfUrl" target="_blank" download>` real
- [ ] Adicionar um `<iframe>` ou modal de preview que exibe o PDF embutido na página quando disponível (usando a mesma presigned URL)
- [ ] Exibir data/hora e hash SHA256 do documento gerado como metadados do arquivo

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
- [ ] Instalar `openai-whisper` e `ffmpeg` (dependência de sistema) no ambiente
- [ ] Criar `backend/app/services/asr_service.py` com função `transcrever_audio(audio_path: str, modelo: str = "base") -> str`
- [ ] A função deve baixar o áudio do MinIO para um arquivo temporário, transcrever, deletar o temp e retornar o texto
- [ ] Atualizar `process_audio_task` para chamar `asr_service.transcrever_audio()` no passo 3
- [ ] Parametrizar o nome do modelo via variável de ambiente `WHISPER_MODEL_SIZE` (default: `base`)

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
- [ ] Criar `backend/app/services/llm_service.py` com função `sintetizar_juridico(texto_asr: str) -> str`
- [ ] A função deve chamar `http://localhost:11434/api/generate` (Ollama) ou a URL do vLLM configurada via `LLM_BASE_URL`
- [ ] Usar temperatura `0.0` para garantir saídas determinísticas (crítico para documentos legais)
- [ ] Atualizar `process_audio_task` para chamar `llm_service.sintetizar_juridico()` no passo 5
- [ ] Documentar no README como instalar e configurar o Ollama localmente

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
