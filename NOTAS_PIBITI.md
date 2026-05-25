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

## Air-Gapped Absoluto

Nenhuma chamada sai para APIs de nuvem — bloqueio em nível de código, não de firewall. Whisper, LeNER-Br e Ollama são executados inteiramente no HPC Mandu (on-premise SSP-PI). Isso é exigência da Portaria MJSP 961/2025 para dados de investigação criminal: depoimentos de suspeitos e testemunhas são classificados como sigilosos e não podem trafegar por infraestrutura de terceiros.

**Decisão arquitetural relevante:** a impossibilidade de usar WireGuard (firewall UFPI bloqueia UDP) levou à adoção de API Gateway com mTLS sobre TCP/443 via WebSocket WSS para comunicação com o HPC (ADR-001 no `CLAUDE.md`).

---

## Human-in-the-Loop com Prevalência Legal (RN-02)

A transcrição bruta ASR (`txt_literal_asr`) tem prevalência jurídica sobre o resumo LLM em caso de contestação — está no rodapé de todas as páginas do PDF e no Anexo I. O Escrivão edita apenas o resumo sintético (`txt_editado_humano`); a transcrição literal nunca é apagada do banco (apenas o áudio bruto e os metadados de trabalho são expurgados). O PDF híbrido une os dois documentos de forma indissociável, tornando a cadeia de custódia auditável.

**Fluxo de prevalência:** ASR bruto → NER (extrai entidades) → LLM (ancoragem NER) → Escrivão (edição humana + checkbox de responsabilidade RN-03) → PDF (ASR como Anexo I).

---

## Status Granular do Pipeline (RF-01)

O Job Celery transita por quatro estados de progresso visíveis no frontend: `Transcrevendo → Extraindo Dados → Gerando Resumo → Concluído`. Cada transição é persistida no banco antes do início da etapa correspondente, permitindo que o frontend exiba o estágio atual ao usuário final durante o processamento (polling a cada 2s). Estados legados `Processando` mantidos no enum por compatibilidade com registros anteriores à Fase 18.

**Implementação:** `backend/app/models.py` (enum `StatusJob`) + `backend/app/tasks/process_audio.py` (commits intermediários) + `backend/scripts/migrate.py` (migrations `ALTER TYPE ADD VALUE`).
