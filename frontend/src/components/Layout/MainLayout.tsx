import { useState } from 'react';
import { DomainType, DOMAIN_CONFIGS } from '../../config/domains';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ChatInterface } from '../Chat/ChatInterface';
import { FileUploadZone } from '../Upload/FileUploadZone';

interface MainLayoutProps {
  user: any;
  currentDomain: DomainType;
  onDomainChange: (domain: DomainType) => void;
}

export function MainLayout({ user, currentDomain, onDomainChange }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [chatActive, setChatActive] = useState(false); // <--- THE FIX

  const domainConfig = DOMAIN_CONFIGS[currentDomain] || DOMAIN_CONFIGS['general'];

  const handleFileUpload = (file: File) => {
    setUploadedFile(file);
    setChatActive(true);
  };

  return (
    <div className="min-h-screen bg-[#0B0C15] relative overflow-hidden">
      <div className="relative z-10 flex h-screen">
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          user={user}
          activeSessionId={activeSessionId}
          onSessionSelect={(id) => { setActiveSessionId(id); setChatActive(true); }}
          currentDomain={currentDomain}
        />

        <div className="flex-1 flex flex-col">
          <Header user={user} currentDomain={currentDomain} onDomainChange={onDomainChange} />
          <main className="flex-1 overflow-hidden">
            {!activeSessionId && !uploadedFile && !chatActive ? (
              <FileUploadZone onFileUpload={handleFileUpload} currentDomain={currentDomain} />
            ) : (
              <ChatInterface
                sessionId={activeSessionId}
                uploadedFile={uploadedFile}
                currentDomain={currentDomain}
                onDomainDetected={onDomainChange}
                onFileProcessed={() => setUploadedFile(null)} 
              />
            )}
          </main>
        </div>
      </div>
    </div>
  );
}