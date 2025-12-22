import { useState } from 'react';
import { Sparkles, ArrowRight, ShieldCheck, Mail } from 'lucide-react';

export function AuthView({ onLogin }: { onLogin: (email: string) => void }) {
  const [email, setEmail] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      onLogin(email);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0C15] flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-blue-500/5 to-purple-500/5" />
      
      <div className="relative z-10 w-full max-w-md px-6">
        <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-8 shadow-2xl">
          <div className="flex items-center justify-center mb-8">
            <Sparkles className="w-12 h-12 text-cyan-400" />
          </div>

          <h1 className="text-3xl font-bold text-center mb-2 text-white">Nexus Aurora</h1>
          <p className="text-center text-gray-400 mb-8 text-sm">Enterprise-Grade Privacy Vault</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-[#0F1117] border border-white/10 rounded-xl px-4 py-3 text-white focus:border-cyan-500/50 focus:outline-none"
              placeholder="analyst@company.com" 
              required 
            />
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold py-3.5 rounded-xl hover:opacity-90 transition-all flex items-center justify-center gap-2"
            >
              Enter Dashboard <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}