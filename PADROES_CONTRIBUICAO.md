# Padrões do Projeto (Termo Fácil)

Este documento define as regras estritas de formatação para Mensagens de Commit e Abertura de Issues, visando manter o repositório profissional, padronizado e alinhado com as melhores práticas de Engenharia de Software.

## Regra de Ouro do Pair Programming (Divisão de Papéis)
Neste projeto, o desenvolvimento ocorre em formato de Pair Programming estruturado:
- **O Usuário (Humano):** É responsável pelo **Back-end** (Python, FastAPI, SQLAlchemy) e **Integrações** (Docker, Celery, Banco, Front com Back). O humano escreve, integra e estrutura o core do sistema e do banco.
- **A Inteligência Artificial:** É responsável pelo **Front-end** (Angular, UI/UX, TypeScript, Design System). A IA escreve e estrutura toda a interface visual e consome a API feita pelo humano. A IA atua no Backend *apenas* de forma consultiva ou quando expressamente solicitada para destravar algo.

---

## 1. Padrão de Commits (Conventional Commits)

Todas as mensagens de commit devem seguir o formato estrito do [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0-beta.4/).

### Formato Obrigatório:
```text
<tipo>(<escopo>): <descrição curta em inglês> (Issue #<numero>)
```

### Tipos Permitidos:
- **`feat`**: Uma nova funcionalidade (Ex: nova rota, novo componente Angular).
- **`fix`**: Correção de um bug.
- **`refactor`**: Mudança no código que não adiciona feature nem corrige bug (ex: renomear variáveis, limpar código).
- **`docs`**: Atualização apenas de documentação.
- **`style`**: Formatação, ponto e vírgula, etc (sem mudança de lógica).
- **`test`**: Adição ou correção de testes automatizados.
- **`chore`**: Atualizações de tarefas de build, pacotes, npm, etc.

### Escopos Permitidos:
- `backend` (FastAPI, Python, Banco de Dados)
- `frontend` (Angular, UI/UX)
- `infra` (Docker, Celery, MinIO)

### Exemplos Válidos:
✅ `feat(backend): implement RBAC dynamic tables (Issue #3)`
✅ `fix(frontend): resolve undefined state in audio polling (Issue #12)`
✅ `refactor(backend): replace CargoUsuario enum with database relation`
✅ `docs(infra): update README with docker setup instructions`

❌ *Evitar:* `criado o endpoint novo` ou `feat: arrumei a tela`

---

## 2. Padrão de Issues (GitHub)

Toda nova Issue criada deve ser altamente descritiva, focada no negócio e acionável.

### Modelo a ser copiado na criação da Issue:

```markdown
# Objetivo
[Explique em 1 a 3 frases o porquê desta issue existir, focando no valor para a SSP-PI ou para o sistema. Ex: "Garantir que as rotas da API estejam protegidas com base no RBAC."]

# Tarefas (Checklist)
- [ ] [Ação técnica 1. Ex: Criar a entidade Cargo]
- [ ] [Ação técnica 2. Ex: Adicionar Injeção de Dependência no Controller]
- [ ] [Ação técnica 3. Ex: Atualizar testes automatizados]

# Contexto Adicional (Opcional)
[Cole aqui links úteis, prints de tela, logs de erro, ou dependências de outras issues. Ex: "Depende da Issue #3".]
```

### Regras de Labels:
Sempre aplique os labels semânticos no GitHub.
- **Arquitetura**: `backend`, `frontend`, `database`, `infra`.
- **Natureza**: `bug`, `enhancement` (melhoria), `security`.
- **Progresso**: `phase-X`.

---

## 3. Documento de Roadmap (ROADMAP.md)

O arquivo [`ROADMAP.md`](./ROADMAP.md) é o **mapa de evolução técnica oficial do projeto**. Ele deve ser tratado como documentação viva e atualizado a cada ciclo de desenvolvimento.

### Estrutura obrigatória do ROADMAP.md

```markdown
## 🚀 Fase N — [Título da Fase]
### Objetivo          ← Por que esta fase existe e qual valor entrega
### Issue #X          ← Uma seção por issue, com:
  - **O que fazer**   ← Descrição técnica clara e acionável
  - **Por que [tech]**← Justificativa da escolha tecnológica
  - **Tarefas**       ← Checklist de sub-tarefas ([ ])
  - **Referência**    ← Esqueleto de código ou diagrama de fluxo (quando aplicável)
```

### Regras de manutenção

1. **Ao iniciar uma fase:** Abra as issues do GitHub para aquela fase usando o modelo de `PADROES_CONTRIBUICAO.md`. Não abra issues de fases futuras ainda.
2. **Ao finalizar uma fase:** Mova o bloco da fase para a seção `## ✅ Fases Concluídas` no fim do `ROADMAP.md`, registrando o mês/ano de conclusão. Feche as issues correspondentes no GitHub.
3. **Ao adicionar uma nova fase:** Inclua sempre o **objetivo de negócio** (por que existe) e a **justificativa tecnológica** (por que usar essa biblioteca/abordagem e não outra). Isso garante rastreabilidade das decisões arquiteturais.
4. **Nunca remova fases concluídas** — elas formam o histórico de decisões do projeto.
5. **Versione o ROADMAP.md junto com o código** — toda alteração neste arquivo deve vir em um commit `docs(infra): update ROADMAP [descrição da mudança]`.
