import { Sparkles, LogOut } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { DomainType, DOMAIN_CONFIGS } from '../../config/domains';
import * as Icons from 'lucide-react';


export function Header({ user, currentDomain, onDomainChange }: HeaderProps) {
  const domainConfig = DOMAIN_CONFIGS[currentDomain];
  const DomainIcon = (Icons as any)[domainConfig.icon] || Icons.BarChart3;

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <header className="border-b border-white/5 bg-white/[0.02] backdrop-blur-xl">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Sparkles className="w-8 h-8 text-cyan-400" />
              <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full blur opacity-20" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 text-transparent bg-clip-text">
                Nexus Aurora
              </h1>
              <p className="text-xs text-gray-500">Ultimate AI Analyst</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border transition-all"
              style={{
                borderColor: `${domainConfig.color}40`,
                backgroundColor: `${domainConfig.color}10`
              }}
            >
              <DomainIcon
                className="w-5 h-5"
                style={{ color: domainConfig.color }}
              />
              <span className="text-sm font-medium text-gray-300">
                {domainConfig.name}
              </span>
            </div>

            <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-white/5 border border-white/10">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white text-sm font-medium">
                {user?.email?.[0].toUpperCase()}
              </div>
              <span className="text-sm text-gray-300">{user?.email}</span>
            </div>

            <button
              onClick={handleSignOut}
              className="p-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 hover:border-red-500/30 transition-all group"
            >
              <LogOut className="w-5 h-5 text-gray-400 group-hover:text-red-400 transition-colors" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
