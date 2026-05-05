# Padrões do Projeto (Termo Fácil)

Este documento define as regras estritas de formatação para Mensagens de Commit e Abertura de Issues, visando manter o repositório profissional, padronizado e alinhado com as melhores práticas de Engenharia de Software.

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
