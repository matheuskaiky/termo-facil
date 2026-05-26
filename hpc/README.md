# Termo Fácil — HPC Bare-Metal Setup

Este diretório contém scripts para rodar o Termo Fácil em clusters HPC (High Performance Computing) **sem Docker e sem sudo**.

## Visão Geral

Os scripts inicializam e gerenciam três serviços de infraestrutura:

- **PostgreSQL 15** — banco de dados principal
- **Redis 7** — fila de tarefas (Celery) e cache
- **MinIO** — armazenamento S3-compatível para áudio e PDFs

Todos os serviços rodam como **processos nativos** em espaço de usuário, armazenando dados e logs em `hpc/.data/` e `hpc/logs/`.

## Compatibilidade Dual-Mode

Os mesmos scripts funcionam em **duas configurações**:

### Máquinas com Docker (Windows, Linux, Mac)
```bash
docker-compose up -d   # Roda PostgreSQL, Redis, MinIO em containers
```

### Cluster HPC (sem Docker, sem sudo)
```bash
./hpc/setup.sh         # Setup inicial (idempotente)
./hpc/start.sh         # Inicia os 3 serviços
```

**Insight:** O `backend/.env` usa `127.0.0.1` para todos os serviços. Se os containers e processos nativos usam as mesmas portas, o código da aplicação funciona identicamente em ambos os modos.

| Serviço | Docker | HPC Bare-Metal |
|---------|--------|----------------|
| PostgreSQL | porta 5432 container | porta 5432 processo |
| Redis | porta 6379 container | porta 6379 processo |
| MinIO | porta 9000 container | porta 9000 processo |

Resultado: **zero adaptação** ao clonar o repo em uma máquina com ou sem Docker.

---

## Primeiro Setup (Cluster HPC)

### 1. Pré-requisitos

- **Linux** (bash, standard Unix utilities)
- **Python 3.8+** com `pip` (para backend)
- Uma das opções abaixo para PostgreSQL:
  - `conda` (recomendado — amplamente disponível em HPC)
  - `module system` (se PostgreSQL estiver disponível como módulo)
  - Compilar manualmente (script oferece instruções)

### 2. Executar Setup Inicial

```bash
./hpc/setup.sh
```

**O que acontece:**

1. Cria estrutura de diretórios (`bin/`, `.data/`, `logs/`)
2. Detecta ou instala PostgreSQL
3. Inicializa cluster PostgreSQL em `hpc/.data/postgres/`
4. Cria user `termo_user` e database `termo_facil`
5. Aplica schema SQL (`arquivos-projeto/modelo_bd.sql`)
6. Executa seed (`backend/scripts/seed_db.py`)
7. Compila ou baixa Redis e MinIO

**Tempo esperado:** 2–5 minutos (mais lento se compilar Redis do source)

**Idempotência:** seguro re-executar — script verifica "já existe?" antes de cada passo.

---

## Uso Diário

### Iniciar Serviços

```bash
./hpc/start.sh
```

Exemplo de output:
```
[INFO] Starting PostgreSQL on port 5432...
[OK] PostgreSQL started (port 5432)

[INFO] Starting Redis on port 6379...
[OK] Redis started (port 6379)

[INFO] Starting MinIO on port 9000...
[OK] MinIO started (port 9000)

All Services Running

PostgreSQL   : 127.0.0.1:5432  (db=termo_facil, user=termo_user)
Redis        : 127.0.0.1:6379
MinIO API    : http://127.0.0.1:9000
MinIO Console: http://127.0.0.1:9001  (user: admin)

Next steps (each in a separate terminal, with .venv active):

  # Terminal 1 — Backend API
  uvicorn app.main:app --reload --app-dir backend

  # Terminal 2 — Celery Worker
  cd backend && celery -A app.core.celery_app worker --loglevel=info -P solo

  # Terminal 3 — Frontend
  cd frontend && npm run start

  # Terminal 4 — Ollama (if not already running)
  ollama serve

API Docs: http://localhost:8000/docs
Frontend: http://localhost:4200
```

### Verificar Status

```bash
./hpc/status.sh
```

Exemplo de output:
```
╔════════════════════════════════════════════════════════════════════════╗
║                  Termo Fácil — HPC Service Status                       ║
╚════════════════════════════════════════════════════════════════════════╝

✓ PostgreSQL      RUNNING
                127.0.0.1:5432  db=termo_facil  user=termo_user
                psql postgresql://termo_user:***@127.0.0.1:5432/termo_facil

✓ Redis           RUNNING
                127.0.0.1:6379
                redis-cli -p 6379

✓ MinIO           RUNNING
                API:     http://127.0.0.1:9000
                Console: http://127.0.0.1:9001
                User: admin  Password: adminpassword
```

### Parar Serviços

```bash
./hpc/stop.sh
```

Parada graceful na ordem inversa: MinIO → Redis → PostgreSQL.

---

## Estrutura de Diretórios

