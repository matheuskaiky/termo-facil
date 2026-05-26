// Extras: criação/edição de servidor, delegacias (lista + form), fluxo CPF-first do depoente,
// permissões com descrição, dashboard segmentado e drill-downs.

/* ─── Descrições de permissões (centralizadas) ─── */
const PERM_DESC = {
  UPLOAD_AUDIO:        'Enviar arquivos de áudio dos depoimentos para transcrição.',
  EDITAR_TERMO:        'Revisar e editar o texto do termo gerado pela IA.',
  APROVAR_TERMO:       'Aprovar oficialmente o termo, autorizando a geração do PDF.',
  GERAR_PDF:           'Gerar e assinar digitalmente o PDF híbrido (resumo + transcrição).',
  VER_METRICAS:        'Acessar o Dashboard com indicadores e gráficos do sistema.',
  GERENCIAR_USUARIOS:  'Cadastrar, editar e desativar servidores, redefinir senhas.',
  GERENCIAR_CARGOS:    'Criar e editar cargos, atribuir permissões aos cargos.',
  GERENCIAR_DELEGACIAS:'Cadastrar e editar delegacias e unidades da SSP-PI.',
  VER_AUDITORIA:       'Consultar o log completo de ações executadas no sistema.',
};

const DELEGACIAS_MOCK = [
  { id: '1', nome: '1ª DP de Teresina',       sinesp: 'PI0001', municipio: 'Teresina', servidores: 18, ativo: true },
  { id: '2', nome: '3ª DP de Teresina',       sinesp: 'PI0003', municipio: 'Teresina', servidores: 12, ativo: true },
  { id: '3', nome: '5ª DP de Parnaíba',       sinesp: 'PI0107', municipio: 'Parnaíba', servidores: 9,  ativo: true },
  { id: '4', nome: '7ª DP de Picos',          sinesp: 'PI0211', municipio: 'Picos',    servidores: 6,  ativo: true },
  { id: '5', nome: 'DEAM Teresina',           sinesp: 'PI0012', municipio: 'Teresina', servidores: 8,  ativo: true },
  { id: '6', nome: 'DP de Floriano',          sinesp: 'PI0305', municipio: 'Floriano', servidores: 4,  ativo: false },
];

/* ─── Helpers de UI ─── */
function FormSection({ title, sub, children }) {
  return (
    <div className="tf-box" style={{ padding: '1.25rem', marginBottom: '1rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.05rem', marginBottom: '.15rem' }}>{title}</h3>
        {sub && <p className="tf-muted tf-small">{sub}</p>}
      </div>
      {children}
    </div>
  );
}

function FormField({ label, required, hint, error, children, full }) {
  return (
    <div style={{ gridColumn: full ? '1 / -1' : undefined }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '.3rem' }}>
        <span className="tf-label">{label}{required && ' *'}</span>
        {hint && <span className="tf-xs tf-muted">{hint}</span>}
      </div>
      {children}
      {error && <div className="tf-xs" style={{ color: 'var(--color-danger-dark)', marginTop: 4, fontWeight: 600 }}>{error}</div>}
    </div>
  );
}

