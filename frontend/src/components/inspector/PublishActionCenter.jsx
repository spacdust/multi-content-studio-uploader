import React from 'react';
import { Upload, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

export default function PublishActionCenter({
  selectedItem,
  uploadingItem,
  isPublishDisabled,
  publishBtnText,
  activePlatforms,
  currentAccData,
  handleUploadItem,
}) {
  const uploaded = selectedItem?.uploaded_platforms || [];
  const hasTiktok = uploaded.includes('tiktok');
  const hasMeta = uploaded.includes('meta') || uploaded.includes('instagram');
  const isAllUploaded = hasTiktok && hasMeta;

  return (
    <div className="pt-2 flex flex-col gap-2.5">
      {/* 0. Live Publication Status Banner */}
      <div className="p-3 rounded-xl bg-zinc-950 border border-zinc-800/90 flex flex-col gap-1.5 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-zinc-400">Status Publikasi Konten:</span>
          {isAllUploaded ? (
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>Semua Platform</span>
            </span>
          ) : hasTiktok ? (
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-cyan-400" />
              <span>TikTok Saja</span>
            </span>
          ) : hasMeta ? (
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-blue-400" />
              <span>Meta Suite Saja</span>
            </span>
          ) : (
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
              <Clock className="w-3 h-3 text-amber-400" />
              <span>Belum Diposting</span>
            </span>
          )}
        </div>

        {/* Platform breakdown detail */}
        <div className="flex items-center gap-3 text-[11px] font-mono pt-1 border-t border-zinc-900">
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${hasTiktok ? 'bg-cyan-400' : 'bg-zinc-700'}`} />
            <span className={hasTiktok ? 'text-cyan-300 font-semibold' : 'text-zinc-500'}>
              TikTok: {hasTiktok ? 'Terposting' : 'Belum'}
            </span>
          </div>

          <span className="text-zinc-800">•</span>

          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${hasMeta ? 'bg-blue-400' : 'bg-zinc-700'}`} />
            <span className={hasMeta ? 'text-blue-300 font-semibold' : 'text-zinc-500'}>
              Meta Suite: {hasMeta ? 'Terposting' : 'Belum'}
            </span>
          </div>
        </div>
      </div>

      {/* 1. Main Unified Dynamic Publish Button */}
      <button
        type="button"
        onClick={() => handleUploadItem(selectedItem, 'all')}
        disabled={uploadingItem === selectedItem.item_key || isPublishDisabled}
        className={`w-full py-3 font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition shadow-lg ${
          isPublishDisabled
            ? 'bg-zinc-800 text-zinc-500 border border-zinc-700/50 cursor-not-allowed'
            : 'bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-zinc-950 shadow-emerald-950/40'
        } disabled:opacity-60`}
      >
        <Upload className={`w-4 h-4 ${uploadingItem === selectedItem.item_key ? 'animate-bounce' : ''}`} />
        {uploadingItem === selectedItem.item_key ? 'Memproses Upload...' : publishBtnText}
      </button>

      {/* 2. Individual Platform Testing Buttons (TikTok Only vs Meta Suite Only) */}
      <div className="grid grid-cols-2 gap-2">
        {/* Publish TikTok Button */}
        <button
          type="button"
          onClick={() => handleUploadItem(selectedItem, 'tiktok')}
          disabled={uploadingItem === selectedItem.item_key || !currentAccData.tiktok_active}
          className={`py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 transition ${
            currentAccData.tiktok_active
              ? hasTiktok
                ? 'bg-cyan-950/20 hover:bg-cyan-950/40 border-cyan-800/40 text-cyan-400/80 active:scale-[0.98]'
                : 'bg-cyan-950/50 hover:bg-cyan-950/80 border-cyan-700/80 text-cyan-200 active:scale-[0.98]'
              : 'bg-zinc-900/50 border-zinc-800/80 text-zinc-600 cursor-not-allowed'
          } disabled:opacity-50`}
          title={hasTiktok ? 'Posting ulang ke TikTok Studio' : 'Upload ke platform TikTok Studio'}
        >
          <Upload className="w-3.5 h-3.5 text-cyan-400" />
          <span>{hasTiktok ? 'Re-Publish TikTok' : 'Publish TikTok'}</span>
        </button>

        {/* Publish Meta Suite Button */}
        <button
          type="button"
          onClick={() => handleUploadItem(selectedItem, 'meta')}
          disabled={uploadingItem === selectedItem.item_key || !currentAccData.meta_active}
          className={`py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 transition ${
            currentAccData.meta_active
              ? hasMeta
                ? 'bg-blue-950/20 hover:bg-blue-950/40 border-blue-800/40 text-blue-400/80 active:scale-[0.98]'
                : 'bg-blue-950/50 hover:bg-blue-950/80 border-blue-700/80 text-blue-200 active:scale-[0.98]'
              : 'bg-zinc-900/50 border-zinc-800/80 text-zinc-600 cursor-not-allowed'
          } disabled:opacity-50`}
          title={hasMeta ? 'Posting ulang ke Meta Business Suite' : 'Upload ke Meta Business Suite (Instagram & Facebook)'}
        >
          <Upload className="w-3.5 h-3.5 text-blue-400" />
          <span>{hasMeta ? 'Re-Publish Meta' : 'Publish Meta Suite'}</span>
        </button>
      </div>

      {/* Target Platform Status Chips */}
      <div className="flex items-center justify-between px-1 text-[11px] text-zinc-500 pt-0.5">
        <span className="text-[10px]">Status Sesi Akun:</span>
        <div className="flex items-center gap-1.5">
          {activePlatforms.length > 0 ? (
            activePlatforms.map((plat) => (
              <span
                key={plat}
                className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-300 flex items-center gap-1"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                {plat}
              </span>
            ))
          ) : (
            <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Belum Ada Sesi Login
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
