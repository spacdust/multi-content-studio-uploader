import React from 'react';
import ContentCard from './ContentCard';

export default function ContentFeedList({
  items,
  loadingContent,
  selectedItemKey,
  onSelectItem,
  onDeleteClick,
}) {
  if (loadingContent) {
    return (
      <div className="flex flex-col gap-3 py-12 text-center text-zinc-500 font-mono text-xs">
        <span className="animate-spin inline-block w-5 h-5 border-2 border-zinc-700 border-t-emerald-400 rounded-full mx-auto" />
        <span>Memuat antrean media...</span>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="py-20 text-center flex flex-col items-center justify-center gap-2 border border-dashed border-zinc-800/80 rounded-2xl bg-zinc-950/40">
        <p className="text-zinc-400 text-xs font-medium">Tidak ada konten di antrean.</p>
        <p className="text-zinc-600 text-[11px]">
          Klik tombol <strong>+ Tambah Media</strong> untuk menambahkan video, poster, atau carousel.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {items.map((item) => (
        <ContentCard
          key={item.item_key}
          item={item}
          isSelected={item.item_key === selectedItemKey}
          onSelect={onSelectItem}
          onDeleteClick={onDeleteClick}
        />
      ))}
    </div>
  );
}
