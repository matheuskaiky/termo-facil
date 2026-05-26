# Termo Fácil - Sistema Inteligente de Redação de Termos de Depoimentos

Um sistema *on-premise* baseado em Inteligência Artificial Generativa destinado a automatizar a transcrição e redação de Termos de Depoimento para a Secretaria de Segurança Pública do Estado do Piauí (SSP-PI).

## Arquitetura e Stack
O sistema adota uma **Arquitetura Orientada a Eventos (EDA)** com os seguintes componentes:
- **FastAPI**: BFF e API Gateway responsável pelo roteamento.
- **PostgreSQL 15**: Banco de dados relacional (via pg8000/SQLAlchemy) que guarda o controle de inquéritos, depoentes e estado da máquina.
- **Redis 7 + Celery**: Message Broker que enfileira os áudios e interage de forma assíncrona com os Workers de IA.
- **MinIO**: Storage S3-compatible utilizado para guardar arquivos pesados de áudio (.wav) antes do expurgo.
- **Angular 17**: Frontend moderno em Single Page Application (SPA), estilizado em GovTech Design System com baixo peso cognitivo (Split-Screen).

---

## Como Iniciar o Projeto

### Escolher seu modo de operação:

**Opção A: Máquinas com Docker (Windows, Mac, Linux)**
```bash
docker-compose up -d
```

**Opção B: Clusters HPC (sem Docker, sem sudo)**
```bash
./hpc/setup.sh      # Uma única vez
./hpc/start.sh      # Cada vez que quer iniciar
```

Para detalhes sobre HPC, ver `hpc/README.md`.

---

### Setup Completo (Passo a Passo)

#### 1. Iniciar Infraestrutura

**Docker (recomendado para desenvolvimento local):**
```bash
docker-compose up -d
```
> O banco de dados iniciará automaticamente consumindo as tabelas do `arquivos-projeto/modelo_bd.sql`.

**HPC Bare-Metal (sem Docker, sem sudo):**
```bash
./hpc/setup.sh      # Inicializa PostgreSQL, Redis, MinIO localmente
```


#### 2. Configurar o Backend (Python)

**Crie e ative o ambiente virtual na raiz do projeto:**

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Linux/Mac (bash):
```bash
python -m venv .venv
source .venv/bin/activate
```

**Instale as dependências:**
```bash
pip install -r backend/requirements.txt
```

#### 3. Popular o Banco de Dados (Seed)

```bash
python backend/scripts/seed_db.py
```

#### 4. Executar os Serviços do Backend (Dois Terminais)

**Terminal 1 — API Server:**
```bash
uvicorn app.main:app --reload --app-dir backend
```
> API Docs: `http://localhost:8000/docs`

**Terminal 2 — Celery Worker:**
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info -P solo
```

#### 5. Configurar Ollama (LLM Local)

O pipeline usa um LLM local via [Ollama](https://ollama.com).

**Instale Ollama:**
- Windows/Mac: [ollama.com/download](https://ollama.com/download)
- Linux: `curl -fsSL https://ollama.com/install.sh | sh`

**Baixe o modelo:**
```bash
ollama pull llama3
```

#### 6. Executar o Frontend (Angular)

**Terminal 3:**
```bash
cd frontend
npm install
npm run start
```
> Frontend: `http://localhost:4200`

---

## Variáveis de Ambiente

Criar `backend/.env` (copiar de `backend/.env.example`):

```bash
cp backend/.env.example backend/.env
```

Principais variáveis:
| Variável | Padrão | Descrição |
|---|---|---|
| `POSTGRES_SERVER` | `127.0.0.1` | Host PostgreSQL |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | URL Redis |
| `MINIO_ENDPOINT` | `127.0.0.1:9000` | MinIO API |
| `LLM_BASE_URL` | `http://localhost:11434` | Servidor LLM (Ollama/vLLM) |
| `LLM_MODEL_NAME` | `llama3` | Modelo LLM |
| `WHISPER_MODEL_SIZE` | `base` | Tamanho Whisper (`base`, `small`, `medium`, `large`) |

---

## Estrutura do Projeto

```
termo-facil/
├── backend/                          # FastAPI + Celery
│   ├── app/
│   │   ├── core/                     # Config, Celery setup
│   │   ├── api/endpoints/            # Rotas HTTP
│   │   ├── models.py                 # ORM/SQLAlchemy
│   │   ├── tasks/                    # Celery tasks (ASR, NER, LLM)
│   │   ├── services/                 # ASR, NER, LLM, PDF, Storage
│   │   └── main.py                   # FastAPI app entry
│   ├── scripts/                      # Setup, migrations, benchmarks
│   ├── requirements.txt              # Dependencies
│   └── .env                          # gitignored — configure aqui
│
├── frontend/                         # Angular 17
│   ├── src/
│   │   ├── app/
│   │   │   ├── pages/                # Main views
│   │   │   ├── components/           # Reusable components
│   │   │   ├── services/             # API client, auth
│   │   │   └── guards/               # Auth/permission guards
│   │   ├── styles/                   # GovTech Design System
│   │   └── main.ts                   # Bootstrap
│   ├── package.json                  # Dependencies
│   └── angular.json                  # Build config
│
├── hpc/                              # HPC bare-metal setup (novo)
│   ├── config.sh                     # Shared variables
│   ├── setup.sh                      # Initialize services
│   ├── start.sh                      # Start services
│   ├── stop.sh                       # Stop services
│   ├── status.sh                     # Check status
│   ├── README.md                     # HPC-specific docs
│   └── .data/                        # gitignored — runtime data
│
├── docker-compose.yml                # Infrastructure (Docker mode)
├── CLAUDE.md                         # Project instructions for Claude
├── ROADMAP.md                        # Technical phases & status
├── NOTAS_PIBITI.md                   # Research notes for scientific report
├── README.md                         # This file (general setup)
└── backend/.env.example              # Template for backend/.env
```

### Principais Rotas
- `GET /api/v1/docs` — Swagger UI
- `POST /api/v1/upload` — Enviar áudio
- `GET /api/v1/jobs/{id}` — Status do job
- `GET /api/v1/termos/{id}` — Termos gerados
- `POST /api/v1/pdf/{id}` — Exportar PDF

### Documentação Adicional
- **CLAUDE.md** — Instruções para Claude Code, legal requirements, architecture
- **ROADMAP.md** — Fases de desenvolvimento (todas concluídas até Fase 21)
- **NOTAS_PIBITI.md** — Notas técnicas para relatório PIBITI
- **hpc/README.md** — Setup no HPC sem Docker (novo!)
