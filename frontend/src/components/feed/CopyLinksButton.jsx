import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Share2, Clock, RefreshCw, CheckCircle2 } from 'lucide-react';
import CopyLinksModal from '../modals/CopyLinksModal';
import { fetchPostLinksApi } from '../../api/contentApi';

const COOLDOWN_MS = 15 * 60 * 1000; // 15 Menit Cooldown Peninjauan Algoritma Platform

function parseUploadTimestamp(item) {
  if (item?.uploaded_timestamps && Object.keys(item.uploaded_timestamps).length > 0) {
    const timestamps = Object.values(item.uploaded_timestamps).map((ts) => {
      if (typeof ts === 'number') return ts > 1e11 ? ts : ts * 1000;
      const parsed = new Date(String(ts).replace(' ', 'T')).getTime();
      return isNaN(parsed) ? 0 : parsed;
    });
    const maxTs = Math.max(...timestamps, 0);
    if (maxTs > 0) return maxTs;
  }
  if (item?.created_at) {
    return typeof item.created_at === 'number' && item.created_at < 1e11 ? item.created_at * 1000 : item.created_at;
  }
  if (item?.mtime) {
    return typeof item.mtime === 'number' && item.mtime < 1e11 ? item.mtime * 1000 : item.mtime;
  }
  return Date.now();
}