```
hpc/
├── config.sh                # Variáveis compartilhadas e funções
├── setup.sh                 # Setup inicial (rodar uma única vez)
├── start.sh                 # Iniciar serviços
├── stop.sh                  # Parar serviços
├── status.sh                # Verificar estado
├── README.md                # Este arquivo
├── .gitignore               # Ignora .data/, bin/, logs/
└── .data/                   # gitignored — dados dos serviços
    ├── postgres/            # PostgreSQL cluster
    ├── redis/               # Redis data files
    └── minio/               # MinIO object storage
```

---

## Arquivos Relacionados

### `backend/.env` (gitignored, não alterar manualmente)

Carregado automaticamente pelo backend. Aponta para `127.0.0.1` em todos os serviços — funciona tanto com Docker quanto com bare-metal.

### `backend/.env.example` (git-tracked)

Documentação de todas as variáveis de ambiente. Use como referência ao configurar uma nova máquina.

### `docker-compose.yml` (intacto)

Continua funcionando normalmente em máquinas com Docker. Nenhuma mudança necessária.

---

## Resolução de Problemas

### "PostgreSQL not found"

**Problema:** `module: command not found` ou PostgreSQL não está disponível no PATH.

**Estratégia 1: Instalar Miniconda (Recomendado)**

Se o cluster não tem gerenciador de pacotes, instale Miniconda (mini conda — 156MB, rápido):

```bash
# Download Miniconda (Linux x86_64)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Instalar em user-space (sem sudo)
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda

# Ativar conda
source $HOME/miniconda/bin/activate

# Agora instalar PostgreSQL e Redis
conda install -c conda-forge postgresql
./hpc/setup.sh
```

**Estratégia 2: Usar módulo do HPC**

Se o cluster tem `module system` (LMOD):

```bash
# Listar módulos disponíveis
module avail | grep -i postgresql

# Carregar módulo (exemplo)
module load postgresql/17

# Re-executar setup
./hpc/setup.sh
```

**Estratégia 3: Compilar manualmente (como último recurso)**

```bash
# O script oferecerá instruções para compilar PostgreSQL do source
./hpc/setup.sh
# Siga os prompts
```

### "Port 5432 is already in use" ou PostgreSQL travado

**Problema:** Outro processo está usando a porta ou PostgreSQL ficou rodando do setup anterior.

```bash
# Verificar qual processo está usando a porta
netstat -tlnp | grep 5432
ss -tlnp | grep 5432

# Se for uma instância anterior do Postgres, parar normalmente:
./hpc/stop.sh

# Se o processo não morrer, matar à força pelo PID:
ps aux | grep postgres        # Encontrar PID
kill -9 <PID>                 # Matar à força

# Remover lock file se ainda existir:
rm -f hpc/.data/postgres/postmaster.pid

# Se múltiplos processos, matar todos de uma vez:
pkill -u $USER postgres
pkill -u $USER pg_ctl

# Tentar iniciar novamente:
./hpc/start.sh
```

**Problema real do HPC:** PostgreSQL deixou lock file após interrupção do setup. Solução:

```bash
# Ver qual PID está em lock
cat hpc/.data/postgres/postmaster.pid

# Matar esse PID
kill <PID>

# Reiniciar
./hpc/start.sh
```

### "redis-server: command not found" ou Redis não inicia

**Problema:** Redis não está disponível e `setup.sh` não conseguiu compilar ou instalar.

**Estratégia 1: Instalar via Conda (Recomendado)**

```bash
# Se conda está disponível
conda install -y -c conda-forge redis

# Re-executar setup (agora Redis será encontrado)
./hpc/setup.sh
```

**Estratégia 2: Forçar compilação**

```bash
# Se setup.sh pulou a compilação, forçar manualmente:
# Editar setup.sh (descomentar seção de compilação) ou rodar manualmente

REDIS_VERSION="7.2.4"
curl -L "https://download.redis.io/releases/redis-${REDIS_VERSION}.tar.gz" \
  -o /tmp/redis.tar.gz
tar xzf /tmp/redis.tar.gz -C hpc/.data/
make -C "hpc/.data/redis-${REDIS_VERSION}" -j$(nproc)
cp "hpc/.data/redis-${REDIS_VERSION}/src/redis-server" hpc/bin/
cp "hpc/.data/redis-${REDIS_VERSION}/src/redis-cli" hpc/bin/

# Agora tentar iniciar
./hpc/start.sh
```

**Estratégia 3: Redis já rodando mas `start.sh` não detecta**

```bash
# Matar todas as instâncias de Redis do usuário
pkill -u $USER redis-server

# Remover arquivo PID
rm -f hpc/.data/redis/redis.pid

# Tentar novamente
./hpc/start.sh
```

**Problema real do HPC:** Redis travava durante `start.sh` porque a função de localização falhava. Solução:

```bash
# Verificar onde Redis foi instalado
which redis-server
conda run -n base which redis-server

# Usar caminho diretamente no script se necessário
# (mas scripts agora fazem detecção automática)
```

### MinIO não inicia

```bash
# Verificar logs
tail hpc/logs/minio.log

# Parar todas as instâncias e limpar
./hpc/stop.sh
rm -rf hpc/.data/minio
./hpc/start.sh
```

### "must be owner of type status_job_enum" — erro de permissão PostgreSQL

