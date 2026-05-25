# Crítica de Design — Termo Fácil Frontend

> **Escopo:** Auditoria completa dos componentes Angular (`login`, `change-password`, `header`, `auditoria`, `process-list`, `admin`, `metricas`).  
> **Metodologia:** First impression → Usabilidade → Hierarquia Visual → Consistência → Acessibilidade.

---

## Impressão Geral

O sistema tem uma base sólida: tokens de design bem definidos no `styles.css`, paleta coerente com a identidade institucional e boas intenções de hierarquia. O problema é que essa base **não está sendo usada**. A maioria dos componentes ignora o sistema de tokens e substitui tudo por inline styles e hexadecimais hardcoded. O resultado é um design que parece ter sido construído por duas pessoas que nunca conversaram entre si.

---

## 1. Problema Estrutural: Inline Styles Dominam o Código

**Severidade: 🔴 Crítica**

`header.component.html`, `admin.component.html`, `login.component.html` e `change-password.component.html` usam quase exclusivamente `style="..."` inline. Isso quebra o sistema de design em múltiplos pontos:

- Impossível fazer alterações globais (mudar um token afeta zero componentes).
- Impossivelmente verboso — o `<header>` tem `style="background-color: var(--color-primary); color: var(--color-white); padding: 0.75rem 2rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-bottom: 3px solid var(--color-border); user-select: none;"` em um único elemento.
- O Angular tem encapsulamento de estilo por componente exatamente para evitar isso — o recurso existe, mas não é usado.

**Recomendação:** Migrar 100% dos inline styles para classes CSS nos arquivos `.css` de cada componente, usando os tokens do `:root`.

---

## 2. `<style>` Injetado Dentro do HTML do Componente

**Severidade: 🔴 Crítica**

Tanto `login.component.html` quanto `change-password.component.html` contêm um bloco `<style>` no final do template:

```html
<style>
  .login-input { ... }
  .btn-submit { ... }
</style>
```

Isso é um anti-padrão grave no Angular. Esses estilos:
1. Escapam o encapsulamento de View Encapsulation.
2. Vazam para outros componentes na mesma página.
3. São duplicados entre `login` e `change-password` — os mesmos seletores `.login-input` e `.btn-submit` definidos duas vezes com valores ligeiramente diferentes.

**Recomendação:** Mover tudo para os respectivos arquivos `.css` do componente. Criar um `auth-form.css` compartilhado se necessário.

---

## 3. Cores Hardcoded Ignorando os Tokens

**Severidade: 🔴 Crítica**

O `styles.css` define tokens limpos. Porém os componentes usam hexadecimais crus em vez deles:

| Cor usada no código | Token correto que deveria usar |
|---|---|
| `#FFF5F5`, `#FEB2B2`, `#C53030` | `var(--color-accent)` com opacity variants |
| `#742A2A` | Sem token — precisa criar `--color-danger-dark` |
| `#EBF8FF`, `#BEE3F8`, `#2B6CB0` | `var(--color-primary)` com opacity variants |
| `#234E52`, `#E6FFFA` | Sem token — variantes de `--color-success` |
| `#718096`, `#A0AEC0` | `var(--color-text-light)` já existe |
| `#2D3748`, `#1A202C` | Próximos de `--color-secondary` mas não documentados |
| `#CBD5E0` | Próximo de `--color-border` |
| `#FEFCBF`, `#744210`, `#F6E05E` | Sem token — badges de aviso |

Resultado: a paleta real tem ~20 cores não documentadas além dos 8 tokens oficiais.

**Recomendação:** Expandir o `:root` com tokens para todas as variantes semânticas necessárias (danger-dark, success-light, warning-*) e substituir todas as ocorrências hardcoded.

---

## 4. Badge "SSP-PI" Usando a Cor de Erro

**Severidade: 🟡 Moderada**

```html
<span style="background-color: var(--color-accent); ...">SSP-PI</span>
```

