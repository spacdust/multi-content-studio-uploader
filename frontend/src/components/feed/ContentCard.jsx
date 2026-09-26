import React, { memo } from 'react';
import {
  Film,
  Image as ImageIcon,
  Layers,
  CalendarClock,
  Clock,
  Trash2,
  Play,
  ChevronUp,
  ChevronDown,
  GripVertical,
  ShoppingBag,
} from 'lucide-react';
import { CATEGORY_COLORS } from '../../utils/constants';
import {
  formatDateDisplay,
  formatTimeDisplay,
} from '../../utils/dateUtils';
import CopyLinksButton from './CopyLinksButton';

function ContentCard({
  item,
  index = 0,
  totalItems = 1,
  isSelected,
  onSelect,
  onDeleteClick,
  onToast,
  onMoveItem,
  isDragging = false,
  isDragOver = false,
  onDragStart,
  onDragOver,
  onDragLeave,
  onDrop,
}) {
  const isScheduled = Boolean(item.meta?.scheduled_time);
  const tiktokProduct = item.meta?.tiktok_product;
  const isYellowBasketOn = Boolean(
    tiktokProduct && (tiktokProduct.enabled === true || tiktokProduct.enabled === 'true')
  );

  return (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('text/plain', item.item_key);
        if (onDragStart) onDragStart(item.item_key);
      }}
      onDragOver={(e) => {
        e.preventDefault();
        if (onDragOver) onDragOver(item.item_key);
      }}
      onDragLeave={() => {
        if (onDragLeave) onDragLeave();
      }}
      onDrop={(e) => {
        e.preventDefault();
        const srcKey = e.dataTransfer.getData('text/plain');
        if (onDrop) onDrop(srcKey, item.item_key);
      }}
      onClick={() => onSelect(item.item_key)}
      className={`group relative p-3 sm:p-3.5 rounded-2xl border transition-all cursor-pointer flex gap-2.5 sm:gap-3.5 items-start ${
        isDragOver
          ? 'bg-emerald-950/40 border-emerald-500 ring-2 ring-emerald-500/50 scale-[1.01]'
          : isDragging
          ? 'opacity-40 border-dashed border-zinc-600'
          : isSelected
          ? 'bg-zinc-900/90 border-zinc-700/80 shadow-md ring-1 ring-zinc-700'
          : 'bg-zinc-950/60 hover:bg-zinc-900/50 border-zinc-800/80 hover:border-zinc-700/60'
      }`}
    >
      {/* Left Sequence Rank & Direct Reorder Column */}
      <div
        className="flex flex-col items-center justify-between self-stretch py-0.5 flex-shrink-0 text-zinc-500 select-none"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Move Up */}
        <button
          type="button"
          disabled={index === 0}
          onClick={(e) => {
            e.stopPropagation();
            if (onMoveItem) onMoveItem(item.item_key, 'up');
          }}
          title="Naikkan Urutan (Ke Atas)"
          className={`p-1 rounded-md transition ${
            index === 0
              ? 'opacity-20 cursor-not-allowed'
              : 'hover:bg-zinc-800 hover:text-emerald-400 cursor-pointer text-zinc-400 active:scale-95'
          }`}
        >
          <ChevronUp className="w-3.5 h-3.5" />
        </button>

        {/* Sequence Number & Grip Drag Handle */}
        <div
          className="flex flex-col items-center gap-0.5 cursor-grab active:cursor-grabbing py-1 group/grip"
          title="Tarik / Geser untuk mengubah urutan antrean"
        >
          <GripVertical className="w-3.5 h-3.5 text-zinc-600 group-hover/grip:text-zinc-300 transition" />
          <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded-md bg-zinc-800/90 border border-zinc-700/60 text-zinc-300 shadow-2xs">
            #{index + 1}
          </span>
        </div>

        {/* Move Down */}
        <button
          type="button"
          disabled={index === totalItems - 1}
          onClick={(e) => {
            e.stopPropagation();
            if (onMoveItem) onMoveItem(item.item_key, 'down');
          }}
          title="Turunkan Urutan (Ke Bawah)"
          className={`p-1 rounded-md transition ${
            index === totalItems - 1
              ? 'opacity-20 cursor-not-allowed'
              : 'hover:bg-zinc-800 hover:text-emerald-400 cursor-pointer text-zinc-400 active:scale-95'
          }`}
        >
          <ChevronDown className="w-3.5 h-3.5" />
        </button>
      </div>
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
            <div className="flex items-center gap-1.5 flex-wrap">
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

              {/* Keranjang Kuning Badge */}
              {isYellowBasketOn && (
                <span
                  title={
                    tiktokProduct?.custom_title
                      ? `Keranjang Kuning: "${tiktokProduct.custom_title}"\nProduk: ${tiktokProduct.title || ''}${tiktokProduct.format_price ? ` (${tiktokProduct.format_price})` : ''}`
                      : tiktokProduct?.title
                      ? `Keranjang Kuning: ${tiktokProduct.title}${tiktokProduct.format_price ? ` (${tiktokProduct.format_price})` : ''}`
                      : 'Keranjang Kuning'
                  }
                  className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-amber-500/15 border border-amber-500/50 text-amber-400 flex items-center gap-1 shadow-xs"
                >
                  <ShoppingBag className="w-2.5 h-2.5 text-amber-400 flex-shrink-0" />
                  <span>Keranjang Kuning</span>
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
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-md bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 flex items-center gap-1 shadow-xs">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span>✓ {labels.join(' · ')}</span>
                    </span>
                    <CopyLinksButton item={item} account={item.account} onToast={onToast} size="sm" />
                  </div>
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
