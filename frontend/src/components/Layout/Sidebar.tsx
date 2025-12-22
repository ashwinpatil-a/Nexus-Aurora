import { useState, useEffect } from 'react';
import { Plus, MessageSquare, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { DomainType, DOMAIN_CONFIGS } from '../../config/domains';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  user: any;
  activeSessionId: string | null;
  onSessionSelect: (sessionId: string | null) => void;
  currentDomain: DomainType;
}

interface Session {
  id: string;
  title: string;
  domain: string | null;
  created_at: string;
}

export function Sidebar({ isOpen, onToggle, user, activeSessionId, onSessionSelect, currentDomain }: SidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, [user]);

  const loadSessions = async () => {
    try {
      const { data, error } = await supabase
        .from('chat_sessions')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setSessions(data || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const createNewSession = async () => {
    try {
      const { data, error } = await supabase
        .from('chat_sessions')
        .insert({
          user_id: user.id,
          title: 'New Analysis',
          domain: currentDomain
        })
        .select()
        .single();

      if (error) throw error;
      setSessions([data, ...sessions]);
      onSessionSelect(data.id);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      const { error } = await supabase
        .from('chat_sessions')
        .delete()
        .eq('id', sessionId);

      if (error) throw error;
      setSessions(sessions.filter(s => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        onSessionSelect(null);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed top-20 left-4 z-50 p-2 rounded-lg bg-white/5 backdrop-blur-xl border border-white/10 hover:bg-white/10 transition-all"
      >
        <ChevronRight className="w-5 h-5 text-gray-400" />
      </button>
    );
  }

  return (
    <aside className="w-80 border-r border-white/5 bg-white/[0.02] backdrop-blur-xl flex flex-col">
      <div className="p-4 border-b border-white/5 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-300">Sessions</h2>
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
        >
          <ChevronLeft className="w-4 h-4 text-gray-400" />
        </button>
      </div>

      <div className="p-4">
        <button
          onClick={createNewSession}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-medium hover:from-cyan-600 hover:to-blue-600 transition-all shadow-lg shadow-cyan-500/20"
        >
          <Plus className="w-5 h-5" />
          New Analysis
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-8 h-8 border-2 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No sessions yet</p>
            <p className="text-xs text-gray-600 mt-1">Create one to get started</p>
          </div>
        ) : (
          sessions.map((session) => {
            const domainConfig = session.domain ? DOMAIN_CONFIGS[session.domain as DomainType] : null;
            const isActive = activeSessionId === session.id;

            return (
              <div
                key={session.id}
                className={`group relative p-3 rounded-lg border transition-all cursor-pointer ${
                  isActive
                    ? 'bg-white/10 border-cyan-500/30'
                    : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/10'
                }`}
                onClick={() => onSessionSelect(session.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-200 truncate">
                      {session.title}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {domainConfig && (
                        <span
                          className="text-xs px-2 py-0.5 rounded"
                          style={{
                            backgroundColor: `${domainConfig.color}20`,
                            color: domainConfig.color
                          }}
                        >
                          {domainConfig.name}
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {new Date(session.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20 transition-all"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