`--color-accent` é `#E53E3E` — vermelho, reservado para erros e estados de perigo em todo o sistema. O logo institucional da SSP-PI aparece em vermelho como se fosse um alerta de erro. Isso é um conflito semântico sério para um usuário que aprende a associar vermelho = problema.

O mesmo badge aparece em `login.component.html` e `header.component.html`, amplificando o problema.

**Recomendação:** Criar um token `--color-brand-badge` com uma cor distinta (ex: azul mais escuro `#1E3A5F` ou um dourado institucional), desvinculando o badge do sistema de erros.

---

## 5. Uso de Emojis em Interface Institucional Governamental

**Severidade: 🟡 Moderada**

O sistema usa emojis em praticamente todas as telas: 🛡️ 📄 ✍️ 📋 ⚙️ 📊 👥 🔑 ➕ ✅ ⚠️ 🎙️ 🔒 🎯 ⏱.

Para um sistema de segurança pública usado em contexto forense e judicial, emojis comunicam informalidade incompatível com o peso legal dos documentos gerados. Além disso, a renderização de emojis varia por SO e fonte, criando inconsistência visual entre máquinas.

Exemplos específicos que incomodam:
- O logo "🛡️ Termo Fácil" na tela de login parece um app de games, não um sistema policial.
- "🎯 Taxa de Sucesso dos Jobs" no dashboard de métricas.
- "🔐" na tela de troca de senha obrigatória — como decoração de um processo de segurança crítico.

**Recomendação:** Substituir emojis por ícones SVG do Material Icons ou Lucide, já usáveis via Angular. Ícones vetoriais são escaláveis, temáticos e semanticamente controláveis.

---

## 6. Border-radius Inconsistente

**Severidade: 🟡 Moderada**

O design system define três tokens: `--radius-sm: 4px`, `--radius-md: 8px`, `--radius-pill: 20px`. Na prática, os componentes usam:

| Valor | Onde aparece |
|---|---|
| `3px` | `.seg-timestamp` |
| `4px` | Definido como `--radius-sm` |
| `5px` | Inputs de login, botões de login/change-password |
| `6px` | `.audio-block` |
| `8px` | Card do login, `--radius-md` |
| `12px` | Status badges no process-list |
| `20px` | Pill badges, `--radius-pill` |

Os valores 3px, 5px, 6px e 12px não existem nos tokens. O botão de login usa `border-radius: 5px` mas o `.btn` global usa `4px` — mesma função, visual diferente.

**Recomendação:** Remover todos os border-radius hardcoded e usar apenas os três tokens definidos. Adicionar `--radius-lg` se necessário.

---

## 7. Tipografia Sem Escala Consistente

**Severidade: 🟡 Moderada**

O `styles.css` define `h1: 1.5rem` e `h2: 1.125rem`. Na prática os títulos dos componentes sobrescrevem livremente:

| Elemento | Tamanho |
|---|---|
| Título de auditoria (`.audit-title`) | `1.6rem` |
| Título no process-list | `1.75rem` |
| Logo no header | `1.4rem` |
| Logo no login | `1.8rem` |
| Logo no change-password | `1.6rem` |
| `h2` base no styles.css | `1.125rem` |

O `h2` mais comum no sistema tem `1.6rem` ou `1.75rem`, mas o token diz `1.125rem`. Nenhum dos `h2` reais usa o token.

**Recomendação:** Redefinir a escala tipográfica com valores realistas (`h1: 2rem`, `h2: 1.5rem`, `h3: 1.25rem`) e remover os font-sizes inline dos componentes.

---

## 8. `change-password` com Cor de Ação Fora do Sistema

**Severidade: 🟡 Moderada**

A tela de troca de senha usa `#D97706` (âmbar/laranja) como cor principal — no header do card e no botão de submit. Essa cor não existe em nenhum token do design system e é a única tela do sistema com essa paleta. Para um usuário que acabou de ver a tela de login em navy (`#1A365D`), a transição para laranja parece que caiu em outro produto.

