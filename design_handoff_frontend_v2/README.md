# Handoff de Design — Termo Fácil · Frontend v2

> **Para o Claude Code**: este pacote contém propostas de redesenho para o frontend Angular do projeto `termo-facil` (SSP-PI). Os arquivos HTML/JSX em `references/` são **mockups de referência** — não copie-os literalmente. A tarefa é **recriar as telas no app Angular 17 existente** (`frontend/`), reaproveitando o design system já presente em `src/styles.css` e seguindo a mesma estrutura de componentes/serviços.

---

## 1. Contexto rápido

- **Projeto**: Sistema on-premise (SSP-PI) de transcrição e redação assistida por IA de Termos de Depoimento.
- **Stack frontend**: Angular 17 (standalone components), Noto Sans, design tokens em CSS vars no `frontend/src/styles.css`.
- **Backend**: FastAPI + Celery + Whisper (ASR) + Ollama/llama3 (LLM) + PostgreSQL + Redis + MinIO. O pipeline produz: transcrição segmentada com timestamps, NER (entidades), resumo formal, e PDF híbrido assinado com SHA-256.
- **Usuários**: Escrivães, delegados, admins. RBAC já existe (`hasUploadPermission`, `hasEditPermission`, `hasPdfPermission`, `canManageUsers`, etc.).

## 2. Fidelidade

**Alta fidelidade.** Cores, tipografia, espaçamentos e copy estão definidos. Reaproveitar tokens existentes (`var(--color-primary)` etc). Onde introduzo tokens novos, eles estão listados na seção "Tokens novos" abaixo — adicionar em `frontend/src/styles.css`.

## 3. Diagnóstico — o que motivou as mudanças

Sete problemas identificados no estado atual:

1. **Pipeline de IA invisível** — 5 estados (`Pendente → Transcrevendo → Extraindo Dados → Gerando Resumo → Concluído`) reduzidos a um badge plano.
2. **Auditoria 100% bloqueada durante processamento** — `*ngIf="status !== 'Concluído'"` cobre as duas colunas com overlay; transcrição parcial nunca aparece.
3. **Sem vínculo visual transcrição ↔ editor ↔ entidades** — timestamps clicáveis existem mas não há feedback de segmento ativo, e o NER do backend não tem UI dedicada.
4. **Lista de processos sem hierarquia** — tabela densa, sem KPIs nem filtros pré-prontos.
5. **Geração de PDF subutilizada** — momento juridicamente sensível tratado como `success-panel` verde.
6. **Login sem peso institucional** — card centralizado pequeno em fundo claro.
7. **Polimento** — audio player espremido, sem visões salvas, tipografia pouco hierarquizada.

## 4. Mudanças por tela

### 4.1 Lista de Processos
**Arquivos afetados**:
- `frontend/src/app/components/process-list/process-list.component.html`
- `frontend/src/app/components/process-list/process-list.component.css`
- `frontend/src/app/components/process-list/process-list.component.ts`

**Mudanças**:
- **Cabeçalho**: adicionar eyebrow uppercase `Inquéritos · <Mês>/<Ano>` (font-size .72rem, letter-spacing 1px, color `--color-text-subtle`) acima do `<h2>`.
- **KPI strip (NOVO)**: grid de 4 cards `padding: .85rem 1rem`, valores em 1.75rem/800. Status mapeados:
  - "Em processamento" (info, count = stage 1-3) — `bg: var(--color-info-bg)`, `color: var(--color-info-dark)`
  - "Aguardando revisão" (success, count = `status === 'Concluído' && !pdf_gerado`) — `bg: var(--color-success-bg)`, `color: var(--color-success-dark)`
  - "Com erro" (count = `status === 'Erro'`) — `bg: var(--color-danger-bg)`, `color: var(--color-danger-dark)`
  - "Concluídos no mês" (count agregado, neutro)
  - Os contadores devem vir do backend (sugestão: endpoint `GET /api/v1/processos/stats`) ou calculados client-side a partir da lista já carregada.
