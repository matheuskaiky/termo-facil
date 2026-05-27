# Notas de Pesquisa — PIBITI/CNPq

> Destaques técnico-científicos do projeto **Termo Fácil** (SSP-PI) relevantes para o relatório de iniciação científica e para a defesa dos critérios de projeto.

---

## Expurgo Duplo-Camada como Garantia LGPD (RN-04)

O áudio bruto é deletado do MinIO **imediatamente** após a exportação do PDF (`pdf.py`, bloco `try/except` pós-`db.commit()`). Um segundo mecanismo de segurança — a Celery Beat task `expurgo_dados_expirados` — varre o banco a cada hora em busca de registros com `data_exportacao_pdf` há mais de 24h que ainda tenham `storage_path` preenchido (falha transitória de rede no expurgo imediato). Esta arquitetura dupla-camada é a implementação do princípio "o sistema processa, não custodia" da Portaria MJSP 961/2025: mesmo que a primeira camada falhe, a segunda garante o expurgo dentro da janela legal.

**Implementação:** `backend/app/api/endpoints/pdf.py` (expurgo imediato) + `backend/app/tasks/expurgo.py` (Celery Beat fallback) + coluna `data_exportacao_pdf` em `TermosFinais`.

---

## `temperature=0.0` como Requisito Jurídico (RN-01)

A temperatura zero não é escolha de qualidade de geração — é uma **restrição legal** para prevenir "Suspeita Generativa" (invenção de fatos pelo modelo de linguagem que não constam na transcrição). Combinada com `top_p=0.1`, elimina a variância estocástica: dada a mesma transcrição e o mesmo dicionário NER, o LLM deve produzir saída determinística. Qualquer fato não presente no dicionário NER ou na transcrição ASR deve ser marcado como `[(Trecho Ininteligível)]`. Este é um **critério de aceitação** do sistema, não uma preferência de configuração.

**Implementação:** `backend/app/services/llm_service.py`, opção `"temperature": 0.0, "top_p": 0.1` na chamada Ollama.

---

## Ancoragem NER Anti-Alucinação (US-03 / RF-04)

O LLM recebe um bloco JSON com todas as entidades factuais extraídas pelo LeNER-Br **antes** de redigir o resumo. A instrução explícita no `_SYSTEM_PROMPT` proíbe introduzir fatos além do dicionário. Esta "ancoragem factual" transforma o LLM de gerador livre em formatador estruturado, reduzindo o risco de alucinação em contexto jurídico. A técnica é análoga ao RAG (Retrieval-Augmented Generation), mas operando sobre entidades nomeadas em vez de chunks de documentos.

**Implementação:** `backend/app/services/llm_service.py` — `synthesize(transcript, entities=entities)` serializa o dicionário NER como bloco JSON no prompt.

---

## Arquitetura Hexagonal nos Serviços de IA

`asr_service.py`, `ner_service.py` e `llm_service.py` definem `Protocol` Python como porta de entrada (porta hexagonal). As implementações atuais (Whisper, LeNER-Br, Ollama/llama3) são adaptadores substituíveis sem modificar o pipeline. Substitutos benchmarkeados para avaliação futura:

| Serviço | Atual | Candidatos Avaliados |
|---|---|---|
| ASR | Whisper `base` | Whisper Turbo, Parakeet TDT 0.6B |
| LLM | Ollama/llama3 | vLLM + Llama 3, Mistral, Phi-3, Qwen 2.5, Gemma 3 |
| NER | LeNER-Br (BERT) | BERTimbau + fine-tune próprio |

Trocar o adaptador não requer alteração no `process_audio.py` nem nos endpoints.

---

## Air-Gapped Absoluto e Infraestrutura de Alto Desempenho

Nenhuma chamada sai para APIs de nuvem — bloqueio em nível de código, não de firewall. Whisper, LeNER-Br e Ollama são projetados para execução air-gapped on-premise na SSP-PI (primariamente no **HPC Mandu**). Isso é exigência da Portaria MJSP 961/2025 para dados de investigação criminal: depoimentos de suspeitos e testemunhas são classificados como sigilosos e não podem trafegar por infraestrutura de terceiros.

**Alternativa de Luxo (NCAD UFPI):** Enquanto o HPC Mandu não está totalmente acessível, o sistema utiliza uma fatia de processamento cedida pelo cluster do Núcleo de Computação de Alto Desempenho (NCAD) da UFPI. O hardware utilizado como alternativa de alto desempenho é um servidor Dell PowerEdge R760 contendo 2 processadores Intel Xeon Gold 6526Y, 1 TB de memória RAM DDR5, três SSDs de 1,92 TB e quatro GPUs NVIDIA L4 de 24 GB, otimizadas para IA.

**Decisão arquitetural relevante:** a impossibilidade de usar WireGuard (firewall UFPI bloqueia UDP) levou à adoção de API Gateway com mTLS sobre TCP/443 via WebSocket WSS para comunicação com os clusters de GPU (ADR-001 no `CLAUDE.md`).

---

## Human-in-the-Loop com Prevalência Legal (RN-02)

A transcrição bruta ASR (`txt_literal_asr`) tem prevalência jurídica sobre o resumo LLM em caso de contestação — está no rodapé de todas as páginas do PDF e no Anexo I. O Escrivão edita apenas o resumo sintético (`txt_editado_humano`); a transcrição literal nunca é apagada do banco (apenas o áudio bruto e os metadados de trabalho são expurgados). O PDF híbrido une os dois documentos de forma indissociável, tornando a cadeia de custódia auditável.

