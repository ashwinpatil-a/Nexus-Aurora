import { User, Bot, Sparkles } from 'lucide-react';

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    metadata?: {
      agent?: string;
      privacyScore?: number;
      domain?: string;
    };
  };
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-4 max-w-4xl mx-auto ${isUser ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}>
      {/* Bot Icon */}
      {!isUser && (
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-900 to-blue-900 flex items-center justify-center shadow-lg shadow-cyan-900/20 flex-shrink-0 border border-white/10 mt-1">
            <Bot size={20} className="text-cyan-400" />
        </div>
      )}

      <div className={`max-w-[85%] space-y-2 ${isUser ? 'items-end flex flex-col' : ''}`}>
        
        {/* The Message Bubble */}
        <div className={`p-5 rounded-2xl text-sm leading-7 shadow-xl ${
            isUser 
            ? 'bg-blue-600 text-white rounded-br-none bg-gradient-to-br from-blue-600 to-blue-700' 
            : 'bg-[#1A1D26] border border-white/10 text-gray-200 rounded-bl-none'
        }`}>
            <div className="whitespace-pre-wrap font-sans">{message.content}</div>
        </div>
        
        {/* Metadata Footer (Agents & Privacy) */}
        {!isUser && message.metadata && (
            <div className="flex items-center gap-3 ml-2 text-[10px] uppercase tracking-widest font-semibold">
                
                {/* Agent Name */}
                <div className="flex items-center gap-1.5 text-cyan-400 bg-cyan-900/10 px-2 py-1 rounded border border-cyan-500/10">
                    <Sparkles size={10} />
                    <span>{message.metadata.agent}</span>
                </div>

                {/* Privacy Score */}
                <div className={`flex items-center gap-1.5 px-2 py-1 rounded border ${
                    (message.metadata.privacyScore || 0) < 100 
                    ? 'text-yellow-400 bg-yellow-900/10 border-yellow-500/10' 
                    : 'text-green-400 bg-green-900/10 border-green-500/10'
                }`}>
                    <span>Privacy {message.metadata.privacyScore}%</span>
                </div>

                <span className="text-gray-600 ml-1">
                    {new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </span>
            </div>
        )}
      </div>

      {/* User Icon */}
      {isUser && (
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-lg flex-shrink-0 border border-white/10 mt-1">
            <User size={20} className="text-white" />
        </div>
      )}
    </div>
  );
}