// Shared shell + small components used across both "current" and "proposed" screens
const { useState } = React;

/* ─── Header (matches current header.component.html, minor refinements only) ─── */
function TFHeader({ active = 'processos', user = { nome: 'Maria Souza', cargo: 'Escrivã', matricula: '4321' } }) {
  const initials = (user.nome || '').split(' ').slice(0, 2).map(s => s[0]).join('');
  return (
    <header className="tf-header">
      <div className="brand">
        <div className="brand-mark">TF</div>
        <span className="brand-name">Termo Fácil</span>
        <span className="brand-badge">SSP-PI</span>
      </div>
      <nav>
        <a className={active === 'processos' ? 'active' : ''}>Processos</a>
        <a className={active === 'admin' ? 'active' : ''}>Painel Admin</a>
        <a className={active === 'metricas' ? 'active' : ''}>Métricas</a>
      </nav>
      <div className="user">
        <div>
          <div className="name">{user.nome}</div>
          <div className="meta">{user.cargo} · Mat. {user.matricula}</div>
        </div>
        <div className="avatar">{initials}</div>
        <button className="logout">Sair</button>
      </div>
    </header>
  );
}

/* ─── Pipeline stepper — NEW proposed component ─── */
const STAGES = [
  { id: 'pendente',      label: 'Pendente' },
  { id: 'transcrevendo', label: 'Transcrevendo' },
  { id: 'extraindo',     label: 'Extraindo Dados' },
  { id: 'resumo',        label: 'Gerando Resumo' },
  { id: 'concluido',     label: 'Concluído' },
];
function PipelineStepper({ activeIndex = 2, error = false, compact = false }) {
  return (
    <ol className={'tf-pipeline' + (compact ? ' compact' : '')}>
      {STAGES.map((s, i) => {
        const done = i < activeIndex;
        const active = i === activeIndex && !error;
        const errored = i === activeIndex && error;
        return (
          <li key={s.id} className={['step', done && 'done', active && 'active', errored && 'errored'].filter(Boolean).join(' ')}>
            <div className="step-marker">
              {done ? <svg width="10" height="10" viewBox="0 0 10 10"><polyline points="1.5,5 4,7.5 8.5,2.5" fill="none" stroke="currentColor" strokeWidth="1.6"/></svg>
                : errored ? '!' : i + 1}
            </div>
            <div className="step-label">{s.label}</div>
            {i < STAGES.length - 1 && <div className="step-line" />}
          </li>
        );
      })}
      <style>{`
        .tf-pipeline {
          list-style: none; padding: 0; margin: 0;
          display: grid; grid-template-columns: repeat(${STAGES.length}, 1fr);
          gap: 0; align-items: start;
        }
        .tf-pipeline .step { position: relative; text-align: center; }
        .tf-pipeline .step-marker {
          width: 24px; height: 24px; border-radius: 50%;
          background: #fff; border: 2px solid var(--color-border-strong);
          color: var(--color-text-light);
          margin: 0 auto 6px; display: flex; align-items: center; justify-content: center;
          font-size: .72rem; font-weight: 800; position: relative; z-index: 2;
          transition: all .2s;
        }
        .tf-pipeline .step-label {
          font-size: .72rem; font-weight: 600;
          color: var(--color-text-light);
        }
        .tf-pipeline .step-line {
          position: absolute; top: 11px; left: 50%; width: 100%; height: 2px;
          background: var(--color-border-strong); z-index: 1;
        }
        .tf-pipeline .step.done .step-marker {
          background: var(--color-success); border-color: var(--color-success); color: #fff;
        }
        .tf-pipeline .step.done ~ .step .step-line,
        .tf-pipeline .step.done .step-line {
          background: var(--color-success);
        }
        .tf-pipeline .step.done .step-label { color: var(--color-success-dark); }
        .tf-pipeline .step.active .step-marker {
          background: var(--color-primary); border-color: var(--color-primary); color: #fff;
          box-shadow: 0 0 0 4px rgba(43,108,176,.18);
          animation: tfPulse 1.6s ease-in-out infinite;
        }
        .tf-pipeline .step.active .step-label { color: var(--color-primary); font-weight: 700; }
        .tf-pipeline .step.errored .step-marker {
          background: var(--color-accent); border-color: var(--color-accent); color: #fff;
        }
        .tf-pipeline .step.errored .step-label { color: var(--color-danger-dark); font-weight: 700; }
        @keyframes tfPulse {
          0%, 100% { box-shadow: 0 0 0 4px rgba(43,108,176,.18); }
          50%      { box-shadow: 0 0 0 8px rgba(43,108,176,.08); }
        }
        .tf-pipeline.compact .step-marker { width: 16px; height: 16px; font-size: .6rem; border-width: 1.5px; }
        .tf-pipeline.compact .step-label  { font-size: .65rem; }
        .tf-pipeline.compact .step-line   { top: 7px; }
      `}</style>
    </ol>
  );
}

/* ─── Small flat status pill (matches current implementation) ─── */
function StatusPill({ status }) {
  const cls = {
    'Sem Upload':'s-sem-upload', 'Pendente':'s-pendente',
    'Transcrevendo':'s-processando','Extraindo Dados':'s-processando',
    'Gerando Resumo':'s-processando','Processando':'s-processando',
    'Concluído':'s-concluido','Erro':'s-erro'
  }[status] || 's-sem-upload';
  return <span className={'tf-status ' + cls}>{status}</span>;
}

/* ─── A subtle stripe placeholder for waveform/audio ─── */
function WaveformPlaceholder({ height = 40 }) {
  // Use deterministic bar heights so layout is stable.
  const bars = Array.from({ length: 80 }).map((_, i) => {
    const seed = Math.sin(i * 1.7) * 0.5 + 0.5;
    return Math.max(0.18, Math.min(1, seed * 0.85 + (i % 7) * 0.04));
  });
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 2, height, padding: '0 2px' }}>
      {bars.map((h, i) => (
        <div key={i} style={{
          width: 3, height: `${h * 100}%`,
          background: i < 28 ? 'var(--color-primary)' : 'var(--color-border-strong)',
          borderRadius: 1
        }} />
      ))}
    </div>
  );
}

/* ─── Diagnostic note card (used as an artboard) ─── */
function DiagnosticNote({ title, items }) {
  return (
    <div style={{
      padding: '1.75rem 2rem', background: '#FFFEF6',
      height: '100%', overflow: 'auto', fontFamily: 'var(--font-base)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '.7rem', marginBottom: '1.25rem' }}>
        <div style={{
          width: 32, height: 32, background: 'var(--color-primary)', color: '#fff',
          borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 800, fontSize: '.8rem'
        }}>TF</div>
        <h2 style={{ margin: 0, fontSize: '1.3rem' }}>{title}</h2>
      </div>
      <ol style={{ paddingLeft: '1.1rem', margin: 0, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {items.map((it, i) => (
          <li key={i} style={{ marginLeft: '.25rem' }}>
            <div style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: '.95rem', marginBottom: '.25rem' }}>
              {it.title}
            </div>
            <div style={{ color: 'var(--color-text-body)', fontSize: '.85rem', lineHeight: 1.55 }}>{it.body}</div>
            {it.fix && (
              <div className="tf-note" style={{ marginTop: '.5rem' }}>
                <strong>Proposta: </strong>{it.fix}
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

Object.assign(window, {
  TFHeader, PipelineStepper, StatusPill, WaveformPlaceholder, DiagnosticNote, STAGES
});
