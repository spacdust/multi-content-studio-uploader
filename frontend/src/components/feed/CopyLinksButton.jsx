import React, { useState, useEffect } from 'react';
import { Copy, Check, Clock, ExternalLink } from 'lucide-react';

const TEN_MINUTES_MS = 10 * 60 * 1000; // 10 minutes in milliseconds

export default function CopyLinksButton({ item, onToast, size = 'sm', className = '' }) {
  const [copied, setCopied] = useState(false);
  const [now, setNow] = useState(Date.now());

  // Determine latest upload timestamp
  const timestamps = item?.uploaded_timestamps || {};
  const timeValues = Object.values(timestamps).filter(Boolean);
  
  let latestUploadTime = 0;
  if (timeValues.length > 0) {
    // Pick the most recent upload timestamp
    timeValues.forEach((tsStr) => {
      // Parse YYYY-MM-DD HH:MM:SS or ISO string
      const parsed = new Date(tsStr.replace(/-/g, '/')).getTime();
      if (!isNaN(parsed) && parsed > latestUploadTime) {
        latestUploadTime = parsed;
      }
    });
  } else if (item?.status === 'UPLOADED' && item?.mtime) {
    // Fallback to item mtime if timestamp dict isn't present
    latestUploadTime = typeof item.mtime === 'number' ? (item.mtime > 1e11 ? item.mtime : item.mtime * 1000) : 0;
  }

  const remainingMs = latestUploadTime > 0 ? Math.max(0, latestUploadTime + TEN_MINUTES_MS - now) : 0;
  const isCooldown = remainingMs > 0;

  // Live timer tick every second while in cooldown
  useEffect(() => {
    if (!isCooldown) return;
    const interval = setInterval(() => {
      setNow(Date.now());
    }, 1000);
    return () => clearInterval(interval);
  }, [isCooldown]);

  const minutes = Math.floor(remainingMs / 60000);
  const seconds = Math.floor((remainingMs % 60000) / 1000);
  const countdownFormatted = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  const postUrls = item?.post_urls || {};

  const handleCopy = async (e) => {
    e.stopPropagation();
    if (isCooldown) {
      if (onToast) {
        onToast(`⏳ Link postingan sedang diproses platform. Tersedia dalam ${countdownFormatted}.`, 'info');
      }
      return;
    }

    const ttLink = postUrls.tiktok || 'https://www.tiktok.com/';
    const igLink = postUrls.instagram || 'https://www.instagram.com/';
    const fbLink = postUrls.facebook || 'https://www.facebook.com/';

    const formattedText = `TikTok:\n${ttLink}\n\nInstagram:\n${igLink}\n\nFacebook:\n${fbLink}`;

    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(formattedText);
      } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = formattedText;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }

      setCopied(true);
      if (onToast) {
        onToast('✓ Semua link postingan (TikTok, IG, FB) berhasil disalin ke clipboard!', 'success');
      }
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      if (onToast) {
        onToast('Gagal menyalin link ke clipboard: ' + err.message, 'error');
      }
    }
  };

  if (size === 'lg') {
    return (
      <div className={`space-y-3 ${className}`}>
        <button
          type="button"
          onClick={handleCopy}
          disabled={isCooldown}
          className={`w-full py-2.5 px-4 rounded-xl font-medium text-xs flex items-center justify-center gap-2 transition-all shadow-md ${
            isCooldown
              ? 'bg-amber-950/30 text-amber-300 border border-amber-800/50 cursor-not-allowed opacity-90'
              : copied
              ? 'bg-emerald-600 text-white border border-emerald-500 shadow-emerald-950/50'
              : 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white border border-emerald-500/50 hover:shadow-emerald-900/30 active:scale-[0.98]'
          }`}
          title={isCooldown ? `Link masih dalam proses indexing platform. Selesai dalam ${countdownFormatted}` : 'Salin format TikTok, Instagram, & Facebook ke clipboard'}
        >
          {isCooldown ? (
            <>
              <Clock className="w-3.5 h-3.5 animate-spin text-amber-400" />
              <span>⏳ Salin Link (Tersedia dlm {countdownFormatted})</span>
            </>
          ) : copied ? (
            <>
              <Check className="w-4 h-4 text-white" />
              <span>✓ Link Tersalin ke Clipboard!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>📋 Salin Semua Link Postingan</span>
            </>
          )}
        </button>
      </div>
    );
  }

  // Default compact size for Feed Card
  return (
    <button
      type="button"
      onClick={handleCopy}
      disabled={isCooldown}
      className={`px-2 py-1 rounded-lg text-[10px] font-medium flex items-center gap-1.5 transition-all ${
        isCooldown
          ? 'bg-amber-950/40 text-amber-300/90 border border-amber-800/40 cursor-not-allowed'
          : copied
          ? 'bg-emerald-600 text-white border border-emerald-500 scale-105'
          : 'bg-zinc-800/90 hover:bg-emerald-950 hover:text-emerald-300 text-zinc-300 border border-zinc-700/60 hover:border-emerald-700/60 active:scale-95 shadow-sm'
      } ${className}`}
      title={isCooldown ? `Tautan siap dalam ${countdownFormatted}` : 'Salin link TikTok, Instagram, Facebook'}
    >
      {isCooldown ? (
        <>
          <Clock className="w-2.5 h-2.5 text-amber-400 animate-pulse" />
          <span>Link ({countdownFormatted})</span>
        </>
      ) : copied ? (
        <>
          <Check className="w-2.5 h-2.5 text-emerald-300" />
          <span>Tersalin!</span>
        </>
      ) : (
        <>
          <Copy className="w-2.5 h-2.5 text-zinc-400" />
          <span>Salin Link</span>
        </>
      )}
    </button>
  );
}
