// PROPOSED redesigns. Same brand (navy SSP-PI), refined hierarchy & workflow signaling.

/* ───────────────────────────────────────────────────────────────
   PROPOSED: Process List
   - Hero KPIs (fila / em processamento / prontos para revisão)
   - Filter chips (preset views) instead of free fields stacked
   - Card-list rows with depoente as the anchor, pipeline mini-strip on in-progress items
   - Status uses a dot + short label so it stops shouting
   ─────────────────────────────────────────────────────────────── */
function ProposedProcessList() {
  const rows = [
    { num: 'IP-2026/001', nome: 'José Maria da Silva Junior', tipo: 'Testemunha', data: '12/03 14:22', escrivao: 'Maria Souza', stage: 4, dur: '07:42' },
    { num: 'IP-2026/002', nome: 'Ana Carolina Mendes',       tipo: 'Vítima',     data: '12/03 13:05', escrivao: 'João Lima',   stage: 1, dur: '12:18' },
    { num: 'IP-2026/003', nome: 'Rafael Augusto Pereira',    tipo: 'Suspeito',   data: '11/03 16:48', escrivao: 'Maria Souza', stage: 3, dur: '21:04' },
    { num: 'IP-2026/004', nome: 'Patricia Helena Coelho',    tipo: 'Testemunha', data: '11/03 11:30', escrivao: 'Carlos Dias', stage: 0, dur: '05:11' },
    { num: 'IP-2026/005', nome: 'Marcos Vinicius Tavares',   tipo: 'Suspeito',   data: '10/03 17:11', escrivao: 'João Lima',   stage: 2, dur: '09:55', error: true },
    { num: 'IP-2026/007', nome: 'Diego Henrique Nunes',      tipo: 'Testemunha', data: '09/03 15:20', escrivao: 'Carlos Dias', stage: 4, dur: '14:33' },
  ];
  const stageLabel = (i, err) => err ? 'Erro em ' + STAGES[i].label.toLowerCase()
                                     : i === 4 ? 'Pronto para revisão'
                                     : i === 0 ? 'Aguardando upload'
                                     : STAGES[i].label;
  const kpis = [
    { label: 'Em processamento', value: 3, color: 'var(--color-info-dark)', bg: 'var(--color-info-bg)' },
    { label: 'Aguardando revisão', value: 2, color: 'var(--color-success-dark)', bg: 'var(--color-success-bg)' },
    { label: 'Com erro', value: 1, color: 'var(--color-danger-dark)', bg: 'var(--color-danger-bg)' },
    { label: 'Concluídos no mês', value: 47, color: 'var(--color-secondary)', bg: '#fff' },
  ];
  const filters = ['Meus processos', 'Aguardando revisão', 'Em processamento', 'Com erro', 'Concluídos'];

  return (
    <div className="tf-screen">
      <TFHeader active="processos" />
      <div style={{ padding: '1.75rem 2rem' }}>
        <div style={{ maxWidth: 1240, margin: '0 auto' }}>
          {/* Header row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.25rem' }}>
            <div>
              <div className="tf-xs" style={{ color: 'var(--color-text-subtle)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 4 }}>
                Inquéritos · Março/2026
              </div>
              <h2 style={{ fontSize: '1.65rem', marginBottom: '.25rem' }}>Processos e Depoimentos</h2>
            </div>
            <div style={{ display: 'flex', gap: '.5rem' }}>
              <button className="tf-btn ghost">Exportar</button>
              <button className="tf-btn lg">+ Novo Processo</button>
            </div>
          </div>

          {/* KPI strip */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '.75rem', marginBottom: '1.25rem' }}>
            {kpis.map(k => (
              <div key={k.label} className="tf-box" style={{ padding: '.85rem 1rem', background: k.bg, borderColor: k.bg === '#fff' ? 'var(--color-border)' : 'transparent' }}>
                <div className="tf-xs" style={{ color: k.color, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.4px' }}>{k.label}</div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: k.color, marginTop: 2 }}>{k.value}</div>
              </div>
            ))}
          </div>

          {/* Filter chips + search */}
          <div style={{ display: 'flex', gap: '.5rem', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap' }}>
            {filters.map((f, i) => (
              <button key={f} className="tf-btn ghost sm" style={{
                borderColor: i === 1 ? 'var(--color-primary)' : 'var(--color-border)',
                background: i === 1 ? 'var(--color-primary)' : 'transparent',
                color: i === 1 ? '#fff' : 'var(--color-secondary)',
                fontWeight: 600,
              }}>{f}{i === 1 ? ' · 2' : ''}</button>
            ))}
            <div style={{ flex: 1, minWidth: 220 }}>
              <input className="tf-input" placeholder="Buscar por nome, CPF ou Nº inquérito…" />
            </div>
          </div>

          {/* List */}
          <div className="tf-box" style={{ overflow: 'hidden' }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '180px 1fr 130px 110px 150px 36px',
              gap: '1rem',
              padding: '.6rem 1.1rem',
              background: 'var(--color-tablehead)',
              borderBottom: '1px solid var(--color-border)',
              fontSize: '.72rem', fontWeight: 700,
              color: 'var(--color-text-light)',
              textTransform: 'uppercase', letterSpacing: '.4px',
            }}>
              <div>Inquérito · Tipo</div><div>Depoente</div><div>Áudio</div><div>Registrado</div><div>Escrivão</div><div></div>
            </div>
            {rows.map((r, idx) => {
              const inProgress = r.stage > 0 && r.stage < 4;
              const done = r.stage === 4;
              const stageColor = r.error ? 'var(--color-accent)' : done ? 'var(--color-success)' : inProgress ? 'var(--color-primary)' : 'var(--color-text-subtle)';
              return (
                <div key={r.num} style={{
                  display: 'grid',
                  gridTemplateColumns: '180px 1fr 130px 110px 150px 36px',
                  gap: '1rem',
                  padding: '.9rem 1.1rem',
                  borderBottom: idx === rows.length - 1 ? 'none' : '1px solid var(--color-border)',
                  alignItems: 'center',
                  cursor: 'pointer',
                  background: '#fff',
                }}>
                  <div>
                    <div style={{ fontWeight: 700, color: 'var(--color-primary)', fontFamily: 'var(--font-mono)', fontSize: '.82rem' }}>{r.num}</div>
                    <div className="tf-xs tf-muted" style={{ marginTop: 2 }}>{r.tipo}</div>
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-body)', fontSize: '.92rem' }}>{r.nome}</div>
                    <div className="tf-xs" style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: '.4rem' }}>
                      <span style={{ width: 7, height: 7, borderRadius: '50%', background: stageColor, flexShrink: 0 }} />
                      <span style={{ color: stageColor, fontWeight: 600 }}>{stageLabel(r.stage, r.error)}</span>
                      {inProgress && !r.error && (
                        <span className="tf-xs tf-muted">· etapa {r.stage}/4</span>
                      )}
                    </div>
                  </div>
                  <div className="tf-mono tf-xs" style={{ color: 'var(--color-text-light)' }}>{r.dur}</div>
                  <div className="tf-xs tf-muted">{r.data}</div>
                  <div className="tf-small">{r.escrivao}</div>
                  <div style={{ color: 'var(--color-text-subtle)', fontSize: '1.1rem', textAlign: 'right' }}>›</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ───────────────────────────────────────────────────────────────
   PROPOSED: Auditoria workspace
   - Pipeline stepper as the page hero (replaces flat status badge)
   - Transcript NOT locked - streams as it arrives, with skeleton lines
   - Selected segment highlighted on the left AND scrolls editor cursor
   - Sidebar with extracted entities (the AI's "structured output")
   - Audio player promoted to persistent bottom bar
   ─────────────────────────────────────────────────────────────── */
function ProposedAuditoria() {
  const segments = [
    { t: '00:00', sp: 'Escrivão', text: 'Por favor, declare seu nome completo e profissão para o registro.' },
    { t: '00:08', sp: 'Depoente', text: 'Meu nome é José Maria da Silva Junior, sou comerciante e moro em Teresina há vinte e dois anos.', entities: [{ start: 11, end: 41, type: 'pessoa' }, { start: 76, end: 84, type: 'local' }] },
    { t: '00:21', sp: 'Escrivão', text: 'Onde o senhor estava na noite do dia 7 de março?' },
    { t: '00:28', sp: 'Depoente', text: 'Eu estava na minha loja na Avenida Frei Serafim, fechei por volta das vinte e duas horas.', entities: [{ start: 23, end: 47, type: 'local' }, { start: 64, end: 87, type: 'data' }], active: true },
    { t: '00:41', sp: 'Escrivão', text: 'O senhor viu alguma movimentação estranha na região naquela noite?' },
    { t: '00:48', sp: 'Depoente', text: 'Vi sim, dois rapazes parados perto do banco do outro lado da rua.' },
  ];

  const entities = [
    { label: 'José Maria da Silva Junior', type: 'Pessoa', conf: 0.98 },
    { label: 'Av. Frei Serafim',          type: 'Local',  conf: 0.94 },
    { label: '07/03/2026',                 type: 'Data',   conf: 0.91 },
    { label: '22h00',                       type: 'Hora',   conf: 0.88 },
    { label: 'Loja do depoente',           type: 'Local',  conf: 0.71, low: true },
  ];

  const renderEntities = (text, ents) => {
    if (!ents) return text;
    const sorted = [...ents].sort((a, b) => a.start - b.start);
    const out = []; let cursor = 0;
    sorted.forEach((e, i) => {
      if (cursor < e.start) out.push(<span key={'t' + i}>{text.slice(cursor, e.start)}</span>);
      out.push(<mark key={'e' + i} className={'ner ner-' + e.type}>{text.slice(e.start, e.end)}</mark>);
      cursor = e.end;
    });
    if (cursor < text.length) out.push(<span key="tend">{text.slice(cursor)}</span>);
    return out;
  };

  return (
    <div className="tf-screen" style={{ display: 'flex', flexDirection: 'column' }}>
      <TFHeader active="processos" />

      <style>{`
        .ner { padding: 0 3px; border-radius: 3px; font-style: normal; }
        .ner-pessoa { background: var(--color-ner-pessoa); }
        .ner-local  { background: var(--color-ner-local); }
        .ner-data   { background: var(--color-ner-data); }
        .ner-org    { background: var(--color-ner-org); }
        .seg-row {
          display: grid; grid-template-columns: 56px 80px 1fr; gap: .65rem;
          padding: .55rem .7rem; border-radius: 6px;
          align-items: start;
        }
        .seg-row + .seg-row { margin-top: 2px; }
        .seg-row:hover { background: var(--color-surface-hover); }
        .seg-row.active { background: #FFF8E0; box-shadow: inset 3px 0 0 #D97706; }
        .seg-time {
          font-family: var(--font-mono); font-size: .72rem;
          background: var(--color-primary); color: #fff;
          border: none; border-radius: 3px; padding: 2px 6px;
          cursor: pointer; align-self: start;
        }
        .seg-speaker { font-size: .72rem; font-weight: 700; color: var(--color-secondary); padding-top: 2px; }
        .seg-text { font-size: .88rem; color: var(--color-text-body); line-height: 1.55; }
      `}</style>

      {/* Sub-header strip: breadcrumb + pipeline */}
      <div style={{ background: '#fff', borderBottom: '1px solid var(--color-border)', padding: '.85rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '.85rem' }}>
            <button className="tf-btn ghost sm">←</button>
            <div>
              <div className="tf-xs tf-muted">
                Processos · <span className="tf-mono">IP-2026/004</span> · Testemunha
              </div>
              <h2 style={{ fontSize: '1.15rem', marginTop: 2 }}>Patricia Helena Coelho</h2>
            </div>
          </div>
          <div style={{ flex: 1, maxWidth: 540 }}>
            <PipelineStepper activeIndex={2} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
            <div className="tf-xs tf-muted" style={{ textAlign: 'right' }}>
              <div>Iniciado <strong style={{ color: 'var(--color-text-body)' }}>há 4 min</strong></div>
              <div>Tempo estimado <strong style={{ color: 'var(--color-text-body)' }}>~2 min</strong></div>
            </div>
            <button className="tf-btn ghost sm">Trocar áudio</button>
          </div>
        </div>
      </div>

      {/* Working area */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr 280px', gap: '1rem', padding: '1rem 2rem 0', minHeight: 0 }}>

        {/* Left: transcript - streams as it arrives, NOT locked */}
        <div className="tf-box" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="tf-box-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Transcrição bruta · ASR ao vivo</span>
            <span className="tf-xs" style={{ color: 'var(--color-info-dark)', fontWeight: 600 }}>
              <span style={{ display: 'inline-block', width: 6, height: 6, background: 'var(--color-info)', borderRadius: '50%', marginRight: 6, animation: 'tfPulse 1.4s infinite' }} />
              transcrevendo…
            </span>
          </div>
          <div style={{ overflow: 'auto', padding: '.6rem', flex: 1 }}>
            {segments.map((s, i) => (
              <div key={i} className={'seg-row ' + (s.active ? 'active' : '')}>
                <button className="seg-time">{s.t}</button>
                <span className="seg-speaker">{s.sp}</span>
                <span className="seg-text">{renderEntities(s.text, s.entities)}</span>
              </div>
            ))}
            {/* Skeleton lines for in-progress chunks */}
            {[0, 1, 2].map(i => (
              <div key={'sk' + i} className="seg-row" style={{ opacity: 1 - i * 0.3 }}>
                <div style={{ background: '#eee', height: 16, borderRadius: 3 }} />
                <div style={{ background: '#eee', height: 16, borderRadius: 3 }} />
                <div style={{ background: '#eee', height: 16, borderRadius: 3, width: `${90 - i * 18}%` }} />
              </div>
            ))}
          </div>
        </div>

        {/* Middle: editor */}
        <div className="tf-box" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="tf-box-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Termo formal · editor</span>
            <span className="tf-xs tf-muted" style={{ fontStyle: 'italic' }}>salvo há 2s · v.3</span>
          </div>
          <div style={{ padding: '.85rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '.65rem', overflow: 'auto' }}>
            <div style={{
              background: 'var(--color-info-bg)', border: '1px solid var(--color-info-border)',
              borderRadius: 4, padding: '.55rem .75rem', fontSize: '.78rem', color: 'var(--color-info-dark)',
              display: 'flex', alignItems: 'center', gap: '.5rem'
            }}>
              <span style={{ fontWeight: 700 }}>ⓘ</span>
              <span>O resumo formal é gerado quando a transcrição é concluída. Você pode revisar entidades extraídas enquanto isso →</span>
            </div>
            <div style={{ textAlign: 'center', padding: '.4rem 0', fontWeight: 800, color: 'var(--color-primary)', fontSize: '.95rem', letterSpacing: '.5px', borderBottom: '1px solid var(--color-border)' }}>
              TERMO DE DEPOIMENTO DE TESTEMUNHA
            </div>
            <div style={{ fontSize: '.86rem', color: 'var(--color-text-body)', lineHeight: 1.65 }}>
              <p style={{ marginBottom: '.6rem' }}>
                Aos sete dias do mês de março do ano de dois mil e vinte e seis, na sede da Delegacia Regional de Teresina, perante a autoridade policial, compareceu o senhor <mark className="ner ner-pessoa">José Maria da Silva Junior</mark>, brasileiro, comerciante, residente em <mark className="ner ner-local">Teresina</mark>.
              </p>
              <p style={{ marginBottom: '.6rem' }}>
                Interrogado sobre os fatos, declarou que, na noite do dia <mark className="ner ner-data">07 de março</mark>, encontrava-se em sua loja, localizada na <mark className="ner ner-local">Avenida Frei Serafim</mark>, tendo encerrado o expediente por volta das vinte e duas horas
                <span style={{ background: 'rgba(43,108,176,.15)', borderLeft: '2px solid var(--color-primary)', padding: '0 4px', marginLeft: 2 }}>|</span>
              </p>
              <p style={{ color: 'var(--color-text-subtle)', fontStyle: 'italic' }}>… resumo continua sendo gerado pela IA</p>
            </div>
          </div>
          {/* Action footer */}
          <div style={{ borderTop: '1px solid var(--color-border)', padding: '.65rem .85rem', display: 'flex', alignItems: 'center', gap: '.75rem', background: '#FAFBFC' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '.5rem', fontSize: '.78rem', color: 'var(--color-text-light)', flex: 1 }}>
              <input type="checkbox" />
              <span>Declaro que revisei e assumo responsabilidade pela autoria</span>
            </label>
            <button className="tf-btn outline sm">Visualizar PDF</button>
            <button className="tf-btn sm" disabled>Aprovar e assinar</button>
          </div>
        </div>

        {/* Right: extracted entities sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.85rem', minHeight: 0 }}>
          <div className="tf-box" style={{ overflow: 'hidden' }}>
            <div className="tf-box-header">Dados extraídos pela IA</div>
            <div style={{ padding: '.65rem .8rem', display: 'flex', flexDirection: 'column', gap: '.55rem' }}>
              {entities.map((e, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '.5rem',
                  padding: '.4rem .55rem',
                  border: '1px solid ' + (e.low ? 'var(--color-warning-border)' : 'var(--color-border)'),
                  background: e.low ? 'var(--color-warning-bg)' : '#fff',
                  borderRadius: 4
                }}>
                  <div style={{ minWidth: 0 }}>
                    <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.3px' }}>{e.type}</div>
                    <div className="tf-small" style={{ fontWeight: 600, color: 'var(--color-text-body)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{e.label}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div className="tf-xs" style={{
                      fontFamily: 'var(--font-mono)',
                      color: e.low ? 'var(--color-warning-dark)' : 'var(--color-success-dark)',
                      fontWeight: 700,
                    }}>{Math.round(e.conf * 100)}%</div>
                    <div className="tf-xs tf-muted">{e.low ? 'revisar' : 'auto'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="tf-box" style={{ padding: '.75rem .85rem' }}>
            <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: '.4rem' }}>Pipeline · detalhes técnicos</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '.78rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span className="tf-muted">ASR</span><span className="tf-mono">whisper-medium</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span className="tf-muted">LLM</span><span className="tf-mono">llama3:8b</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span className="tf-muted">Job ID</span><span className="tf-mono">c4f9…21ab</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* Persistent audio player at bottom */}
      <div style={{
        marginTop: '1rem', background: '#fff',
        borderTop: '1px solid var(--color-border)',
        padding: '.65rem 2rem',
        display: 'flex', alignItems: 'center', gap: '1rem'
      }}>
        <button style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'var(--color-primary)', color: '#fff', border: 'none',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer',
        }}>
          <svg width="11" height="12" viewBox="0 0 11 12"><polygon points="1,0 11,6 1,12" fill="currentColor"/></svg>
        </button>
        <span className="tf-mono tf-xs" style={{ color: 'var(--color-secondary)' }}>00:28</span>
        <div style={{ flex: 1, height: 32 }}>
          <WaveformPlaceholder height={32} />
        </div>
        <span className="tf-mono tf-xs tf-muted">12:18</span>
        <div style={{ borderLeft: '1px solid var(--color-border)', paddingLeft: '1rem', display: 'flex', gap: '.4rem', alignItems: 'center' }}>
          <button className="tf-btn ghost sm">0.75×</button>
          <button className="tf-btn sm" style={{ background: 'var(--color-text-body)' }}>1.0×</button>
          <button className="tf-btn ghost sm">1.5×</button>
        </div>
      </div>
    </div>
  );
}

/* ───────────────────────────────────────────────────────────────
   PROPOSED: Sign & Approve moment (replaces success-panel block)
   - The legal act gets its own modal
   - SHA-256 hash + matrícula + timestamp shown like a notarial seal
   - "Hybrid PDF" structure visualized
   ─────────────────────────────────────────────────────────────── */
function ProposedSignModal() {
  return (
    <div style={{
      width: '100%', height: '100%',
      background: 'rgba(15, 34, 64, 0.45)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '2rem'
    }}>
      <div style={{
        width: 560, background: '#fff', borderRadius: 8,
        boxShadow: 'var(--shadow-modal)', overflow: 'hidden'
      }}>
        <div style={{
          background: 'var(--color-primary)', color: '#fff',
          padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', gap: '.75rem'
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            background: 'rgba(255,255,255,.18)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: '1px solid rgba(255,255,255,.3)'
          }}>
            <svg width="14" height="16" viewBox="0 0 14 16" fill="none"><path d="M7 0 L13 3 V8 C13 11.5 10.5 14.5 7 16 C3.5 14.5 1 11.5 1 8 V3 Z" stroke="#fff" strokeWidth="1.4"/><polyline points="4.5,8 6.5,10 9.5,6" stroke="#fff" strokeWidth="1.4" fill="none"/></svg>
          </div>
          <div>
            <h3 style={{ color: '#fff', fontSize: '1rem', margin: 0 }}>Termo aprovado e assinado</h3>
            <div className="tf-xs" style={{ color: 'rgba(255,255,255,.7)' }}>PDF híbrido gerado e arquivado</div>
          </div>
        </div>
        <div style={{ padding: '1.25rem 1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '.5rem 1rem', fontSize: '.85rem', marginBottom: '1rem' }}>
            <span className="tf-muted">Assinado por</span><span><strong>Maria Souza</strong> · Escrivã · Mat. 4321</span>
            <span className="tf-muted">Data/hora</span><span className="tf-mono">26/05/2026 14:38:07 BRT</span>
            <span className="tf-muted">Inquérito</span><span className="tf-mono">IP-2026/004</span>
            <span className="tf-muted">Modelo de IA</span><span className="tf-mono">whisper-medium + llama3:8b</span>
          </div>
          <div style={{
            background: 'var(--color-code-bg)', borderRadius: 4,
            padding: '.6rem .75rem', fontFamily: 'var(--font-mono)',
            fontSize: '.7rem', color: 'var(--color-text-body)',
            wordBreak: 'break-all', lineHeight: 1.4,
            border: '1px solid var(--color-border)'
          }}>
            <div className="tf-xs" style={{ color: 'var(--color-text-light)', fontFamily: 'var(--font-base)', marginBottom: 4, fontWeight: 700 }}>SHA-256 do PDF</div>
            f3a9c2e4b7d1a6f8e0c3b2d1a4e5f6c7d8b9a0e1f2c3b4d5a6e7f8c9b0a1d2e3
          </div>

          {/* Hybrid PDF visualization */}
          <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '.5rem' }}>
            {[
              { n: 'I', title: 'Resumo Oficial', desc: 'Termo formal revisado pelo escrivão' },
              { n: 'II', title: 'Transcrição Literal', desc: 'Texto bruto com timestamps + áudio' },
            ].map(p => (
              <div key={p.n} style={{ border: '1px solid var(--color-border)', borderRadius: 4, padding: '.65rem .8rem' }}>
                <div className="tf-xs tf-muted" style={{ fontWeight: 700 }}>PARTE {p.n}</div>
                <div className="tf-small" style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{p.title}</div>
                <div className="tf-xs tf-muted" style={{ marginTop: 2 }}>{p.desc}</div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '.5rem', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
            <button className="tf-btn ghost">Copiar hash</button>
            <button className="tf-btn outline">Abrir PDF</button>
            <button className="tf-btn">Baixar arquivo</button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ───────────────────────────────────────────────────────────────
   PROPOSED: Login — same brand, more institutional weight
   - Two-pane: brand story on left, form on right
   - Background uses the SSP-PI navy as canvas
   ─────────────────────────────────────────────────────────────── */
function ProposedLogin() {
  return (
    <div className="tf-screen" style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', height: '100%' }}>
      {/* Left brand panel */}
      <div style={{
        background: 'linear-gradient(160deg, #0F2240 0%, #1A365D 60%, #2B6CB0 130%)',
        color: '#fff', padding: '3rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '.6rem' }}>
          <div style={{
            width: 38, height: 38, background: '#fff', color: 'var(--color-primary)',
            borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 800, fontSize: '.95rem'
          }}>TF</div>
          <span style={{ fontSize: '1.05rem', fontWeight: 800, letterSpacing: '-.3px' }}>Termo Fácil</span>
          <span style={{ marginLeft: '.4rem', fontSize: '.6rem', padding: '2px 8px', borderRadius: 999, background: 'rgba(255,255,255,.14)', fontWeight: 700, letterSpacing: '.8px' }}>SSP-PI</span>
        </div>
        <div>
          <div className="tf-xs" style={{ color: 'rgba(255,255,255,.55)', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: 12 }}>Sistema institucional</div>
          <h1 style={{ color: '#fff', fontSize: '2.1rem', lineHeight: 1.15, marginBottom: '.85rem' }}>
            Redação assistida de termos de depoimento
          </h1>
          <p style={{ color: 'rgba(255,255,255,.75)', fontSize: '.95rem', maxWidth: 360 }}>
            Inteligência Artificial generativa local, com auditoria humana obrigatória — Secretaria de Segurança Pública do Piauí.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1.5rem', fontSize: '.75rem', color: 'rgba(255,255,255,.55)' }}>
          <div><strong style={{ color: '#fff', display: 'block', fontSize: '1.1rem', fontWeight: 800 }}>100% on-premise</strong>Processamento local</div>
          <div><strong style={{ color: '#fff', display: 'block', fontSize: '1.1rem', fontWeight: 800 }}>Híbrido</strong>Resumo + transcrição</div>
          <div><strong style={{ color: '#fff', display: 'block', fontSize: '1.1rem', fontWeight: 800 }}>SHA-256</strong>Assinatura digital</div>
        </div>
      </div>

      {/* Right form */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem' }}>
        <div style={{ width: '100%', maxWidth: 360 }}>
          <h2 style={{ fontSize: '1.3rem', marginBottom: '.35rem' }}>Acesso ao sistema</h2>
          <p className="tf-muted tf-small" style={{ marginBottom: '1.5rem' }}>Use sua matrícula funcional SSP-PI</p>
          <div style={{ marginBottom: '1rem' }}>
            <div className="tf-label" style={{ marginBottom: '.35rem' }}>Matrícula funcional</div>
            <input className="tf-input" placeholder="Ex: 123456" />
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <div className="tf-label" style={{ marginBottom: '.35rem', display: 'flex', justifyContent: 'space-between' }}>
              <span>Senha</span>
              <a className="tf-xs" style={{ color: 'var(--color-primary-mid)', textDecoration: 'none', fontWeight: 600 }}>Esqueci minha senha</a>
            </div>
            <input className="tf-input" type="password" placeholder="••••••••" />
          </div>
          <button className="tf-btn" style={{ width: '100%', padding: '.75rem', fontSize: '.95rem' }}>Entrar</button>
          <p className="tf-xs tf-muted" style={{ marginTop: '1.5rem', textAlign: 'center' }}>
            Uso exclusivo de servidores autorizados<br/>
            Versão 2.4.1 · Última atualização há 3 dias
          </p>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ProposedProcessList, ProposedAuditoria, ProposedSignModal, ProposedLogin });
