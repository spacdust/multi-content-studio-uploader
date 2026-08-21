import React, { useState } from 'react';
import { Copy, Share2, Link2, Check } from 'lucide-react';
import CopyLinksModal from '../modals/CopyLinksModal';

export default function CopyLinksButton({ item, account, onToast, size = 'sm', className = '' }) {
  const [modalOpen, setModalOpen] = useState(false);

  const handleClick = (e) => {
    e.stopPropagation();
    setModalOpen(true);
  };

  const hasLinks = item?.post_urls && Object.values(item.post_urls).some(Boolean);

  if (size === 'lg') {
    return (
      <>
        <div className={`space-y-3 ${className}`}>
          <button
            type="button"
            onClick={handleClick}
            className="w-full py-2.5 px-4 rounded-xl font-medium text-xs flex items-center justify-center gap-2 transition-all shadow-md bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white border border-emerald-500/50 hover:shadow-emerald-900/30 active:scale-[0.98]"
            title="Buka panel pencarian dan salin link postingan"
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

  // Compact size for Feed Card / Grid View
  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        className={`px-2.5 py-1 rounded-lg text-[10px] font-medium flex items-center gap-1.5 transition-all shadow-sm ${
          hasLinks
            ? 'bg-emerald-950/70 text-emerald-300 border border-emerald-700/60 hover:bg-emerald-900 active:scale-95'
            : 'bg-zinc-800/90 hover:bg-emerald-950 hover:text-emerald-300 text-zinc-300 border border-zinc-700/60 hover:border-emerald-700/60 active:scale-95'
        } ${className}`}
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
