import { useState, useEffect } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { AuthView } from './components/Auth/AuthView';
import { auth } from './firebase'; // Ensure this points to your firebase.ts
import { onAuthStateChanged } from 'firebase/auth';

function App() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Listen for Firebase Auth changes (Login/Logout)
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  if (loading) {
    return <div className="h-screen w-full bg-[#0B0C15] flex items-center justify-center text-cyan-400">Loading Nexus...</div>;
  }

  // If no user, show Login. If user, show App.
  if (!user) {
    return <AuthView />;
  }

  return <MainLayout user={user} />;
}

export default App;