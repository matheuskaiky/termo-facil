# Termo Fácil - Sistema Inteligente de Redação de Termos de Depoimentos

Um sistema *on-premise* baseado em Inteligência Artificial Generativa destinado a automatizar a transcrição e redação de Termos de Depoimento para a Secretaria de Segurança Pública do Estado do Piauí (SSP-PI).

## Arquitetura e Stack
O sistema adota uma **Arquitetura Orientada a Eventos (EDA)** com os seguintes componentes:
- **FastAPI**: BFF e API Gateway responsável pelo roteamento.
- **PostgreSQL**: Banco de dados relacional que guarda o controle de inquéritos, depoentes e estado da máquina de processamento.
- **Redis + Celery**: Message Broker que enfileira os áudios e interage de forma assíncrona com os Workers de IA.
- **MinIO**: Storage em S3-compatible utilizado para guardar arquivos pesados de áudio (.wav) antes do expurgo.
- **SQLAlchemy (ORM)**: Para abstração da modelagem de dados da API.

## Como Iniciar o Projeto (Backend)

Siga os passos abaixo para rodar a fundação do projeto em sua máquina local:

### 1. Iniciar Infraestrutura com Docker Compose
É obrigatório subir o PostgreSQL, Redis e MinIO para o funcionamento do sistema.
```bash
docker-compose up -d
```
> O banco de dados PostgreSQL iniciará automaticamente consumindo o schema `arquivos-projeto/modelo_bd.sql`.

### 2. Configurar o Ambiente Virtual Python
Navegue até a pasta `backend`, crie e ative seu ambiente virtual:

**No Windows:**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar as Dependências
Com o ambiente ativado, instale os pacotes necessários:
```bash
pip install -r requirements.txt
```

### 4. Rodar o Servidor FastAPI
Para rodar a aplicação em modo de desenvolvimento (hot-reload), utilize o Uvicorn dentro do diretório `backend`:
```bash
uvicorn app.main:app --reload
```
A API estará disponível em: `http://localhost:8000/docs`

> **Nota de Erro Comum (ModuleNotFoundError)**: Não tente rodar `python app/main.py` diretamente fora do diretório `backend` ou sem o ambiente virtual ativado, pois as importações (como `from app.core.config import settings`) não serão reconhecidas pelo caminho do Python.

## Estrutura do Backend
- `app/core/config.py`: Gestão de variáveis e chaves da infraestrutura.
- `app/db.py`: Conector do SQLAlchemy.
- `app/models.py`: Mapeamento ORM refletindo o esquema do banco de dados (Tabelas e Relacionamentos).
- `app/main.py`: Entrada principal.

O projeto garante o expurgo sistemático dos dados confidenciais (*Air-gapped Concept*) para conformidade com a LGPD e Segurança da Informação (WireGuard).
