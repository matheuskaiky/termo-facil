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