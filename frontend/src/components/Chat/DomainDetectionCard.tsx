import { CheckCircle, Shield, Zap } from 'lucide-react';
import { DomainType, DOMAIN_CONFIGS } from '../../config/domains';
import * as Icons from 'lucide-react';

interface DomainDetectionCardProps {
  domain: DomainType;
}

export function DomainDetectionCard({ domain }: DomainDetectionCardProps) {
  const domainConfig = DOMAIN_CONFIGS[domain];
  const DomainIcon = (Icons as any)[domainConfig.icon] || Icons.BarChart3;

  return (
    <div
      className="p-6 rounded-2xl border transition-all animate-in fade-in slide-in-from-top-4 duration-500"
      style={{
        backgroundColor: `${domainConfig.color}10`,
        borderColor: `${domainConfig.color}40`
      }}
    >
      <div className="flex items-start gap-4">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{
            backgroundColor: `${domainConfig.color}20`,
            border: `2px solid ${domainConfig.color}60`
          }}
        >
          <DomainIcon className="w-6 h-6" style={{ color: domainConfig.color }} />
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <h3 className="text-lg font-semibold text-white">
              Domain Detected: {domainConfig.name}
            </h3>
          </div>

          <p className="text-sm text-gray-300 mb-4">
            The Chameleon engine has successfully identified your data domain and optimized the analysis pipeline.
          </p>

          <div className="grid grid-cols-3 gap-3">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
              <Shield className="w-4 h-4 text-cyan-400" />
              <div>
                <p className="text-xs text-gray-400">Privacy</p>
                <p className="text-sm font-medium text-white">100%</p>
              </div>
            </div>

            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
              <Zap className="w-4 h-4 text-yellow-400" />
              <div>
                <p className="text-xs text-gray-400">Agent</p>
                <p className="text-sm font-medium text-white">Ready</p>
              </div>
            </div>

            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
              <DomainIcon className="w-4 h-4" style={{ color: domainConfig.color }} />
              <div>
                <p className="text-xs text-gray-400">Mode</p>
                <p className="text-sm font-medium text-white">Active</p>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-white/10">
            <p className="text-xs text-gray-400 mb-2">Optimized KPIs for this domain:</p>
            <div className="flex flex-wrap gap-2">
              {domainConfig.kpis.slice(0, 4).map((kpi) => (
                <span
                  key={kpi}
                  className="px-2 py-1 rounded text-xs font-medium"
                  style={{
                    backgroundColor: `${domainConfig.color}20`,
                    color: domainConfig.color
                  }}
                >
                  {kpi}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
