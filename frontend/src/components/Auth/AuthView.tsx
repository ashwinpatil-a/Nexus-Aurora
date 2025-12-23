import { useState } from 'react';
import { auth } from '../../firebase';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { Sparkles, ArrowRight } from 'lucide-react';

export function AuthView() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState('');

  const handleGoogle = async () => {
    try { await signInWithPopup(auth, new GoogleAuthProvider()); } 
    catch (err: any) { setError(err.message); }
  };

  const handleEmail = async (e: any) => {
    e.preventDefault();
    try {
      if (isLogin) await signInWithEmailAndPassword(auth, email, password);
      else await createUserWithEmailAndPassword(auth, email, password);
    } catch (err: any) { setError(err.message); }
  };

  return (
    <div className="min-h-screen bg-[#0B0C15] flex items-center justify-center font-sans">
      <div className="w-full max-w-md p-8 bg-[#1A1D26]/50 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl">
        <div className="flex justify-center mb-6"><Sparkles className="w-12 h-12 text-cyan-400" /></div>
        <h1 className="text-3xl font-bold text-center text-white mb-8">Nexus Aurora</h1>

        {/* GOOGLE BUTTON */}
        <button onClick={handleGoogle} className="w-full bg-white text-gray-900 font-bold py-3 rounded-xl hover:bg-gray-100 transition-all flex items-center justify-center gap-2 mb-6">
           <img src="https://www.google.com/favicon.ico" className="w-5 h-5" alt="G" /> 
           Continue with Google
        </button>

        <div className="relative my-6"><div className="border-t border-white/10"></div><span className="absolute top-[-10px] left-[45%] bg-[#1A1D26] px-2 text-xs text-gray-500">OR</span></div>

        <form onSubmit={handleEmail} className="space-y-4">
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} className="w-full bg-[#0F1117] border border-white/10 rounded-xl px-4 py-3 text-white focus:border-cyan-500/50 outline-none" placeholder="Email" required />
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} className="w-full bg-[#0F1117] border border-white/10 rounded-xl px-4 py-3 text-white focus:border-cyan-500/50 outline-none" placeholder="Password" required />
          {error && <p className="text-red-400 text-sm text-center">{error}</p>}
          <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-all">
            {isLogin ? 'Sign In' : 'Create Account'}
          </button>
        </form>
        <p className="mt-6 text-center text-gray-400 cursor-pointer hover:text-white" onClick={()=>setIsLogin(!isLogin)}>{isLogin ? "Need account? Sign up" : "Have account? Login"}</p>
      </div>
    </div>
  );
}