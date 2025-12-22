import { useState, useEffect, useRef } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { DomainType } from '../../config/domains';
import { ChatMessage } from './ChatMessage';
import { DomainDetectionCard } from './DomainDetectionCard';

interface ChatInterfaceProps {
  sessionId: string | null;
  uploadedFile: File | null;
  currentDomain: DomainType;
  onDomainDetected: (domain: DomainType) => void;
  onFileProcessed: () => void; 
}

export function ChatInterface({ sessionId, uploadedFile, currentDomain, onDomainDetected, onFileProcessed }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages]);

  useEffect(() => {
    if (uploadedFile) processUploadedFile(uploadedFile);
  }, [uploadedFile]);

  const processUploadedFile = async (file: File) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'system',
      content: `Reading file: ${file.name}...`,
      metadata: {},
      created_at: new Date().toISOString()
    }]);

    if (file.type.includes('text') || file.type.includes('csv')) {
      const reader = new FileReader();
      reader.onload = async (e) => {
        await sendMessage(e.target?.result as string);
        onFileProcessed();
      };
      reader.readAsText(file);
    } else {
       await sendMessage(`Analyze uploaded file: ${file.name}`);
       onFileProcessed();
    }
  };

  const sendMessage = async (textToSend: string = input) => {
    if (!textToSend.trim()) return;
    
    const userMsg = { id: Date.now().toString(), role: 'user', content: textToSend, metadata: {}, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    if (input) setInput('');
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToSend, preferred_model: "auto", session_id: sessionId })
      });
      const data = await response.json();

      const aiMsg = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.analysis,
        created_at: new Date().toISOString(),
        metadata: {
          agentUsed: data.engine,
          safePreview: data.original_redacted,
          confidence: 0.99
        }
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'system', content: "⚠️ Backend Error", metadata: {}, created_at: new Date().toISOString() }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 pt-6"><DomainDetectionCard domain={currentDomain} /></div>
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map(msg => <ChatMessage key={msg.id} message={msg} currentDomain={currentDomain} />)}
        {loading && <div className="ml-4 text-cyan-400 text-sm animate-pulse">Nexus is thinking...</div>}
        <div ref={messagesEndRef} />
      </div>
      <div className="p-4 border-t border-white/10">
        <div className="relative flex items-center bg-white/5 rounded-xl border border-white/10">
          <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()} className="flex-1 bg-transparent p-3 text-white outline-none" placeholder="Ask Nexus..." />
          <button onClick={() => sendMessage()} disabled={loading} className="p-2 text-cyan-400"><Send size={20} /></button>
        </div>
      </div>
    </div>
  );
}