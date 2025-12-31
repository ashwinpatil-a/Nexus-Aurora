import { User, Bot, Sparkles, BarChart2 } from 'lucide-react';

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    metadata?: {
      agent?: string;
      privacyScore?: number;
      chart?: { title?: string; data: { label: string; value: number }[] };
    };
  };
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  const renderChart = (chart: any) => {
    if (!chart?.data?.length) return null;
    const maxVal = Math.max(...chart.data.map((d: any) => d.value));

    return (
      <div className="mt-4 p-5 bg-[#0F1117] rounded-xl border border-white/10 shadow-inner">
        <div className="flex items-center gap-2 mb-4 text-cyan-400 text-xs font-bold uppercase tracking-wider">
          <BarChart2 size={16} /> {chart.title || "Visual Insight"}
        </div>
        <div className="space-y-3">
          {chart.data.map((item: any, i: number) => (
            <div key={i} className="flex items-center gap-3 text-xs">
              <span className="w-24 truncate text-gray-400 text-right">{item.label}</span>
              <div className="flex-1 h-3 bg-gray-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-cyan-600 to-blue-600 rounded-full transition-all duration-1000" 
                  style={{ width: `${(item.value / maxVal) * 100}%` }} 
                />
              </div>
              <span className="w-12 text-white font-mono text-right">{item.value.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className={`flex gap-4 max-w-4xl mx-auto ${isUser ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}>
      {!isUser && (
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-900 to-blue-900 flex items-center justify-center shadow-lg border border-white/10 mt-1">
            <Bot size={20} className="text-cyan-400" />
        </div>
      )}

      <div className={`max-w-[85%] space-y-2 ${isUser ? 'items-end flex flex-col' : ''}`}>
        <div className={`p-5 rounded-2xl text-sm leading-7 shadow-xl ${
            isUser ? 'bg-blue-600 text-white rounded-br-none' : 'bg-[#1A1D26] border border-white/10 text-gray-200 rounded-bl-none'
        }`}>
            <div className="whitespace-pre-wrap font-sans">{message.content}</div>
            {!isUser && message.metadata?.chart && renderChart(message.metadata.chart)}
        </div>
        
        {!isUser && message.metadata && (
            <div className="flex items-center gap-3 ml-2 text-[10px] uppercase tracking-widest font-semibold">
                <div className="flex items-center gap-1.5 text-cyan-400 bg-cyan-900/10 px-2 py-1 rounded border border-cyan-500/10">
                    <Sparkles size={10} /> <span>{message.metadata.agent}</span>
                </div>
            </div>
        )}
      </div>
    </div>
  );
}