A intenção é comunicar "atenção/urgência" para a troca obrigatória — válida semanticamente, mas a execução quebra a identidade visual.

**Recomendação:** Adicionar um token `--color-warning: #D97706` ao design system e usar em todos os lugares onde há estados de aviso (não só nessa tela). Alternativamente, manter navy com um banner de aviso em âmbar dentro do card, sem mudar a cor estrutural da página.

---

## 9. Áudio Player Nativo Sem Estilização

**Severidade: 🟡 Moderada**

```html
<audio #audioPlayer [src]="audioUrl" controls></audio>
```

O elemento `<audio controls>` nativo renderiza com o estilo padrão do navegador — completamente diferente em Chrome, Firefox e Edge. Em um sistema com design system definido, esse player está completamente fora do vocabulário visual da aplicação: bordas arredondadas estranhas, controles cinzas do SO, alturas variáveis.

**Recomendação:** Implementar um player customizado com `<audio>` headless (sem `controls`) e botões/sliders estilizados com os tokens do sistema. Um componente simples com play/pause, timeline e tempo decorrido resolve 90% dos casos de uso.

---

## 10. Input de Arquivo Nativo Sem Estilização

**Severidade: 🟡 Moderada**

```html
<input type="file" accept=".wav,.mp3,.m4a,.opus" ... />
```

O `<input type="file">` nativo é o elemento mais feio e mais inconsistente entre navegadores em toda a web. No contexto atual, ele aparece ao lado de um botão estilizado, criando uma quebra visual óbvia na barra de upload.

**Recomendação:** Ocultar o input nativo com `display: none`, criar uma área de drop zone estilizada (ou ao menos um botão com `label[for]` apontando para o input oculto), e exibir o nome do arquivo selecionado em texto formatado.

---

## 11. Botão "Abrir" Redundante na Tabela de Processos

**Severidade: 🟢 Menor**

A tabela de processos tem `.clickable-row` (a linha inteira é clicável) e também uma coluna de ações com um botão "Abrir" que faz a mesma coisa. O `$event.stopPropagation()` no botão confirma que o desenvolvedor percebeu o conflito e tentou contornar em vez de resolver.

Duas affordances idênticas confundem: o usuário não sabe qual é "o jeito certo" de abrir. Além disso, o botão ocupa uma coluna inteira da tabela sem adicionar valor.

**Recomendação:** Remover a coluna "Ações" e manter apenas o `clickable-row`. Opcionalmente, substituir por um ícone de seta sutil no hover da linha para reforçar a clicabilidade.

---

## 12. Status Badges com CSS Frágil

**Severidade: 🟢 Menor**

```html
[ngClass]="p.status_job.toLowerCase().replace(' ', '-')"
```

A lógica de aplicar classes CSS está amarrada ao formato da string retornada pela API. Há inclusive dois seletores CSS para o mesmo estado:

```css
.status-badge.concluído,
.status-badge.concluido { ... }
```

Isso é um workaround para problema de encoding (acento vs. sem acento). O comentário no CSS confirma: "Suporte aos dois formatos: com e sem acento (depende do encoding da resposta da API)".

**Recomendação:** Usar um pipe ou função no TypeScript que mapeia o valor da API para uma classe CSS fixa (`'Concluído' → 'status-concluido'`), desacoplando completamente o CSS do formato da API.

---

## 13. Estado "Bloqueado" com Opacidade 50% é Péssimo para Acessibilidade

**Severidade: 🟡 Moderada**

```css
.is-locked {
  opacity: 0.5;
  pointer-events: none;
}
```

Colunas inteiras (transcrição e editor) ficam em 50% de opacidade quando o job não está concluído. Problemas:
1. Contraste de texto dentro das colunas cai para menos de 3:1 — reprovação WCAG AA garantida.
2. `pointer-events: none` impede leitores de tela de acessar o conteúdo — o conteúdo existe no DOM mas é inacessível.
3. O usuário não tem feedback claro de *por que* está bloqueado ou *quanto tempo* falta.