- **Chips de filtros pré-prontos (NOVO)**: substituir os 3 selects/inputs por chips clicáveis:
  - "Meus processos" — filtra `escrivao === authService.activeUser.nome`
  - "Aguardando revisão" — `status === 'Concluído' && !pdf_gerado`
  - "Em processamento" — status ∈ {Transcrevendo, Extraindo Dados, Gerando Resumo, Processando}
  - "Com erro" — `status === 'Erro'`
  - "Concluídos"
  - Chip ativo: `background: var(--color-primary)`, `color: #fff`. Inativo: `var(--color-secondary)` sobre transparente com border `var(--color-border)`.
  - Search box continua, mas embutido na mesma linha à direita dos chips.
- **Linha-cartão (substitui a tabela densa)**: grid `180px 1fr 130px 110px 150px 36px`, `padding: .9rem 1.1rem`. Colunas:
  - Inquérito + Tipo (Nº em mono `.82rem/700` cor primary; abaixo o tipo em `.72rem` muted)
  - Depoente (`.92rem/600`) + linha de status com **dot colorido + label "etapa X/4"** quando in-progress
  - Áudio (duração em mono)
  - Registrado (`dd/MM HH:mm`)
  - Escrivão
  - Chevron ›
- **Status visual**: substituir os 5 `status-badge` por um único padrão `dot + label`. Cores: erro `--color-accent`, concluído `--color-success`, in-progress `--color-primary`, idle `--color-text-subtle`.

**Componentes Angular sugeridos**:
- `<app-kpi-card [label] [value] [tone]>`
- `<app-filter-chip [active] [count]>`
- `<app-pipeline-dot [stage] [error]>` (versão compacta do stepper)

---

### 4.2 Auditoria (a tela mais importante)
**Arquivos afetados**:
- `frontend/src/app/components/auditoria/auditoria.component.html`
- `frontend/src/app/components/auditoria/auditoria.component.css`
- `frontend/src/app/components/auditoria/auditoria.component.ts`

**Mudanças**:

**(a) Sub-header com Pipeline Stepper (NOVO)** — substitui o badge plano de status:
- Barra branca abaixo do header global, `border-bottom: 1px solid var(--color-border)`, `padding: .85rem 2rem`.
- 3 zonas: breadcrumb à esquerda (`Processos · IP-2026/004 · Testemunha` + `<h2>` com nome do depoente em 1.15rem), stepper centralizado, meta à direita (`Iniciado há X` / `Tempo estimado ~Y`).
- Stepper: 5 etapas como círculos 24×24 conectados por linha de 2px. Marker concluído = `var(--color-success)`. Marker ativo = `var(--color-primary)` com box-shadow pulsante `0 0 0 4px rgba(43,108,176,.18)` animando entre 4px/.18 e 8px/.08 a cada 1.6s. Marker errado = `var(--color-accent)` com "!". Label em `.72rem/600`.

**(b) Layout de 3 colunas** (`1fr 1fr 280px`) substitui o `.content-cols` atual:
- **Coluna 1 — Transcrição (NÃO bloqueada)**: remover o `<div class="locked-overlay">`. Mostrar transcrição segmento a segmento conforme o ASR entrega; no fim da lista, exibir 3 skeleton-rows com opacidades decrescentes (1.0, 0.7, 0.4) enquanto `status !== 'Concluído'`. Cabeçalho da box mostra "transcrevendo…" com dot pulsante `--color-info` quando ainda processando.
- **Coluna 2 — Editor formal**: também não bloqueia. Enquanto `status !== 'Concluído'`:
  - Banner info no topo: "O resumo formal é gerado quando a transcrição é concluída. Você pode revisar entidades extraídas enquanto isso →"
  - O texto base aparece progressivamente; cursor "|" piscando indica posição da geração ao vivo.
- **Coluna 3 — Sidebar de entidades (NOVO)**: card "Dados extraídos pela IA" listando NER (já existe no backend, `highlightEntitiesInText`). Para cada entidade:
  - Tipo em uppercase `.72rem/700` muted
  - Label em `.82rem/600`
  - Confiança em mono à direita, com cor `var(--color-success-dark)` se ≥ 0.85, `var(--color-warning-dark)` se < 0.85 (e fundo `var(--color-warning-bg)` na linha)
  - "auto" ou "revisar" como sublegenda
  - Card secundário abaixo: "Pipeline · detalhes técnicos" (ASR model, LLM model, job ID em mono)