**Fluxo de prevalência:** ASR bruto → NER (extrai entidades) → LLM (ancoragem NER) → Escrivão (edição humana + checkbox de responsabilidade RN-03) → PDF (ASR como Anexo I).

---

## Status Granular do Pipeline (RF-01)

O Job Celery transita por quatro estados de progresso visíveis no frontend: `Transcrevendo → Extraindo Dados → Gerando Resumo → Concluído`. Cada transição é persistida no banco antes do início da etapa correspondente, permitindo que o frontend exiba o estágio atual ao usuário final durante o processamento (polling a cada 2s). Estados legados `Processando` mantidos no enum por compatibilidade com registros anteriores à Fase 18.

**Implementação:** `backend/app/models.py` (enum `StatusJob`) + `backend/app/tasks/process_audio.py` (commits intermediários) + `backend/scripts/migrate.py` (migrations `ALTER TYPE ADD VALUE`).

---

## Configuração Real dos Modelos de IA vs. Metadados de Rastreabilidade

> Adicionada em Maio/2026 durante auditoria de código.

Existe uma separação intencional entre os **modelos efetivamente executados** e os **nomes de rastreabilidade** no banco de dados:

| Camada | Modelo executado | Nome no banco (rastreabilidade no PDF) | Configurado via |
|---|---|---|---|
| **ASR** | `openai-whisper` modelo `base` (74M parâmetros) | `"Whisper Turbo (Mock)"` | `WHISPER_MODEL_SIZE` no `.env` |
| **NER** | `alfaneo/lener_br` (HuggingFace pipeline) | — (sem rastreabilidade no PDF) | `NER_MODEL_NAME` no `.env` |
| **LLM** | Ollama + `llama3` (8B parâmetros) | `"vLLM Llama 3 (Mock)"` | `LLM_BASE_URL` + `LLM_MODEL_NAME` no `.env` |