function formatCountdown(totalSeconds) {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

export default function CopyLinksButton({ item, account, onToast, size = 'sm', className = '' }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [localPostUrls, setLocalPostUrls] = useState(item?.post_urls || {});
  const [isSearching, setIsSearching] = useState(false);
  const [searchAttempted, setSearchAttempted] = useState(false);

  // Sync postUrls if item prop changes
  useEffect(() => {
    if (item?.post_urls) {
      setLocalPostUrls(item.post_urls);
    }
  }, [item?.post_urls]);

  const hasLinks = localPostUrls && Object.values(localPostUrls).some((u) => u && String(u).trim().length > 5);

  // Cooldown calculation
  const [remainingSec, setRemainingSec] = useState(() => {
    if (hasLinks) return 0;
    const uploadTs = parseUploadTimestamp(item);
    const elapsed = Date.now() - uploadTs;
    return Math.max(0, Math.ceil((COOLDOWN_MS - elapsed) / 1000));
  });

  // Countdown timer ticker
  useEffect(() => {
    if (hasLinks) {
      setRemainingSec(0);
      return;
    }

    const updateTimer = () => {
      const uploadTs = parseUploadTimestamp(item);
      const elapsed = Date.now() - uploadTs;
      const leftSec = Math.max(0, Math.ceil((COOLDOWN_MS - elapsed) / 1000));
      setRemainingSec(leftSec);
    };

    updateTimer();
    const timer = setInterval(updateTimer, 1000);
    return () => clearInterval(timer);
  }, [item, hasLinks]);

  // Background auto-fetch when countdown hits 0
  const autoSearchRef = useRef(false);

  const executeAutoSearch = useCallback(async () => {
    if (isSearching || hasLinks || !item) return;
    setIsSearching(true);
    setSearchAttempted(true);

    try {
      const res = await fetchPostLinksApi(
        account || item.account || 'default',
        item.item_key || item.name,
        item.caption || '',
        item.category || '',
        item.uploaded_platforms || ['tiktok', 'instagram', 'facebook'],
        false
      );

      if (res?.status === 'success' && res?.data?.urls) {
        const foundUrls = res.data.urls;
        if (Object.values(foundUrls).some((u) => u && String(u).trim().length > 5)) {
          setLocalPostUrls(foundUrls);
          if (item) {
            item.post_urls = { ...(item.post_urls || {}), ...foundUrls };
          }
          if (onToast) {
            onToast(`✓ Link postingan untuk '${item.name}' otomatis ditemukan dan siap disalin!`, 'success');
          }
        }
      }
    } catch (err) {
      console.warn('Auto link search failed:', err);
    } finally {
      setIsSearching(false);
    }
  }, [account, item, hasLinks, isSearching, onToast]);

  useEffect(() => {
    if (!hasLinks && remainingSec === 0 && !autoSearchRef.current && !isSearching) {
      autoSearchRef.current = true;
      executeAutoSearch();
    }
  }, [remainingSec, hasLinks, isSearching, executeAutoSearch]);

  const handleClick = (e) => {
    e.stopPropagation();
    if (remainingSec > 0 && !hasLinks) {
      if (onToast) {
        onToast(`Konten dalam masa peninjauan platform (~15m). Sisa waktu: ${formatCountdown(remainingSec)}`, 'info');
      }
      return;
    }
    setModalOpen(true);
  };

  const handleManualReSearch = (e) => {
    e.stopPropagation();
    autoSearchRef.current = false;
    executeAutoSearch();
  };

  // Large Button (For Inspector/Modal or Detail View)
  if (size === 'lg') {
    if (hasLinks) {
      return (
        <>
          <div className={`space-y-3 ${className}`}>
            <button
              type="button"
              onClick={handleClick}
              className="w-full py-2.5 px-4 rounded-xl font-medium text-xs flex items-center justify-center gap-2 transition-all shadow-md bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white border border-emerald-500/50 hover:shadow-emerald-900/30 active:scale-[0.98] cursor-pointer"
              title="Klik untuk melihat dan menyalin link postingan"
            >
              <Share2 className="w-4 h-4" />
              <span>📋 Salin Link Postingan (TikTok, IG, FB)</span>
            </button>
          </div>

          <CopyLinksModal
            isOpen={modalOpen}
            onClose={() => setModalOpen(false)}
            item={item}
            account={account || item?.account}
            onToast={onToast}
          />
        </>
      );
    }

    if (isSearching) {
      return (
        <div className={`space-y-3 ${className}`}>
          <button
            type="button"
            disabled
            className="w-full py-2.5 px-4 rounded-xl font-medium text-xs flex items-center justify-center gap-2 shadow-xs bg-cyan-950/70 text-cyan-300 border border-cyan-700/60 opacity-90 cursor-wait"
            title="Sedang memindai tautan publik postingan di latar belakang..."
          >
            <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
            <span>🔍 Sedang Mencari Link di Latar Belakang...</span>
          </button>
        </div>
      );
    }

    if (remainingSec > 0) {
      return (
        <div className={`space-y-3 ${className}`}>
          <button
            type="button"
            onClick={handleClick}
            className="w-full py-2.5 px-4 rounded-xl font-medium text-xs flex items-center justify-center gap-2 shadow-xs bg-zinc-900/90 text-amber-300/90 border border-amber-800/40 hover:border-amber-700/60 transition cursor-pointer"
            title="Konten dalam masa peninjauan platform (~15m). Pencarian link akan dimulai otomatis saat waktu habis."
          >
            <Clock className="w-4 h-4 text-amber-400 animate-pulse" />
            <span>⏳ Menunggu Peninjauan Platform ({formatCountdown(remainingSec)})</span>
          </button>
        </div>
      );
    }

    // Cooldown finished & search attempted but links not yet found
    return (
      <>
        <div className={`space-y-3 ${className}`}>
          <button
            type="button"
            onClick={handleManualReSearch}
            className="w-full py-2.5 px-4 rounded-xl font-medium text-xs flex items-center justify-center gap-2 transition-all shadow-sm bg-zinc-900 hover:bg-emerald-950 text-zinc-200 hover:text-emerald-300 border border-zinc-700 hover:border-emerald-600 active:scale-[0.98] cursor-pointer"
            title="Link belum terindeks di profil. Klik untuk memindai ulang."
          >
            <RefreshCw className="w-4 h-4 text-emerald-400" />
            <span>🔍 Cari Ulang Link Postingan</span>
          </button>
        </div>

        <CopyLinksModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          item={item}
          account={account || item?.account}
          onToast={onToast}
        />
      </>
    );
  }

  // Compact size for Feed Card / Grid View
  if (hasLinks) {
    return (
      <>
        <button
          type="button"
          onClick={handleClick}
          className={`px-2.5 py-1 rounded-lg text-[10px] font-medium flex items-center gap-1.5 transition-all shadow-sm bg-emerald-950/80 text-emerald-300 border border-emerald-600/70 hover:bg-emerald-900 hover:border-emerald-500 active:scale-95 cursor-pointer ${className}`}
          title="Salin tautan postingan (TikTok, Instagram, Facebook)"
        >
          <Share2 className="w-3 h-3 text-emerald-400" />
          <span>Salin Link</span>
        </button>

        <CopyLinksModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          item={item}
          account={account || item?.account}
          onToast={onToast}
        />
      </>
    );
  }

  if (isSearching) {
    return (
      <button
        type="button"
        disabled
        className={`px-2.5 py-1 rounded-lg text-[10px] font-medium flex items-center gap-1.5 shadow-sm bg-cyan-950/80 text-cyan-300 border border-cyan-700/60 opacity-90 cursor-wait ${className}`}
        title="Sedang mencari tautan postingan di latar belakang..."
      >
        <RefreshCw className="w-3 h-3 animate-spin text-cyan-400" />
        <span>Mencari Link...</span>
      </button>
    );
  }

  if (remainingSec > 0) {
    return (
      <button
        type="button"
        onClick={handleClick}
        className={`px-2.5 py-1 rounded-lg text-[10px] font-mono font-medium flex items-center gap-1.5 shadow-sm bg-zinc-900/90 text-amber-300/90 border border-amber-800/50 hover:border-amber-600/70 transition cursor-pointer ${className}`}
        title={`Konten dalam masa peninjauan platform (~15m). Sisa waktu: ${formatCountdown(remainingSec)}`}
      >
        <Clock className="w-3 h-3 text-amber-400 animate-pulse" />
        <span>⏳ {formatCountdown(remainingSec)}</span>
      </button>
    );
  }

  // Cooldown expired, links not found yet
  return (
    <>
      <button
        type="button"
        onClick={handleManualReSearch}
        className={`px-2.5 py-1 rounded-lg text-[10px] font-medium flex items-center gap-1.5 transition-all shadow-sm bg-zinc-800/90 hover:bg-emerald-950 hover:text-emerald-300 text-zinc-300 border border-zinc-700 hover:border-emerald-600 active:scale-95 cursor-pointer ${className}`}
        title="Link belum ditemukan di profil. Klik untuk mencari ulang sekarang."
      >
        <RefreshCw className="w-3 h-3 text-emerald-400" />
        <span>Cari Ulang</span>
      </button>

      <CopyLinksModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        item={item}
        account={account || item?.account}
        onToast={onToast}
      />
    </>
  );
}
