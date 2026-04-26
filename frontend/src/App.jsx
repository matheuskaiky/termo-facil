import React from 'react';
import Header from './components/Header';
import AudioPlayer from './components/AudioPlayer';
import Auditoria from './pages/Auditoria';

function App() {
  return (
    <div className="container-fluid">
      <Header />
      <AudioPlayer />
      <Auditoria />
    </div>
  );
}

export default App;