**(c) Segmento ativo destacado**: ao clicar num timestamp ou ao tocar o áudio, o segmento atual recebe `background: #FFF8E0; box-shadow: inset 3px 0 0 #D97706;`. Auto-scroll suave da coluna para mantê-lo visível (use `Element.scrollIntoView({ block: 'nearest', behavior: 'smooth' })`).

**(d) NER inline na transcrição e no editor**: highlights coloridos por tipo:
- Pessoa: `background: var(--color-ner-pessoa)` (#BEE3F8)
- Local: `var(--color-ner-local)` (#C6F6D5)
- Data: `var(--color-ner-data)` (#FBD38D)
- Organização: `var(--color-ner-org)` (#E9D8FD)
- Padding `0 3px`, `border-radius: 3px`.

**(e) Player de áudio persistente (NOVO)**: footer de toda a página, `background: #fff`, `border-top: 1px solid var(--color-border)`, `padding: .65rem 2rem`. Conteúdo:
- Play button circular 36×36 navy
- Timestamp atual em mono
- Waveform (componente novo `<app-waveform>` ou estilo placeholder atual)
- Duração total em mono muted
- Controles de velocidade 0.75× / 1.0× / 1.5× (toggle group)
- Remover o player inline do `.audio-block` atual.

**(f) Action footer do editor enxuto**: linha única no rodapé da coluna 2 com:
- Checkbox de responsabilidade compacto à esquerda (texto `.78rem`)
- "Visualizar PDF" (outline)
- "Aprovar e assinar" (primary, disabled até checkbox marcada)
- Remover o `.success-panel` grande — sucesso vira modal (ver 4.3).

---

### 4.3 Modal de Assinatura (NOVO)
**Substitui**: o atual `.success-panel` dentro do `auditoria.component.html`.

**Estrutura**:
- Modal centralizado 560px, `border-radius: 8px`, shadow `0 20px 60px rgba(0,0,0,.25)`.
- **Cabeçalho navy** (`background: var(--color-primary)`, `padding: 1rem 1.5rem`): ícone de escudo circular 32×32 com fundo `rgba(255,255,255,.18)`, ao lado `<h3>Termo aprovado e assinado</h3>` + sublinha `PDF híbrido gerado e arquivado`.
- **Corpo**:
  - Grid de metadados (`auto 1fr`, `gap: .5rem 1rem`, `.85rem`):
    - "Assinado por" → `<strong>{{ user.nome }}</strong> · {{ user.cargo }} · Mat. {{ user.matricula }}`
    - "Data/hora" → `26/05/2026 14:38:07 BRT` em mono
    - "Inquérito" → `IP-2026/XXX` em mono
    - "Modelo de IA" → `whisper-medium + llama3:8b` em mono
  - Bloco SHA-256: `background: var(--color-code-bg)`, mono `.7rem`, word-break, com label "SHA-256 do PDF" acima.
  - Grid 2 colunas mostrando estrutura do PDF híbrido:
    - PARTE I — Resumo Oficial — "Termo formal revisado pelo escrivão"
    - PARTE II — Transcrição Literal — "Texto bruto com timestamps + áudio"
  - Footer: 3 botões à direita — "Copiar hash" (ghost) / "Abrir PDF" (outline) / "Baixar arquivo" (primary).

---

### 4.4 Login
**Arquivos afetados**:
- `frontend/src/app/components/login/login.component.html`
- `frontend/src/app/components/login/login.component.css`

**Mudanças**:
- Layout `display: grid; grid-template-columns: 1.1fr 1fr;` ocupando 100vh.
- **Painel esquerdo institucional**:
  - `background: linear-gradient(160deg, #0F2240 0%, #1A365D 60%, #2B6CB0 130%);`
  - Padding 3rem, conteúdo distribuído em `space-between`:
    - Topo: logo TF + "Termo Fácil" + badge SSP-PI
    - Meio: eyebrow "SISTEMA INSTITUCIONAL" + `<h1>` 2.1rem "Redação assistida de termos de depoimento" + parágrafo descritivo
    - Base: 3 stats (100% on-premise · Híbrido · SHA-256)
- **Painel direito**: form max-width 360px, mesmo input style atual, com link "Esqueci minha senha" ao lado do label de senha, e rodapé com versão do app.

---

### 4.5 Cadastro & Edição de Processo (NOVA tela dedicada)
**Substitui**: o modal de "Novo Processo" dentro de `process-list.component.html`.

**Arquivos sugeridos**:
- `frontend/src/app/components/process-form/process-form.component.html`
- `frontend/src/app/components/process-form/process-form.component.css`
- `frontend/src/app/components/process-form/process-form.component.ts`
- Rotas: `/processos/novo` (create) e `/processos/:id/editar` (edit)
- Remover lógica do modal em `process-list.component.ts` (`abrirModal`, `submeterFormulario`, `formData`, `formErrors`).

**Estrutura**:
- **Sub-header** com breadcrumb (`Processos · IP-2026/XXX` quando edit) + ações à direita: "Descartar" (ghost), "Salvar rascunho" (outline), "Criar processo" / "Salvar alterações" (primary).
- **Grid 3 colunas**: `240px 1fr 320px`.
  - **Coluna 1** — navegação de seções como steps verticais (Identificação / Dados do depoente / Vinculação / Observações). Cada item com circle 18×18 marcado quando preenchido; borda esquerda 3px primary quando ativo.
  - **Coluna 2** — formulário em cards. Para cada seção:
    - Título `.95-1.05rem` + sub `.tf-small` muted.
    - Inputs em grid responsivo (1fr 1fr / 1fr 1fr 1fr conforme densidade).
    - Cards inativos com `opacity: .85` e chevron `▾` à direita (collapsible).
  - **Coluna 3** — sidebar de contexto:
    - Card "Contexto" com delegacia, autoridade, escrivão (preenchidos via `authService.activeUser` e endpoints `/delegacias/me`), status (só edit).
    - Card "Histórico de alterações" (só edit) — timeline vertical lendo `GET /api/v1/processos/:id/audit-log`. Cada item: dot 9×9, linha 1px conectora, texto principal `.82rem` + autor/quando `.xs muted`.
    - Card "Boas práticas" em info-bg, com padrão do Nº de procedimento `IP-AAAA/NNN`.

**Campos novos** (vs. modal atual):
- RG / órgão emissor
- Data de nascimento
- Telefone de contato
- Profissão
- Endereço, município, UF
- Natureza do feito (select)

Esses campos são todos opcionais por enquanto — exigirá migration no backend ou simplesmente armazenar em coluna JSON `dados_extras` na tabela de depoentes.

**Validação**:
- Manter validação de CPF e máscara via `onCpfInput` (já existe).
- Marcar obrigatórios com `*` no label.
- Erros inline em `.error-text` (já existe no projeto).

---

### 4.6 Painel Admin (RBAC) — redesign completo
**Arquivos afetados**:
- `frontend/src/app/components/admin/admin.component.html`
- `frontend/src/app/components/admin/admin.component.css`
- `frontend/src/app/components/admin/admin.component.ts`

**Mudanças**:

**(a) Página header** — substituir título "Painel de Controle de Acesso (RBAC)" por hierarquia:
- Eyebrow `.xs uppercase var(--color-text-subtle)`: "Administração"
- `<h2>` 1.55rem: "Controle de acesso"
- Sub: "Servidores, cargos e permissões da SSP-PI."
- Ações à direita: "Exportar lista" (ghost), "+ Novo servidor" (primary).
- Remover o `stats-row` com 3 boxes — virar contador dentro das próprias abas (ver b).

**(b) Tabs** — passar de 2 para **3 abas**:
- "Usuários" (39)
- "Cargos" (4)
- "Matriz de permissões" (NOVA)

Contador em badge ao lado do label, `bg: var(--color-tablehead)`, font-size .7rem.

**(c) Aba "Usuários"** — substituir tabela densa por **lista com drawer**:
- **Esquerda**: filtros (chips `Todos / Escrivão / Delegado / Investigador / Admin SSP / Senha temporária / Inativos`) + search + lista. Linha de usuário:
  - Avatar 32px com iniciais (fundo `tablehead` normal, `primary` quando selecionado, texto branco)
  - Nome em 600 + meta (`temp ativa`/`inativo` em xs)
  - Matrícula em mono
  - Unidade em small
  - Cargo em pill `info-bg/info-dark`
  - Último login em xs muted
  - Linha selecionada: `background: var(--color-info-bg)`, `border-left: 3px solid var(--color-primary)`.
  - Linha inativa: `opacity: .55`.
- **Direita** (380px fixo): **drawer de detalhes do usuário selecionado**:
  - Cabeçalho navy (full bleed dentro do card): avatar 44px + nome + matrícula + unidade.
  - Corpo:
    - Select "Cargo" (substitui select inline na tabela atual)
    - "Permissões herdadas do cargo" como lista de chips mono em verde (`#F0FFF4` bg, `#22543D` color, `#C6F6D5` border)
    - "Status da senha" — exibe info + botão "Gerar senha temporária" no warning style
  - Footer: "Desativar" (ghost danger) + "Salvar alterações" (primary)
- Bloco "Atividade recente" abaixo do drawer (últimas 3 ações do usuário, lendo `/admin/users/:id/activity`).

**(d) Aba "Cargos"** — mantém os role-cards atuais, mas refinar:
- Cards do mesmo tamanho em grid `repeat(auto-fill, minmax(280px, 1fr))`.
- Header do card: nome em 1rem + count de usuários (`12 servidores`) à direita.
- Permissões agrupadas por categoria (Processos / Administração / Análise) ao invés de lista plana.
- Remover o painel "Criar Novo Cargo" permanente à direita; substituir por **botão `+ Novo cargo`** no header da aba que abre um **drawer ou modal** com o form (mesmo campos).

**(e) Aba "Matriz de Permissões" (NOVA)**:
- Tabela linhas = permissões, colunas = cargos.
- Linhas agrupadas por categoria com header `background: var(--color-bg-deep)`, uppercase `.72rem` muted.
- Permissão em mono (`UPLOAD_AUDIO`).
- Célula com checkbox visual: quadrado 22×22 `border-radius: 4px`, com check branco em fundo `--color-success` quando ativo; só borda quando inativo. Toggleable.
- Cabeçalho de coluna fixa (sticky) ao rolar.
- Salva alterações via `PUT /admin/cargos/:id/permissions` (endpoint já existe).

**(f) Modal de senha temporária** — manter como está, mas aplicar visual do "Modal de Assinatura" (seção 4.3) por consistência: header navy com escudo, copy mais formal sobre o canal seguro.

**Componentes Angular novos sugeridos**:
- `user-list-row.component.ts`
- `user-detail-drawer.component.ts`
- `permission-matrix.component.ts`
- `role-card.component.ts`
- `create-role-drawer.component.ts`

---

### 4.7 Dashboard (renomeia Métricas) — redesign completo
**Mudança no roteamento**: renomear rota `/metricas` para `/dashboard` (ou manter `/metricas` e só trocar o label exibido). No `header.component.html` trocar `<a routerLink="/metricas">Métricas</a>` → `Dashboard`. O `permission.guard` continua checando `VER_METRICAS` — a permissão pode manter o nome técnico no backend.

**Arquivos afetados**:
- `frontend/src/app/components/metricas/metricas.component.{html,css,ts}` (renomear para `dashboard/dashboard.component.*` é opcional)
- `frontend/src/app/app.routes.ts` (rota + label)
- `frontend/src/app/components/header/header.component.html` (label do link)

**Mudanças no layout**:

**(a) Page header**:
- Eyebrow "Indicadores"
- `<h2>` "Dashboard"
- À direita: **seletor de período** (segmented control: `7 dias / 30 dias / Este ano / Custom` — chip ativo navy) + botão "Exportar".

**(b) KPIs — 5 cards** (substitui o grid 3×2 atual):
- Layout: `display: grid; grid-template-columns: repeat(5, 1fr); gap: .75rem;`
- Cada card: padding `.9rem 1rem`, contém:
  - Label uppercase `.xs/600` muted
  - **Valor + Sparkline** lado a lado (`flex; justify-content: space-between; align-items: flex-end`)
  - Valor 1.75rem/800 primary
  - Sparkline 80×24px SVG, stroke `--color-primary-mid` 1.5px
  - **Delta vs. período anterior**: `▲ +12%` em `--color-success-dark` (ou `▼` + danger). Sufixo "vs. período anterior" em xs muted.
- KPIs: Depoimentos · Termos pela IA · PDFs assinados · Taxa de sucesso · Horas economizadas (com nota PIBITI).

**(c) Charts row** (`grid: 2fr 1fr`):
- **Volume de depoimentos · últimos 30 dias** — area chart SVG. Linha 2px primary com fill em gradient linear `rgba(43,108,176,.35) → rgba(0,0,0,0)`. Eixo invisível, padding 8px nas bordas. Subtítulo: "média X/dia".
- **Jobs por status** — donut chart (R=50, stroke-width=18). Fatias: Concluído (success), Processando (info), Pendente (warning), Erro (danger). Legenda à direita com dot 9×9 + label + valor.

**(d) Pipeline avg time + Top escrivães** (`grid: 1fr 1fr`):
- **Tempo médio por etapa** — barra horizontal stacked (24px de altura, 4px radius) com 4 segmentos coloridos (transcrição/extração/resumo/revisão). Abaixo, legenda com cor + label + valor em mono. Total no rodapé com border-top dashed.
- **Produção por escrivão · 30 dias** — barras horizontais simples (140px nome / 1fr barra / 40px valor). Barra: altura 7px, `var(--color-primary)` em fundo `--color-bg-deep`.

**(e) Estados**:
- Empty state quando período sem dados: mostrar mesma estrutura mas com mensagem central nos charts.
- Loading: skeleton dos KPIs e charts (não o spinner atual).
- Acesso negado: manter o `.access-denied` mas refinar visual (mesmo padrão de banner do app).

**Componentes Angular novos sugeridos**:
- `kpi-card.component.ts` (reaproveitável)
- `sparkline.component.ts`
- `donut-chart.component.ts`
- `area-chart.component.ts`
- `stacked-bar.component.ts`
- `ranking-bar.component.ts`
- `period-selector.component.ts`

**Endpoints sugeridos** (backend):
- `GET /api/v1/metricas?period=30d` (já parcialmente existe — adicionar `delta`, `serie_volume`, `serie_jobs_status`, `tempo_medio_por_etapa`, `top_escrivaes`)
- Ou múltiplos endpoints especializados se preferir.

---

### 4.8 Header
**Arquivos afetados**:
- `frontend/src/app/components/header/header.component.html`
- `frontend/src/app/components/header/header.component.css`

**Mudanças mínimas**: a estrutura está bem. Polimentos opcionais:
- Aumentar `gap` entre links de nav.
- Aproveitar o mesmo dot+label do pipeline para mostrar status do worker/Celery (opcional, se houver endpoint de health).

---

## 5. Tokens novos a adicionar em `frontend/src/styles.css`

```css
:root {
  /* Cores adicionais */
  --color-primary-dark: #0F2240;
  --color-bg-deep: #EEF2F7;
  --color-border-strong: #CBD5E0;

  /* NER por tipo */
  --color-ner-pessoa: #BEE3F8;
  --color-ner-local:  #C6F6D5;
  --color-ner-data:   #FBD38D;
  --color-ner-org:    #E9D8FD;

  /* Sombras */
  --shadow-lifted: 0 8px 24px rgba(15, 34, 64, 0.12);

  /* Tipografia mono */
  --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}
```

Adicionar import:
```css
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');
```

## 6. Componentes Angular novos sugeridos

Criar em `frontend/src/app/components/shared/`:

- `pipeline-stepper.component.ts` — `[activeIndex] [error] [compact]`
- `kpi-card.component.ts` — `[label] [value] [tone] [delta] [sparkline]`
- `sparkline.component.ts` — recebe `data: number[]`
- `donut-chart.component.ts` — recebe `data: {label,value,color}[]`
- `area-chart.component.ts` — recebe `data: number[]` ou `{x,y}[]`
- `stacked-bar.component.ts` — segmentos coloridos para tempo médio
- `ranking-bar.component.ts` — barras horizontais com nome + valor
- `period-selector.component.ts` — segmented control de período
- `filter-chip.component.ts` — `[active] [count]`
- `status-dot.component.ts` — versão mini do stepper para listas
- `audio-player.component.ts` — standalone, recebe `[src] [segments]`, emite `(timeUpdate)`
- `waveform.component.ts` — placeholder ou render via Web Audio API
- `signature-modal.component.ts` — `{hash, timestamp, user, jobId, pdfUrl}`
- `entity-list.component.ts` — array de entidades agrupado por tipo
- `user-list-row.component.ts`
- `user-detail-drawer.component.ts`
- `permission-matrix.component.ts`
- `role-card.component.ts`
- `create-role-drawer.component.ts`
- `audit-timeline.component.ts` — timeline vertical reaproveitável

## 7. Comportamentos / estados

- **Stepper animado**: ao mudar `activeIndex`, o marker fica com pulse infinito (1.6s ease-in-out).
- **Skeleton de transcrição**: enquanto `status` ∈ {Transcrevendo, Extraindo Dados, Gerando Resumo}, mostrar 3 linhas de skeleton com opacidades 1.0/0.7/0.4 depois dos segmentos já entregues.
- **Segmento ativo**: sincronizar com `currentTime` do `<audio>`; ao clicar timestamp, fazer `audio.currentTime = seg.start`.
- **Filtros**: persistir chip ativo em query param (`?view=meus`) para deep-link.
- **Auto-save do editor**: já existe (`autoSaveLabel`); manter.

## 8. Acessibilidade

- Todos os botões com `aria-label` (player, chips, ações do modal).
- Stepper marcado com `role="list"` e cada step com `aria-current="step"` quando ativo.
- Modal de assinatura com `role="dialog"`, `aria-modal="true"`, focus trap.
- Cores de status sempre acompanhadas de label texto (não cor sozinha).

## 9. Arquivos de referência neste pacote

- `references/index.html` — canvas com todas as telas
- `references/src/tokens.css` — tokens completos (inclui os novos)
- `references/src/shared.jsx` — componentes compartilhados (Header, PipelineStepper, StatusPill, Waveform)
- `references/src/current.jsx` — recriação fiel do estado atual (lista, auditoria, login)
- `references/src/proposed.jsx` — propostas redesenhadas (lista, auditoria, login, modal de assinatura)
- `references/src/admin-dashboard-process.jsx` — admin, dashboard, cadastro/edição de processo

Para inspecionar visualmente: abrir `references/index.html` no navegador.

## 10. Como instruir o Claude Code

Sugestão de prompt inicial:
> Estou no repo `termo-facil`. Leia `design_handoff_frontend_v2/README.md` e implemente as mudanças da seção 4.2 (Auditoria) primeiro: adicionar o `pipeline-stepper.component.ts` na pasta `frontend/src/app/components/shared/`, integrá-lo ao `auditoria.component.html` como sub-header, remover o `.locked-overlay` e adicionar skeleton-rows na transcrição. Mantenha o RBAC e o serviço `api.service.ts` intactos. Use os tokens CSS já existentes em `styles.css` e adicione os novos listados na seção 5 do handoff.

**Ordem sugerida** (uma seção por PR, do maior impacto pro menor):
1. **4.2 Auditoria** — pipeline stepper + remover bloqueio + sidebar de entidades
2. **4.1 Lista de Processos** — KPIs + chips + linha-cartão
3. **4.5 Cadastro & Edição** — formulário em página dedicada
4. **4.6 Admin** — drawer + matriz de permissões
5. **4.7 Dashboard** — renomear Métricas + gráficos + período
6. **4.3 Modal de assinatura** — peso jurídico no momento do PDF
7. **4.4 Login** — visual institucional
8. **4.8 Header** — polimento final
