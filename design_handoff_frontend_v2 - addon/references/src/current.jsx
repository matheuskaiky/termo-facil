// Recreations of the CURRENT (Angular) screens, static.
// These are visual copies of what's in the repo today - used as "before" frames.

/* ─── CURRENT: Process List ─── */
function CurrentProcessList() {
  const rows = [
    { num: 'IP-2026/001', nome: 'José Maria da Silva Junior', tipo: 'Testemunha', data: '12/03/2026 14:22', escrivao: 'Maria Souza', status: 'Concluído' },
    { num: 'IP-2026/002', nome: 'Ana Carolina Mendes',       tipo: 'Vítima',     data: '12/03/2026 13:05', escrivao: 'João Lima',   status: 'Transcrevendo' },
    { num: 'IP-2026/003', nome: 'Rafael Augusto Pereira',    tipo: 'Suspeito',   data: '11/03/2026 16:48', escrivao: 'Maria Souza', status: 'Gerando Resumo' },
    { num: 'IP-2026/004', nome: 'Patricia Helena Coelho',    tipo: 'Testemunha', data: '11/03/2026 11:30', escrivao: 'Carlos Dias', status: 'Pendente' },
    { num: 'IP-2026/005', nome: 'Marcos Vinicius Tavares',   tipo: 'Suspeito',   data: '10/03/2026 17:11', escrivao: 'João Lima',   status: 'Erro' },
    { num: 'IP-2026/006', nome: 'Beatriz Rocha Albuquerque', tipo: 'Vítima',     data: '10/03/2026 09:55', escrivao: 'Maria Souza', status: 'Sem Upload' },
    { num: 'IP-2026/007', nome: 'Diego Henrique Nunes',      tipo: 'Testemunha', data: '09/03/2026 15:20', escrivao: 'Carlos Dias', status: 'Concluído' },
  ];
  return (
    <div className="tf-screen">
      <TFHeader active="processos" />
      <div style={{ padding: '2rem', minHeight: 'calc(100% - 56px)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <div>
              <h2 style={{ fontSize: '1.75rem', marginBottom: '.4rem' }}>Processos e Depoimentos</h2>
              <p className="tf-muted tf-small">Lista de todos os inquéritos e oitivas registradas no sistema.</p>
            </div>
            <button className="tf-btn lg">Novo Processo</button>
          </div>

          <div className="tf-box" style={{ display: 'flex', gap: '1.5rem', padding: '1rem', marginBottom: '1.25rem' }}>
            <div style={{ flex: 1 }}>
              <div className="tf-label" style={{ marginBottom: '.4rem' }}>Buscar (Nome ou Nº)</div>
              <input className="tf-input" placeholder="Ex: IP-2026/001 ou José Maria..." />
            </div>
            <div style={{ flex: 1 }}>
              <div className="tf-label" style={{ marginBottom: '.4rem' }}>Status</div>
              <select className="tf-input"><option>Todos</option></select>
            </div>
            <div style={{ flex: 1 }}>
              <div className="tf-label" style={{ marginBottom: '.4rem' }}>Escrivão</div>
              <input className="tf-input" placeholder="Filtrar por escrivão..." />
            </div>
          </div>

          <div className="tf-box">
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--color-surface-hover)' }}>
                  {['Nº Inquérito','Depoente','Tipo','Data/Hora','Escrivão','Status do Áudio'].map(h => (
                    <th key={h} style={{
                      padding: '.85rem 1rem', textAlign: 'left',
                      borderBottom: '1px solid var(--color-border)',
                      color: 'var(--color-text-light)',
                      fontSize: '.78rem', fontWeight: 600,
                      textTransform: 'uppercase', letterSpacing: '.3px'
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(r => (
                  <tr key={r.num} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '.85rem 1rem' }}><strong>{r.num}</strong></td>
                    <td style={{ padding: '.85rem 1rem' }}>{r.nome}</td>
                    <td style={{ padding: '.85rem 1rem' }}>
                      <span style={{ background: 'var(--color-border)', padding: '.2rem .5rem', borderRadius: 4, fontSize: '.72rem', fontWeight: 500 }}>{r.tipo}</span>
                    </td>
                    <td style={{ padding: '.85rem 1rem' }}>{r.data}</td>
                    <td style={{ padding: '.85rem 1rem' }}>{r.escrivao}</td>
                    <td style={{ padding: '.85rem 1rem' }}><StatusPill status={r.status} /></td>
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

/* ─── CURRENT: Auditoria ─── */
function CurrentAuditoria() {
  return (
    <div className="tf-screen" style={{ display: 'flex', flexDirection: 'column' }}>
      <TFHeader active="processos" />
      <div style={{ padding: '1.5rem 2rem 2rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button className="tf-btn outline sm">← Voltar</button>
            <div>
              <h2 style={{ fontSize: '1.4rem' }}>Auditoria Human-in-the-Loop</h2>
              <p className="tf-muted tf-small" style={{ marginTop: '.2rem' }}>Validação humana dos fatos e correções de termos de depoimentos assistidos por Inteligência Artificial.</p>
            </div>
          </div>
          <div className="tf-box" style={{ display: 'flex', alignItems: 'center', gap: '.75rem', padding: '.5rem .875rem' }}>
            <button className="tf-btn outline sm">Selecionar Arquivo</button>
            <span className="tf-small tf-muted" style={{ fontStyle: 'italic' }}>Nenhum arquivo selecionado</span>
            <button className="tf-btn sm" disabled>Fazer Upload</button>
            <div style={{ borderLeft: '1px solid var(--color-border)', paddingLeft: '.75rem', fontSize: '.85rem' }}>
              Status: <strong style={{ color: 'var(--color-info-dark)' }}>Transcrevendo</strong>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1.5rem', flex: 1, minHeight: 0 }}>
          {/* Left column - transcript locked */}
          <div className="tf-box" style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column' }}>
            <div className="tf-box-header">Transcrição Bruta (Linguagem Falada)</div>
            <div style={{ padding: '1rem', flex: 1 }}>
              <p className="tf-muted tf-small" style={{ fontStyle: 'italic' }}>Texto literal extraído pelo modelo ASR. Utilize como referência para validação jurídica.</p>
            </div>
            <div style={{
              position: 'absolute', inset: 0, background: 'rgba(247,250,252,.88)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              backdropFilter: 'blur(1px)'
            }}>
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontWeight: 600, color: 'var(--color-primary)', marginBottom: 4 }}>Aguardando processamento</p>
                <small className="tf-muted">Status atual: <strong>Transcrevendo</strong></small>
              </div>
            </div>
          </div>
          {/* Right column - editor locked */}
          <div className="tf-box" style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column' }}>
            <div className="tf-box-header">Editor do Termo Final (Sintético)</div>
            <div style={{ padding: '1rem', flex: 1 }}>
              <p className="tf-muted tf-small" style={{ fontStyle: 'italic' }}>Área editável: O escrivão adapta o texto para o formato formal de inquérito policial.</p>
              <h3 style={{ textAlign: 'center', margin: '.8rem 0', fontWeight: 800, fontSize: '1.05rem', letterSpacing: '.5px' }}>
                TERMO DE DEPOIMENTO DE TESTEMUNHA/SUSPEITO
              </h3>
              <div style={{
                flex: 1, minHeight: 280, border: '2px solid var(--color-primary)',
                borderRadius: 4, padding: '1rem', background: 'var(--color-background)',
                fontSize: '.9rem', color: 'var(--color-text-light)', fontStyle: 'italic'
              }}>O resumo gerado pela IA aparecerá aqui para edição...</div>
            </div>
            <div style={{
              position: 'absolute', inset: 0, background: 'rgba(247,250,252,.88)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              backdropFilter: 'blur(1px)'
            }}>
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontWeight: 600, color: 'var(--color-primary)', marginBottom: 4 }}>Aguardando processamento</p>
                <small className="tf-muted">Status atual: <strong>Transcrevendo</strong></small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── CURRENT: Login ─── */
function CurrentLogin() {
  return (
    <div className="tf-screen" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      <div style={{ width: '100%', maxWidth: 420, padding: '1rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '.75rem', marginBottom: '.6rem' }}>
            <div style={{
              width: 38, height: 38, background: 'var(--color-primary)', color: '#fff',
              borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 800, fontSize: '1rem'
            }}>TF</div>
            <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--color-primary)', letterSpacing: '-.5px' }}>Termo Fácil</span>
          </div>
          <span className="tf-status" style={{ background: 'var(--color-brand-badge)', color: '#fff', fontSize: '.7rem', padding: '2px 10px' }}>SSP-PI</span>
          <p className="tf-muted tf-small" style={{ marginTop: '.75rem' }}>Sistema de Gestão de Termos de Depoimento</p>
        </div>

        <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 4px 20px rgba(0,0,0,.08)', border: '1px solid var(--color-border)', overflow: 'hidden' }}>
          <div style={{ background: 'var(--color-primary)', padding: '1.25rem 1.75rem' }}>
            <h2 style={{ color: '#fff', fontSize: '1.05rem', margin: 0 }}>Acesso ao Sistema</h2>
            <p style={{ color: 'rgba(255,255,255,.7)', fontSize: '.8rem', margin: '.25rem 0 0' }}>Use sua matrícula funcional SSP-PI</p>
          </div>
          <div style={{ padding: '1.75rem' }}>
            <div style={{ marginBottom: '1.25rem' }}>
              <div className="tf-label" style={{ marginBottom: '.4rem' }}>Matrícula Funcional</div>
              <input className="tf-input" placeholder="Ex: 123456" />
            </div>
            <div style={{ marginBottom: '1.5rem' }}>
              <div className="tf-label" style={{ marginBottom: '.4rem' }}>Senha</div>
              <input className="tf-input" placeholder="••••••••" type="password" />
            </div>
            <button className="tf-btn" style={{ width: '100%', padding: '.75rem', fontSize: '1rem' }}>Entrar</button>
          </div>
        </div>
        <p className="tf-xs" style={{ textAlign: 'center', color: 'var(--color-text-subtle)', marginTop: '1.5rem' }}>
          Secretaria de Segurança Pública do Piauí — Uso exclusivo de servidores autorizados
        </p>
      </div>
    </div>
  );
}

Object.assign(window, { CurrentProcessList, CurrentAuditoria, CurrentLogin });
