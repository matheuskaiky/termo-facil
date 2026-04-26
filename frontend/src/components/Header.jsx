import React from 'react';

const Header = () => {
  return (
    <header style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0.75rem 2rem',
      backgroundColor: 'var(--color-white)',
      borderBottom: '1px solid var(--color-border)',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          width: '32px',
          height: '32px',
          backgroundColor: 'var(--color-primary)',
          borderRadius: '50%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          color: 'var(--color-white)',
          fontWeight: 'bold',
          fontSize: '12px'
        }}>
          PI
        </div>
        <h1 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--color-primary)' }}>
          Termo Fácil
        </h1>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', fontSize: '0.9rem' }}>
        <div>
          Status: <span className="text-success">VPN Segura</span>
        </div>
        <div>
          Policial: <strong>João Silva</strong>
        </div>
      </div>
    </header>
  );
};

export default Header;
