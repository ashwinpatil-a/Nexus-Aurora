import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, UploadCloud, Shield, Zap, CheckCircle, Bot } from 'lucide-react';
import { auth } from '../../firebase';
import { ChatMessage } from './ChatMessage';
import { DomainDetectionCard } from './DomainDetectionCard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    privacyScore?: number;
    agent?: string;
    domain?: string;
  };
}

export function ChatInterface({ sessionId }: { sessionId: string | null }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeDomain, setActiveDomain] = useState<string>("General");
  const [localSessionId, setLocalSessionId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentSessionId = sessionId || localSessionId;

  // 🟢 IMPROVED: Scroll when messages change OR when loading starts/stops
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (sessionId) {
        setLocalSessionId(null); 
        const fetchMessages = async () => {
            try {
                const res = await fetch(`http://localhost:8000/sessions/${sessionId}/messages`);
                const data = await res.json();
                setMessages(data);
            } catch (e) { console.error(e); }
        };
        fetchMessages();
    } else {
        setLocalSessionId(null); 
        setMessages([]); 
    }
  }, [sessionId]);

  const sendMessage = async (e?: React.FormEvent, overrideText?: string) => {
    e?.preventDefault();
    const textToSend = overrideText || input;
    if (!textToSend.trim() || loading) return;

    setInput('');
    
    const userMsg: Message = { 
      id: Date.now().toString(), role: 'user', content: textToSend, timestamp: new Date().toISOString() 
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const token = await auth.currentUser?.getIdToken();
      
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ 
            text: textToSend, 
            session_id: currentSessionId, 
            user_email: auth.currentUser?.email 
        })
      });

      if (!response.ok) throw new Error("Server Error");

      const data = await response.json();
      if (data.domain) setActiveDomain(data.domain);
      
      if (data.session_id && !currentSessionId) {
          setLocalSessionId(data.session_id);
      }

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(), role: 'assistant', content: data.analysis, timestamp: new Date().toISOString(),
        metadata: {
            privacyScore: data.privacyScore || 100, agent: data.agent || "Swarm", domain: data.domain || "General"
        }
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(), role: 'assistant', content: `⚠️ Error: ${error.message}`, timestamp: new Date().toISOString()
      }]);
    }
    setLoading(false);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    
    const userMsg: Message = { 
        id: Date.now().toString(), role: 'user', content: `[Uploading File: ${file.name}]`, timestamp: new Date().toISOString() 
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
        const token = await auth.currentUser?.getIdToken();
        const formData = new FormData();
        formData.append("file", file);
        
        const res = await fetch("http://localhost:8000/upload", {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}`, "user-email": auth.currentUser?.email || "anonymous" }, 
            body: formData
        });
        
        const data = await res.json();
        setActiveDomain(data.domain);

        if (data.session_id) {
            setLocalSessionId(data.session_id);
        }
        
        const aiMsg: Message = {
            id: (Date.now() + 1).toString(), role: 'assistant', content: data.analysis, timestamp: new Date().toISOString(),
            metadata: { privacyScore: 100, agent: data.agent, domain: data.domain }
        };
        setMessages(prev => [...prev, aiMsg]);

    } catch (err) {
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: "Upload Failed", timestamp: new Date().toISOString() }]);
    }
    setLoading(false);
  };

  const isChatActive = messages.length > 0;

  return (
    <div className="flex flex-col h-full bg-[#0B0C15] relative font-sans overflow-hidden">
      
      {/* === STATE 1: WELCOME SCREEN (Empty Chat) === */}
      {!isChatActive && (
        <div className="absolute inset-0 flex flex-col items-center justify-center p-8 z-10 overflow-y-auto">
            <div className="w-20 h-20 bg-gradient-to-br from-cyan-500/10 to-blue-600/10 rounded-[2rem] flex items-center justify-center mb-6 border border-cyan-500/20 shadow-2xl shadow-cyan-900/30">
                <UploadCloud size={40} className="text-cyan-400" />
            </div>
            <h1 className="text-4xl font-bold text-white mb-4 text-center">Welcome to Nexus Aurora</h1>
            <p className="text-gray-400 mb-10 text-center max-w-xl">Upload your data to unlock intelligent, privacy-first analysis.</p>
            <div className="w-full max-w-xl mb-12">
                <label className="flex flex-col items-center justify-center w-full h-64 border border-dashed border-white/10 rounded-3xl bg-[#0F1117] hover:bg-[#151720] transition-all cursor-pointer group">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <UploadCloud className="w-10 h-10 text-gray-500 mb-4 group-hover:text-cyan-400 transition-colors" />
                        <p className="mb-2 text-lg text-white font-medium">Drop files here</p>
                        <p className="text-sm text-gray-500 mb-6">CSV, JSON, PDF, Excel</p>
                        <span className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-900/30">Select File</span>
                    </div>
                    <input type="file" className="hidden" onChange={handleFileUpload} />
                </label>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-4xl px-4">
                {[
                    { title: "Microsoft Vault", icon: Shield, desc: "PII scrubbed locally", color: "text-green-400" },
                    { title: "Swarm Agents", icon: Zap, desc: "6 Specialized bots", color: "text-purple-400" },
                    { title: "Enterprise", icon: CheckCircle, desc: "SOC2 Compliant", color: "text-blue-400" }
                ].map((item, i) => (
                    <div key={i} className="p-4 rounded-xl bg-[#1A1D26]/40 border border-white/5 backdrop-blur-sm">
                        <div className={`mb-3 ${item.color}`}><item.icon size={24} /></div>
                        <h3 className="font-bold text-white text-md mb-1">{item.title}</h3>
                        <p className="text-xs text-gray-500">{item.desc}</p>
                    </div>
                ))}
            </div>
        </div>
      )}

      {/* 🟢 NEW: Full Screen Loading Overlay for INITIAL Interaction (e.g., File Upload) */}
      {loading && messages.length <= 1 && (
         <div className="absolute inset-0 z-50 bg-[#0B0C15]/90 backdrop-blur-sm flex flex-col items-center justify-center animate-in fade-in duration-300">
            <div className="relative">
                <div className="w-20 h-20 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                    <Bot size={28} className="text-cyan-400" />
                </div>
            </div>
            <h3 className="mt-8 text-2xl font-bold text-white tracking-tight">Processing Data</h3>
            <div className="mt-3 flex flex-col items-center gap-1 text-gray-400 text-sm">
                <p>🔒 Vault is scrubbing PII...</p>
                <p>☁️ Securely transmitting to Swarm...</p>
                <p>🤖 Agents are analyzing...</p>
            </div>
         </div>
      )}

      {isChatActive && (
        <>
            <div className="flex-shrink-0 p-4 border-b border-white/5 bg-[#1A1D26]/50 backdrop-blur-md z-10">
               <DomainDetectionCard domain={activeDomain} />
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth">
                {messages.map((msg) => (
                    <ChatMessage key={msg.id} message={msg} />
                ))}
                
                {/* 🟢 NEW: High-Visibility Processing Indicator */}
                {loading && messages.length > 1 && (
                    <div className="flex justify-start max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-2 duration-300">
                        {/* Bot Icon */}
                        <div className="w-10 h-10 rounded-xl bg-cyan-900/20 flex items-center justify-center border border-cyan-500/30 mt-1">
                            <Bot size={20} className="text-cyan-400 animate-pulse" />
                        </div>
                        
                        {/* Text Box */}
                        <div className="ml-4 p-4 rounded-2xl bg-[#1A1D26] border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.1)] flex items-center gap-4">
                            
                            {/* Spinner */}
                            <Loader2 size={20} className="animate-spin text-cyan-400" />
                            
                            <div className="flex flex-col">
                                <span className="text-cyan-100 font-medium text-sm animate-pulse">
                                    Nexus Swarm is thinking...
                                </span>
                                <span className="text-cyan-500/60 text-xs">
                                    Analyzing privacy vault & cloud data
                                </span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            <div className="flex-shrink-0 p-6 bg-[#0B0C15] border-t border-white/5 z-20">
                <form onSubmit={(e) => sendMessage(e)} className="relative max-w-4xl mx-auto">
                <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask Nexus anything..." className="w-full bg-[#1A1D26] text-white rounded-xl pl-6 pr-14 py-4 border border-white/10 focus:border-cyan-500/50 outline-none transition-all shadow-xl"/>
                <button type="submit" disabled={!input.trim() || loading} className="absolute right-2 top-2 p-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg text-white hover:opacity-90 disabled:opacity-50 transition-all"><Send size={18} /></button>
                </form>
            </div>
        </>
      )}
    </div>
  );
}