function SubHeader({ crumbs, title, actions }) {
  return (
    <div style={{ background: '#fff', borderBottom: '1px solid var(--color-border)', padding: '.85rem 2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: '.85rem', alignItems: 'center' }}>
          <button className="tf-btn ghost sm">←</button>
          <div>
            <div className="tf-xs tf-muted">{crumbs}</div>
            <h2 style={{ fontSize: '1.2rem', marginTop: 2 }}>{title}</h2>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '.5rem' }}>{actions}</div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   SERVIDOR: criar
   - Matrícula + CPF únicos; mostra validação em tempo real
   - Delegacia é select, com botão "+ Criar delegacia" abaixo
   ═══════════════════════════════════════════════════════════════ */
function ProposedServerCreate({ duplicated = false }) {
  return (
    <div className="tf-screen">
      <TFHeader active="admin" />
      <SubHeader
        crumbs="Administração · Usuários"
        title="Novo servidor"
        actions={[
          <button key="c" className="tf-btn ghost sm">Cancelar</button>,
          <button key="s" className="tf-btn sm">Cadastrar servidor</button>,
        ]}
      />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem', padding: '1.5rem 2rem' }}>
        <div>
          <FormSection title="Identificação" sub="Dados básicos do servidor. CPF e matrícula precisam ser únicos.">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.85rem' }}>
              <FormField label="CPF" required hint="11 dígitos" error={duplicated ? 'Já existe um servidor com este CPF: João Lima (Mat. 5678).' : null}>
                <div style={{ position: 'relative' }}>
                  <input className={'tf-input tf-mono' + (duplicated ? ' tf-input-error' : '')} defaultValue={duplicated ? '987.654.321-00' : '123.456.789-00'} />
                  {!duplicated && (
                    <span style={{ position: 'absolute', right: 10, top: 9, fontSize: '.75rem', color: 'var(--color-success-dark)', fontWeight: 700 }}>✓ disponível</span>
                  )}
                </div>
              </FormField>
              <FormField label="Matrícula funcional" required hint="6 dígitos">
                <input className="tf-input tf-mono" placeholder="000000" />
              </FormField>
              <FormField label="Nome completo" required full>
                <input className="tf-input" placeholder="Nome conforme registro funcional" />
              </FormField>
              <FormField label="E-mail institucional">
                <input className="tf-input" placeholder="nome@ssp.pi.gov.br" />
              </FormField>
              <FormField label="Telefone">
                <input className="tf-input" placeholder="(86) 9 9999-9999" />
              </FormField>
            </div>
          </FormSection>

          <FormSection title="Vinculação e cargo" sub="Onde o servidor atua e qual o perfil de permissões.">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.85rem', alignItems: 'start' }}>
              <FormField label="Delegacia / Unidade" required hint="Selecione da lista">
                <select className="tf-input">
                  <option value="">Selecionar…</option>
                  {DELEGACIAS_MOCK.filter(d => d.ativo).map(d => (
                    <option key={d.id} value={d.id}>{d.nome} ({d.sinesp})</option>
                  ))}
                </select>
                <button className="tf-btn ghost sm" style={{ marginTop: 6, padding: '.3rem .6rem', fontSize: '.75rem' }}>
                  + Criar nova delegacia
                </button>
              </FormField>
              <FormField label="Cargo" required hint="Define as permissões iniciais">
                <select className="tf-input">
                  <option>Escrivão</option><option>Delegado</option><option>Investigador</option><option>Admin SSP</option>
                </select>
              </FormField>
            </div>
          </FormSection>

          <FormSection title="Senha inicial" sub="Uma senha temporária será gerada ao criar o servidor.">
            <div style={{
              background: 'var(--color-info-bg)', border: '1px solid var(--color-info-border)',
              borderRadius: 4, padding: '.65rem .85rem',
              fontSize: '.82rem', color: 'var(--color-info-dark)',
            }}>
              <strong>ⓘ</strong> Ao cadastrar, o sistema gerará uma senha temporária exibida <strong>uma única vez</strong>. Repasse ao servidor por canal seguro. Ele será obrigado a trocar a senha no primeiro acesso.
            </div>
          </FormSection>
        </div>

        <aside style={{ display: 'flex', flexDirection: 'column', gap: '.85rem' }}>
          <div className="tf-box" style={{ padding: '.85rem 1rem' }}>
            <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.55rem' }}>Validações automáticas</div>
            <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 6, fontSize: '.82rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8, color: duplicated ? 'var(--color-danger-dark)' : 'var(--color-success-dark)' }}>
                <span>{duplicated ? '✗' : '✓'}</span> CPF único na base
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-success-dark)' }}>
                <span>✓</span> Matrícula única
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-light)' }}>
                <span>○</span> Nome completo (mín. 2 palavras)
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-light)' }}>
                <span>○</span> Delegacia selecionada
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-light)' }}>
                <span>○</span> Cargo atribuído
              </li>
            </ul>
          </div>
          <div className="tf-box" style={{ padding: '.85rem 1rem', background: 'var(--color-info-bg)', borderColor: 'var(--color-info-border)' }}>
            <div className="tf-xs" style={{ color: 'var(--color-info-dark)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.4rem' }}>Permissões do cargo selecionado</div>
            <p className="tf-small" style={{ color: 'var(--color-info-dark)', marginBottom: '.5rem' }}>Escrivão · 4 permissões</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {['UPLOAD_AUDIO','EDITAR_TERMO','GERAR_PDF','VER_METRICAS'].map(p => (
                <div key={p} className="tf-xs" style={{ color: 'var(--color-info-dark)' }}>
                  <span className="tf-mono" style={{ fontWeight: 700 }}>{p}</span>
                  <div style={{ color: 'rgba(44,82,130,.8)', marginTop: 1 }}>{PERM_DESC[p]}</div>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      <style>{`.tf-input-error { border-color: var(--color-accent); background: var(--color-danger-bg); }`}</style>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   SERVIDOR: editar
   ═══════════════════════════════════════════════════════════════ */
function ProposedServerEdit() {
  return (
    <div className="tf-screen">
      <TFHeader active="admin" />
      <SubHeader
        crumbs={<>Administração · Usuários · <span className="tf-mono">Mat. 4321</span></>}
        title="Editar servidor — Maria Souza"
        actions={[
          <button key="c" className="tf-btn ghost sm">Cancelar</button>,
          <button key="d" className="tf-btn ghost sm" style={{ color: 'var(--color-danger-dark)' }}>Desativar</button>,
          <button key="s" className="tf-btn sm">Salvar alterações</button>,
        ]}
      />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem', padding: '1.5rem 2rem' }}>
        <div>
          <FormSection title="Identificação" sub="CPF e matrícula não podem ser alterados após o cadastro.">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.85rem' }}>
              <FormField label="CPF" hint="bloqueado">
                <input className="tf-input tf-mono" defaultValue="111.222.333-44" disabled />
              </FormField>
              <FormField label="Matrícula funcional" hint="bloqueado">
                <input className="tf-input tf-mono" defaultValue="4321" disabled />
              </FormField>
              <FormField label="Nome completo" required full>
                <input className="tf-input" defaultValue="Maria Souza" />
              </FormField>
              <FormField label="E-mail institucional">
                <input className="tf-input" defaultValue="maria.souza@ssp.pi.gov.br" />
              </FormField>
              <FormField label="Telefone">
                <input className="tf-input" defaultValue="(86) 9 8888-1212" />
              </FormField>
            </div>
          </FormSection>

          <FormSection title="Vinculação e cargo">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.85rem', alignItems: 'start' }}>
              <FormField label="Delegacia / Unidade" required hint="Selecione da lista">
                <select className="tf-input">
                  {DELEGACIAS_MOCK.filter(d => d.ativo).map(d => (
                    <option key={d.id} value={d.id} selected={d.id === '1'}>{d.nome} ({d.sinesp})</option>
                  ))}
                </select>
                <button className="tf-btn ghost sm" style={{ marginTop: 6, padding: '.3rem .6rem', fontSize: '.75rem' }}>
                  + Criar nova delegacia
                </button>
              </FormField>
              <FormField label="Cargo" required>
                <select className="tf-input">
                  <option selected>Escrivão</option><option>Delegado</option><option>Investigador</option><option>Admin SSP</option>
                </select>
              </FormField>
            </div>
          </FormSection>

          <FormSection title="Senha" sub="Status atual da credencial e ações administrativas.">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '.55rem .85rem', background: 'var(--color-background)', border: '1px solid var(--color-border)', borderRadius: 4 }}>
              <div className="tf-small">Definitiva · trocada há 14 dias</div>
              <button className="tf-btn ghost sm" style={{ background: 'var(--color-warning-bg)', color: 'var(--color-warning-dark)', borderColor: 'var(--color-warning-border)' }}>
                Gerar senha temporária
              </button>
            </div>
          </FormSection>
        </div>

        <aside style={{ display: 'flex', flexDirection: 'column', gap: '.85rem' }}>
          <div className="tf-box" style={{ padding: '.85rem 1rem' }}>
            <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.5rem' }}>Atividade</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '.35rem .75rem', fontSize: '.82rem' }}>
              <span className="tf-muted">Último login</span><span>há 2 horas</span>
              <span className="tf-muted">Processos no mês</span><span><strong>47</strong></span>
              <span className="tf-muted">PDFs assinados</span><span><strong>42</strong></span>
              <span className="tf-muted">Cadastrado em</span><span>03/2024</span>
            </div>
          </div>
          <div className="tf-box" style={{ padding: '.85rem 1rem' }}>
            <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.5rem' }}>Histórico</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '.6rem' }}>
              {[
                { w: 'Cargo alterado: Investigador → Escrivão', by: 'Renata Albuquerque', t: 'há 3 meses' },
                { w: 'Vinculado à 1ª DP Teresina',              by: 'Renata Albuquerque', t: 'há 11 meses' },
                { w: 'Servidor criado',                          by: 'Sistema',           t: 'há 2 anos' },
              ].map((e, i, arr) => (
                <div key={i} style={{ display: 'flex', gap: '.55rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--color-border-strong)', marginTop: 5 }} />
                    {i < arr.length - 1 && <div style={{ flex: 1, width: 1, background: 'var(--color-border)', minHeight: 14 }} />}
                  </div>
                  <div>
                    <div className="tf-small">{e.w}</div>
                    <div className="tf-xs tf-muted">{e.by} · {e.t}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   DELEGACIAS: aba de lista no admin
   ═══════════════════════════════════════════════════════════════ */
function ProposedDelegaciasList() {
  return (
    <div className="tf-screen">
      <TFHeader active="admin" />
      <div style={{ padding: '1.5rem 2rem 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <div className="tf-xs" style={{ color: 'var(--color-text-subtle)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 4 }}>Administração</div>
            <h2 style={{ fontSize: '1.55rem' }}>Controle de acesso</h2>
            <p className="tf-muted tf-small" style={{ marginTop: 2 }}>Servidores, cargos, permissões e delegacias da SSP-PI.</p>
          </div>
          <button className="tf-btn">+ Nova delegacia</button>
        </div>
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--color-border)' }}>
          {[
            { l: 'Usuários', n: 39 },
            { l: 'Cargos', n: 4 },
            { l: 'Matriz de permissões' },
            { l: 'Delegacias', n: 6, active: true },
          ].map((t, i) => (
            <div key={i} style={{
              padding: '.7rem 1rem', fontWeight: 600, fontSize: '.88rem',
              color: t.active ? 'var(--color-primary)' : 'var(--color-secondary)',
              borderBottom: '2px solid ' + (t.active ? 'var(--color-primary)' : 'transparent'),
              marginBottom: -1, cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '.4rem',
            }}>
              {t.l}
              {t.n != null && <span style={{ fontSize: '.7rem', background: 'var(--color-tablehead)', color: 'var(--color-secondary)', padding: '1px 6px', borderRadius: 999, fontWeight: 700 }}>{t.n}</span>}
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: '1rem 2rem 2rem' }}>
        <div style={{ display: 'flex', gap: '.4rem', alignItems: 'center', marginBottom: '.85rem' }}>
          {['Todas','Teresina','Parnaíba','Interior','Inativas'].map((f, i) => (
            <button key={f} className="tf-btn ghost sm" style={{
              background: i === 0 ? 'var(--color-primary)' : 'transparent',
              color: i === 0 ? '#fff' : 'var(--color-secondary)',
              borderColor: i === 0 ? 'var(--color-primary)' : 'var(--color-border)',
            }}>{f}</button>
          ))}
          <div style={{ flex: 1, minWidth: 220 }}>
            <input className="tf-input" placeholder="Buscar por nome, SINESP ou município…" />
          </div>
        </div>

        <div className="tf-box" style={{ overflow: 'hidden' }}>
          <div style={{
            display: 'grid', gridTemplateColumns: '2fr 120px 1fr 120px 100px 60px',
            gap: '1rem', padding: '.6rem 1rem', background: 'var(--color-tablehead)',
            borderBottom: '1px solid var(--color-border)',
            fontSize: '.7rem', fontWeight: 700, color: 'var(--color-text-light)',
            textTransform: 'uppercase', letterSpacing: '.4px'
          }}>
            <div>Nome da unidade</div><div>SINESP</div><div>Município</div><div>Servidores</div><div>Status</div><div></div>
          </div>
          {DELEGACIAS_MOCK.map((d, i) => (
            <div key={d.id} style={{
              display: 'grid', gridTemplateColumns: '2fr 120px 1fr 120px 100px 60px',
              gap: '1rem', padding: '.85rem 1rem',
              borderBottom: i === DELEGACIAS_MOCK.length - 1 ? 'none' : '1px solid var(--color-border)',
              alignItems: 'center', cursor: 'pointer', background: '#fff',
              opacity: d.ativo ? 1 : .6,
            }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-body)', fontSize: '.92rem' }}>{d.nome}</div>
              </div>
              <div className="tf-mono tf-small" style={{ color: 'var(--color-text-light)' }}>{d.sinesp}</div>
              <div className="tf-small">{d.municipio}</div>
              <div className="tf-small"><strong>{d.servidores}</strong> <span className="tf-muted">servidores</span></div>
              <div>
                <span className="tf-status" style={{
                  background: d.ativo ? 'var(--color-success-bg)' : 'var(--color-tablehead)',
                  color: d.ativo ? 'var(--color-success-dark)' : 'var(--color-secondary)',
                  border: d.ativo ? '1px solid #C6F6D5' : '1px solid var(--color-border)',
                }}>{d.ativo ? 'Ativa' : 'Inativa'}</span>
              </div>
              <div style={{ color: 'var(--color-text-subtle)', fontSize: '1.1rem', textAlign: 'right' }}>›</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   DELEGACIA: cadastro + edição (mesmo form, mode prop)
   ═══════════════════════════════════════════════════════════════ */
function ProposedDelegaciaForm({ mode = 'create', duplicated = false }) {
  const isEdit = mode === 'edit';
  return (
    <div className="tf-screen">
      <TFHeader active="admin" />
      <SubHeader
        crumbs={<>Administração · Delegacias{isEdit && <> · <span className="tf-mono">PI0001</span></>}</>}
        title={isEdit ? 'Editar delegacia — 1ª DP de Teresina' : 'Nova delegacia'}
        actions={[
          <button key="c" className="tf-btn ghost sm">Cancelar</button>,
          isEdit && <button key="d" className="tf-btn ghost sm" style={{ color: 'var(--color-danger-dark)' }}>Desativar</button>,
          <button key="s" className="tf-btn sm">{isEdit ? 'Salvar alterações' : 'Cadastrar delegacia'}</button>,
        ].filter(Boolean)}
      />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem', padding: '1.5rem 2rem' }}>
        <div>
          <FormSection title="Identificação" sub="O código SINESP identifica unicamente a unidade no sistema nacional.">
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '.85rem' }}>
              <FormField label="Nome da unidade" required>
                <input className="tf-input" defaultValue={isEdit ? '1ª DP de Teresina' : ''} placeholder="Ex: 2ª DP de Teresina" />
              </FormField>
              <FormField
                label="Código SINESP"
                required
                hint="6 caracteres"
                error={duplicated ? 'Já existe uma unidade com este SINESP: 1ª DP de Teresina.' : null}
              >
                <div style={{ position: 'relative' }}>
                  <input
                    className={'tf-input tf-mono' + (duplicated ? ' tf-input-error' : '')}
                    defaultValue={duplicated ? 'PI0001' : (isEdit ? 'PI0001' : 'PI0002')}
                    maxLength="6"
                  />
                  {!duplicated && !isEdit && (
                    <span style={{ position: 'absolute', right: 10, top: 9, fontSize: '.75rem', color: 'var(--color-success-dark)', fontWeight: 700 }}>✓ disponível</span>
                  )}
                </div>
              </FormField>
              <FormField label="Tipo" required>
                <select className="tf-input">
                  <option>Delegacia de Polícia (DP)</option>
                  <option>Delegacia Especializada (DEAM, DERCC…)</option>
                  <option>Superintendência</option>
                  <option>Posto Policial</option>
                </select>
              </FormField>
              <FormField label="Sigla">
                <input className="tf-input" defaultValue={isEdit ? '1ª DP' : ''} placeholder="Ex: 2ª DP" />
              </FormField>
            </div>
          </FormSection>

          <FormSection title="Localização">
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '.85rem' }}>
              <FormField label="Endereço" full>
                <input className="tf-input" defaultValue={isEdit ? 'Av. Frei Serafim, 2150 — Centro' : ''} placeholder="Rua, número, bairro" />
              </FormField>
              <FormField label="Município" required>
                <select className="tf-input">
                  <option selected={isEdit}>Teresina</option><option>Parnaíba</option><option>Picos</option><option>Floriano</option>
                </select>
              </FormField>
              <FormField label="UF">
                <input className="tf-input" defaultValue="PI" maxLength="2" disabled />
              </FormField>
              <FormField label="CEP">
                <input className="tf-input tf-mono" defaultValue={isEdit ? '64001-020' : ''} placeholder="00000-000" />
              </FormField>
            </div>
          </FormSection>

          <FormSection title="Contato">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.85rem' }}>
              <FormField label="Telefone">
                <input className="tf-input" defaultValue={isEdit ? '(86) 3216-7000' : ''} />
              </FormField>
              <FormField label="E-mail institucional">
                <input className="tf-input" defaultValue={isEdit ? '1dp.teresina@ssp.pi.gov.br' : ''} />
              </FormField>
            </div>
          </FormSection>
        </div>

        <aside style={{ display: 'flex', flexDirection: 'column', gap: '.85rem' }}>
          <div className="tf-box" style={{ padding: '.85rem 1rem' }}>
            <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.55rem' }}>Validações</div>
            <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 6, fontSize: '.82rem' }}>
              <li style={{ color: duplicated ? 'var(--color-danger-dark)' : 'var(--color-success-dark)' }}>
                {duplicated ? '✗' : '✓'} Código SINESP único
              </li>
              <li style={{ color: 'var(--color-success-dark)' }}>✓ Nome único por município</li>
              <li className="tf-muted">○ Endereço preenchido</li>
              <li className="tf-muted">○ Telefone ou e-mail informados</li>
            </ul>
          </div>

          {isEdit && (
            <div className="tf-box" style={{ padding: '.85rem 1rem' }}>
              <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.5rem' }}>Servidores vinculados</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1.1 }}>18</div>
              <p className="tf-xs tf-muted">Desativar a delegacia impede novos vínculos, mas mantém os existentes.</p>
              <button className="tf-btn ghost sm" style={{ width: '100%', marginTop: '.5rem' }}>Ver servidores</button>
            </div>
          )}

          <div className="tf-box" style={{ padding: '.85rem 1rem', background: 'var(--color-info-bg)', borderColor: 'var(--color-info-border)' }}>
            <div className="tf-xs" style={{ color: 'var(--color-info-dark)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.4rem' }}>Sobre SINESP</div>
            <p className="tf-small" style={{ color: 'var(--color-info-dark)', lineHeight: 1.5 }}>
              O código SINESP segue o padrão <span className="tf-mono">UFNNNN</span> (ex.: <span className="tf-mono">PI0001</span>). Deve ser obtido junto à coordenação da SSP-PI.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   DEPOENTE: fluxo CPF-first (3 estados)
   ═══════════════════════════════════════════════════════════════ */
function ProposedDepoenteCpfFlow({ state = 'empty' }) {
  // states: 'empty' | 'not-found' | 'found' | 'found-modified'
  const cpf = state === 'empty' ? '' : '987.654.321-00';
  const known = state === 'found' || state === 'found-modified';
  const fieldsLocked = state === 'empty';

  return (
    <div className="tf-screen">
      <TFHeader active="processos" />
      <SubHeader
        crumbs="Processos · Novo processo"
        title="Dados do depoente"
        actions={[
          <button key="b" className="tf-btn ghost sm">Voltar</button>,
          <button key="n" className="tf-btn sm" disabled={state === 'empty'}>Continuar</button>,
        ]}
      />

      <div style={{ padding: '1.5rem 2rem' }}>
        {/* Status banner */}
        {state === 'not-found' && (
          <div className="tf-box" style={{
            padding: '.75rem 1rem', marginBottom: '1rem',
            background: 'var(--color-warning-bg)', borderColor: 'var(--color-warning-border)',
            borderLeft: '3px solid var(--color-warning)',
            color: 'var(--color-warning-dark)', display: 'flex', alignItems: 'center', gap: '.75rem'
          }}>
            <div style={{ fontSize: '1.2rem' }}>ⓘ</div>
            <div className="tf-small">
              <strong>CPF não cadastrado na base.</strong> Preencha os dados do depoente abaixo. Eles ficarão vinculados a este CPF para futuros depoimentos.
            </div>
          </div>
        )}
        {state === 'found' && (
          <div className="tf-box" style={{
            padding: '.75rem 1rem', marginBottom: '1rem',
            background: 'var(--color-success-bg)', borderColor: '#C6F6D5',
            borderLeft: '3px solid var(--color-success)',
            color: 'var(--color-success-dark)', display: 'flex', alignItems: 'center', gap: '.75rem'
          }}>
            <div style={{ fontSize: '1.2rem' }}>✓</div>
            <div className="tf-small" style={{ flex: 1 }}>
              <strong>Depoente já cadastrado.</strong> Os dados abaixo foram preenchidos automaticamente — última atualização há 3 meses (IP-2025/118). Por favor, confirme se ainda estão corretos.
            </div>
            <button className="tf-btn sm" style={{ background: 'var(--color-success)' }}>Confirmar dados</button>
          </div>
        )}
        {state === 'found-modified' && (
          <div className="tf-box" style={{
            padding: '.75rem 1rem', marginBottom: '1rem',
            background: 'var(--color-warning-bg)', borderColor: 'var(--color-warning-border)',
            borderLeft: '3px solid var(--color-warning)',
            color: 'var(--color-warning-dark)', display: 'flex', alignItems: 'center', gap: '.75rem'
          }}>
            <div style={{ fontSize: '1.2rem' }}>⚠</div>
            <div className="tf-small" style={{ flex: 1 }}>
              <strong>2 campos foram alterados em relação ao cadastro existente.</strong> Os campos modificados estão destacados. Ao salvar, os dados base do depoente serão atualizados para todos os processos futuros.
            </div>
          </div>
        )}

        <FormSection title="CPF do depoente" sub="O CPF é o identificador único. A partir dele o sistema verifica se já existe cadastro.">
          <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1rem', alignItems: 'start' }}>
            <FormField label="CPF" required hint="só números ou formato 000.000.000-00">
              <div style={{ position: 'relative' }}>
                <input
                  className="tf-input tf-mono"
                  value={cpf}
                  placeholder="000.000.000-00"
                  style={{ paddingRight: 110 }}
                  readOnly
                />
                <span style={{
                  position: 'absolute', right: 10, top: 9, fontSize: '.72rem', fontWeight: 700,
                  color: state === 'empty' ? 'var(--color-text-subtle)'
                       : state === 'not-found' ? 'var(--color-warning-dark)'
                       : 'var(--color-success-dark)',
                }}>
                  {state === 'empty'      && '— aguardando —'}
                  {state === 'not-found'  && '⚠ não encontrado'}
                  {known                  && '✓ encontrado'}
                </span>
              </div>
            </FormField>
            {known && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem', height: '100%', paddingTop: 22 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: '50%',
                  background: 'var(--color-primary)', color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 800
                }}>JM</div>
                <div>
                  <div style={{ fontWeight: 700 }}>José Maria da Silva Junior</div>
                  <div className="tf-xs tf-muted">3 depoimentos anteriores · última vez em IP-2025/118</div>
                </div>
              </div>
            )}
          </div>
        </FormSection>

        <FormSection
          title="Dados pessoais"
          sub={fieldsLocked ? 'Informe o CPF acima para liberar os campos.' : known ? 'Campos preenchidos automaticamente. Confirme ou edite se necessário.' : 'Preencha os dados completos do depoente.'}
        >
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '.85rem', opacity: fieldsLocked ? .45 : 1, pointerEvents: fieldsLocked ? 'none' : 'auto' }}>
            <FormField label="Nome completo" required>
              <input className="tf-input" defaultValue={known ? 'José Maria da Silva Junior' : ''} placeholder="Nome completo" />
            </FormField>
            <FormField label="Data de nascimento">
              <input className="tf-input" type="date" defaultValue={known ? '1978-04-12' : ''} />
            </FormField>
            <FormField label="Tipo de depoente" required>
              <select className="tf-input">
                <option>Testemunha</option><option>Vítima</option><option>Suspeito</option><option>Indiciado</option>
              </select>
            </FormField>
            <FormField label="RG / órgão emissor">
              <input className="tf-input" defaultValue={known ? '1234567 SSP-PI' : ''} />
            </FormField>
            <FormField label="Telefone">
              <input
                className={'tf-input' + (state === 'found-modified' ? ' tf-input-modified' : '')}
                defaultValue={state === 'found-modified' ? '(86) 9 7777-0000' : known ? '(86) 9 9999-1234' : ''}
              />
              {state === 'found-modified' && <div className="tf-xs" style={{ color: 'var(--color-warning-dark)', marginTop: 3, fontWeight: 600 }}>alterado · era (86) 9 9999-1234</div>}
            </FormField>
            <FormField label="Profissão">
              <input className="tf-input" defaultValue={known ? 'Comerciante' : ''} />
            </FormField>
            <FormField label="Endereço" full>
              <input
                className={'tf-input' + (state === 'found-modified' ? ' tf-input-modified' : '')}
                defaultValue={state === 'found-modified' ? 'Av. Frei Serafim, 3200 — Centro' : known ? 'Av. Frei Serafim, 2100 — Centro' : ''}
                placeholder="Rua, número, bairro"
              />
              {state === 'found-modified' && <div className="tf-xs" style={{ color: 'var(--color-warning-dark)', marginTop: 3, fontWeight: 600 }}>alterado · era Av. Frei Serafim, 2100 — Centro</div>}
            </FormField>
            <FormField label="Município">
              <input className="tf-input" defaultValue={known ? 'Teresina' : ''} />
            </FormField>
            <FormField label="UF">
              <input className="tf-input" defaultValue={known ? 'PI' : ''} maxLength="2" />
            </FormField>
          </div>
        </FormSection>
      </div>
      <style>{`
        .tf-input-modified {
          border-color: var(--color-warning);
          background: var(--color-warning-bg);
        }
      `}</style>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   PERMISSÕES com descrição — substitui a matriz anterior
   ═══════════════════════════════════════════════════════════════ */
function ProposedAdminMatrixV2() {
  const cargos = ['Escrivão','Delegado','Investigador','Admin SSP'];
  const matrix = {
    'Processos e depoimentos': [
      { name: 'UPLOAD_AUDIO',        v: [1,0,1,0] },
      { name: 'EDITAR_TERMO',        v: [1,1,1,0] },
      { name: 'APROVAR_TERMO',       v: [0,1,0,0] },
      { name: 'GERAR_PDF',           v: [1,1,0,0] },
    ],
    'Administração do sistema': [
      { name: 'GERENCIAR_USUARIOS',  v: [0,1,0,1] },
      { name: 'GERENCIAR_CARGOS',    v: [0,0,0,1] },
      { name: 'GERENCIAR_DELEGACIAS',v: [0,0,0,1] },
    ],
    'Análise e auditoria': [
      { name: 'VER_METRICAS',        v: [1,1,0,1] },
      { name: 'VER_AUDITORIA',       v: [0,0,0,1] },
    ],
  };
  return (
    <div className="tf-screen">
      <TFHeader active="admin" />
      <div style={{ padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <div className="tf-xs" style={{ color: 'var(--color-text-subtle)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 4 }}>Administração</div>
            <h2 style={{ fontSize: '1.55rem' }}>Matriz de permissões</h2>
            <p className="tf-muted tf-small" style={{ marginTop: 2 }}>Cada permissão tem uma descrição clara do que ela libera no sistema.</p>
          </div>
          <button className="tf-btn">+ Novo cargo</button>
        </div>

        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--color-border)', marginBottom: '1.25rem' }}>
          {['Usuários','Cargos','Matriz de permissões','Delegacias'].map((l, i) => (
            <div key={l} style={{
              padding: '.7rem 1rem', fontWeight: 600, fontSize: '.88rem',
              color: i === 2 ? 'var(--color-primary)' : 'var(--color-secondary)',
              borderBottom: '2px solid ' + (i === 2 ? 'var(--color-primary)' : 'transparent'),
              marginBottom: -1,
            }}>{l}</div>
          ))}
        </div>

        <div className="tf-box" style={{ overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ background: 'var(--color-tablehead)', padding: '.7rem 1rem', textAlign: 'left', fontSize: '.72rem', textTransform: 'uppercase', letterSpacing: '.4px', color: 'var(--color-text-light)', fontWeight: 700, width: '50%' }}>Permissão</th>
                {cargos.map(c => (
                  <th key={c} style={{ background: 'var(--color-tablehead)', padding: '.7rem 1rem', textAlign: 'center', fontSize: '.72rem', textTransform: 'uppercase', letterSpacing: '.4px', color: 'var(--color-primary)', fontWeight: 700, minWidth: 110 }}>{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(matrix).map(([grp, rows]) => (
                <React.Fragment key={grp}>
                  <tr>
                    <td colSpan={cargos.length + 1} style={{
                      background: 'var(--color-bg-deep)', padding: '.45rem 1rem',
                      fontSize: '.72rem', fontWeight: 700, color: 'var(--color-secondary)',
                      textTransform: 'uppercase', letterSpacing: '.4px',
                    }}>{grp}</td>
                  </tr>
                  {rows.map(r => (
                    <tr key={r.name} style={{ borderBottom: '1px solid var(--color-border)' }}>
                      <td style={{ padding: '.7rem 1rem' }}>
                        <div className="tf-mono" style={{ fontSize: '.78rem', fontWeight: 700, color: 'var(--color-primary)' }}>{r.name}</div>
                        <div className="tf-xs tf-muted" style={{ marginTop: 2, lineHeight: 1.45 }}>{PERM_DESC[r.name]}</div>
                      </td>
                      {r.v.map((on, i) => (
                        <td key={i} style={{ textAlign: 'center', padding: '.7rem 1rem' }}>
                          <span style={{
                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                            width: 22, height: 22, borderRadius: 4,
                            background: on ? 'var(--color-success)' : 'transparent',
                            border: on ? 'none' : '1px solid var(--color-border-strong)',
                            cursor: 'pointer'
                          }}>
                            {on ? <svg width="12" height="12" viewBox="0 0 12 12"><polyline points="2,6 5,9 10,3" fill="none" stroke="#fff" strokeWidth="2"/></svg> : null}
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   DASHBOARD: visão geral com segmentação por delegacia
   ═══════════════════════════════════════════════════════════════ */
function ProposedDashboardByDelegacia() {
  const delegacias = [
    { id: 'todas', n: 'Todas as delegacias',    sub: '6 ativas',  vol: 342, taxa: '94%', p: 1.0,  active: true },
    { id: '1',     n: '1ª DP de Teresina',      sub: 'PI0001',    vol: 128, taxa: '96%', p: .37 },
    { id: '2',     n: '3ª DP de Teresina',      sub: 'PI0003',    vol: 84,  taxa: '94%', p: .25 },
    { id: '3',     n: '5ª DP de Parnaíba',      sub: 'PI0107',    vol: 56,  taxa: '92%', p: .16 },
    { id: '5',     n: 'DEAM Teresina',          sub: 'PI0012',    vol: 41,  taxa: '95%', p: .12 },
    { id: '4',     n: '7ª DP de Picos',         sub: 'PI0211',    vol: 33,  taxa: '88%', p: .10 },
  ];

  return (
    <div className="tf-screen">
      <TFHeader active="metricas" />
      <div style={{ padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.25rem' }}>
          <div>
            <div className="tf-xs" style={{ color: 'var(--color-text-subtle)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 4 }}>Indicadores</div>
            <h2 style={{ fontSize: '1.55rem' }}>Dashboard</h2>
            <p className="tf-muted tf-small" style={{ marginTop: 2 }}>Visão consolidada · 30 dias</p>
          </div>
          <div style={{ display: 'flex', gap: '.4rem', alignItems: 'center' }}>
            <select className="tf-input" style={{ width: 'auto', fontWeight: 600 }}>
              <option>Por delegacia</option><option>Por município</option><option>Por escrivão</option>
            </select>
            <div className="tf-box" style={{ display: 'flex', padding: 2 }}>
              {['7 dias','30 dias','Este ano'].map((p, i) => (
                <button key={p} className="tf-btn ghost sm" style={{
                  border: 'none', borderRadius: 3,
                  background: i === 1 ? 'var(--color-primary)' : 'transparent',
                  color: i === 1 ? '#fff' : 'var(--color-secondary)',
                }}>{p}</button>
              ))}
            </div>
            <button className="tf-btn ghost">Exportar</button>
          </div>
        </div>

        {/* Delegacias como cards selecionáveis (substitui segmented control quando >5 itens) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '.6rem', marginBottom: '1.25rem' }}>
          {delegacias.map(d => (
            <div key={d.id} className="tf-box" style={{
              padding: '.7rem .85rem', cursor: 'pointer',
              borderColor: d.active ? 'var(--color-primary)' : 'var(--color-border)',
              background: d.active ? 'var(--color-info-bg)' : '#fff',
              borderWidth: d.active ? 2 : 1,
            }}>
              <div className="tf-xs" style={{ color: d.active ? 'var(--color-primary)' : 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.3px' }}>{d.sub}</div>
              <div className="tf-small" style={{ fontWeight: 700, color: 'var(--color-text-body)', marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{d.n}</div>
              <div style={{ marginTop: 8, display: 'flex', alignItems: 'baseline', gap: '.4rem' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-primary)' }}>{d.vol}</span>
                <span className="tf-xs tf-muted">depoim.</span>
              </div>
              <div className="tf-xs" style={{ marginTop: 2, color: 'var(--color-success-dark)' }}>taxa {d.taxa}</div>
            </div>
          ))}
        </div>

        {/* Top: ranking de delegacias */}
        <div className="tf-box" style={{ marginBottom: '1.25rem' }}>
          <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>Produção por delegacia · 30 dias</div>
            <div className="tf-xs tf-muted">clique para detalhar</div>
          </div>
          <div style={{ padding: '.85rem 1rem', display: 'flex', flexDirection: 'column', gap: '.55rem' }}>
            {delegacias.filter(d => d.id !== 'todas').map(d => (
              <div key={d.id} style={{ display: 'grid', gridTemplateColumns: '220px 60px 1fr 60px', gap: '.65rem', alignItems: 'center', cursor: 'pointer', padding: '.25rem 0' }}>
                <div className="tf-small" style={{ color: 'var(--color-text-body)' }}>{d.n}</div>
                <div className="tf-mono tf-xs tf-muted">{d.sub}</div>
                <div style={{ height: 8, background: 'var(--color-bg-deep)', borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ width: `${d.p * 100}%`, height: '100%', background: 'var(--color-primary)' }} />
                </div>
                <div className="tf-mono" style={{ fontWeight: 700, color: 'var(--color-primary)', textAlign: 'right' }}>{d.vol}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom row: comparativos */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.82rem', fontWeight: 700, color: 'var(--color-primary)' }}>Taxa de sucesso por delegacia</div>
            <div style={{ padding: '.85rem 1rem', display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
              {delegacias.filter(d => d.id !== 'todas').map(d => {
                const pct = parseInt(d.taxa);
                return (
                  <div key={d.id} style={{ display: 'grid', gridTemplateColumns: '1fr 50px', gap: '.5rem', alignItems: 'center' }}>
                    <div className="tf-xs">
                      <div>{d.n}</div>
                      <div style={{ marginTop: 2, height: 5, background: 'var(--color-bg-deep)', borderRadius: 999 }}>
                        <div style={{ width: `${pct}%`, height: '100%', background: pct >= 94 ? 'var(--color-success)' : pct >= 90 ? 'var(--color-warning)' : 'var(--color-accent)', borderRadius: 999 }} />
                      </div>
                    </div>
                    <div className="tf-mono tf-xs" style={{ fontWeight: 700, textAlign: 'right' }}>{d.taxa}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.82rem', fontWeight: 700, color: 'var(--color-primary)' }}>Tempo médio de processamento</div>
            <div style={{ padding: '.85rem 1rem', display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
              {delegacias.filter(d => d.id !== 'todas').map((d, i) => {
                const min = [12.3, 14.2, 16.1, 18.5, 13.7][i];
                return (
                  <div key={d.id} style={{ display: 'grid', gridTemplateColumns: '1fr 70px', gap: '.5rem', alignItems: 'center' }}>
                    <div className="tf-xs">{d.n}</div>
                    <div className="tf-mono tf-xs" style={{ fontWeight: 700, textAlign: 'right' }}>{min} min</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.82rem', fontWeight: 700, color: 'var(--color-primary)' }}>Pendências por delegacia</div>
            <div style={{ padding: '.85rem 1rem', display: 'flex', flexDirection: 'column', gap: '.55rem' }}>
              {delegacias.filter(d => d.id !== 'todas').map((d, i) => {
                const p = [3, 5, 2, 7, 1][i];
                return (
                  <div key={d.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="tf-xs">{d.n}</span>
                    <span className="tf-status" style={{
                      background: p > 5 ? 'var(--color-danger-bg)' : p > 2 ? 'var(--color-warning-bg)' : 'var(--color-success-bg)',
                      color: p > 5 ? 'var(--color-danger-dark)' : p > 2 ? 'var(--color-warning-dark)' : 'var(--color-success-dark)',
                      fontSize: '.7rem',
                    }}>{p} aguardando</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   DASHBOARD: drill-down de uma delegacia
   ═══════════════════════════════════════════════════════════════ */
function ProposedDashboardDelegaciaDetail() {
  const escrivaes = [
    { n: 'Maria Souza',       v: 47, p: 1.0, taxa: '98%' },
    { n: 'João Lima',         v: 38, p: .81, taxa: '96%' },
    { n: 'Carlos Dias',       v: 29, p: .62, taxa: '93%' },
    { n: 'Renata Albuquerque', v: 14, p: .30, taxa: '92%' },
  ];
  const ultimos = [
    { num: 'IP-2026/004', dep: 'Patricia Helena Coelho', esc: 'Maria Souza',  status: 'Concluído', when: 'há 2h' },
    { num: 'IP-2026/003', dep: 'Rafael Augusto Pereira', esc: 'João Lima',    status: 'Concluído', when: 'há 5h' },
    { num: 'IP-2026/002', dep: 'Ana Carolina Mendes',    esc: 'Maria Souza',  status: 'Concluído', when: 'há 8h' },
    { num: 'IP-2026/005', dep: 'Marcos Vinicius Tavares', esc: 'João Lima',   status: 'Erro',      when: 'há 1d' },
  ];

  return (
    <div className="tf-screen">
      <TFHeader active="metricas" />
      <SubHeader
        crumbs={<>Dashboard · Delegacias · <span className="tf-mono">PI0001</span></>}
        title="1ª DP de Teresina"
        actions={[
          <button key="b" className="tf-btn ghost sm">← Voltar ao dashboard</button>,
          <button key="e" className="tf-btn ghost sm">Exportar relatório</button>,
        ]}
      />

      <div style={{ padding: '1.25rem 2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '.75rem', marginBottom: '1.25rem' }}>
          {[
            { l: 'Depoimentos',     v: 128, d: '+14%' },
            { l: 'Servidores ativos', v: 18,  d: '+1' },
            { l: 'Taxa de sucesso', v: '96%', d: '+1.5pp' },
            { l: 'Tempo médio',     v: '12.3 min', d: '-0.8 min' },
          ].map(k => (
            <div key={k.l} className="tf-box" style={{ padding: '.9rem 1rem' }}>
              <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.4px' }}>{k.l}</div>
              <div style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1.1, marginTop: 4 }}>{k.v}</div>
              <div className="tf-xs" style={{ color: 'var(--color-success-dark)', fontWeight: 700, marginTop: 2 }}>▲ {k.d}</div>
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>Escrivães da unidade</div>
            <div style={{ padding: '.85rem 1rem', display: 'flex', flexDirection: 'column', gap: '.55rem' }}>
              {escrivaes.map(e => (
                <div key={e.n} style={{ display: 'grid', gridTemplateColumns: '160px 1fr 50px 50px', gap: '.65rem', alignItems: 'center', cursor: 'pointer' }}>
                  <div className="tf-small">{e.n}</div>
                  <div style={{ height: 7, background: 'var(--color-bg-deep)', borderRadius: 999 }}>
                    <div style={{ width: `${e.p * 100}%`, height: '100%', background: 'var(--color-primary)', borderRadius: 999 }} />
                  </div>
                  <div className="tf-mono tf-xs" style={{ fontWeight: 700, textAlign: 'right' }}>{e.v}</div>
                  <div className="tf-xs" style={{ color: 'var(--color-success-dark)', textAlign: 'right', fontWeight: 700 }}>{e.taxa}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>Tipos de depoente · 30 dias</div>
            <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '.7rem' }}>
              {[
                { l: 'Testemunha', v: 71, c: 'var(--color-primary)' },
                { l: 'Vítima',     v: 32, c: 'var(--color-info)' },
                { l: 'Suspeito',   v: 18, c: 'var(--color-warning)' },
                { l: 'Indiciado',  v: 7,  c: 'var(--color-accent)' },
              ].map((t, i) => (
                <div key={t.l}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span className="tf-small">{t.l}</span>
                    <span className="tf-mono tf-xs" style={{ fontWeight: 700 }}>{t.v}</span>
                  </div>
                  <div style={{ height: 8, background: 'var(--color-bg-deep)', borderRadius: 999 }}>
                    <div style={{ width: `${(t.v / 128) * 100}%`, height: '100%', background: t.c, borderRadius: 999 }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="tf-box">
          <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>Atividade recente desta delegacia</div>
            <a className="tf-xs" style={{ color: 'var(--color-primary-mid)', fontWeight: 600 }}>ver todos →</a>
          </div>
          <div>
            {ultimos.map((u, i) => (
              <div key={u.num} style={{
                display: 'grid', gridTemplateColumns: '140px 1fr 160px 120px 80px',
                gap: '1rem', padding: '.7rem 1rem',
                borderBottom: i === ultimos.length - 1 ? 'none' : '1px solid var(--color-border)',
                alignItems: 'center',
              }}>
                <div className="tf-mono tf-small" style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{u.num}</div>
                <div className="tf-small">{u.dep}</div>
                <div className="tf-small tf-muted">{u.esc}</div>
                <div><StatusPill status={u.status} /></div>
                <div className="tf-xs tf-muted" style={{ textAlign: 'right' }}>{u.when}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   DASHBOARD: drill-down de um escrivão
   ═══════════════════════════════════════════════════════════════ */
function ProposedDashboardEscrivaoDetail() {
  const days = Array.from({length: 30}).map((_, i) => Math.max(0, Math.round(1 + Math.sin(i / 4) * 1.5 + Math.cos(i / 9) * 1.2 + 1)));
  const max = Math.max(...days);

  return (
    <div className="tf-screen">
      <TFHeader active="metricas" />
      <SubHeader
        crumbs={<>Dashboard · Escrivães · <span className="tf-mono">Mat. 4321</span></>}
        title="Maria Souza — 1ª DP de Teresina"
        actions={[
          <button key="b" className="tf-btn ghost sm">← Voltar ao dashboard</button>,
          <button key="p" className="tf-btn ghost sm">Ver perfil</button>,
        ]}
      />

      <div style={{ padding: '1.25rem 2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '.75rem', marginBottom: '1.25rem' }}>
          {[
            { l: 'Depoimentos',  v: 47, d: '+12 vs. mês anterior' },
            { l: 'Termos editados', v: 47, d: '100% do produzido' },
            { l: 'PDFs assinados',  v: 42, d: '89% conclusão' },
            { l: 'Taxa de sucesso', v: '98%', d: '+2pp' },
            { l: 'Tempo médio',     v: '10.4 min', d: '-1.2 min' },
          ].map(k => (
            <div key={k.l} className="tf-box" style={{ padding: '.85rem 1rem' }}>
              <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.4px' }}>{k.l}</div>
              <div style={{ fontSize: '1.55rem', fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1.1, marginTop: 4 }}>{k.v}</div>
              <div className="tf-xs tf-muted" style={{ marginTop: 2 }}>{k.d}</div>
            </div>
          ))}
        </div>

        <div className="tf-box" style={{ marginBottom: '1.25rem' }}>
          <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>Produção diária · últimos 30 dias</div>
          <div style={{ padding: '1rem', display: 'flex', alignItems: 'flex-end', gap: 3, height: 140 }}>
            {days.map((d, i) => (
              <div key={i} title={`Dia ${i + 1}: ${d} depoimentos`} style={{
                flex: 1, height: `${(d / max) * 100}%`,
                background: 'var(--color-primary)', borderRadius: '2px 2px 0 0',
                opacity: 0.5 + (d / max) * 0.5,
                minHeight: 2,
              }} />
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.82rem', fontWeight: 700, color: 'var(--color-primary)' }}>Distribuição por tipo de depoente</div>
            <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '.55rem' }}>
              {[{l:'Testemunha',v:28,c:'var(--color-primary)'},{l:'Vítima',v:11,c:'var(--color-info)'},{l:'Suspeito',v:6,c:'var(--color-warning)'},{l:'Indiciado',v:2,c:'var(--color-accent)'}].map(t => (
                <div key={t.l}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                    <span className="tf-small">{t.l}</span>
                    <span className="tf-mono tf-xs" style={{ fontWeight: 700 }}>{t.v}</span>
                  </div>
                  <div style={{ height: 7, background: 'var(--color-bg-deep)', borderRadius: 999 }}>
                    <div style={{ width: `${(t.v / 47) * 100}%`, height: '100%', background: t.c, borderRadius: 999 }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.82rem', fontWeight: 700, color: 'var(--color-primary)' }}>Pontos de atenção</div>
            <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '.6rem' }}>
              <div style={{ display: 'flex', gap: '.6rem', alignItems: 'flex-start' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--color-warning)', marginTop: 6 }} />
                <div className="tf-small">5 termos com mais de 3 edições pós-geração — pode indicar baixa qualidade do prompt LLM nesse perfil de caso.</div>
              </div>
              <div style={{ display: 'flex', gap: '.6rem', alignItems: 'flex-start' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--color-info)', marginTop: 6 }} />
                <div className="tf-small">Tempo médio de revisão humana 0.8 min abaixo da média da delegacia.</div>
              </div>
              <div style={{ display: 'flex', gap: '.6rem', alignItems: 'flex-start' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--color-success)', marginTop: 6 }} />
                <div className="tf-small">42 PDFs assinados — 100% com revisão humana confirmada (checkbox de responsabilidade).</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   DASHBOARD: drill-down de erros (análise de falhas)
   ═══════════════════════════════════════════════════════════════ */
function ProposedDashboardErrorsView() {
  const errors = [
    { num: 'IP-2026/005', dep: 'Marcos Vinicius Tavares', etapa: 'Transcrevendo', detail: 'Áudio com 4 falantes simultâneos — diarização falhou.', when: 'há 6h', deleg: '3ª DP Teresina' },
    { num: 'IP-2026/011', dep: 'Bruno Soares',            etapa: 'Gerando Resumo', detail: 'LLM atingiu limite de contexto (>16k tokens).', when: 'há 1d',  deleg: '7ª DP Picos' },
    { num: 'IP-2026/014', dep: 'Aline Cardoso',           etapa: 'Extraindo Dados', detail: 'NER não encontrou pessoas — pode ser depoimento sem nomes próprios.', when: 'há 1d', deleg: '5ª DP Parnaíba' },
    { num: 'IP-2026/018', dep: 'Henrique Tavares',        etapa: 'Transcrevendo', detail: 'Áudio corrompido — header do .wav inválido.', when: 'há 2d', deleg: '7ª DP Picos' },
  ];

  return (
    <div className="tf-screen">
      <TFHeader active="metricas" />
      <SubHeader
        crumbs="Dashboard · Análise de falhas"
        title="Jobs com erro · últimos 30 dias"
        actions={[
          <button key="b" className="tf-btn ghost sm">← Voltar ao dashboard</button>,
          <button key="e" className="tf-btn ghost sm">Exportar CSV</button>,
        ]}
      />

      <div style={{ padding: '1.25rem 2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '.75rem', marginBottom: '1.25rem' }}>
          {[
            { l: 'Jobs com erro',         v: 18,    d: '5.3% do total' },
            { l: 'Falha no ASR',          v: 9,     c: 'var(--color-info)' },
            { l: 'Falha na extração',     v: 3,     c: 'var(--color-warning)' },
            { l: 'Falha no LLM',          v: 6,     c: 'var(--color-accent)' },
          ].map(k => (
            <div key={k.l} className="tf-box" style={{ padding: '.9rem 1rem', borderLeft: k.c ? `3px solid ${k.c}` : undefined }}>
              <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.4px' }}>{k.l}</div>
              <div style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1.1, marginTop: 4 }}>{k.v}</div>
              {k.d && <div className="tf-xs tf-muted" style={{ marginTop: 2 }}>{k.d}</div>}
            </div>
          ))}
        </div>

        <div className="tf-box">
          <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>Lista de falhas</div>
            <div style={{ display: 'flex', gap: '.4rem' }}>
              {['Todas','ASR','NER','LLM'].map((f, i) => (
                <button key={f} className="tf-btn ghost sm" style={{
                  background: i === 0 ? 'var(--color-primary)' : 'transparent',
                  color: i === 0 ? '#fff' : 'var(--color-secondary)',
                  borderColor: i === 0 ? 'var(--color-primary)' : 'var(--color-border)',
                }}>{f}</button>
              ))}
            </div>
          </div>
          <div>
            {errors.map((e, i) => (
              <div key={e.num} style={{
                display: 'grid', gridTemplateColumns: '140px 1fr 140px 80px',
                gap: '1rem', padding: '.85rem 1rem',
                borderBottom: i === errors.length - 1 ? 'none' : '1px solid var(--color-border)',
                alignItems: 'flex-start',
              }}>
                <div>
                  <div className="tf-mono tf-small" style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{e.num}</div>
                  <div className="tf-xs tf-muted">{e.deleg}</div>
                </div>
                <div>
                  <div className="tf-small">{e.dep}</div>
                  <div className="tf-xs" style={{ color: 'var(--color-danger-dark)', marginTop: 2 }}>{e.detail}</div>
                </div>
                <div><StatusPill status={e.etapa} /></div>
                <div style={{ textAlign: 'right' }}>
                  <div className="tf-xs tf-muted">{e.when}</div>
                  <button className="tf-btn ghost sm" style={{ marginTop: 4, padding: '.25rem .5rem', fontSize: '.7rem' }}>Reprocessar</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  PERM_DESC,
  ProposedServerCreate, ProposedServerEdit,
  ProposedDelegaciasList, ProposedDelegaciaForm,
  ProposedDepoenteCpfFlow,
  ProposedAdminMatrixV2,
  ProposedDashboardByDelegacia,
  ProposedDashboardDelegaciaDetail,
  ProposedDashboardEscrivaoDetail,
  ProposedDashboardErrorsView,
});