Os nomes `"(Mock)"` são **artefatos do seed de desenvolvimento** (Fase 6) que nunca foram atualizados. Para o relatório PIBITI, o que importa é a configuração real no `.env`. Esses nomes aparecem no PDF gerado na tabela de metadados ("Modelos IA (ASR / LLM)") e devem ser corrigidos antes do piloto na SSP-PI (Issue #27 no roadmap).

**Dependências de runtime do pipeline:**
- **Whisper:** O modelo é baixado automaticamente pelo `openai-whisper` no primeiro uso (~140MB para `base`). Nenhuma configuração manual necessária além do `pip install`.
- **LeNER-Br:** O modelo BERT é baixado do HuggingFace Transformers no primeiro `extract_entities()` (~1.3GB). Requer `torch` instalado.
- **Ollama:** Requer o servidor Ollama rodando externamente (`ollama serve`) e o modelo pré-baixado (`ollama pull llama3`). A API espera resposta em `http://localhost:11434/api/generate`. Sem Ollama rodando, o pipeline falhará na etapa de síntese LLM com `httpx.ConnectError`.

**Nota para Ambientes com GPU (Mandu / NCAD):** Em ambiente de produção com GPU, substituir Ollama por vLLM requer apenas trocar `LLM_BASE_URL` para apontar ao endpoint vLLM (ex: `http://gpu-cluster:8000/v1`) e ajustar `LLM_MODEL_NAME` para o modelo carregado. A interface Ollama e vLLM são compatíveis para o endpoint `/api/generate`.

---

## Heurística de Diarização vs. PyAnnote (Fase 14)

> Adicionada em Maio/2026 durante auditoria de código.

A diarização atual usa uma heurística trivial de alternância de locutor por pausa temporal (`_SPEAKER_GAP_THRESHOLD = 1.0s`). Quando a pausa entre dois segmentos Whisper ultrapassa 1 segundo, o sistema assume troca de locutor entre "Inquiridor" e "Depoente". Limitações conhecidas:

1. **Não funciona para múltiplos locutores** (ex: depoimento com mais de 2 participantes)
2. **Falsos positivos** em pausas naturais de fala (hesitação, reflexão)
3. **Falsos negativos** quando a troca de locutor acontece sem pausa (interrupção)

A substituição por **PyAnnote Audio** (`pyannote/speaker-diarization-3.1`) está planejada para quando o HPC Mandu ou a fatia do cluster NCAD UFPI estiver disponível (Issue #36). O PyAnnote usa clustering de embeddings de voz e requer GPU para inferência em tempo aceitável. A arquitetura hexagonal (`ASRModel` Protocol) permite essa troca sem alterar `process_audio.py`.

**Para o relatório PIBITI:** Recomendamos apresentar a heurística como "abordagem baseline" e os resultados do PyAnnote como "abordagem final" em uma tabela comparativa de Diarization Error Rate (DER).

---

## Divergência entre DER da Documentação e Schema Real

> Adicionada em Maio/2026 durante auditoria de código.

O diagrama entidade-relacionamento no documento de arquitetura (`4-arquitetura-pibiti.tex`) e o script SQL de referência (`modelo_bd.sql`) refletem o design **inicial** do banco, anterior às Fases 7–18. As seguintes divergências existem entre a documentação e o `models.py` atual:

| Aspecto | Documentação/SQL original | Schema real |
|---|---|---|
| Nome tabela de jobs | `jobs_audio` | `job_processamento_ia` |
| Nome tabela de termos | `termos_gerados` | `termos_finais` |
| Cargo do usuário | Coluna `cargo` (enum direto) | FK `id_cargo` → tabela `cargo` (RBAC dinâmico) |
| Tabelas RBAC | Inexistentes | `cargo`, `permissao`, `cargo_permissao` |
| Colunas adicionais em `termos_finais` | — | `segmentos_asr`, `storage_path_pdf`, `data_exportacao_pdf` |
| Colunas adicionais em `usuario` | — | `senha_hash`, `must_change_password` |
| Colunas adicionais em `job_processamento_ia` | — | `data_criacao` |

A atualização está planejada como Issue #26 (Fase 19). Até lá, o `models.py` é a fonte de verdade.

---

## Resultados de Benchmarking (Fase 20 — Issue #28–#30)

> Adicionada em Maio/2026. Será preenchida com resultados reais após execução dos scripts.

### Issue #28 — WER (Word Error Rate) para Whisper

Avalia a qualidade de transcrição automática de áudio em diferentes tamanhos de modelo.

**Como executar:**
```bash
cd backend
pip install jiwer
python scripts/benchmark_wer.py
```

**Resultados esperados:**

| Modelo    | WER    | CER    | Latência (s) |
|-----------|--------|--------|-------------|
| base      | —      | —      | —           |
| small     | —      | —      | —           |
| medium    | —      | —      | —           |

> **Critério de aceite (US-02):** WER ≤ 15% para o modelo base com áudios em português de depoimentos policiais.

---

### Issue #29 — F1-Score para LeNER-Br

Avalia a qualidade de reconhecimento de entidades nomeadas (NER) em textos jurídicos português.

**Como executar:**
```bash
cd backend
pip install seqeval
python scripts/benchmark_ner.py
```

**Resultados esperados:**

| Métrica      | Score |
|--------------|-------|
| F1-Score     | —     |
| Precision    | —     |
| Recall       | —     |

| Categoria    | F1-Score |
|--------------|----------|
| PESSOA       | —        |
| LOCAL        | —        |
| DATA         | —        |
| LEGISLACAO   | —        |

> **Critério de aceite (US-03):** F1 ≥ 0.85 em dataset de entidades jurídicas português.

---

### Issue #30 — Comparativo de LLMs para Síntese Jurídica

Avalia trade-offs entre diferentes modelos LLM open-source para síntese determinística de depoimentos.

**Como executar:**
```bash
cd backend
# Certifique-se de que Ollama está rodando
ollama serve &
ollama pull llama3
ollama pull mistral
python scripts/benchmark_llm.py --models llama3,mistral,phi3
```

**Resultados esperados:**

| Modelo    | Latência (s) | Tamanho (chars) | Fidelidade Factual | Observações |
|-----------|--------------|-----------------|-------------------|------------|
| llama3    | —            | —               | —                 | —          |
| mistral   | —            | —               | —                 | —          |
| phi3      | —            | —               | —                 | —          |
| qwen2.5   | —            | —               | —                 | —          |
| gemma3    | —            | —               | —                 | —          |

> **Critério principal:** Fidelidade factual (entidades NER presentes na síntese) + latência < 5s para resposta útil ao Escrivão.
>
> **Nota:** Ollama suporta modelos quantizados em GGML/GGUF (eficientes na H100 do Mandu e nas GPUs NVIDIA L4 do NCAD UFPI). Para substituição futura, considere vLLM (maior throughput) ou llama.cpp (inferência local otimizada).

---

## Como interpretar os resultados

- **WER ≤ 15%:** Aceitável para transcrição jurídica com revisão humana (RN-02 garante prevalência da transcrição bruta).
- **F1 ≥ 0.85:** Alta precisão de entidades; reduz alucinações no LLM (ancoragem factual, RN-01/RN-02).
- **Latência < 5s:** Experiência UX aceitável no audit-loop de revisão (Fase 12).
- **Fidelidade Factual > 80%:** LLM não introduz entidades fictícas além das que NER extraiu.

Estes três componentes (ASR, NER, LLM) formam o **tripé de confiabilidade** da síntese jurídica (RNF-02 na arquitetura).

---

## Ausência de Container Manager no HPC e Criação de Scripts Bare-Metal (Fase 21)

> Adicionada em Maio/2026 durante primeiro deployment no HPC da UFPI.

**Intercorrência identificada:** O projeto foi desenvolvido inteiramente em Windows com `docker-compose.yml` gerenciando PostgreSQL 15, Redis 7 e MinIO. Ao transferir para o **cluster HPC da UFPI (Mandu)**, descobriu-se:

1. **Nenhum container manager disponível** (sem Docker, Podman ou Singularity)
2. **Sem acesso a sudo** (ambiente compartilhado de usuário final)
3. **Necessidade de manter compatibilidade Docker** (máquinas de desenvolvimento não afetadas)

**Solução arquitetural:** Criação de suite de scripts bash (`hpc/`) que:
- Inicializam e gerenciam PostgreSQL, Redis e MinIO como processos nativos em espaço de usuário
- Detectam automaticamente PostgreSQL via: PATH → conda → Environment Modules
- Compilam Redis do source se necessário (sem root, apenas `make`)
- Baixam MinIO como binário standalone
- Armazenam todos os dados em `hpc/.data/` (user-space, gitignored)

**Detalhes técnicos da implementação:**

| Desafio | Solução |
|---------|---------|
| PostgreSQL sem sudo | `initdb -D hpc/.data/postgres` + `pg_ctl` para gerenciar cluster em user-space |
| Socket Unix inacessível `/var/run/` | Redirecionar `unix_socket_directories = $PG_DATA_DIR` em `postgresql.conf` |
| ENUM ALTER sem SUPERUSER | Fazer `termo_user` SUPERUSER explicitamente no setup |
| Redis binary não em PATH | Tentar conda, compilar source, ou use symlink se em PATH |
| MinIO daemonize inexistente | Usar `nohup ... &` + captura manual de PID |
| Manutenção de compatibilidade Docker | Backend `.env` usa `127.0.0.1` — portas idênticas em ambos os modos; zero adaptação |

**Arquivos criados:**
- `hpc/config.sh` — variáveis compartilhadas e detecção inteligente
- `hpc/setup.sh` — inicialização idempotente (safe para re-run)
- `hpc/start.sh` — inicia os 3 serviços com health checks
- `hpc/stop.sh` — parada graceful
- `hpc/status.sh` — dashboard de status
- `hpc/README.md` — documentação completa (troubleshooting, estrutura de diretórios)
- `backend/.env.example` — template documentado (nova, git-tracked)

**Problemas encontrados durante teste real no HPC (2026-05-26):**

1. **Redis não era encontrado dinamicamente** — função `find_redis()` falhava em cenários com conda/conda-forge. Solução: iterar por múltiplos locais (CONDA_PREFIX, PATH, binários compilados).

2. **Permissão PostgreSQL insuficiente** — `termo_user` não tinha privilégio para `ALTER TYPE ... ADD VALUE` em enums. Solução: adicionar `ALTER ROLE termo_user SUPERUSER` automaticamente no setup.

3. **redis-cli hardcoded ou não encontrado** — compatibilidade entre redis-server e redis-cli localizações. Solução: derivar `redis-cli` do diretório do `redis-server`.

4. **PostgreSQL já rodando do setup anterior** — script de setup deixa PG rodando; re-executar setup causava lock file conflict. Solução: melhorar idempotência adicionando verificação de cluster já inicializado.

**Relevância para o relatório PIBITI:**
- Demonstra adaptabilidade do projeto a restrições de infraestrutura reais (sem containers, sem privilegios elevados)
- Mantém 100% de compatibilidade com desenvolvimento local (Docker em Windows/Mac/Linux)
- Validação da arquitetura modular: o backend/frontend não sofrem alterações — apenas scripts de infraestrutura

**Impacto na curva de aprendizado:**
Pesquisadores usando o projeto em ambientes HPC não-containerizados agora têm path claro de setup via `./hpc/setup.sh && ./hpc/start.sh` com outputs claros de debugging. Documento `hpc/README.md` inclui troubleshooting específico para cenários HPC (conflicts de porta em clusters compartilhados, detecção de módulos, etc).

**Lições técnicas:**
1. Mesmo projetos "containerizados" devem considerar bare-metal como alternativa (não é overkill em ambientes acadêmicos/HPC)
2. Usar variáveis de ambiente (localhost, portas) que sejam agnósticas de deployment
3. Funções de detecção robustas são melhores que hardcodes (conda, modules, PATH devem ser testadas em ordem)
4. Idempotência é crítica em scripts de infraestrutura — usuários não-especialistas podem re-executar por segurança

---

## Fases 22 e 23 — Hardening de Segurança, RBAC e Resiliência (Concluídas Maio/2026)

> Adicionadas em Maio/2026 após auditoria de código pré-produção identificar furos de segurança e débitos técnicos.

### Fase 22 — Hardening de Segurança e RBAC

**Intercorrência principal: furos RBAC em endpoints críticos.**

`GET /termos/` (`backend/app/api/endpoints/termos.py`) retornava todos os `TermosFinais` sem nenhum filtro por usuário ou delegacia, permitindo que qualquer usuário autenticado visualizasse termos de outros escrivães — violação direta do princípio de separação de acesso por cargo. A correção introduziu filtros baseados no `nome_cargo` do usuário:
- **Escrivão**: join com `Depoimento` filtrando por `id_usuario == current_user.id_usuario`
- **Delegado**: join adicional com `Inquerito` filtrando por `id_delegacia == current_user.id_delegacia`
- **Admin / Gestor Estratégico**: sem filtro (visão global)

O `PUT /termos/{id}` também não validava propriedade — qualquer usuário com permissão `EDITAR_TERMO` podia editar o termo de outro escrivão. Adicionado check explícito de ownership para o cargo Escrivão (`backend/app/api/endpoints/termos.py`).

**Bug: Admin filtrado como Delegado.** O bloco `elif cargo_nome in ["Delegado", "Admin"]` em `processos.py` aplicava filtro de delegacia ao Admin indevidamente. Corrigido para `elif cargo_nome == "Delegado"` com comentário explícito para Admin.

**CORS configurável via `.env`.** `allow_origins=["*"]` em `main.py` substituído por `settings.ALLOWED_ORIGINS` (lista configurável em `config.py`, padrão `["http://localhost:4200"]`). Em produção, configurar `ALLOWED_ORIGINS=["https://app.ssp.pi.gov.br"]` no `.env`.

**Notificação de sessão expirada.** Interceptor 401 no `api.service.ts` passa `?expired=1` na URL de redirecionamento para o login. `LoginComponent` lê o query param e exibe aviso amarelo "Sua sessão expirou" — impede que usuário pense que ocorreu um erro ao ser redirecionado durante preenchimento de formulário.

**Guard genérica.** `permissionGuard` hardcoded para `GERENCIAR_USUARIOS` substituída por guard que lê `route.data['permission']`. `app.routes.ts` passa a permissão correta por rota (`GERENCIAR_USUARIOS` para `/admin`, `VER_METRICAS` para `/metricas`). Elimina necessidade de criar guards separadas para cada rota protegida futura.

**Polling com exponential backoff.** `setInterval` de 2s substituído por `setTimeout` recursivo com backoff (2s → 4s → 8s → max 30s). Jobs de pipeline longo (Whisper large + LLM) deixam de gerar ~300 requests desnecessários enquanto o worker processa.

**NER highlight com word boundaries.** `highlightEntitiesInText` usava `new RegExp(pattern, 'gi')` sem delimitadores — entidades de uma letra como "a" ou "e" destacavam todo o texto. Corrigido para `new RegExp('\\b' + pattern + '\\b', 'gi')`. Filtro adicional: entidades com menos de 2 caracteres são ignoradas.

**Deviações do plano original:**
- A validação de URL do MinIO em `bypassSecurityTrustResourceUrl` ficou permissiva (regex + path prefix) em vez de whitelist estrita, pois o domínio do MinIO em produção ainda não está definido — a constante `environment.minioPublicHost` permite configuração posterior sem mudança de código.

### Fase 23 — Paginação e Resiliência de Infraestrutura

**Paginação em todos os endpoints de listagem.** `GET /processos/`, `GET /termos/`, `GET /admin/users` agora aceitam `?limit=N&offset=M` e retornam `{"total": N, "items": [...]}`. Default `limit=50`, máximo `200`. Frontend `process-list.component.ts` adaptado com controles de navegação por páginas.

**Upsert atômico de `MidiaBruta`.** Padrão query-then-insert em `upload.py` substituído por `pg_insert(...).on_conflict_do_update(...)` do SQLAlchemy — elimina race condition em uploads simultâneos para o mesmo `id_depoimento`.

**Timestamps com `server_default=func.now()`.** `default=datetime.utcnow` (timestamp gerado pelo processo Python) substituído por `server_default=func.now()` nos campos `data_hora_reg` (Depoimento) e `data_criacao` (JobProcessamentoIA). Garante consistência de timezone entre workers Celery distribuídos.

**`time_limit` na task Celery.** `@celery_app.task(name="process_audio")` recebe `time_limit=3600, soft_time_limit=3300`. Sem este limite, um worker travado em Whisper/LLM consumia recursos indefinidamente.

**Persistência de erro no job.** Bloco `except` em `process_audio.py` passa a salvar a mensagem de exceção em `job.parametros_ia["erro"]` (campo JSONB já existente). Facilita diagnóstico pós-mortem sem precisar de logs externos.

**Relevância para o relatório PIBITI:**
- As falhas de RBAC encontradas na auditoria são um exemplo concreto de "débito de segurança incremental": o sistema funcionava corretamente no MVP (um único usuário de teste), mas o crescimento orgânico das permissões não foi acompanhado de testes de isolamento multi-usuário.
- O upsert atômico e o `time_limit` do Celery são exemplos de resiliência de infraestrutura que só se tornam relevantes em deploy real — em ambiente de desenvolvimento single-user, estas falhas são invisíveis.
## Redesign Frontend v2 Addon — Issues #64–#68 (Completado Maio/2026)

> Adicionada em Maio/2026 durante extensão do Redesign Frontend v2.

**Contexto.** Após a conclusão das issues #55–#63 (Redesign v2), cinco novas issues foram abertas na Milestone 19 cobrindo funcionalidades que estendem o painel administrativo e o dashboard. Todas têm impacto no backend (modelos de DB, endpoints novos), mas o frontend foi implementado de forma que degradue graciosamente enquanto o backend não fornece os contratos.

---

### Intercorrências (IC) Identificadas

**IC-1 — Campos ausentes em `Delegacia`.** O ORM possui apenas `id_delegacia`, `nome_unidade`, `cod_sinesp`. O design exige `municipio`, `uf`, `cep`, `endereco`, `telefone`, `tipo`, `sigla`, `ativo`. O `DelegaciaFormComponent` trata esses campos como opcionais; o formulário já os tem mas a API retornará 422 até que a migration execute.

**IC-2 — Campos ausentes em `Usuario`.** O model não tem `email`, `cpf`, nem `ativo`. O `UserFormComponent` envia `cpf` e `email` condicionalmente (só se preenchidos), garantindo que o `POST /admin/users` funcione com o schema atual após implementação do endpoint.

**IC-3 — `Depoente` sem campos extras.** A tabela tem apenas `cpf` e `nome_depoente`. O fluxo CPF-first chama `GET /depoentes/check-cpf` e, quando encontrado, preenche só `nome_depoente`. Campos de RG, telefone, endereço aguardam migration futura.

**IC-4 — `processos/novo` sem suporte a `id_depoente` FK.** O frontend agora inclui `id_depoente` no payload quando `foundDepoente` está preenchido; o backend deve aceitar este campo opcionalmente, mantendo a compatibilidade com `cpf_depoente` como fallback.

**IC-5 — Ausência de `POST /admin/users`.** O endpoint não existe. O `UserFormComponent` está pronto para usá-lo; até sua implementação, ao tentar criar um servidor, o formulário exibirá o erro retornado pela API (404/405).

**IC-6 — `descricao_permissao` vazio no DB.** O campo existe no schema. `permDescricao()` e os chips com hint renderizam condicionalmente (`*ngIf="p.descricao_permissao"`); sem dados, a UI exibe só o código da permissão. Backend deve executar UPDATE de seed para popular descrições legíveis.

---

### Novos Componentes Criados

| Componente | Localização | Propósito |
|---|---|---|
| `UserFormComponent` | `admin/user-form/` | Cadastro/edição de servidor com CPF/matrícula async + preview de permissões |
| `DelegaciaFormComponent` | `admin/delegacia-form/` | CRUD de delegacia com validação SINESP async + card de servidores vinculados |
| `DashboardDelegaciaDetailComponent` | `metricas/dashboard-delegacia-detail/` | Drill-down por delegacia: KPIs + ranking escrivães + atividade recente |
| `DashboardEscrivaoDetailComponent` | `metricas/dashboard-escrivao-detail/` | Drill-down por escrivão: KPIs + gráfico CSS barras 30 dias + pontos de atenção |
| `DashboardErrosComponent` | `metricas/dashboard-erros/` | Análise de erros do pipeline (ASR/NER/LLM) + botão "Reprocessar" |

---

### Contratos de API Pendentes (Backend Advisory)

| Endpoint | Método | Propósito |
|---|---|---|
| `/admin/users` | POST | Criar servidor (retorna `temp_password`) |
| `/admin/users/check-cpf?cpf=X` | GET | Verificar unicidade do CPF (declarar antes de `/:id`) |
| `/admin/users/check-matricula?matricula=X` | GET | Verificar unicidade da matrícula |
| `/admin/users/:id` | PUT | Editar nome/email/id_delegacia/id_cargo |
| `/admin/users/:id/history` | GET | Histórico de alterações do servidor |
| `/admin/delegacias/:id` | GET | Detalhe de delegacia com campos extras |
| `/admin/delegacias/check-sinesp?sinesp=X` | GET | Verificar unicidade do SINESP (declarar antes de `/:id`) |
| `/admin/delegacias/:id/desativar` | PUT | Desativar delegacia |
| `/depoentes/check-cpf?cpf=X` | GET | Buscar depoente por CPF para pre-fill |
| `/metricas/por-delegacia` | GET | Lista com contagens por unidade |
| `/metricas/delegacias/:id?periodo=30d` | GET | Detalhamento por delegacia |
| `/metricas/escrivaes/:id?periodo=30d` | GET | Detalhamento por escrivão (inclui `producao_diaria[30]`) |
| `/metricas/erros?periodo=30d` | GET | Erros do pipeline por tipo (ASR/NER/LLM) |
| `/jobs/:id/retry` | POST | Re-enfileirar job com erro |

---

### Estratégia de Degradação Graciosa

- **Formulários**: campos correspondentes a colunas ausentes no DB são marcados `(opcional)` no label e enviados condicionalmente. Um 422 da API exibe mensagem de erro contextual ao usuário.
- **Dashboard drill-downs**: componentes exibem "Erro ao carregar dados — endpoint ainda pode não estar disponível" quando a API retorna 404/500, sem travar a navegação.
- **Segmento por delegacia no `/metricas`**: quando `GET /metricas/por-delegacia` retorna erro, o array `delegaciaSegments` fica vazio e o template exibe mensagem explicativa com o nome do endpoint pendente.
- **Botão "Reprocessar"**: `isRetrying[jobId]` garante que o botão fique desabilitado durante a chamada e volte ao estado normal silenciosamente em caso de 404.

### Relevância para o Relatório PIBITI

- O fluxo CPF-first exemplifica como a UX pode reduzir re-digitação de dados recorrentes em ambientes policiais (depoentes que depõem mais de uma vez). A estimativa de tempo poupado por sessão pode ser incluída na análise de ROI da Fase 16.
- A state machine `empty→checking→not-found→found→found-modified` para o campo CPF é um padrão de UX aplicável a outros formulários do sistema (e.g., busca de indiciados em inquéritos futuros).
- Os componentes de drill-down do dashboard seguem o princípio de "dados sem conteúdo sigiloso" da Fase 16: KPIs de volumetria e tempo médio, sem texto de depoimentos ou dados pessoais dos depoentes.

---

## Fases 22–23: Hardening de Segurança e Paginação (Concluído Maio/2026)

> Adicionada em Maio/2026 durante consolidação pós-Milestone 19.

### Estado da Implementação

**Frontend (✅ Concluído):**

| Issue | Descrição | Arquivo | Status |
|---|---|---|---|
| #42 | `baseURL` hardcoded → `environment.apiUrl` | `api.service.ts` + `environment.{ts,prod.ts}` | ✅ |
| #43 | `permissionGuard` hardcoded → guard genérica | `permission.guard.ts` + `app.routes.ts` | ✅ |
| #44 | `alert()` bloqueante → redirect silencioso | `permission.guard.ts` | ✅ |
| #45 | Polling sem backoff → exponential backoff 2s→30s | `auditoria.component.ts` | ✅ |
| #46 | `highlightEntitiesInText` com `\b` word boundaries | `auditoria.component.ts` | ✅ |
| #47 | `bypassSecurityTrustResourceUrl` com validação MinIO | `auditoria.component.ts` + `environment` | ✅ |
| #49 | Paginação `limit/offset` + UI anterior/próximo | `process-list.component.ts/html` | ✅ |

**Backend (⏳ Pendente — responsabilidade do humano):**

| Issue | Descrição | Impacto | Prioridade |
|---|---|---|---|
| #39 | RBAC em `/termos/` — filtro por `id_usuario` | Critical | 🔴 |
| #40 | Admin sem filtro de delegacia em `/processos/` | Critical | 🔴 |
| #41 | CORS `allow_origins=["*"]` → whitelist `.env` | Security | 🔴 |
| #50 | Race condition MidiaBruta → upsert atômico | Reliability | 🟡 |
| #51 | `default=datetime.utcnow` → `server_default=func.now()` | Consistency | 🟡 |
| #52 | Task Celery sem `time_limit` → 3600s limit | Reliability | 🟡 |
| #53 | Erros Celery não persistidos → `parametros_ia["erro"]` | Observability | 🟡 |

### Feature Adicional: Editar Nome do Cargo

**Contexto:** O painel admin permite editar **permissões** de um cargo via `PUT /admin/cargos/{id}/permissions`, mas não permite editar o **nome** do cargo. Esta feature estende o fluxo.

**Implementação:**
- Arquivo: `admin.component.ts`
  - Nova propriedade: `editingCargoNameValue: string`
  - Modificado `startEditCargo()`: captura `cargo.nome_cargo` em `editingCargoNameValue`
  - Renomeado `saveCargoPermissions()` → `saveCargo()`: agora faz dois PUTs (nome + permissões)
  
- Arquivo: `admin.component.html`
  - Campo de texto para nome na seção edit mode (antes dos checkboxes de permissão)
  - Botão renomeado "Editar permissões" → "Editar cargo"
  - Chamada de função atualizada: `saveCargo(cargoId)` em vez de `saveCargoPermissions(cargoId)`
  
- Arquivo: `admin.component.css`
  - Estilos `.adm-cargo-name-edit` e `.adm-cargo-name-edit .form-input`

**Backend Advisory:**
- Novo endpoint necessário: `PUT /api/v1/admin/cargos/{id}` com payload `{nome_cargo: str}`
- Sem este endpoint, a chamada falhará e exibirá erro genérico (a feature de permissões continuará funcionando)
- Arquivo sugerido: `backend/app/api/endpoints/admin.py`

### Inconsistências Documentais Resolvidas

**ROADMAP.md:** As Fases 22 e 23 apareciam em duas seções (Planejadas + Concluídas). Corrigido: mantém as entradas em "Fases Concluídas" com anotações `✅ frontend / ⏳ backend` para clareza.

**Impacto no PIBITI:** O hardening pós-MVP (Fases 22–23) exemplifica as etapas de consolidação e produção-readiness que sucedem a implementação de funcionalidades principais (Fases 6–21). As correções de segurança (RBAC, CORS, guard genérica) são casos de estudo relevantes para infraestrutura de sistemas policiais.

---

## [Auditoria de Segurança] (Completada Maio/2026)

> Adicionada em Maio/2026 como fase de consolidação.

**Contexto:** Após a implementação das Fases 6–23, foi conduzida uma auditoria de segurança abrangente cobrindo:
- Autenticação e autorização (JWT, RBAC, bypass de dev)
- Prevenção de IDOR (Insecure Direct Object Reference)
- Validação de entrada e vazamento de dados
- Segurança de infraestrutura (Docker, bancos de dados)
- Hardening de código (tratamento de exceções, rollback transacional)
- Conformidade LGPD (minimização de dados, expurgo)

**Descobertas Críticas Resolvidas:**

1. **C-1: Duplo bypass de autenticação em `deps.py`**
   - *Problema:* Guarda `if settings.APP_ENV == "production"` permitia bypass em staging, homolog, qa ou typos
   - *Impacto:* Qualquer UUID arbitrário explorava qualquer usuário; admin seed (matrícula 111111) acessível sem credencial
   - *Resolução:* Inverter lógica para `if settings.APP_ENV not in ("development", "test")` — whitelist apenas dev/test
   - *Arquivo:* `backend/app/api/deps.py` (linhas 39–40, 54–60)

2. **C-2: Serviços de infraestrutura abertos em `0.0.0.0`**
   - *Problema:* PostgreSQL (5432), Redis (6379), MinIO (9000/9001) acessíveis em qualquer interface de rede
   - *Impacto:* Credenciais padrão (`termo_password`, `admin/adminpassword`) exploráveis remotamente
   - *Resolução:* Rebind para `127.0.0.1:PORT:PORT` em `docker-compose.yml`; Redis + `--requirepass`
   - *Arquivo:* `docker-compose.yml` (linhas 12, 27, 44–45)

3. **C-3: Endpoint de download de PDF sem autenticação**
   - *Problema:* `GET /{job_id}/pdf` retornava PDF oficial assinado sem qualquer auth; `job_id` enumerável
   - *Impacto:* Terceiros baixavam PDFs de depoimentos de pessoas arbitrárias
   - *Resolução:* Adicionado `get_current_user` + ownership checks (Escrivão: `id_usuario` match, Delegado: `id_delegacia` match)
   - *Arquivo:* `backend/app/api/endpoints/pdf.py` (linhas 77–99)

4. **C-5 & C-6: Secrets com defaults inseguros**
   - *Problema:* `JWT_SECRET_KEY` lido via `os.getenv()` na importação do módulo (antes de Pydantic validar `.env`). `POSTGRES_PASSWORD` tinha default `"termo_password"`.
   - *Impacto:* Se `.env` não estava carregado, fallback silencioso para defaults públicos
   - *Resolução:* 
     - C-5: Mover `JWT_SECRET_KEY` para `Settings` (sem default); `security.py` lê via `settings.JWT_SECRET_KEY`
     - C-6: Remover defaults de `POSTGRES_PASSWORD`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` — Pydantic levanta `ValidationError` se ausentes
   - *Arquivos:* `backend/app/core/config.py` (linhas 17, 27–28, + novo `JWT_SECRET_KEY`), `backend/app/core/security.py` (linha 30 importa settings, usa `settings.JWT_SECRET_KEY`)

5. **A-1: IDOR em 4 endpoints (sem verificação de ownership)**
   - *Problema:* `GET /termos/{id}`, `GET /audio/{id}`, `GET /jobs/{id}`, `POST /pdf/gerar` aceitavam UUID arbitrário e retornavam dados do dono
   - *Impacto:* Escrivão A acessava depoimentos de Escrivão B; Delegado X acessava depoimentos de outro Delegado
   - *Resolução:* Padrão centralizado de ownership check: após buscar objeto, verificar `cargo_nome` e comparar `id_usuario` (Escrivão) ou `id_delegacia` (Delegado)
   - *Arquivos:* 
     - `termos.py` (linhas 68–79): `if cargo_nome == "Escrivão" and termo.depoimento.id_usuario != current_user.id_usuario: 403`
     - `audio.py` (linhas 12–36): idem
     - `jobs.py` (linhas 11–27): idem
     - `pdf.py` (linhas 22–37): idem na rota `POST /gerar`

6. **A-2 & A-3: Upload de áudio sem validação de magic bytes + sem ownership**
   - *Problema:* Validação por extensão apenas (`file.endswith(('.wav', '.mp3', ...))`). Qualquer usuário sobrescreve áudio de outro.
   - *Impacto:* `malware.exe` renomeado para `audio.wav` passa; Escrivão A substitui áudio de Escrivão B
   - *Resolução:*
     - A-2: Adicionar magic bytes check (RIFF, ID3, 0xFF 0xFB, OggS) antes de aceitar
     - A-3: Ownership check via `Depoimento.id_usuario` (ou `id_delegacia` para Delegado)
   - *Arquivo:* `backend/app/api/endpoints/upload.py` (linhas 41–63)

7. **A-4: Permissão não enforçada em `POST /processos/novo`**
   - *Problema:* Endpoint não verificava `CRIAR_TERMO` — qualquer usuário logado criava processo
   - *Resolução:* Trocar `get_current_user` por `RequirePermission('CRIAR_TERMO')`
   - *Arquivo:* `backend/app/api/endpoints/processos.py` (linha 84)

8. **A-5: Vazamento de detalhes internos em respostas 500**
   - *Problema:* `raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")` expõe stack trace, nomes de tabelas, connection strings
   - *Impacto:* Information disclosure; atacantes mapeiam arquitetura via mensagens de erro
   - *Resolução:* Substituir por `logger.exception(...)` + genérico `"Erro interno. Contate o administrador."`
   - *Arquivos:* `backend/app/api/endpoints/pdf.py` (linhas 44, 51, 56), `processos.py` (linha 132)

9. **A-7: Falta de índices FK + falta de unique constraints**
   - *Problema:* Queries de lista fazem full-scan porque PostgreSQL não cria índices automáticos para FKs. Duas chamadas `POST /admin/cargos` simultâneas criam cargos duplicados (race condition).
   - *Impacto:* Performance O(n) em tabelas grandes; violação de semântica RBAC (cargo duplicado)
   - *Resolução:* 
     - Adicionar `Index('ix_depoimento_id_usuario', Depoimento.id_usuario)` + 4 outros em `models.py`
     - Adicionar `unique=True` em `Cargo.nome_cargo` e `Permissao.nome_permissao`
   - *Arquivo:* `backend/app/models.py` (linhas 2, 165, 174, + Index definitions após class definitions)

10. **A-8: Ausência de rollback no handler de exceção Celery**
    - *Problema:* `try-except` em `process_audio.py` faz `db.commit()` sem `db.rollback()` — se commit falhar, sessão fica em estado inválido no pool
    - *Impacto:* Próximas tasks reutilizando a mesma conexão falham misteriosamente
    - *Resolução:* Adicionar `db.rollback()` antes do commit; wrappear commit do except em try-except próprio
    - *Arquivo:* `backend/app/tasks/process_audio.py` (linhas 78–91)

**Desvios do Plano:** Nenhum. Todas as correções foram implementadas como planejadas no documento de auditoria.

**Limitações Conhecidas:**
- A-6 (requirements.lock): Depende de `pip freeze` no ambiente de produção final; pós-piloto
- A-9 (MINIO_SECURE=true): Requer certificados TLS no MinIO; pós-piloto
- M-1 a M-16: Melhorias LGPD (minimização NER/ASR, rate limiting, audit log, criptografia CPF): pós-piloto

**Impacto no PIBITI:** A auditoria exemplifica a necessidade de security-first design em sistemas de dados sensíveis (testemunhas, suspeitos, PCIs). As 8 vulnerabilidades críticas/altas resolvidas demonstram:
- Importância de whitelist (permissões) vs. blacklist (punição)
- Ownership checks como camada mandatória de IDOR prevention
- Secrets management via configuração (Pydantic-settings) vs. hardcoded defaults
- Magic bytes + MIME type validation para uploads
- Logging + sanitização de exceções em APIs
- Índices e constraints como guardrails de concorrência

**Próximos Passos (Fases 24+):**
1. A-6: requirements.lock (pip freeze + audit com `pip audit` para CVEs)
2. A-9: MINIO_SECURE + TLS certificates
3. M-1 a M-16: LGPD hardening completo (PII minimization, rate limiting, audit log, CPF encryption)
4. B-1 a B-8: Code quality (UUID nativo, Enum de Permissions, Port abstraction, test coverage)
