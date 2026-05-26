// Telas extras: Admin (RBAC), Dashboard (substitui Métricas), Cadastro/Edição de Processo
// "Current" recreations + "Proposed" redesigns.

/* ─────────────────────────────────────────────────────────
   CURRENT: Admin / RBAC
   ───────────────────────────────────────────────────────── */
function CurrentAdmin() {
  const users = [
    { nome: 'Maria Souza',        mat: '4321', unidade: '1ª DP Teresina',  sinesp: 'PI0001', cargo: 'Escrivã',          temp: false },
    { nome: 'João Lima',          mat: '5678', unidade: '3ª DP Teresina',  sinesp: 'PI0003', cargo: 'Delegado',         temp: true  },
    { nome: 'Carlos Dias',        mat: '6210', unidade: '5ª DP Parnaíba',  sinesp: 'PI0107', cargo: 'Investigador',     temp: false },
    { nome: 'Renata Albuquerque', mat: '4498', unidade: '1ª DP Teresina',  sinesp: 'PI0001', cargo: 'Admin SSP',        temp: false },
  ];
  const cargos = [
    { nome: 'Escrivão',     perms: ['UPLOAD_AUDIO','EDITAR_TERMO','GERAR_PDF','VER_METRICAS'] },
    { nome: 'Delegado',     perms: ['EDITAR_TERMO','APROVAR_TERMO','GERAR_PDF','VER_METRICAS','GERENCIAR_USUARIOS'] },
    { nome: 'Investigador', perms: ['UPLOAD_AUDIO','EDITAR_TERMO'] },
    { nome: 'Admin SSP',    perms: ['GERENCIAR_USUARIOS','GERENCIAR_CARGOS','VER_AUDITORIA','VER_METRICAS'] },
  ];
  const permissions = ['UPLOAD_AUDIO','EDITAR_TERMO','APROVAR_TERMO','GERAR_PDF','VER_METRICAS','GERENCIAR_USUARIOS','GERENCIAR_CARGOS','VER_AUDITORIA'];

  return (
    <div className="tf-screen">
      <TFHeader active="admin" />
      <div style={{ padding: '2rem', height: 'calc(100% - 56px)', overflow: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)', paddingBottom: '1.5rem', marginBottom: '1.5rem' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem' }}>Painel de Controle de Acesso (RBAC)</h2>
            <p className="tf-muted tf-small" style={{ marginTop: 4 }}>Gerencie as atribuições de cargos dos policiais e crie perfis de permissões customizados para a SSP-PI.</p>
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            {[
              { v: users.length, l: 'Usuários' },
              { v: cargos.length, l: 'Cargos' },
              { v: permissions.length, l: 'Permissões' },
            ].map(s => (
              <div key={s.l} className="tf-box" style={{ padding: '.5rem 1.25rem', textAlign: 'center', minWidth: 80 }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1.2 }}>{s.v}</div>
                <div className="tf-xs" style={{ color: 'var(--color-secondary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.3px', opacity: .7, marginTop: 2 }}>{s.l}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '.25rem', borderBottom: '2px solid var(--color-border)', marginBottom: '1.5rem' }}>
          <div style={{ padding: '.7rem 1.25rem', fontWeight: 600, color: 'var(--color-primary)', borderBottom: '3px solid var(--color-primary)', marginBottom: -2 }}>Usuários Cadastrados</div>
          <div style={{ padding: '.7rem 1.25rem', fontWeight: 600, color: 'var(--color-secondary)' }}>Matriz de Cargos & Criar Cargo</div>
        </div>

        <div className="tf-box">
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--color-tablehead)' }}>
                {['Nome do Servidor','Matrícula','Unidade / Delegacia','Cargo Atual','Alterar Cargo','Senha'].map(h => (
                  <th key={h} style={{ padding: '.85rem 1rem', textAlign: 'left', color: 'var(--color-primary)', fontSize: '.82rem', fontWeight: 700, borderBottom: '2px solid var(--color-border)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.mat} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '.85rem 1rem' }}>
                    <div style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{u.nome}</div>
                  </td>
                  <td style={{ padding: '.85rem 1rem' }}>
                    <span style={{ fontFamily: 'monospace', background: 'var(--color-code-bg)', padding: '.2rem .5rem', borderRadius: 4, fontWeight: 700, fontSize: '.82rem' }}>{u.mat}</span>
                  </td>
                  <td style={{ padding: '.85rem 1rem' }}>
                    <div style={{ fontWeight: 500, fontSize: '.85rem' }}>{u.unidade}</div>
                    <div className="tf-xs tf-muted">SINESP: {u.sinesp}</div>
                  </td>
                  <td style={{ padding: '.85rem 1rem' }}>
                    <span style={{ background: 'var(--color-info-bg)', color: 'var(--color-info)', padding: '.2rem .7rem', borderRadius: 999, fontSize: '.78rem', fontWeight: 700, border: '1px solid var(--color-info-border)' }}>{u.cargo}</span>
                  </td>
                  <td style={{ padding: '.85rem 1rem' }}>
                    <select className="tf-input" style={{ width: 'auto', fontWeight: 600, color: 'var(--color-secondary)', fontSize: '.85rem' }}>
                      <option>Atribuir: {u.cargo}</option>
                    </select>
                  </td>
                  <td style={{ padding: '.85rem 1rem' }}>
                    <div style={{ display: 'flex', gap: '.5rem', alignItems: 'center' }}>
                      {u.temp && <span style={{ background: 'var(--color-warning-bg)', color: 'var(--color-warning-dark)', border: '1px solid var(--color-warning-border)', borderRadius: 999, padding: '2px 7px', fontSize: '.7rem', fontWeight: 700 }}>Temp</span>}
                      <button style={{ background: 'var(--color-warning-bg)', border: '1px solid var(--color-warning-border)', color: 'var(--color-warning-dark)', borderRadius: 4, padding: '.3rem .65rem', fontSize: '.78rem', fontWeight: 700, cursor: 'pointer' }}>Gerar Temp</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   PROPOSED: Admin / RBAC
   - Tabs: Usuários · Cargos · Matriz de Permissões (NOVA aba)
   - Lista de usuários com avatar, último login, filtros por delegacia
   - Drawer lateral para edição (substitui select inline)
   - Matriz cargos × permissões (a "matriz" prometida pelo título atual)
   ───────────────────────────────────────────────────────── */
function ProposedAdmin() {
  const users = [
    { nome: 'Maria Souza',        mat: '4321', unidade: '1ª DP Teresina',  cargo: 'Escrivão',     login: 'há 2h',   ativo: true,  temp: false, sel: true },
    { nome: 'João Lima',          mat: '5678', unidade: '3ª DP Teresina',  cargo: 'Delegado',     login: 'há 1 dia', ativo: true,  temp: true  },
    { nome: 'Carlos Dias',        mat: '6210', unidade: '5ª DP Parnaíba',  cargo: 'Investigador', login: 'há 6 dias', ativo: true, temp: false },
    { nome: 'Renata Albuquerque', mat: '4498', unidade: '1ª DP Teresina',  cargo: 'Admin SSP',    login: 'há 11 min', ativo: true, temp: false },
    { nome: 'Paulo Cesar Mota',   mat: '7012', unidade: '7ª DP Picos',     cargo: 'Investigador', login: 'há 32 dias', ativo: false, temp: false },
  ];
  const allPerms = [
    { grp: 'Processos',      name: 'UPLOAD_AUDIO' },
    { grp: 'Processos',      name: 'EDITAR_TERMO' },
    { grp: 'Processos',      name: 'APROVAR_TERMO' },
    { grp: 'Processos',      name: 'GERAR_PDF' },
    { grp: 'Administração',  name: 'GERENCIAR_USUARIOS' },
    { grp: 'Administração',  name: 'GERENCIAR_CARGOS' },
    { grp: 'Análise',        name: 'VER_METRICAS' },
    { grp: 'Análise',        name: 'VER_AUDITORIA' },
  ];
  const cargos = [
    { nome: 'Escrivão',     count: 12, perms: ['UPLOAD_AUDIO','EDITAR_TERMO','GERAR_PDF','VER_METRICAS'] },
    { nome: 'Delegado',     count: 4,  perms: ['EDITAR_TERMO','APROVAR_TERMO','GERAR_PDF','VER_METRICAS','GERENCIAR_USUARIOS'] },
    { nome: 'Investigador', count: 21, perms: ['UPLOAD_AUDIO','EDITAR_TERMO'] },
    { nome: 'Admin SSP',    count: 2,  perms: ['GERENCIAR_USUARIOS','GERENCIAR_CARGOS','VER_AUDITORIA','VER_METRICAS'] },
  ];
  const initials = n => n.split(' ').slice(0, 2).map(s => s[0]).join('');
  const filters = ['Todos', 'Escrivão', 'Delegado', 'Investigador', 'Admin SSP', 'Senha temporária', 'Inativos'];
  const selected = users.find(u => u.sel) || users[0];
  const selectedCargo = cargos.find(c => c.nome === selected.cargo) || cargos[0];

  return (
    <div className="tf-screen">
      <TFHeader active="admin" />

      {/* Page header */}
      <div style={{ padding: '1.5rem 2rem 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <div className="tf-xs" style={{ color: 'var(--color-text-subtle)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 4 }}>
              Administração
            </div>
            <h2 style={{ fontSize: '1.55rem' }}>Controle de acesso</h2>
            <p className="tf-muted tf-small" style={{ marginTop: 2 }}>Servidores, cargos e permissões da SSP-PI.</p>
          </div>
          <div style={{ display: 'flex', gap: '.5rem' }}>
            <button className="tf-btn ghost">Exportar lista</button>
            <button className="tf-btn">+ Novo servidor</button>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--color-border)' }}>
          {[
            { id: 'users', l: 'Usuários', n: 39, active: true },
            { id: 'roles', l: 'Cargos', n: 4 },
            { id: 'matrix', l: 'Matriz de permissões' },
          ].map(t => (
            <div key={t.id} style={{
              padding: '.7rem 1rem', fontWeight: 600, fontSize: '.88rem',
              color: t.active ? 'var(--color-primary)' : 'var(--color-secondary)',
              borderBottom: '2px solid ' + (t.active ? 'var(--color-primary)' : 'transparent'),
              marginBottom: -1, cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '.4rem'
            }}>
              {t.l}
              {t.n != null && (
                <span style={{ fontSize: '.7rem', background: 'var(--color-tablehead)', color: 'var(--color-secondary)', padding: '1px 6px', borderRadius: 999, fontWeight: 700 }}>{t.n}</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Working area: list + detail drawer side by side */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '1.25rem', padding: '1rem 2rem 2rem', height: 'calc(100% - 56px - 175px)' }}>
        {/* Left: user list */}
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {/* Filter chips + search */}
          <div style={{ display: 'flex', gap: '.4rem', flexWrap: 'wrap', marginBottom: '.85rem', alignItems: 'center' }}>
            {filters.map((f, i) => (
              <button key={f} className="tf-btn ghost sm" style={{
                background: i === 0 ? 'var(--color-primary)' : 'transparent',
                color: i === 0 ? '#fff' : 'var(--color-secondary)',
                borderColor: i === 0 ? 'var(--color-primary)' : 'var(--color-border)',
              }}>{f}</button>
            ))}
            <div style={{ flex: 1, minWidth: 220 }}>
              <input className="tf-input" placeholder="Buscar por nome, matrícula ou delegacia…" />
            </div>
          </div>

          {/* User cards */}
          <div className="tf-box" style={{ overflow: 'auto', flex: 1 }}>
            <div style={{
              display: 'grid', gridTemplateColumns: '40px 1fr 100px 140px 110px 90px',
              gap: '1rem', padding: '.6rem 1rem', background: 'var(--color-tablehead)',
              borderBottom: '1px solid var(--color-border)',
              fontSize: '.7rem', fontWeight: 700, color: 'var(--color-text-light)',
              textTransform: 'uppercase', letterSpacing: '.4px'
            }}>
              <div></div><div>Servidor</div><div>Matrícula</div><div>Unidade</div><div>Cargo</div><div>Último login</div>
            </div>
            {users.map((u, i) => {
              const isSel = u.sel;
              return (
                <div key={u.mat} style={{
                  display: 'grid', gridTemplateColumns: '40px 1fr 100px 140px 110px 90px',
                  gap: '1rem', padding: '.7rem 1rem',
                  borderBottom: i === users.length - 1 ? 'none' : '1px solid var(--color-border)',
                  alignItems: 'center', cursor: 'pointer',
                  background: isSel ? 'var(--color-info-bg)' : '#fff',
                  borderLeft: isSel ? '3px solid var(--color-primary)' : '3px solid transparent',
                  opacity: u.ativo ? 1 : .55,
                }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: isSel ? 'var(--color-primary)' : 'var(--color-tablehead)',
                    color: isSel ? '#fff' : 'var(--color-secondary)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: '.78rem',
                  }}>{initials(u.nome)}</div>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-body)', fontSize: '.9rem' }}>{u.nome}</div>
                    {u.temp && <span className="tf-xs" style={{ color: 'var(--color-warning-dark)', fontWeight: 700 }}>· senha temporária ativa</span>}
                    {!u.ativo && <span className="tf-xs" style={{ color: 'var(--color-text-light)' }}>· inativo</span>}
                  </div>
                  <div className="tf-mono tf-small" style={{ color: 'var(--color-text-light)' }}>{u.mat}</div>
                  <div className="tf-small">{u.unidade}</div>
                  <div>
                    <span style={{ background: 'var(--color-info-bg)', color: 'var(--color-info-dark)', padding: '.15rem .55rem', borderRadius: 999, fontSize: '.72rem', fontWeight: 700, border: '1px solid var(--color-info-border)' }}>{u.cargo}</span>
                  </div>
                  <div className="tf-xs tf-muted">{u.login}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: detail drawer for selected user */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.85rem', minHeight: 0 }}>
          <div className="tf-box" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ background: 'var(--color-primary)', color: '#fff', padding: '1rem' }}>
              <div style={{ display: 'flex', gap: '.75rem', alignItems: 'center' }}>
                <div style={{
                  width: 44, height: 44, borderRadius: '50%',
                  background: '#fff', color: 'var(--color-primary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 800, fontSize: '1rem'
                }}>{initials(selected.nome)}</div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{selected.nome}</div>
                  <div className="tf-xs" style={{ color: 'rgba(255,255,255,.7)' }}>Mat. {selected.mat} · {selected.unidade}</div>
                </div>
              </div>
            </div>
            <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '.85rem' }}>
              <div>
                <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.35rem' }}>Cargo</div>
                <select className="tf-input">
                  {cargos.map(c => <option key={c.nome} selected={c.nome === selected.cargo}>{c.nome}</option>)}
                </select>
              </div>

              <div>
                <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.35rem', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Permissões herdadas do cargo</span>
                  <span style={{ color: 'var(--color-primary)' }}>{selectedCargo.perms.length} ativas</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '.3rem' }}>
                  {selectedCargo.perms.map(p => (
                    <span key={p} className="tf-mono tf-xs" style={{
                      background: '#F0FFF4', color: '#22543D',
                      padding: '.15rem .5rem', borderRadius: 4,
                      border: '1px solid #C6F6D5', fontWeight: 700
                    }}>{p}</span>
                  ))}
                </div>
              </div>

              <div>
                <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.35rem' }}>Status da senha</div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '.5rem .75rem', background: 'var(--color-background)', borderRadius: 4, border: '1px solid var(--color-border)' }}>
                  <div className="tf-small">Definitiva · trocada há 14 dias</div>
                  <button className="tf-btn ghost sm" style={{ background: 'var(--color-warning-bg)', color: 'var(--color-warning-dark)', borderColor: 'var(--color-warning-border)' }}>
                    Gerar senha temporária
                  </button>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '.75rem', display: 'flex', gap: '.5rem' }}>
                <button className="tf-btn ghost sm" style={{ flex: 1, color: 'var(--color-danger-dark)' }}>Desativar</button>
                <button className="tf-btn sm" style={{ flex: 1 }}>Salvar alterações</button>
              </div>
            </div>
          </div>

          <div className="tf-box" style={{ padding: '.75rem .9rem' }}>
            <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.4rem' }}>Atividade recente</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '.4rem', fontSize: '.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Aprovou IP-2026/004</span><span className="tf-muted tf-xs">há 2h</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Editou IP-2026/003</span><span className="tf-muted tf-xs">há 4h</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Login</span><span className="tf-muted tf-xs">hoje 08:14</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   PROPOSED: Matriz de Permissões (nova aba)
   ───────────────────────────────────────────────────────── */
function ProposedAdminMatrix() {
  const cargos = ['Escrivão','Delegado','Investigador','Admin SSP'];
  const matrix = {
    'Processos': [
      { name: 'UPLOAD_AUDIO',       v: [1,0,1,0] },
      { name: 'EDITAR_TERMO',       v: [1,1,1,0] },
      { name: 'APROVAR_TERMO',      v: [0,1,0,0] },
      { name: 'GERAR_PDF',          v: [1,1,0,0] },
    ],
    'Administração': [
      { name: 'GERENCIAR_USUARIOS', v: [0,1,0,1] },
      { name: 'GERENCIAR_CARGOS',   v: [0,0,0,1] },
    ],
    'Análise': [
      { name: 'VER_METRICAS',       v: [1,1,0,1] },
      { name: 'VER_AUDITORIA',      v: [0,0,0,1] },
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
            <p className="tf-muted tf-small" style={{ marginTop: 2 }}>Visualize e edite quais cargos têm acesso a cada permissão.</p>
          </div>
          <button className="tf-btn">+ Novo cargo</button>
        </div>

        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--color-border)', marginBottom: '1.25rem' }}>
          {['Usuários','Cargos','Matriz de permissões'].map((l, i) => (
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
                <th style={{ background: 'var(--color-tablehead)', padding: '.7rem 1rem', textAlign: 'left', fontSize: '.72rem', textTransform: 'uppercase', letterSpacing: '.4px', color: 'var(--color-text-light)', fontWeight: 700 }}>Permissão</th>
                {cargos.map(c => (
                  <th key={c} style={{ background: 'var(--color-tablehead)', padding: '.7rem 1rem', textAlign: 'center', fontSize: '.72rem', textTransform: 'uppercase', letterSpacing: '.4px', color: 'var(--color-primary)', fontWeight: 700, minWidth: 120 }}>{c}</th>
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
                      <td style={{ padding: '.7rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '.78rem', fontWeight: 600 }}>{r.name}</td>
                      {r.v.map((on, i) => (
                        <td key={i} style={{ textAlign: 'center', padding: '.7rem 1rem' }}>
                          <span style={{
                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                            width: 22, height: 22, borderRadius: 4,
                            background: on ? 'var(--color-success)' : 'transparent',
                            border: on ? 'none' : '1px solid var(--color-border-strong)',
                            cursor: 'pointer'
                          }}>
                            {on ? (
                              <svg width="12" height="12" viewBox="0 0 12 12"><polyline points="2,6 5,9 10,3" fill="none" stroke="#fff" strokeWidth="2"/></svg>
                            ) : null}
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

/* ─────────────────────────────────────────────────────────
   CURRENT: Métricas (just KPI cards)
   ───────────────────────────────────────────────────────── */
function CurrentMetricas() {
  const cards = [
    { v: '342', l: 'Depoimentos Registrados' },
    { v: '298', l: 'Termos Gerados pela IA' },
    { v: '271', l: 'PDFs Exportados e Assinados' },
    { v: '94%', l: 'Taxa de Sucesso dos Jobs' },
    { v: '745h', l: 'Horas Economizadas (estimativa PIBITI)', note: 'Base: 2,5h por depoimento vs. redação manual' },
  ];
  const jobs = [
    { l: 'Concluído', v: 271 },
    { l: 'Processando', v: 32 },
    { l: 'Pendente', v: 21 },
    { l: 'Erro', v: 18 },
  ];
  return (
    <div className="tf-screen">
      <TFHeader active="metricas" />
      <div style={{ padding: '2rem' }}>
        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.6rem' }}>Dashboard de Métricas</h2>
          <p className="tf-muted tf-small" style={{ marginTop: 4 }}>Visão estratégica do sistema de transcrição assistida por IA — SSP-PI</p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
          {cards.map(c => (
            <div key={c.l} className="tf-box" style={{ padding: '1.5rem', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,.05)' }}>
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1.1, marginBottom: '.4rem' }}>{c.v}</div>
              <div style={{ fontSize: '.85rem', color: 'var(--color-secondary)', fontWeight: 600 }}>{c.l}</div>
              {c.note && <div className="tf-xs" style={{ color: 'var(--color-secondary)', fontStyle: 'italic', marginTop: '.3rem' }}>{c.note}</div>}
            </div>
          ))}
          <div className="tf-box" style={{ padding: '1.5rem' }}>
            <div style={{ fontSize: '.85rem', color: 'var(--color-secondary)', fontWeight: 600, marginBottom: '.8rem' }}>Jobs por Status</div>
            <table style={{ width: '100%' }}>
              <tbody>
                {jobs.map(j => (
                  <tr key={j.l}>
                    <td style={{ padding: '.3rem 0', fontSize: '.85rem', color: 'var(--color-secondary)', fontWeight: 600 }}>{j.l}</td>
                    <td style={{ padding: '.3rem 0', fontSize: '.95rem', fontWeight: 800, color: 'var(--color-primary)', textAlign: 'right' }}>{j.v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   PROPOSED: Dashboard (renomeia Métricas)
   - Period selector
   - KPIs com sparkline + delta vs período anterior
   - Volume ao longo do tempo (área simples em SVG)
   - Jobs por status (donut)
   - Tempo médio por etapa do pipeline (stacked bar)
   - Top escrivães + feed de atividade recente
   ───────────────────────────────────────────────────────── */
function ProposedDashboard() {
  const periods = ['7 dias','30 dias','Este ano','Custom'];
  const kpis = [
    { v: '342', l: 'Depoimentos',        d: '+12%', up: true },
    { v: '298', l: 'Termos pela IA',     d: '+9%',  up: true },
    { v: '271', l: 'PDFs assinados',     d: '+14%', up: true },
    { v: '94%', l: 'Taxa de sucesso',    d: '+1.2pp', up: true },
    { v: '745h', l: 'Horas economizadas', d: '+58h', up: true, note: 'Base PIBITI: 2,5h/depoimento' },
  ];
  // Sparkline points
  const spark = (seed) => Array.from({length: 14}).map((_, i) => 20 + Math.sin(i * 0.7 + seed) * 8 + i * 1.2);
  // Pipeline stage avg time (in minutes)
  const stages = [
    { l: 'Transcrição',  v: 4.2, c: 'var(--color-primary)' },
    { l: 'Extração NER', v: 0.9, c: 'var(--color-primary-mid)' },
    { l: 'Resumo LLM',   v: 2.7, c: 'var(--color-info)' },
    { l: 'Revisão humana', v: 6.4, c: 'var(--color-warning)' },
  ];
  const totalMin = stages.reduce((a, s) => a + s.v, 0);

  const Donut = () => {
    const data = [
      { l: 'Concluído', v: 271, c: 'var(--color-success)' },
      { l: 'Processando', v: 32, c: 'var(--color-info)' },
      { l: 'Pendente', v: 21, c: 'var(--color-warning)' },
      { l: 'Erro', v: 18, c: 'var(--color-accent)' },
    ];
    const total = data.reduce((a, d) => a + d.v, 0);
    let acc = 0;
    const R = 50, C = 2 * Math.PI * R;
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <svg viewBox="0 0 130 130" width={130} height={130} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx="65" cy="65" r={R} fill="none" stroke="var(--color-border)" strokeWidth="18" />
          {data.map((d, i) => {
            const len = (d.v / total) * C;
            const off = (acc / total) * C;
            acc += d.v;
            return <circle key={i} cx="65" cy="65" r={R} fill="none" stroke={d.c} strokeWidth="18" strokeDasharray={`${len} ${C - len}`} strokeDashoffset={-off} />;
          })}
        </svg>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.35rem', flex: 1 }}>
          {data.map(d => (
            <div key={d.l} style={{ display: 'flex', alignItems: 'center', gap: '.5rem', fontSize: '.82rem' }}>
              <span style={{ width: 9, height: 9, background: d.c, borderRadius: 2 }} />
              <span style={{ flex: 1, color: 'var(--color-secondary)' }}>{d.l}</span>
              <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{d.v}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const AreaChart = () => {
    const data = Array.from({length: 30}).map((_, i) => 12 + Math.sin(i / 3) * 4 + Math.cos(i / 7) * 3 + (i / 4));
    const max = Math.max(...data);
    const W = 560, H = 160, P = 8;
    const pts = data.map((v, i) => [P + (i / (data.length - 1)) * (W - P*2), H - P - (v / max) * (H - P*2)]);
    const d = 'M ' + pts.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' L ');
    const da = d + ` L ${(W - P).toFixed(1)},${H - P} L ${P.toFixed(1)},${H - P} Z`;
    return (
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none">
        <defs>
          <linearGradient id="dashGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(43,108,176,.35)" />
            <stop offset="100%" stopColor="rgba(43,108,176,0)" />
          </linearGradient>
        </defs>
        <path d={da} fill="url(#dashGrad)" />
        <path d={d} fill="none" stroke="var(--color-primary)" strokeWidth="2" />
      </svg>
    );
  };

  const Sparkline = ({ data }) => {
    const max = Math.max(...data), min = Math.min(...data);
    const W = 80, H = 24;
    const pts = data.map((v, i) => [(i / (data.length - 1)) * W, H - ((v - min) / (max - min)) * H]);
    return (
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} preserveAspectRatio="none">
        <polyline fill="none" stroke="var(--color-primary-mid)" strokeWidth="1.5"
          points={pts.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ')} />
      </svg>
    );
  };

  const topEscrivaes = [
    { n: 'Maria Souza',       c: 47, p: 1.0 },
    { n: 'João Lima',         c: 38, p: 0.81 },
    { n: 'Carlos Dias',       c: 29, p: 0.62 },
    { n: 'Renata Albuquerque', c: 22, p: 0.47 },
    { n: 'Paulo Cesar Mota',  c: 15, p: 0.32 },
  ];

  return (
    <div className="tf-screen">
      <TFHeader active="metricas" />
      <div style={{ padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.25rem' }}>
          <div>
            <div className="tf-xs" style={{ color: 'var(--color-text-subtle)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 4 }}>Indicadores</div>
            <h2 style={{ fontSize: '1.55rem' }}>Dashboard</h2>
            <p className="tf-muted tf-small" style={{ marginTop: 2 }}>Visão estratégica do sistema de transcrição assistida por IA — SSP-PI</p>
          </div>
          <div style={{ display: 'flex', gap: '.4rem', alignItems: 'center' }}>
            <div className="tf-box" style={{ display: 'flex', gap: 0, padding: 2 }}>
              {periods.map((p, i) => (
                <button key={p} className="tf-btn ghost sm" style={{
                  border: 'none', borderRadius: 3,
                  background: i === 1 ? 'var(--color-primary)' : 'transparent',
                  color: i === 1 ? '#fff' : 'var(--color-secondary)',
                  fontWeight: 600,
                }}>{p}</button>
              ))}
            </div>
            <button className="tf-btn ghost">Exportar</button>
          </div>
        </div>

        {/* KPIs */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '.75rem', marginBottom: '1.25rem' }}>
          {kpis.map((k, i) => (
            <div key={k.l} className="tf-box" style={{ padding: '.9rem 1rem' }}>
              <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.4px' }}>{k.l}</div>
              <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 4 }}>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1.1 }}>{k.v}</div>
                <Sparkline data={spark(i)} />
              </div>
              <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: '.35rem' }}>
                <span className="tf-xs" style={{ color: k.up ? 'var(--color-success-dark)' : 'var(--color-danger-dark)', fontWeight: 700 }}>
                  {k.up ? '▲' : '▼'} {k.d}
                </span>
                <span className="tf-xs tf-muted">vs. período anterior</span>
              </div>
              {k.note && <div className="tf-xs tf-muted" style={{ marginTop: 4, fontStyle: 'italic' }}>{k.note}</div>}
            </div>
          ))}
        </div>

        {/* Charts row */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>Volume de depoimentos · últimos 30 dias</div>
              <div className="tf-xs tf-muted">média 11.4/dia</div>
            </div>
            <div style={{ padding: '.5rem' }}>
              <AreaChart />
            </div>
          </div>
          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>Jobs por status</div>
            <div style={{ padding: '1rem' }}><Donut /></div>
          </div>
        </div>

        {/* Pipeline avg time + top escrivaes */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>
              Tempo médio por etapa <span className="tf-xs tf-muted" style={{ fontWeight: 500 }}>(min)</span>
            </div>
            <div style={{ padding: '1rem' }}>
              <div style={{ display: 'flex', height: 24, borderRadius: 4, overflow: 'hidden', marginBottom: '.75rem' }}>
                {stages.map(s => (
                  <div key={s.l} style={{ width: `${(s.v / totalMin) * 100}%`, background: s.c }} title={`${s.l}: ${s.v}min`} />
                ))}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '.4rem' }}>
                {stages.map(s => (
                  <div key={s.l} style={{ display: 'flex', alignItems: 'center', gap: '.55rem', fontSize: '.82rem' }}>
                    <span style={{ width: 9, height: 9, background: s.c, borderRadius: 2 }} />
                    <span style={{ flex: 1, color: 'var(--color-secondary)' }}>{s.l}</span>
                    <span className="tf-mono" style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{s.v} min</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: '.8rem', paddingTop: '.5rem', borderTop: '1px dashed var(--color-border)', display: 'flex', justifyContent: 'space-between', fontSize: '.82rem' }}>
                <span className="tf-muted">Total médio</span>
                <span className="tf-mono" style={{ fontWeight: 700 }}>{totalMin.toFixed(1)} min</span>
              </div>
            </div>
          </div>
          <div className="tf-box">
            <div style={{ padding: '.85rem 1rem', borderBottom: '1px solid var(--color-border)', fontSize: '.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>
              Produção por escrivão · 30 dias
            </div>
            <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '.55rem' }}>
              {topEscrivaes.map(e => (
                <div key={e.n} style={{ display: 'grid', gridTemplateColumns: '140px 1fr 40px', gap: '.65rem', alignItems: 'center', fontSize: '.82rem' }}>
                  <div style={{ color: 'var(--color-text-body)' }}>{e.n}</div>
                  <div style={{ height: 7, background: 'var(--color-bg-deep)', borderRadius: 999, overflow: 'hidden' }}>
                    <div style={{ width: `${e.p * 100}%`, height: '100%', background: 'var(--color-primary)' }} />
                  </div>
                  <div className="tf-mono" style={{ fontWeight: 700, color: 'var(--color-primary)', textAlign: 'right' }}>{e.c}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   CURRENT: Cadastro de processo (it's a modal in the current app)
   ───────────────────────────────────────────────────────── */
function CurrentProcessForm() {
  return (
    <div className="tf-screen" style={{ background: 'rgba(26,54,93,.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      <div style={{ width: '90%', maxWidth: 540, background: 'var(--color-background)', borderRadius: 4, boxShadow: '0 10px 40px rgba(0,0,0,.12)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem', borderBottom: '1px solid var(--color-border)' }}>
          <h3 style={{ fontSize: '1.25rem' }}>Novo Processo</h3>
          <span style={{ fontSize: '1.5rem', color: 'var(--color-text-light)' }}>×</span>
        </div>
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <div className="tf-label" style={{ marginBottom: '.4rem', color: 'var(--color-primary)' }}>Nº Procedimento</div>
              <input className="tf-input" placeholder="Ex: IP-2026/002" />
            </div>
            <div>
              <div className="tf-label" style={{ marginBottom: '.4rem', color: 'var(--color-primary)' }}>Data de Instauração</div>
              <input className="tf-input" type="date" />
            </div>
          </div>
          <div>
            <div className="tf-label" style={{ marginBottom: '.4rem', color: 'var(--color-primary)' }}>Nome do Depoente</div>
            <input className="tf-input" placeholder="Exemplo: João Silva" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <div className="tf-label" style={{ marginBottom: '.4rem', color: 'var(--color-primary)' }}>CPF</div>
              <input className="tf-input" placeholder="000.000.000-00" />
            </div>
            <div>
              <div className="tf-label" style={{ marginBottom: '.4rem', color: 'var(--color-primary)' }}>Tipo de Depoente</div>
              <select className="tf-input"><option>Testemunha</option></select>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', paddingTop: '1rem', borderTop: '1px solid var(--color-border)' }}>
            <button className="tf-btn ghost">Cancelar</button>
            <button className="tf-btn">Criar Processo</button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   PROPOSED: Cadastro/Edição de Processo (full page)
   - Layout em 2 colunas com navegação por seções
   - Campos opcionais expandidos (RG, endereço, telefone)
   - Vinculação automática a delegacia/escrivão pelo usuário logado
   - Modo de edição inclui timeline de auditoria
   ───────────────────────────────────────────────────────── */
function ProposedProcessForm({ mode = 'edit' }) {
  const sections = [
    { id: 'inquerito', l: 'Identificação do inquérito', done: true },
    { id: 'depoente',  l: 'Dados do depoente',          done: true, active: true },
    { id: 'vinculo',   l: 'Vinculação institucional',   done: false },
    { id: 'observ',    l: 'Observações e anexos',       done: false },
  ];

  const isEdit = mode === 'edit';

  return (
    <div className="tf-screen">
      <TFHeader active="processos" />

      {/* Sub-header */}
      <div style={{ background: '#fff', borderBottom: '1px solid var(--color-border)', padding: '.85rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '.85rem', alignItems: 'center' }}>
            <button className="tf-btn ghost sm">←</button>
            <div>
              <div className="tf-xs tf-muted">
                Processos {isEdit && <> · <span className="tf-mono">IP-2026/004</span></>}
              </div>
              <h2 style={{ fontSize: '1.2rem', marginTop: 2 }}>
                {isEdit ? 'Editar processo' : 'Novo processo'}
              </h2>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '.5rem' }}>
            <button className="tf-btn ghost sm">Descartar</button>
            <button className="tf-btn outline sm">Salvar rascunho</button>
            <button className="tf-btn sm">{isEdit ? 'Salvar alterações' : 'Criar processo'}</button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr 320px', gap: '1.5rem', padding: '1.5rem 2rem', height: 'calc(100% - 56px - 65px)', overflow: 'hidden' }}>

        {/* Section nav */}
        <div>
          <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.6rem' }}>
            Seções do formulário
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '.25rem' }}>
            {sections.map((s, i) => (
              <button key={s.id} className="tf-btn ghost" style={{
                textAlign: 'left', justifyContent: 'flex-start', padding: '.55rem .7rem',
                border: 'none', background: s.active ? 'var(--color-info-bg)' : 'transparent',
                color: s.active ? 'var(--color-primary)' : 'var(--color-secondary)',
                fontWeight: s.active ? 700 : 500,
                borderLeft: '3px solid ' + (s.active ? 'var(--color-primary)' : 'transparent'),
                borderRadius: 0, gap: '.5rem'
              }}>
                <span style={{
                  width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
                  background: s.done ? 'var(--color-success)' : '#fff',
                  border: '1.5px solid ' + (s.done ? 'var(--color-success)' : 'var(--color-border-strong)'),
                  color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '.7rem', fontWeight: 800,
                }}>
                  {s.done ? <svg width="9" height="9" viewBox="0 0 9 9"><polyline points="1,4.5 3.5,7 8,2" fill="none" stroke="#fff" strokeWidth="1.6"/></svg> : i + 1}
                </span>
                <span style={{ flex: 1, fontSize: '.85rem' }}>{s.l}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Main form */}
        <div style={{ overflow: 'auto', paddingRight: '.5rem' }}>
          {/* Section: Identificação do inquérito */}
          <div className="tf-box" style={{ padding: '1.25rem', marginBottom: '1rem' }}>
            <div style={{ marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.05rem', marginBottom: '.15rem' }}>Identificação do inquérito</h3>
              <p className="tf-muted tf-small">Dados que identificam o procedimento policial.</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '.85rem' }}>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Nº Procedimento *</div>
                <input className="tf-input tf-mono" defaultValue="IP-2026/004" />
              </div>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Data de instauração *</div>
                <input className="tf-input" type="date" defaultValue="2026-03-11" />
              </div>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Natureza do feito</div>
                <select className="tf-input"><option>Furto qualificado</option><option>Roubo</option><option>Lesão corporal</option></select>
              </div>
            </div>
          </div>

          {/* Section: Dados do depoente (active) */}
          <div className="tf-box" style={{ padding: '1.25rem', marginBottom: '1rem', borderLeft: '3px solid var(--color-primary)' }}>
            <div style={{ marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.05rem', marginBottom: '.15rem' }}>Dados do depoente</h3>
              <p className="tf-muted tf-small">Pessoa que prestará o depoimento.</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '.85rem', marginBottom: '.85rem' }}>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Nome completo *</div>
                <input className="tf-input" defaultValue="Patricia Helena Coelho" />
              </div>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Tipo de depoente *</div>
                <select className="tf-input"><option>Testemunha</option><option>Vítima</option><option>Suspeito</option><option>Indiciado</option></select>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '.85rem', marginBottom: '.85rem' }}>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>CPF *</div>
                <input className="tf-input tf-mono" defaultValue="123.456.789-00" />
              </div>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>RG / órgão emissor</div>
                <input className="tf-input" placeholder="0000000 SSP-PI" />
              </div>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Data de nascimento</div>
                <input className="tf-input" type="date" />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.85rem', marginBottom: '.85rem' }}>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Telefone de contato</div>
                <input className="tf-input" placeholder="(86) 9 9999-9999" />
              </div>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Profissão</div>
                <input className="tf-input" placeholder="Ex: comerciante" />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '.85rem' }}>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Endereço</div>
                <input className="tf-input" placeholder="Rua, número, bairro" />
              </div>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>Município</div>
                <input className="tf-input" defaultValue="Teresina" />
              </div>
              <div>
                <div className="tf-label" style={{ marginBottom: '.3rem' }}>UF</div>
                <input className="tf-input" defaultValue="PI" maxLength="2" />
              </div>
            </div>
          </div>

          {/* Section: Vinculação (collapsed visual) */}
          <div className="tf-box" style={{ padding: '1rem 1.25rem', marginBottom: '1rem', opacity: .85 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '.95rem' }}>Vinculação institucional</h3>
                <p className="tf-muted tf-xs" style={{ marginTop: 2 }}>Delegacia, autoridade policial e escrivão responsável (preenchido automaticamente).</p>
              </div>
              <span className="tf-muted">▾</span>
            </div>
          </div>

          <div className="tf-box" style={{ padding: '1rem 1.25rem', opacity: .85 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '.95rem' }}>Observações e anexos</h3>
                <p className="tf-muted tf-xs" style={{ marginTop: 2 }}>Notas internas e arquivos adicionais ao processo.</p>
              </div>
              <span className="tf-muted">▾</span>
            </div>
          </div>
        </div>

        {/* Right sidebar: context / audit log */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.85rem', overflow: 'auto' }}>
          {/* Context card */}
          <div className="tf-box" style={{ padding: '.85rem 1rem' }}>
            <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.5rem' }}>
              Contexto
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '.4rem .75rem', fontSize: '.82rem' }}>
              <span className="tf-muted">Delegacia</span><span>1ª DP Teresina</span>
              <span className="tf-muted">Autoridade</span><span>Dr. João Lima</span>
              <span className="tf-muted">Escrivão</span><span>Maria Souza · você</span>
              {isEdit && <><span className="tf-muted">Status</span><span><StatusPill status="Concluído" /></span></>}
            </div>
          </div>

          {/* Audit timeline - only in edit mode */}
          {isEdit && (
            <div className="tf-box" style={{ padding: '.85rem 1rem' }}>
              <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.7rem' }}>
                Histórico de alterações
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '.7rem' }}>
                {[
                  { who: 'Maria Souza', what: 'Editou dados do depoente', when: 'há 4 min' },
                  { who: 'Maria Souza', what: 'Aprovou e assinou PDF', when: 'há 2h' },
                  { who: 'Sistema',     what: 'Pipeline concluído', when: 'há 3h' },
                  { who: 'João Lima',   what: 'Fez upload do áudio', when: 'há 3h' },
                  { who: 'Maria Souza', what: 'Criou processo', when: 'há 4h' },
                ].map((e, i, arr) => (
                  <div key={i} style={{ display: 'flex', gap: '.6rem', position: 'relative' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                      <div style={{
                        width: 9, height: 9, borderRadius: '50%',
                        background: i === 0 ? 'var(--color-primary)' : 'var(--color-border-strong)',
                        marginTop: 4,
                      }} />
                      {i < arr.length - 1 && <div style={{ width: 1, flex: 1, background: 'var(--color-border)', minHeight: 18 }} />}
                    </div>
                    <div style={{ paddingBottom: '.2rem' }}>
                      <div style={{ fontSize: '.82rem', color: 'var(--color-text-body)' }}>{e.what}</div>
                      <div className="tf-xs tf-muted">{e.who} · {e.when}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Help card */}
          <div className="tf-box" style={{ padding: '.85rem 1rem', background: 'var(--color-info-bg)', borderColor: 'var(--color-info-border)' }}>
            <div className="tf-xs" style={{ color: 'var(--color-info-dark)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '.4rem' }}>Boas práticas</div>
            <p className="tf-small" style={{ color: 'var(--color-info-dark)', lineHeight: 1.5 }}>
              O Nº do procedimento segue o padrão <span className="tf-mono">IP-AAAA/NNN</span>. Após criar o processo, faça upload do áudio na tela de Auditoria para iniciar a transcrição automática.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  CurrentAdmin, ProposedAdmin, ProposedAdminMatrix,
  CurrentMetricas, ProposedDashboard,
  CurrentProcessForm, ProposedProcessForm
});
