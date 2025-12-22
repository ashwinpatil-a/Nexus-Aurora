import { useState, useCallback } from 'react';
import { Upload, FileText, Database, Image as ImageIcon, AlertCircle } from 'lucide-react';
import { DomainType, DOMAIN_CONFIGS } from '../../config/domains';

interface FileUploadZoneProps {
  onFileUpload: (file: File) => void;
  currentDomain: DomainType;
}

export function FileUploadZone({ onFileUpload, currentDomain }: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const domainConfig = DOMAIN_CONFIGS[currentDomain];

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const validateFile = (file: File): boolean => {
    const maxSize = 100 * 1024 * 1024;
    const allowedTypes = [
      'text/csv',
      'application/json',
      'application/pdf',
      'image/png',
      'image/jpeg',
      'text/plain',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];

    if (file.size > maxSize) {
      setError('File size must be less than 100MB');
      return false;
    }

    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(csv|json|pdf|png|jpg|jpeg|txt|xls|xlsx)$/i)) {
      setError('Invalid file type. Please upload CSV, JSON, PDF, or image files.');
      return false;
    }

    setError(null);
    return true;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file && validateFile(file)) {
      onFileUpload(file);
    }
  }, [onFileUpload]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      onFileUpload(file);
    }
  };

  return (
    <div className="h-full flex items-center justify-center p-8">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-8">
          <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 text-transparent bg-clip-text">
            Welcome to Nexus Aurora
          </h2>
          <p className="text-gray-400 text-lg">
            Upload your data to unlock intelligent, privacy-first analysis
          </p>
        </div>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-2xl p-12 transition-all ${
            isDragging
              ? 'border-cyan-500 bg-cyan-500/10'
              : 'border-white/20 bg-white/5 hover:border-cyan-500/50 hover:bg-white/10'
          }`}
        >
          <div className="flex flex-col items-center justify-center space-y-6">
            <div className="relative">
              <div
                className="w-24 h-24 rounded-full flex items-center justify-center transition-all"
                style={{
                  backgroundColor: `${domainConfig.color}20`,
                  border: `2px solid ${domainConfig.color}40`
                }}
              >
                <Upload
                  className="w-12 h-12 transition-all"
                  style={{ color: domainConfig.color }}
                />
              </div>
              <div
                className="absolute -inset-2 rounded-full blur-xl opacity-30 animate-pulse"
                style={{ backgroundColor: domainConfig.color }}
              />
            </div>

            <div className="text-center">
              <p className="text-xl font-semibold text-white mb-2">
                Drop your files here
              </p>
              <p className="text-gray-400 mb-4">
                or click to browse
              </p>
              <label className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-medium hover:from-cyan-600 hover:to-blue-600 cursor-pointer transition-all shadow-lg shadow-cyan-500/20">
                <Upload className="w-5 h-5" />
                Select File
                <input
                  type="file"
                  onChange={handleFileSelect}
                  className="hidden"
                  accept=".csv,.json,.pdf,.png,.jpg,.jpeg,.txt,.xls,.xlsx"
                />
              </label>
            </div>

            {error && (
              <div className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <div className="flex items-center gap-8 pt-6">
              <div className="flex items-center gap-2 text-gray-400">
                <FileText className="w-5 h-5" />
                <span className="text-sm">CSV, Excel</span>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <Database className="w-5 h-5" />
                <span className="text-sm">JSON</span>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <ImageIcon className="w-5 h-5" />
                <span className="text-sm">Images</span>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <FileText className="w-5 h-5" />
                <span className="text-sm">PDF</span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center mb-3">
              <span className="text-2xl">🔒</span>
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">Zero-Trust Privacy</h3>
            <p className="text-xs text-gray-400">
              PII scrubbed locally before cloud analysis
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center mb-3">
              <span className="text-2xl">🧠</span>
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">Auto-Adaptive</h3>
            <p className="text-xs text-gray-400">
              Chameleon engine detects domain automatically
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center mb-3">
              <span className="text-2xl">⚡</span>
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">Enterprise-Grade</h3>
            <p className="text-xs text-gray-400">
              Multi-agent swarm for accurate analysis
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
