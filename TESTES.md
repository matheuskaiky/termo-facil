# Testes & Benchmarks — Termo Fácil

> Documento de referência da estratégia de testes automatizados, benchmarks científicos
> (PIBITI) e CI/CD do projeto. Mantenha-o atualizado ao adicionar novos testes ou alterar
> a infraestrutura.

## Visão geral

| Camada | Framework | Local | Como rodar |
|---|---|---|---|
| Backend | pytest + pytest-mock + httpx | `backend/tests/` | `python -m pytest` (de `backend/`) |
| Frontend | Karma + Jasmine | `frontend/src/app/**/*.spec.ts` | `npm run test:ci` (de `frontend/`) |
| Benchmarks | jiwer / seqeval | `backend/scripts/benchmark_*.py` | `python scripts/benchmark_*.py` |
| CI/CD | GitHub Actions | `.github/workflows/ci.yml` | automático em push/PR para `main` |

**Estado atual:** 130 testes de backend passando, **82% de cobertura** (`--cov=app`).

---

## Backend (pytest)

### Estrutura

```
backend/
├── pytest.ini                  # config: markers, asyncio_mode, pythonpath, filtros
└── tests/
    ├── conftest.py             # fixtures: DB SQLite in-memory, client, test_user, storage/celery mocks
    ├── ai_availability.py      # detecção real-vs-mock (Whisper/LeNER/Ollama/PyAnnote)
    ├── mocks.py                # adapters mock dos Protocols (ports.py)
    ├── factories.py            # builders da cadeia ORM (Delegacia→…→TermosFinais)
    ├── pipeline_helpers.py     # executa process_audio_task com IA real ou mock
    ├── micro-machines.wav      # áudio de amostra (ASR)
    ├── unit/                   # security (JWT/bcrypt), mask_cpf, _validar_cpf, query_scopes, audit
    ├── services/               # pdf, speaker_role, llm, asr, storage, expurgo, diarization
    ├── api/                    # auth, admin, delegacias, audio, jobs, processos, metricas, pdf, termos, upload, idor
    ├── integration/            # pipeline ponta-a-ponta (mock) + ai_pipeline_real (requires_models)
    └── test_ner.py             # NER real (requires_models)
```

### Markers (`pytest.ini`)

| Marker | Significado |
|---|---|
| `unit` | rápido, isolado (sem DB/rede/modelos) |
| `integration` | usa o app FastAPI + DB SQLite |
| `requires_models` | exige modelo real (Whisper/LeNER/Ollama/PyAnnote); **pulado** automaticamente quando indisponível |
| `slow` | carregamento de modelo / processamento de áudio |

### Modelos reais vs. mock — `TEST_AI_MODE`

**Prioridade é rodar com modelos reais.** A política é controlada pela variável de ambiente
`TEST_AI_MODE`:

| Valor | Comportamento |
|---|---|
| `auto` (default) | usa o modelo **real quando detectado**, senão cai para mock — por serviço (ASR/NER/LLM independentes) |
| `real` | força modelos reais (pula/falha se ausente) |
| `mock` | força mocks (rápido, determinístico, usado no CI) |

A detecção (`tests/ai_availability.py`) é conservadora para manter a suíte verde offline:
- **Whisper:** importável **e** com pesos em cache **e** `ffmpeg` no PATH (o serviço decodifica áudio via ffmpeg);
- **LeNER-Br:** `transformers`+`torch` importáveis e modelo em cache HuggingFace;
- **Ollama:** servidor responde em `LLM_BASE_URL/api/tags`;
- Em `TEST_AI_MODE=real`, a checagem de cache é ignorada (tenta baixar).

> No ambiente de desenvolvimento atual o **LeNER-Br roda de verdade** nos testes; ASR real exige
> `ffmpeg` instalado e o benchmark LLM exige Ollama no ar (ver Limitações).

### Como rodar

```bash
cd backend
source ../.venv/bin/activate

python -m pytest                       # tudo (auto: real quando disponível)
python -m pytest --cov=app --cov-report=term-missing
python -m pytest -m "not requires_models"   # só o que roda sem modelos pesados (modo CI)
python -m pytest -m unit               # só unit
TEST_AI_MODE=mock python -m pytest     # força mocks (rápido)
TEST_AI_MODE=real python -m pytest -m requires_models   # força modelos reais

python -m pytest tests/api/test_pdf.py -v          # um arquivo
python -m pytest tests/api/test_auth.py::test_login_success
```

### Notas de infraestrutura

- **Banco:** SQLite in-memory (`StaticPool`); tipos PostgreSQL (`JSONB`/`UUID`/`BYTEA`) são
  recompilados para SQLite via `@compiles` no `conftest.py`.
- **Rate limiter:** o `slowapi` é um singleton global que conta por IP; ele é **desativado
  globalmente** nos testes (senão após 10 logins tudo vira HTTP 429). O teste
  `test_login_rate_limited_after_10_attempts` o reativa propositalmente.
- **`test_user`:** usuário "tudo-pode" (todas as permissões) para os testes de endpoint;
  cenários de negação (IDOR/RBAC) constroem usuários com escopo via `factories.py`.
- **Injeção de IA:** o design hexagonal (`app/services/ports.py`) permite trocar os adapters
  reais pelos mocks de `tests/mocks.py` sem tocar no pipeline.

---

