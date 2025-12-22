import { User, Sparkles, Info } from 'lucide-react';
import { DomainType, DOMAIN_CONFIGS } from '../../config/domains';

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    metadata: any;
    created_at: string;
  };
  currentDomain: DomainType;
}

export function ChatMessage({ message, currentDomain }: ChatMessageProps) {
  const domainConfig = DOMAIN_CONFIGS[currentDomain];

  if (message.role === 'system') {
    return (
      <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-white/5 border border-white/10">
        <Info className="w-4 h-4 text-gray-400" />
        <p className="text-sm text-gray-400">{message.content}</p>
      </div>
    );
  }

  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-3 max-w-3xl ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-gradient-to-br from-cyan-500 to-blue-500'
            : 'bg-white/10 border border-white/10'
        }`}>
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : (
            <Sparkles className="w-5 h-5 text-cyan-400" />
          )}
        </div>

        <div className="flex-1">
          <div className={`rounded-2xl p-4 ${
            isUser
              ? 'bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30'
              : 'bg-white/5 border border-white/10'
          }`}>
            <p className="text-sm text-gray-200 whitespace-pre-wrap">
              {message.content}
            </p>
          </div>

          {!isUser && message.metadata && Object.keys(message.metadata).length > 0 && (
            <div className="mt-2 p-3 rounded-lg bg-white/5 border border-white/10">
              <p className="text-xs font-semibold text-gray-400 mb-2">Transparency Card</p>
              <div className="space-y-1">
                {message.metadata.agentUsed && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Agent Used:</span>
                    <span
                      className="font-medium"
                      style={{ color: domainConfig.color }}
                    >
                      {message.metadata.agentUsed}
                    </span>
                  </div>
                )}
                {message.metadata.processingTime && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Processing Time:</span>
                    <span className="text-gray-300">{message.metadata.processingTime}</span>
                  </div>
                )}
                {message.metadata.redactedCount !== undefined && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">PII Entities Redacted:</span>
                    <span className="text-green-400">{message.metadata.redactedCount}</span>
                  </div>
                )}
                {message.metadata.confidence && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Confidence:</span>
                    <span className="text-gray-300">
                      {(message.metadata.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
