import React, { memo } from 'react';
import {
  Film,
  Image as ImageIcon,
  Layers,
  CalendarClock,
  Clock,
  Trash2,
  Play,
} from 'lucide-react';
import { CATEGORY_COLORS } from '../../utils/constants';
import {
  formatDateDisplay,
  formatTimeDisplay,
} from '../../utils/dateUtils';

function ContentCard({
  item,
  isSelected,
  onSelect,
  onDeleteClick,
}) {
  const isScheduled = Boolean(item.meta?.scheduled_time);

  return (
    <div
      onClick={() => onSelect(item.item_key)}
      className={`group relative p-3.5 rounded-2xl border transition-all cursor-pointer flex gap-3.5 items-start ${
        isSelected
          ? 'bg-zinc-900/90 border-zinc-700/80 shadow-md ring-1 ring-zinc-700'
          : 'bg-zinc-950/60 hover:bg-zinc-900/50 border-zinc-800/80 hover:border-zinc-700/60'
      }`}
    >
      {/* Thumbnail / Media Preview */}
      <div className="w-16 h-20 sm:w-20 sm:h-24 rounded-xl bg-zinc-900 border border-zinc-800 flex-shrink-0 overflow-hidden relative flex items-center justify-center">
        {item.category === 'Video' ? (
          <div className="relative w-full h-full bg-zinc-900 flex items-center justify-center">
            {item.media_url ? (
              <video
                src={item.media_url}
                className="w-full h-full object-cover pointer-events-none opacity-85 group-hover:opacity-100 transition-opacity"
                muted
                playsInline
                preload="metadata"
              />
            ) : (
              <Film className="w-6 h-6 text-zinc-600 group-hover:text-emerald-400 transition" />
            )}
            <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
              <div className="w-6 h-6 rounded-full bg-black/60 backdrop-blur-xs flex items-center justify-center text-white/90">
                <Play className="w-3 h-3 fill-current ml-0.5" />
              </div>
            </div>
          </div>
        ) : item.media_url ? (
          <img
            src={item.media_url}
            alt={item.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        ) : (
          <ImageIcon className="w-6 h-6 text-zinc-600" />
        )}

        {/* Badge: Carousel Slides Count */}
        {item.category === 'Carousel' && item.slides && item.slides.length > 0 && (
          <span className="absolute bottom-1 right-1 bg-black/80 backdrop-blur-xs text-[9px] font-mono font-bold text-purple-300 px-1.5 py-0.2 rounded border border-purple-800/60 flex items-center gap-0.5">
            📑 {item.slides.length}
          </span>
        )}
      </div>

      {/* Content Info */}
      <div className="flex-1 min-w-0 flex flex-col justify-between self-stretch">
        <div>
          {/* Header Badges: Category & Status */}
          <div className="flex items-center justify-between gap-2 mb-1.5 flex-wrap">
            <div className="flex items-center gap-2">
              {/* Category Badge */}
              <span
                className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md border flex items-center gap-1 ${
                  CATEGORY_COLORS[item.category] || 'bg-zinc-800 text-zinc-300'
                }`}
              >
                {item.category === 'Video' && <Film className="w-2.5 h-2.5" />}
                {item.category === 'Poster' && <ImageIcon className="w-2.5 h-2.5" />}
                {item.category === 'Carousel' && <Layers className="w-2.5 h-2.5" />}
                <span>{item.category}</span>
              </span>

              {/* Scheduled Badge */}
              {isScheduled && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 flex items-center gap-1">
                  <CalendarClock className="w-2.5 h-2.5" />
                  <span>Terjadwal</span>
                </span>
              )}
            </div>

            {/* Platform-Specific Status Badge */}
            {(() => {
              const uploaded = item.uploaded_platforms || [];
              const hasTiktok = uploaded.includes('tiktok');
              const hasInstagram = uploaded.includes('instagram') || uploaded.includes('meta');
              const hasFacebook = uploaded.includes('facebook');

              const labels = [];
              if (hasTiktok) labels.push('TT');
              if (hasInstagram) labels.push('IG');
              if (hasFacebook) labels.push('FB');

              if (labels.length > 0) {
                return (
                  <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-md bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 flex items-center gap-1 shadow-xs">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span>✓ {labels.join(' · ')}</span>
                  </span>
                );
              }
              return (
                <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-md bg-amber-950/60 border border-amber-800/70 text-amber-400 flex items-center gap-1 shadow-xs">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  <span>PENDING</span>
                </span>
              );
            })()}
          </div>

          {/* Item Name */}
          <h3 className="text-xs font-semibold text-zinc-100 truncate group-hover:text-emerald-400 transition-colors">
            {item.name}
          </h3>

          {/* Caption Snippet */}
          <p className="text-[11px] text-zinc-400 line-clamp-2 mt-1 leading-relaxed">
            {item.caption || <span className="italic text-zinc-600">Belum ada caption...</span>}
          </p>
        </div>

        {/* Footer: Styled Date Badge (Sejajar dengan tombol Trash) */}
        <div className="flex items-center justify-between pt-2.5 mt-1.5 border-t border-zinc-900/80">
          <div className="flex items-center gap-2 flex-wrap">
            {/* Styled Date Badge */}
            <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-md bg-zinc-900 border border-zinc-800 text-zinc-300 flex items-center gap-1.5 shadow-xs">
              <span className="text-[11px]">📅</span>
              <span>{formatDateDisplay(item.date)}</span>
            </span>

            {/* Scheduled Time Badge */}
            {isScheduled && (
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-md bg-cyan-950/70 border border-cyan-800/70 text-cyan-300 flex items-center gap-1.5 shadow-xs">
                <Clock className="w-3 h-3 text-cyan-400" />
                <span>Pukul {formatTimeDisplay(item.meta.scheduled_time)} WIB</span>
              </span>
            )}
          </div>

          {/* Trash Delete Action */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDeleteClick(item);
            }}
            title="Hapus Media dari Antrean"
            className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-950/40 border border-transparent hover:border-red-800/40 transition flex items-center justify-center flex-shrink-0"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default memo(ContentCard);