**Problema:** `termo_user` não tem permissão para alterar tipos ENUM (necessário para `RN-02 compliance`).

```bash
# Conectar como postgres superuser
PG_BIN="/home/aluno_matheus/miniconda/bin"  # Ajustar para sua instalação
$PG_BIN/pg_ctl -D hpc/.data/postgres start

# Conectar com psql como postgres
$PG_BIN/psql -h hpc/.data/postgres -U postgres -d termo_facil

# Dentro do psql:
ALTER ROLE termo_user SUPERUSER;
\q

# Parar e re-executar setup
$PG_BIN/pg_ctl -D hpc/.data/postgres stop
./hpc/setup.sh
```

**Nota:** O script agora faz isso automaticamente, mas se setup.sh falhar nesse ponto, use essa estratégia manual.

---

### Banco de dados corrompido após crash

```bash
# Parar serviços
./hpc/stop.sh

# Backup do cluster PostgreSQL (opcional)
cp -r hpc/.data/postgres hpc/.data/postgres.backup

# Reinicializar do seed
rm -rf hpc/.data/postgres
./hpc/setup.sh

# Isso vai recriar o cluster, schema e dados de teste
```

---

### Rodando em nó GPU do cluster (SLURM)

Se o cluster usa SLURM (gerenciador de jobs), você pode precisar executar em um nó específico:

```bash
# Alocar nó GPU interativo
srun --partition=gpu --gres=gpu:1 --pty bash

# Dentro do nó GPU, executar setup/start normalmente
source $HOME/miniconda/bin/activate
./hpc/setup.sh
./hpc/start.sh
```

Depois, em outros terminais, conectar-se ao mesmo nó:

```bash
# Em outro terminal, entrar no mesmo nó
ssh <gpu-node-name>
source $HOME/miniconda/bin/activate
# Services já estarão rodando
```

---

### Clusters compartilhados — conflito de portas

Se múltiplos usuários estão rodando Termo Fácil no mesmo cluster:

```bash
# Verificar quem está usando as portas padrão
netstat -tln | grep -E "5432|6379|9000|9001"

# Se alguém já está usando, você pode:
# 1. Usar máquina diferente (recomendado)
# 2. Mudar portas editando hpc/config.sh (não recomendado — afeta .env)
# 3. Esperar que libere (menos recomendado)
```

---

## Notas Técnicas

### Por que `unix_socket_directories` no `postgresql.conf`?

Por padrão, PostgreSQL coloca sockets Unix em `/var/run/postgresql/`. Sem sudo, isso é inacessível. O script redireciona para `hpc/.data/postgres/`, mantendo tudo em espaço de usuário.

O backend se conecta via TCP (`-h 127.0.0.1`), então o socket path não afeta a aplicação — apenas os scripts de setup usam o socket local.

### Idempotência

Todos os scripts (`setup.sh`, `start.sh`) são idempotentes:

- `setup.sh` verifica "já existe?" antes de cada passo
- `start.sh` detecta se um serviço já está rodando
- `stop.sh` trata gracefully o caso de serviço já parado

Seguro re-executar quantas vezes forem necessárias.

### Persistência de Dados

- **PostgreSQL**: persiste em `hpc/.data/postgres/`
- **Redis**: persiste em `hpc/.data/redis/appendonly.aof` (AOF mode)
- **MinIO**: persiste em `hpc/.data/minio/`

Todos os arquivos são gitignored (`.data/` em `hpc/.gitignore` e `.gitignore` raiz).

### Logs

- `hpc/logs/postgres.log` — logs do PostgreSQL
- `hpc/logs/redis.log` — logs do Redis
- `hpc/logs/minio.log` — logs do MinIO

---

## Próximos Passos Após Iniciar

1. **Backend**:
   ```bash
   source .venv/bin/activate
   uvicorn app.main:app --reload --app-dir backend
   # Acesse API Docs em http://localhost:8000/docs
   ```

2. **Celery Worker**:
   ```bash
   cd backend
   celery -A app.core.celery_app worker --loglevel=info -P solo
   ```

3. **Frontend**:
   ```bash
   cd frontend
   npm install  # se não tiver feito antes
   npm run start
   # Acesse em http://localhost:4200
   ```

4. **Ollama** (se não estiver rodando):
   ```bash
   ollama serve
   # Puxa modelo: ollama pull llama3
   ```

---

## Compatibilidade em Outras Máquinas

Após clonar este repo em uma máquina com Docker:

```bash
# Docker mode — funciona sem nenhuma mudança
docker-compose up -d
```

O `docker-compose.yml` não foi alterado. Os scripts `hpc/` existem, mas são ignorados quando se usa Docker.

---

## Suporte e Documentação

- **CLAUDE.md** — Documentação geral do projeto
- **ROADMAP.md** — Fases e status de desenvolvimento
- **README.md (raiz)** — Setup e arquitetura

---

## Créditos

Scripts criados para permitir desenvolvimento e deployment em clusters HPC (UFPI Mandu) sem dependência de Docker ou privilégios elevados, mantendo compatibilidade total com desenvolvimento local em máquinas com Docker.
