import { Activity, Shield, Zap } from 'lucide-react';

export function DomainDetectionCard({ domain }: { domain: string }) {
  return (
    <div className="max-w-4xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3 text-cyan-400">
            <Activity size={18} className="animate-pulse" />
            <span className="font-bold uppercase tracking-wider text-xs">
                Active Session: {domain}
            </span>
        </div>
        
        <div className="flex gap-4">
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#0B0C15]/50 border border-white/5">
                    <Shield size={12} className="text-green-400" />
                    <span className="text-xs text-gray-400">Vault: <span className="text-white font-mono">Secure</span></span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#0B0C15]/50 border border-white/5">
                    <Zap size={12} className="text-purple-400" />
                    <span className="text-xs text-gray-400">Mode: <span className="text-white font-mono">Swarm</span></span>
            </div>
        </div>
    </div>
  );
}