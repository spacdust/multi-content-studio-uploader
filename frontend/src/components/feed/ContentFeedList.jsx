import React from 'react';
import ContentCard from './ContentCard';

export default function ContentFeedList({
  items,
  loadingContent,
  selectedItemKey,
  onSelectItem,
  onDeleteClick,
  filterDate,
  setFilterDate,
  onToast,
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
      <div className="py-16 text-center flex flex-col items-center justify-center gap-2.5 border border-dashed border-zinc-800/80 rounded-2xl bg-zinc-950/40 px-4">
        <p className="text-zinc-300 text-xs font-medium">
          {filterDate === 'TODAY'
            ? 'Belum ada media untuk hari ini.'
            : filterDate !== 'All'
            ? `Tidak ada media untuk tanggal ${filterDate}.`
            : 'Tidak ada konten di antrean.'}
        </p>
        <p className="text-zinc-500 text-[11px]">
          Klik tombol <strong>+ Tambah Media</strong> untuk menambahkan video, poster, atau carousel.
        </p>
        {filterDate !== 'All' && (
          <button
            type="button"
            onClick={() => setFilterDate && setFilterDate('All')}
            className="mt-1 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700/80 text-zinc-200 hover:text-white rounded-lg text-xs transition font-medium shadow-xs"
          >
            🌐 Tampilkan Semua Tanggal
          </button>
        )}
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
          onToast={onToast}
        />
      ))}
    </div>
  );
}
