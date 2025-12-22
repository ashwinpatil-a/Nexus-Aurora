import { useState } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { AuthView } from './components/Auth/AuthView';
import { DomainType } from './config/domains';

function App() {
  // Simple Local Auth State
  const [user, setUser] = useState<{email: string} | null>(null);
  const [currentDomain, setCurrentDomain] = useState<DomainType>('general');

  // 1. Show Auth Screen if no user
  if (!user) {
    return <AuthView onLogin={(email) => setUser({ email })} />;
  }

  // 2. Show Dashboard if logged in
  return (
    <MainLayout 
      user={user} 
      currentDomain={currentDomain} 
      onDomainChange={setCurrentDomain} 
    />
  );
}

export default App;