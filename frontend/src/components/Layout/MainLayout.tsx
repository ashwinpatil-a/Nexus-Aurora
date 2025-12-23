import { useState } from 'react';
import { Sidebar } from './Sidebar';
import { ChatInterface } from '../Chat/ChatInterface';
import { Menu, LogOut, LayoutDashboard } from 'lucide-react';
import { auth } from '../../firebase';
import { signOut } from 'firebase/auth';

export function MainLayout({ user }: { user: any }) {
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  return (
    // FIX: h-screen forces exact viewport height. overflow-hidden prevents body scroll.
    <div className="flex h-screen w-full bg-[#0B0C15] text-white overflow-hidden font-sans">
      
      {/* 1. SIDEBAR */}
      <div 
        className={`transition-all duration-300 ease-in-out border-r border-white/5 bg-[#0F1117] flex-shrink-0 h-full
          ${isSidebarOpen ? 'w-[280px]' : 'w-0 overflow-hidden'}
        `}
      >
         <Sidebar 
            isOpen={isSidebarOpen} 
            user={user}
            activeSessionId={currentSessionId}
            onSessionSelect={setCurrentSessionId}
            onToggle={() => setSidebarOpen(false)}
         />
      </div>

      {/* 2. MAIN CONTENT WRAPPER */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative">
        
        {/* HEADER (Fixed Height) */}
        <div className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[#0B0C15]/80 backdrop-blur-md z-30 flex-shrink-0">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setSidebarOpen(!isSidebarOpen)}
              className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white"
            >
              <Menu size={20} />
            </button>
            <div className="flex items-center gap-2">
               <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                   <LayoutDashboard size={18} className="text-white" />
               </div>
               <span className="font-bold text-lg tracking-tight">Nexus Aurora</span>
            </div>
          </div>
          
          <button 
             onClick={() => signOut(auth)} 
             className="flex items-center gap-2 text-sm text-gray-400 hover:text-red-400 transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5"
          >
             <LogOut size={16} /> Logout
          </button>
        </div>

        {/* CHAT AREA (Flex-1 fills remaining height, overflow-hidden keeps scroll internal) */}
        <div className="flex-1 overflow-hidden relative bg-[#0B0C15]">
          <ChatInterface sessionId={currentSessionId} />
        </div>
      </div>
    </div>
  );
}