import React, { useState, useEffect, useCallback } from 'react';
import { 
  X, 
  Copy, 
  Check, 
  ExternalLink, 
  RefreshCw, 
  Link2, 
  Sparkles, 
  AlertCircle,
  FileText,
  Share2
} from 'lucide-react';
import { fetchPostLinksApi, updatePostLinksApi } from '../../api/contentApi';

const PLATFORM_CONFIG = [
  {
    id: 'tiktok',
    name: 'TikTok',
    color: 'from-pink-500/20 to-rose-500/10 text-pink-400 border-pink-500/30',
    badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
    icon: '🎵',
    placeholder: 'https://www.tiktok.com/@username/video/...'
  },
  {
    id: 'instagram',
    name: 'Instagram',
    color: 'from-fuchsia-500/20 to-purple-500/10 text-fuchsia-400 border-fuchsia-500/30',
    badge: 'bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/20',
    icon: '📷',
    placeholder: 'https://www.instagram.com/p/...'
  },
  {
    id: 'facebook',
    name: 'Facebook',
    color: 'from-blue-500/20 to-indigo-500/10 text-blue-400 border-blue-500/30',
    badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    icon: '📘',
    placeholder: 'https://www.facebook.com/reel/...'
  }
];

export default function CopyLinksModal({ isOpen, onClose, item, account, onToast }) {
  const [loading, setLoading] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [postUrls, setPostUrls] = useState({});
  const [platformStatus, setPlatformStatus] = useState({});
  const [errorMsg, setErrorMsg] = useState(null);

  const scannedKeyRef = React.useRef(null);

  // Initialize postUrls and scan only when modal is newly opened for an item
  useEffect(() => {
    if (isOpen && item) {
      const currentKey = `${account || item.account}_${item.item_key || item.name}`;
      const initialUrls = item.post_urls || {};
      setPostUrls((prev) => (Object.keys(prev).length > 0 ? prev : initialUrls));
      setErrorMsg(null);
      
      if (scannedKeyRef.current !== currentKey) {
        scannedKeyRef.current = currentKey;
        handleScanLinks(false);
      }
    } else if (!isOpen) {
      scannedKeyRef.current = null;
    }
  }, [isOpen, item?.item_key, item?.name, account]);

  const handleScanLinks = async (forceRefresh = false) => {
    if (!item) return;
    setLoading(true);
    setErrorMsg(null);

    // Set initial searching states
    const initialStatus = {};
    PLATFORM_CONFIG.forEach(p => {
      initialStatus[p.id] = { loading: true, message: `Memindai postingan di ${p.name}...` };
    });
    setPlatformStatus(initialStatus);

    try {
      const res = await fetchPostLinksApi(
        account || item.account || 'default',
        item.item_key || item.name,
        item.caption || '',
        item.category || '',
        ['tiktok', 'instagram', 'facebook'],
        forceRefresh
      );

      if (res?.status === 'success' && res?.data) {
        const found = res.data.urls || {};
        const platformsData = res.data.platforms || {};

        setPostUrls(found);

        const newStatus = {};
        PLATFORM_CONFIG.forEach(p => {
          const pData = platformsData[p.id] || {};
          newStatus[p.id] = {
            loading: false,
            success: pData.success || !!found[p.id],
            message: pData.message || (found[p.id] ? 'Link berhasil ditemukan' : 'Belum ditemukan di profil')
          };
        });
        setPlatformStatus(newStatus);
      } else {
        setErrorMsg(res?.message || 'Gagal memindai link postingan.');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Terjadi kesalahan jaringan.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text, key) => {
    if (!text) return;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }

      if (key === 'all') {
        setCopiedAll(true);
        setTimeout(() => setCopiedAll(false), 2500);
        if (onToast) onToast('📋 Semua link postingan berhasil disalin!', 'success');
      } else {
        setCopiedKey(key);
        setTimeout(() => setCopiedKey(null), 2000);
        if (onToast) onToast(`✓ Link ${key.toUpperCase()} berhasil disalin!`, 'success');
      }
    } catch (err) {
      if (onToast) onToast('Gagal menyalin link: ' + err.message, 'error');
    }
  };

  const generateShareSummary = useCallback(() => {
    const lines = [];
    if (postUrls.tiktok) lines.push(`🎵 TikTok:\n${postUrls.tiktok}`);
    if (postUrls.instagram) lines.push(`📷 Instagram:\n${postUrls.instagram}`);
    if (postUrls.facebook) lines.push(`📘 Facebook:\n${postUrls.facebook}`);

    if (lines.length === 0) {
      const accClean = (account || item?.account || '').toLowerCase().replace(/\s+/g, '');
      const accSlug = (account || item?.account || '').toLowerCase().replace(/\s+/g, '_');
      return `TikTok:\nhttps://www.tiktok.com/@${accClean}\n\nInstagram:\nhttps://www.instagram.com/${accSlug}/\n\nFacebook:\nhttps://www.facebook.com/${accClean}`;
    }
    return lines.join('\n\n');
  }, [postUrls, account, item]);

  if (!isOpen || !item) return null;

  const foundCount = Object.values(postUrls).filter(Boolean).length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-xl bg-[#0e0e12] border border-zinc-800/90 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800/80 bg-zinc-900/40">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Share2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                Salin Link Postingan Publik
                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  {item.category || 'Konten'}
                </span>
              </h3>
              <p className="text-xs text-zinc-400 truncate max-w-sm">
                {account || item.account} • <span className="text-zinc-300 font-medium">{item.name}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-lg transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5 custom-scrollbar">
          
          {/* Item Caption Preview */}
          {item.caption && (
            <div className="p-3 bg-zinc-900/60 border border-zinc-800/60 rounded-xl">
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-zinc-400 mb-1">
                <FileText className="w-3.5 h-3.5 text-zinc-500" />
                <span>Caption Acuan Pencarian:</span>
              </div>
              <p className="text-xs text-zinc-300 italic line-clamp-2 leading-relaxed">
                "{item.caption}"
              </p>
            </div>
          )}

          {/* Platform Link Rows */}
          <div className="space-y-3">
            {PLATFORM_CONFIG.map((platform) => {
              const url = postUrls[platform.id];
              const pStatus = platformStatus[platform.id] || {};
              const isSearching = loading || pStatus.loading;
              const isCopied = copiedKey === platform.id;

              return (
                <div 
                  key={platform.id}
                  className={`p-3.5 rounded-xl border transition-all ${
                    url 
                      ? 'bg-zinc-900/80 border-zinc-700/70 shadow-sm' 
                      : 'bg-zinc-900/30 border-zinc-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{platform.icon}</span>
                      <span className="text-xs font-semibold text-zinc-200">{platform.name}</span>
                      {url ? (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-1">
                          <Check className="w-2.5 h-2.5" /> Ditemukan
                        </span>
                      ) : isSearching ? (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center gap-1">
                          <RefreshCw className="w-2.5 h-2.5 animate-spin" /> Memindai...
                        </span>
                      ) : (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                          Belum terhubung
                        </span>
                      )}
                    </div>

                    {url && (
                      <a
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[11px] text-zinc-400 hover:text-emerald-400 flex items-center gap-1 transition-colors"
                        title="Buka postingan di tab baru"
                      >
                        <span>Buka</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  {/* URL Display / Copy Input */}
                  <div className="flex items-center gap-2">
                    <div className="flex-1 min-w-0 bg-black/50 border border-zinc-800 rounded-lg px-3 py-2 text-xs font-mono text-zinc-300 truncate select-all">
                      {isSearching ? (
                        <span className="text-zinc-500 italic flex items-center gap-2">
                          <RefreshCw className="w-3 h-3 animate-spin text-emerald-400" />
                          Memindai feed {platform.name}...
                        </span>
                      ) : url ? (
                        <span className="text-emerald-300/90">{url}</span>
                      ) : (
                        <span className="text-zinc-600 italic">Belum ada link yang terdeteksi</span>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={() => copyToClipboard(url, platform.id)}
                      disabled={!url || isSearching}
                      className={`px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all whitespace-nowrap shadow-sm ${
                        !url || isSearching
                          ? 'bg-zinc-800/50 text-zinc-600 border border-zinc-800 cursor-not-allowed'
                          : isCopied
                          ? 'bg-emerald-600 text-white border border-emerald-500 scale-105'
                          : 'bg-zinc-800 hover:bg-emerald-950 hover:text-emerald-300 text-zinc-200 border border-zinc-700/70 hover:border-emerald-700 active:scale-95'
                      }`}
                    >
                      {isCopied ? (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Tersalin!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Salin</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Formatted Share Preview Box */}
          <div className="p-3.5 bg-black/40 border border-zinc-800/80 rounded-xl space-y-2">
            <div className="flex items-center justify-between text-[11px] text-zinc-400 font-medium">
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                Format Salin Lengkap (WhatsApp / Laporan):
              </span>
              <button
                type="button"
                onClick={() => copyToClipboard(generateShareSummary(), 'all')}
                className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition-colors"
              >
                {copiedAll ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                <span>{copiedAll ? 'Tersalin!' : 'Salin Semua Format'}</span>
              </button>
            </div>
            <pre className="p-2.5 bg-zinc-950/80 border border-zinc-900 rounded-lg text-[11px] font-mono text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-28 overflow-y-auto custom-scrollbar">
              {generateShareSummary()}
            </pre>
          </div>

          {errorMsg && (
            <div className="p-3 bg-red-950/30 border border-red-800/50 rounded-xl flex items-center gap-2 text-xs text-red-300">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-zinc-800/80 bg-zinc-900/40">
          <button
            type="button"
            onClick={() => handleScanLinks(true)}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl text-xs font-medium text-zinc-400 hover:text-zinc-200 bg-zinc-800/60 hover:bg-zinc-800 border border-zinc-700/50 flex items-center gap-2 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
            <span>Pindai Ulang Live</span>
          </button>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => copyToClipboard(generateShareSummary(), 'all')}
              disabled={foundCount === 0}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-md ${
                copiedAll
                  ? 'bg-emerald-600 text-white border border-emerald-500'
                  : foundCount > 0
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white border border-emerald-500/40 active:scale-95'
                  : 'bg-zinc-800 text-zinc-500 border border-zinc-700/50 cursor-not-allowed'
              }`}
            >
              {copiedAll ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>Semua Link Tersalin!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span>Salin Semua Link ({foundCount}/3)</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800 hover:bg-zinc-700/80 border border-zinc-700/70 transition-all"
            >
              Tutup
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