**Recomendação:** Substituir por um overlay com mensagem explicativa ("Aguardando processamento — status: Processando") em vez de degradar o conteúdo existente. Usar `aria-disabled` e `aria-describedby` para acessibilidade.

---

## 14. Avisos de Permissão Poluem o Layout

**Severidade: 🟡 Moderada**

Há múltiplos banners de aviso de permissão espalhados pelo `auditoria.component.html`:
- Um no header (upload)
- Um no editor (edição)
- Um no footer (PDF)

Um usuário sem permissões vê três banners vermelhos/amarelos na mesma tela, o que é visualmente agressivo e tecnicamente informa a mesma coisa repetidamente.

**Recomendação:** Consolidar em um único painel de avisos de permissão no topo da página, ou simplesmente ocultar as ações sem permissão e exibir um tooltip no hover explicando o motivo.

---

## 15. Gradiente de Texto com `-webkit-background-clip` no Header

**Severidade: 🟢 Menor**

```css
background: linear-gradient(135deg, #FFFFFF, #E2E8F0);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

O gradiente no logo do header usa propriedades com prefixo `-webkit-` sem o equivalente padrão. Além disso, a diferença entre branco puro e `#E2E8F0` é praticamente imperceptível — o efeito existe, mas não acrescenta nada visualmente. Apenas adiciona complexidade e risco de compatibilidade.

**Recomendação:** Remover o gradiente. Usar `color: var(--color-white)` simples. Se houver necessidade de destaque, um `font-weight: 800` sobre fundo navy já é suficientemente impactante.

---

## 16. Preview de PDF em Iframe com Altura Fixa

**Severidade: 🟢 Menor**

```css
.pdf-preview {
  height: 350px;
}
```

O iframe de preview do PDF tem 350px fixos — insuficiente para visualizar qualquer documento legal real. O usuário precisa usar o scroll interno do iframe (scroll dentro de scroll) para navegar, o que é uma experiência horrível.

**Recomendação:** Ou remover o preview inline (um link de download já resolve) ou implementar com altura de pelo menos `70vh`. Considerar abrir em modal de tela cheia.

---

## 17. Ausência de Skeleton Loading

**Severidade: 🟢 Menor**

O sistema usa um spinner simples para estado de carregamento. Para a tabela de processos (o componente central do sistema), um skeleton loading (linhas cinzas animadas no lugar das linhas reais) reduziria a sensação de "tela em branco" e é padrão em interfaces institucionais modernas.

---

## O Que Funciona Bem

Para equilibrar, estes aspectos estão bem implementados:

- Os tokens de design no `styles.css` são bem pensados — o problema é a adoção, não a definição.
- As status badges no process-list têm boa semântica de cor (verde = concluído, vermelho = erro, azul = processando).
- O comportamento de NER highlight (`--color-highlight: #FEEBC8`) é elegante e útil.
- Os timestamps clicáveis na transcrição (`seg-timestamp`) são funcionalmente bem implementados.
- O checkbox de responsabilidade (RN-03) tem bom design — o card azul claro comunica "declaração formal" sem ser agressivo.
- O `autosave-label` é um toque de UX refinado.
- Responsividade no `auditoria` está bem pensada com o media query de 900px.

---

## Prioridades de Correção

1. **Migrar inline styles para CSS classes** (estrutural — desbloqueia tudo mais)
2. **Mover `<style>` de dentro dos HTMLs para os arquivos `.css`** (antes que o leak cause bugs)
3. **Substituir hexadecimais hardcoded por tokens** (depois de resolver os inline styles)
4. **Corrigir o badge SSP-PI** (impacto visual imediato, muda percepção institucional)
5. **Substituir emojis por ícones SVG** (profissionalismo)
6. **Estilizar o audio player e o input de arquivo** (componentes mais usados na tela principal)
7. **Corrigir estado is-locked para acessibilidade** (requisito legal potencial)
