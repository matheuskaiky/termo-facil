# Termo Fácil - Sistema Inteligente de Redação de Termos de Depoimentos

Um sistema *on-premise* baseado em Inteligência Artificial Generativa destinado a automatizar a transcrição e redação de Termos de Depoimento para a Secretaria de Segurança Pública do Estado do Piauí (SSP-PI).

## Arquitetura e Stack
O sistema adota uma **Arquitetura Orientada a Eventos (EDA)** com os seguintes componentes:
- **FastAPI**: BFF e API Gateway responsável pelo roteamento.
- **PostgreSQL**: Banco de dados relacional (via pg8000/SQLAlchemy) que guarda o controle de inquéritos, depoentes e estado da máquina.
- **Redis + Celery**: Message Broker que enfileira os áudios e interage de forma assíncrona com os Workers de IA.
- **MinIO**: Storage S3-compatible utilizado para guardar arquivos pesados de áudio (.wav) antes do expurgo.
- **React + Vite**: Frontend moderno em Single Page Application (SPA), estilizado em Vanilla CSS (GovTech) com baixo peso cognitivo (Split-Screen).

---

## Como Iniciar o Projeto (Passo a Passo Completo)

Siga os passos abaixo para rodar toda a aplicação na sua máquina (Full-Stack).

### 1. Iniciar Infraestrutura Local (Docker)
É obrigatório subir o PostgreSQL, Redis e MinIO para o funcionamento do ecossistema.
```bash
docker-compose up -d
```
> O banco de dados iniciará automaticamente consumindo as tabelas do `arquivos-projeto/modelo_bd.sql`.

### 2. Configurar o Backend (Python)
Para suportar o Python 3.13 no Windows de forma nativa, o projeto utiliza drivers pure-python (como `pg8000`) e as bibliotecas mais recentes. 

**Crie e ative o ambiente virtual na raiz do projeto:**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**Instale as dependências:**
```bash
pip install -r backend\requirements.txt
```

### 3. Popular o Banco de Dados (Seed)
Para que o PostgreSQL não bloqueie os envios do Frontend por falta de Chave Estrangeira, rode o script que cadastra automaticamente Modelos e Inquéritos simulados:
```bash
python backend\scripts\seed_db.py
```
> Isso gerará o arquivo `frontend/src/mock_ids.json` que o React consumirá.

### 4. Executar os Serviços do Backend (Dois Terminais)
Abra **dois terminais** na pasta raiz do projeto (com o `.venv` ativado em ambos):

**Terminal 1 - O Servidor da API:**
```bash
uvicorn app.main:app --reload --app-dir backend
```
> A API e o Swagger ficam disponíveis em: `http://localhost:8000/docs`

**Terminal 2 - O Worker Assíncrono (Celery):**
Entre na pasta `backend` e inicie o consumidor da fila:
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info -P solo
```

### 5. Executar o Frontend (React)
Abra um **terceiro terminal**, entre na pasta do Frontend, instale os pacotes Node e suba o Vite:
```bash
cd frontend
npm install
npm run dev
```
> O sistema web estará acessível em: `http://localhost:5173`

---

## Estrutura do Projeto
- `backend/app/core/`: Configurações do ambiente, setup do Celery.
- `backend/app/api/`: Rotas HTTP (`/upload`, `/jobs`).
- `backend/app/models.py`: Mapeamento ORM do banco.
- `backend/app/tasks/`: Código dos "Workers" simulando a IA pesada.
- `frontend/src/pages/`: Páginas do sistema em React (Ex: Auditoria Split-Screen).
- `frontend/src/services/api.js`: Comunicação Axios com o FastAPI.
