import React from 'react';

const AudioPlayer = () => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '1rem',
      padding: '1rem',
      backgroundColor: 'var(--color-white)',
      borderBottom: '1px solid var(--color-border)'
    }}>
      <button className="btn" style={{ padding: '0.5rem 1rem' }}>▶ PLAY</button>
      <button className="btn btn-secondary" style={{ padding: '0.5rem 1rem' }}>⏸ PAUSE</button>
      
      <div style={{ 
        width: '50%', 
        height: '8px', 
        backgroundColor: 'var(--color-tablehead)', 
        borderRadius: '4px',
        position: 'relative',
        margin: '0 1rem'
      }}>
        <div style={{
          width: '15%',
          height: '100%',
          backgroundColor: 'var(--color-primary)',
          borderRadius: '4px'
        }}></div>
      </div>

      <span style={{ fontWeight: 'bold', color: 'var(--color-secondary)' }}>05:12 / 42:00</span>
      <span style={{ fontSize: '0.9rem', color: 'var(--color-secondary)' }}>Velocidade: [1.5x]</span>
    </div>
  );
};

export default AudioPlayer;
