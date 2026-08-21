import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Clock,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Minimize2,
  Maximize2,
  X,
  Terminal,
  Copy,
  Check,
  Film,
  Image as ImageIcon,
  Layers,
  Bot
} from 'lucide-react';

export default function PublishProgressModal({
  isOpen,
  onClose,
  sessionData,
  isMinimized,
  setIsMinimized
}) {
  const [autoScroll, setAutoScroll] = useState(true);
  const [copiedLog, setCopiedLog] = useState(false);
  const [logsExpanded, setLogsExpanded] = useState(true);
  const terminalEndRef = useRef(null);

  // Auto scroll terminal logs to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [sessionData?.logs, autoScroll, isOpen]);

  if (!isOpen || !sessionData) return null;

  const {
    account = 'default',
    item_name = 'Konten',
    category = 'Video',
    status = 'running',
    percent = 0,
    current_step = 'Menyiapkan proses publish...',
    platforms = {},
    logs = [],
    error_msg = null,
    started_at
  } = sessionData;

  const isCompleted = status === 'completed';
  const isFailed = status === 'failed';

  const handleCopyLogs = () => {
    const text = logs
      .map((l) => `[${l.timestamp || l.time || ''}] [${(l.platform || 'SYS').toUpperCase()}] ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopiedLog(true);
    setTimeout(() => setCopiedLog(false), 2000);
  };

  const getCategoryIcon = (cat) => {
    switch (cat?.toLowerCase()) {
      case 'video':
        return <Film className="w-4 h-4 text-emerald-400" />;
      case 'poster':
        return <ImageIcon className="w-4 h-4 text-emerald-400" />;
      case 'carousel':
        return <Layers className="w-4 h-4 text-emerald-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-emerald-400" />;
    }
  };

  const getPlatformBrand = (pKey) => {
    const key = pKey.toLowerCase();
    if (key.includes('tiktok')) {
      return {
        name: 'TikTok Studio',
        iconColor: 'text-zinc-200',
        badge: 'bg-zinc-800 text-zinc-300 border-zinc-700',
      };
    }
    if (key.includes('instagram')) {
      return {
        name: 'Instagram',
        iconColor: 'text-zinc-200',
        badge: 'bg-zinc-800 text-zinc-300 border-zinc-700',
      };
    }
    if (key.includes('facebook')) {
      return {
        name: 'Facebook Fanpage',
        iconColor: 'text-zinc-200',
        badge: 'bg-zinc-800 text-zinc-300 border-zinc-700',
      };
    }
    return {
      name: pKey,
      iconColor: 'text-zinc-300',
      badge: 'bg-zinc-800 text-zinc-300 border-zinc-700',
    };
  };

  // Minimized Floating Pill
  if (isMinimized) {
    return (
      <div
        onClick={() => setIsMinimized(false)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-3.5 px-4 py-3 bg-zinc-900/95 backdrop-blur-md border border-zinc-700 rounded-2xl shadow-2xl cursor-pointer hover:border-emerald-500 hover:scale-105 transition-all duration-200 group"
      >
        <div className="relative flex items-center justify-center w-8 h-8 rounded-xl bg-zinc-950 border border-zinc-800 text-emerald-400">
          {isCompleted ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 animate-bounce" />
          ) : isFailed ? (
            <AlertCircle className="w-5 h-5 text-rose-400" />
          ) : (
            <Bot className="w-5 h-5 text-emerald-400 animate-pulse" />
          )}
          {!isCompleted && !isFailed && (
            <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
          )}
        </div>

        <div className="flex flex-col max-w-[200px]">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-zinc-200 truncate">
            <span className="text-emerald-400 font-mono">{percent}%</span>
            <span className="truncate">{item_name}</span>
          </div>
          <span className="text-[10px] text-zinc-400 truncate">{current_step}</span>
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsMinimized(false);
          }}
          className="p-1.5 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-800 transition"
          title="Buka Layar Penuh"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs transition-all duration-300 animate-fadeIn">
      <div className="relative w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Subtle accent top border */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-emerald-500 to-cyan-500" />

        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-950/50">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-zinc-950 border border-zinc-800 text-emerald-400 shadow-inner">
              {isCompleted ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              ) : isFailed ? (
                <AlertCircle className="w-5 h-5 text-rose-400" />
              ) : (
                <Bot className="w-5 h-5 text-emerald-400 animate-pulse" />
              )}
              {!isCompleted && !isFailed && (
                <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
              )}
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-zinc-100 tracking-wide">
                  {isCompleted ? 'Penerbitan Selesai!' : isFailed ? 'Penerbitan Gagal' : 'Sedang Mempublikasikan...'}
                </h3>
                <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700">
                  {account}
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                {getCategoryIcon(category)}
                <span className="font-medium text-zinc-300">{category}</span>
                <span>•</span>
                <span className="truncate max-w-[240px] text-zinc-300">{item_name}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setIsMinimized(true)}
              className="p-2 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/80 rounded-xl transition cursor-pointer"
              title="Kecilkan ke pojok (Minimize)"
            >
              <Minimize2 className="w-4 h-4" />
            </button>
            {(isCompleted || isFailed) && (
              <button
                onClick={onClose}
                className="p-2 text-zinc-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-xl transition cursor-pointer"
                title="Tutup Modal"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 custom-scrollbar bg-zinc-900">
          
          {/* Progress Header & Animated Bar */}
          <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 shadow-inner">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                  Progress Pipeline
                </span>
                {isCompleted && (
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                    SELESAI 100%
                  </span>
                )}
              </div>
              <span className="text-sm font-extrabold text-emerald-400 tracking-tight font-mono">
                {percent}%
              </span>
            </div>

            {/* Progress track */}
            <div className="w-full h-2.5 bg-zinc-800/80 rounded-full overflow-hidden p-0.5 border border-zinc-700/50">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400 transition-all duration-500 ease-out relative"
                style={{ width: `${Math.max(5, percent)}%` }}
              >
                {!isCompleted && !isFailed && (
                  <div className="absolute inset-0 bg-white/20 animate-pulse" />
                )}
              </div>
            </div>

            {/* Active status step label */}
            <div className="mt-2.5 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-zinc-300 font-medium">
                {!isCompleted && !isFailed && (
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                )}
                <span className="text-zinc-200 font-mono text-[11px]">{current_step}</span>
              </div>
            </div>
          </div>

          {/* Platforms Status Grid */}
          <div>
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2.5">
              Platform Target
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(platforms).map(([pKey, pState]) => {
                const brand = getPlatformBrand(pKey);
                const isPlatDone = pState.status === 'completed';
                const isPlatFail = pState.status === 'failed';
                const isPlatActive = pState.status === 'in_progress' || pState.status === 'running';

                return (
                  <div
                    key={pKey}
                    className={`p-3.5 rounded-xl border bg-zinc-950 flex flex-col justify-between transition-all duration-200 ${
                      isPlatActive
                        ? 'border-emerald-500/50 ring-1 ring-emerald-500/30'
                        : isPlatDone
                        ? 'border-emerald-500/30'
                        : isPlatFail
                        ? 'border-rose-500/30'
                        : 'border-zinc-800'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-zinc-200">{brand.name}</span>
                        {isPlatDone ? (
                          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                            <Check className="w-3 h-3" /> Berhasil
                          </span>
                        ) : isPlatFail ? (
                          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40">
                            <AlertCircle className="w-3 h-3" /> Gagal
                          </span>
                        ) : isPlatActive ? (
                          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse">
                            Memproses...
                          </span>
                        ) : (
                          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700">
                            Menunggu
                          </span>
                        )}
                      </div>

                      <div className="text-[11px] text-zinc-400 font-mono line-clamp-2 min-h-[32px]">
                        {pState.current_step || 'Menunggu antrean...'}
                      </div>
                    </div>

                    <div className="mt-3 pt-2 border-t border-zinc-800/80">
                      {pState.post_url ? (
                        <a
                          href={pState.post_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 hover:text-emerald-300 hover:underline"
                        >
                          <ExternalLink className="w-3 h-3" /> Buka Postingan
                        </a>
                      ) : (
                        <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${
                              isPlatDone
                                ? 'bg-emerald-400'
                                : isPlatFail
                                ? 'bg-rose-400'
                                : isPlatActive
                                ? 'bg-cyan-400'
                                : 'bg-zinc-700'
                            }`}
                            style={{ width: `${pState.percent || 0}%` }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Live Monospace Terminal Log Viewer */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-950 shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-3.5 py-2.5 bg-zinc-900/90 border-b border-zinc-800 text-xs">
              <div className="flex items-center gap-2 font-mono text-zinc-300">
                <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-semibold text-[11px]">Live Bot Terminal Logs</span>
                <span className="px-1.5 py-0.2 text-[10px] rounded bg-zinc-800 text-zinc-400">
                  {logs.length} baris
                </span>
              </div>

              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1 text-[11px] text-zinc-400 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={autoScroll}
                    onChange={(e) => setAutoScroll(e.target.checked)}
                    className="w-3 h-3 rounded bg-zinc-800 border-zinc-700 text-emerald-500 focus:ring-0"
                  />
                  Auto-scroll
                </label>

                <button
                  onClick={handleCopyLogs}
                  className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-zinc-200 px-2 py-0.5 rounded hover:bg-zinc-800 transition cursor-pointer"
                  title="Salin Log"
                >
                  {copiedLog ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  {copiedLog ? 'Tersalin' : 'Salin'}
                </button>

                <button
                  onClick={() => setLogsExpanded(!logsExpanded)}
                  className="text-zinc-400 hover:text-zinc-200 p-0.5 rounded hover:bg-zinc-800 transition cursor-pointer"
                >
                  {logsExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {logsExpanded && (
              <div className="p-3 font-mono text-xs max-h-48 overflow-y-auto space-y-1 select-text custom-scrollbar bg-black/60">
                {logs.length === 0 ? (
                  <div className="text-zinc-500 italic text-[11px]">Menghubungkan ke log stream bot...</div>
                ) : (
                  logs.map((l, idx) => {
                    const typeColor =
                      l.type === 'error'
                        ? 'text-rose-400'
                        : l.type === 'success'
                        ? 'text-emerald-400 font-semibold'
                        : l.type === 'warn'
                        ? 'text-amber-400'
                        : l.type === 'step'
                        ? 'text-cyan-300'
                        : 'text-zinc-300';

                    return (
                      <div key={idx} className="leading-relaxed flex items-start gap-2 hover:bg-zinc-900/60 px-1 rounded">
                        <span className="text-zinc-600 select-none text-[10px] mt-0.5">[{l.timestamp || l.time}]</span>
                        <span className="text-[10px] font-bold select-none uppercase text-zinc-400">
                          [{l.platform || 'SYS'}]
                        </span>
                        <span className={`flex-1 break-words text-[11px] ${typeColor}`}>
                          {l.message}
                        </span>
                      </div>
                    );
                  })
                )}
                <div ref={terminalEndRef} />
              </div>
            )}
          </div>

          {/* Celebratory Completion Box or Error Alert */}
          {isCompleted && (
            <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-emerald-200 flex items-center justify-between shadow-lg animate-fadeIn">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-emerald-300">Penerbitan Konten Berhasil!</h4>
                  <p className="text-xs text-emerald-400/80">
                    Semua platform target telah berhasil dipublikasikan.
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="px-4 py-2 text-xs font-bold rounded-xl bg-emerald-500 hover:bg-emerald-400 text-zinc-950 shadow-lg shadow-emerald-950/50 transition-all duration-150 cursor-pointer"
              >
                Selesai & Tutup
              </button>
            </div>
          )}

          {isFailed && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-200 flex items-center justify-between shadow-lg">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-6 h-6 text-rose-400 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-bold text-rose-300">Terjadi Kendala Saat Upload</h4>
                  <p className="text-xs text-rose-400/80">{error_msg || 'Periksa detail log di atas.'}</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="px-4 py-2 text-xs font-bold rounded-xl bg-rose-600 hover:bg-rose-500 text-white transition-all cursor-pointer"
              >
                Tutup
              </button>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-3.5 border-t border-zinc-800 bg-zinc-950/50 text-xs text-zinc-400">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400"></span>
            <span className="text-zinc-400">Studio Multi-Content Pipeline</span>
          </div>

          <div className="flex items-center gap-2">
            {!isCompleted && !isFailed ? (
              <span className="italic text-zinc-500 text-[11px]">Browser visual sedang berjalan di latar belakang...</span>
            ) : (
              <button
                onClick={onClose}
                className="px-4 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 font-semibold transition cursor-pointer"
              >
                Tutup
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
