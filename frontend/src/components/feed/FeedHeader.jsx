import React from 'react';
import { Plus } from 'lucide-react';
import { getLocalNowIso, getLocalTodayDate } from '../../utils/dateUtils';

export default function FeedHeader({
  itemCount,
  setSingleMediaFile,
  setSingleMediaPreviewUrl,
  setCarouselSlides,
  setIsScheduledUpload,
  setUploadScheduleTime,
  setUploadDate,
  setShowUploadModal,
}) {
  return (
    <div className="flex items-center justify-between pb-1">
      <div className="flex items-center gap-2.5">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <h2 className="text-sm font-bold text-zinc-100 tracking-tight">Antrean Konten</h2>
        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-400">
          {itemCount} Media
        </span>
      </div>

      {/* Primary Call-to-Action: Tambah Media */}
      <button
        onClick={() => {
          setSingleMediaFile(null);
          setSingleMediaPreviewUrl(null);
          setCarouselSlides([]);
          setIsScheduledUpload(false);
          setUploadScheduleTime(getLocalNowIso());
          setUploadDate(getLocalTodayDate());
          setShowUploadModal(true);
        }}
        className="px-3.5 py-1.5 bg-zinc-100 hover:bg-white text-zinc-950 font-bold text-xs rounded-xl flex items-center gap-1.5 transition shadow-sm hover:shadow-md active:scale-[0.98]"
      >
        <Plus className="w-3.5 h-3.5 text-zinc-900" />
        <span>Tambah Media</span>
      </button>
    </div>
  );
}