## Benchmarks científicos (PIBITI — Fase 20)

Scripts em `backend/scripts/`, resultados gravados em `backend/benchmarks/results/*.json`.

| Script | Issue | Métrica | Critério de aceite |
|---|---|---|---|
| `benchmark_wer.py` | #28 | WER/CER + latência + **RTF** | WER ≤ 15% (US-02) |
| `benchmark_ner.py` | #29 | F1 / Precision / Recall (seqeval) | F1 ≥ 0.85 (US-03) |
| `benchmark_llm.py` | #30 | latência + fidelidade factual | latência < 5s; fidelidade > 80% |

### Como rodar

```bash
cd backend
python scripts/benchmark_wer.py --model base          # transcrição real (ffmpeg-free loader)
python scripts/benchmark_ner.py                        # baixa LeNER (~1.3GB) no 1º uso
python scripts/benchmark_llm.py --models llama3        # exige `ollama serve` + `ollama pull llama3`
```

### Resultados reais (execução de Junho/2026, CPU)

**ASR — Whisper `base`** (sobre `tests/micro-machines.wav`, 29,89 s de áudio):

| Métrica | Valor |
|---|---|
| Latência | 6,84 s |
| **RTF** (tempo / duração) | **0,229** (~4,4× mais rápido que tempo real) |
| WER | N/A — sem corpus de áudio rotulado em PT-BR |

**NER — LeNER-Br** (`pierreguillou/ner-bert-large-cased-pt-lenerbr`, 3 sentenças anotadas):

| Métrica | Valor |
|---|---|
| **F1-Score** | **90,9%** |
| Precision | 100,0% |
| Recall | 83,3% (perdeu a entidade `LEGISLACAO` "Lei 8.072/1990") |

**LLM — Ollama/llama3:** ⏳ pendente — requer o servidor Ollama em execução (não disponível
no ambiente de CI/dev atual). O script grava `{"status": "skipped — Ollama unavailable"}`.

> **Sobre o WER:** o cálculo de WER exige áudio com transcrição de referência (ground-truth).
> O projeto ainda não dispõe de um corpus rotulado de depoimentos em PT-BR, então o benchmark
> executa **transcrição real** e mede latência/RTF, deixando o WER pendente de um corpus rotulado
> (entrada necessária para a validação completa da US-02). O benchmark anterior era **fictício**
> (comparava a referência com ela mesma alterada) e foi reescrito para inferência real.

---

## Frontend (Karma + Jasmine)

Specs em `frontend/src/app/`:

- `app.component.spec.ts` — criação + `showHeader`
- `services/auth.guard.spec.ts` — login/forced-change/acesso
- `services/permission.guard.spec.ts` — leitura genérica de `route.data['permission']`, redirect silencioso
- `services/auth.service.spec.ts` — decode JWT, expiração, merge de perfil, login/logout (axios mockado)

```bash
cd frontend
npm install
npm run test:ci        # ChromeHeadless, single-run
npm run build          # build de produção
```

> Requer Chrome/Chromium instalado (`CHROME_BIN`). O CI instala via `browser-actions/setup-chrome`.

---

## CI/CD — GitHub Actions

`.github/workflows/ci.yml`, disparado em push/PR para `main`:

- **`backend-tests`**: Python 3.12, instala `requirements*.txt`, roda
  `pytest -m "not requires_models" --cov=app` em `TEST_AI_MODE=mock`. Variáveis de ambiente
  obrigatórias (`config.py` não tem defaults inseguros) são injetadas no job:
  `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `APP_ENV=test`.
- **`frontend-tests`**: Node 20, `npm ci`, `npm run test:ci` (ChromeHeadless) e `npm run build`.

Testes `requires_models` **não rodam no CI** (sem GPU/ffmpeg/Ollama) — devem ser executados no
HPC Mandu / cluster NCAD UFPI.

---

## Bugs reais encontrados pelos testes

A construção da suíte revelou e corrigiu falhas de runtime:

1. **Upload quebrado (`upload.py`):** `async for chunk in file` não funciona — `UploadFile` não é
   async-iterável nesta versão do Starlette. Substituído por `await file.read(chunk)`. **Todo upload
   estava falhando** antes da correção.
2. **Expurgo LGPD nunca funcionava (`expurgo.py` + `models.py`):** a task de segurança RN-04 fazia
   `midia.storage_path = None`, mas a coluna era `NOT NULL` → `IntegrityError` + rollback a cada
   ciclo. Coluna tornada `nullable=True` + migração idempotente em `scripts/migrate.py`.
3. **Benchmark LLM (`benchmark_llm.py`):** chamava `synthesize(transcript=...)`, mas o parâmetro é
   `text` → falharia mesmo com Ollama no ar. Corrigido.
4. **Benchmark WER fictício:** reescrito para inferência real (loader de áudio sem ffmpeg).

---

## Limitações conhecidas / pendências

- **ffmpeg ausente** no ambiente atual → testes de ASR real via serviço (`requires_models`) são
  pulados; o benchmark WER usa loader próprio sem ffmpeg.
- **Ollama ausente** → benchmark LLM e teste LLM real pendentes (rodar no HPC).
- **Corpus PT-BR rotulado** ausente → número de WER pendente para a US-02.
- Cobertura de componentes Angular complexos (auditoria) ainda é mínima — guards/serviços cobertos.
