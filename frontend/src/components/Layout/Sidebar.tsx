import { useState, useEffect } from 'react';
import { Plus, MessageSquare, Trash2, FileText } from 'lucide-react';
import { db } from '../../firebase'; // Ensure this points to firebase.ts
import { collection, query, where, orderBy, onSnapshot, addDoc, deleteDoc, doc } from 'firebase/firestore';

interface SidebarProps {
  isOpen: boolean;
  user: any;
  activeSessionId: string | null;
  onSessionSelect: (id: string | null) => void;
  onToggle: () => void;
}

export function Sidebar({ isOpen, user, activeSessionId, onSessionSelect }: SidebarProps) {
  const [sessions, setSessions] = useState<any[]>([]);

  useEffect(() => {
    if (!user) return;

    // Listen to Firestore 'chat_sessions'
    const q = query(
      collection(db, "chat_sessions"),
      where("user_id", "==", user.uid),
      orderBy("created_at", "desc")
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const loadedSessions = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setSessions(loadedSessions);
    });

    return () => unsubscribe();
  }, [user]);

  const handleDelete = async (e: any, id: string) => {
    e.stopPropagation();
    if (confirm("Delete this history?")) {
        await deleteDoc(doc(db, "chat_sessions", id));
        if (activeSessionId === id) onSessionSelect(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={() => onSessionSelect(null)}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-semibold hover:opacity-90 transition-all shadow-lg shadow-cyan-900/20"
        >
          <Plus size={18} /> New Analysis
        </button>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto px-3 space-y-1 custom-scrollbar">
        <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Recent History
        </div>
        
        {sessions.map((session) => (
          <div
            key={session.id}
            onClick={() => onSessionSelect(session.id)}
            className={`group flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
              activeSessionId === session.id 
                ? 'bg-white/10 text-white border border-white/10' 
                : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
            }`}
          >
            {session.file_attached ? (
                <FileText size={16} className="text-purple-400 shrink-0" />
            ) : (
                <MessageSquare size={16} className="text-cyan-400 shrink-0" />
            )}
            
            <div className="flex-1 min-w-0">
                <div className="truncate text-sm font-medium">{session.title}</div>
                <div className="text-[10px] text-gray-600">
                    {new Date(session.created_at).toLocaleDateString()}
                </div>
            </div>

            <button 
                onClick={(e) => handleDelete(e, session.id)}
                className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 hover:text-red-400 rounded transition-all"
            >
                <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
      
      {/* User Info Footer */}
      <div className="p-4 border-t border-white/5 bg-[#0B0C15]/50">
          <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-500 flex items-center justify-center text-xs font-bold text-white">
                  {user.email?.[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-white truncate">{user.email}</div>
                  <div className="text-[10px] text-green-400 flex items-center gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                      Online
                  </div>
              </div>
          </div>
      </div>
    </div>
  );
}