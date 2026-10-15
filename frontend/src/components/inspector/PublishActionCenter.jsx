import React from 'react';
import { Upload, CheckCircle2, Clock, Sparkles, RotateCcw } from 'lucide-react';

export default function PublishActionCenter({
  selectedItem,
  uploadingItem,
  isPublishDisabled,
  publishBtnText,
  activePlatforms,
  currentAccData,
  handleUploadItem,
  handleResetStatus,
  showToast,
}) {
  const uploaded = selectedItem?.uploaded_platforms || [];
  const hasTiktok = uploaded.includes('tiktok');
  const hasInstagram = uploaded.includes('instagram') || uploaded.includes('meta');
  const hasFacebook = uploaded.includes('facebook');

  // Connected platforms for currently active account
  const connectedPlatforms = [];
  if (currentAccData?.tiktok_active) {
    connectedPlatforms.push({ id: 'tiktok', name: 'TikTok', isUploaded: hasTiktok });
  }
  if (currentAccData?.instagram_active) {
    connectedPlatforms.push({ id: 'instagram', name: 'Instagram', isUploaded: hasInstagram });
  }
  if (currentAccData?.facebook_active) {
    connectedPlatforms.push({ id: 'facebook', name: 'Facebook', isUploaded: hasFacebook });
  }

  const remainingPlatforms = connectedPlatforms.filter((p) => !p.isUploaded);
  const isAllConnectedUploaded = connectedPlatforms.length > 0 && remainingPlatforms.length === 0;

  const isUploading = uploadingItem === selectedItem?.item_key;
  const [isResettingAndUploading, setIsResettingAndUploading] = React.useState(false);

  const handleForceReuploadAll = async () => {
    if (!selectedItem || !handleResetStatus) return;
    setIsResettingAndUploading(true);
    try {
      showToast?.(`Mereset status dan memulai publish ulang untuk '${selectedItem.name}'...`, 'info');
      await handleResetStatus(selectedItem);
      handleUploadItem(selectedItem, 'all');
    } catch {
      showToast?.('Gagal mereset status untuk publish ulang', 'error');
    } finally {
      setIsResettingAndUploading(false);
    }
  };

  return (
    <div className="pt-2 flex flex-col gap-2.5">
      {/* 0. Live Publication Status Banner */}
      <div className="p-3 rounded-xl bg-zinc-950 border border-zinc-800/90 flex flex-col gap-2 shadow-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-semibold text-zinc-400">Status Publikasi:</span>
            {uploaded.length > 0 && handleResetStatus && (
              <button
                type="button"
                onClick={() => handleResetStatus(selectedItem)}
                title="Reset status publikasi konten ini kembali menjadi PENDING"
                className="text-[9px] font-mono font-medium text-zinc-400 hover:text-amber-400 hover:bg-zinc-800/80 px-1.5 py-0.5 rounded border border-zinc-800 flex items-center gap-1 transition active:scale-95"
              >
                <RotateCcw className="w-2.5 h-2.5" />
                <span>Reset Status</span>
              </button>
            )}
          </div>
          {isAllConnectedUploaded ? (
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>Semua Platform ({connectedPlatforms.map((p) => p.name.slice(0, 2).toUpperCase()).join(' · ')})</span>
            </span>
          ) : uploaded.length > 0 ? (
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-cyan-400" />
              <span>Terbit Parsial ({uploaded.map((p) => p.slice(0, 2).toUpperCase()).join(' · ')})</span>
            </span>
          ) : (
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
              <Clock className="w-3 h-3 text-amber-400" />
              <span>Belum Diposting</span>
            </span>
          )}
        </div>

        {/* 3 Platforms breakdown detail */}
        <div className="flex items-center justify-between text-[11px] font-mono pt-1.5 border-t border-zinc-900 flex-wrap gap-2">
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${hasTiktok ? 'bg-cyan-400' : 'bg-zinc-700'}`} />
            <span className={hasTiktok ? 'text-cyan-300 font-semibold' : 'text-zinc-500'}>
              TikTok: {hasTiktok ? 'Terposting' : 'Belum'}
            </span>
          </div>

          <span className="text-zinc-800">•</span>

          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${hasInstagram ? 'bg-pink-400' : 'bg-zinc-700'}`} />
            <span className={hasInstagram ? 'text-pink-300 font-semibold' : 'text-zinc-500'}>
              IG: {hasInstagram ? 'Terposting' : 'Belum'}
            </span>
          </div>

          <span className="text-zinc-800">•</span>

          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${hasFacebook ? 'bg-blue-400' : 'bg-zinc-700'}`} />
            <span className={hasFacebook ? 'text-blue-300 font-semibold' : 'text-zinc-500'}>
              FB Fanspage: {hasFacebook ? 'Terposting' : 'Belum'}
            </span>
          </div>
        </div>
      </div>

      {/* 1. Main Unified Master Publish Button & Smart Flow */}
      {isAllConnectedUploaded ? (
        <div className="flex flex-col gap-2">
          <div className="w-full py-2.5 px-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 flex items-center justify-between text-emerald-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <div className="flex flex-col">
                <span className="text-xs font-bold leading-tight">Semua Platform Sudah Terbit</span>
                <span className="text-[10px] text-emerald-400/80 font-mono">
                  {connectedPlatforms.map((p) => p.name).join(' · ')} Selesai 100%
                </span>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={handleForceReuploadAll}
            disabled={isUploading || isResettingAndUploading}
            className="w-full py-2.5 font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition shadow-md bg-zinc-900 hover:bg-zinc-800 active:bg-zinc-950 text-amber-300 border border-amber-500/30 hover:border-amber-400/50 disabled:opacity-60"
            title="Reset status publikasi konten ini dan kirim ulang ke seluruh platform"
          >
            <RotateCcw className={`w-3.5 h-3.5 text-amber-400 ${isResettingAndUploading ? 'animate-spin' : ''}`} />
            <span>{isResettingAndUploading ? 'Mereset & Memulai Ulang...' : 'Reset & Upload Ulang Semua Platform'}</span>
          </button>
          <p className="text-[10px] text-zinc-500 text-center px-1 leading-tight">
            ✓ Konten ini sudah terposting di seluruh platform. Bot otomatis melewatinya agar tidak duplikat.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-1.5">
          <button
            type="button"
            onClick={() => handleUploadItem(selectedItem, 'all')}
            disabled={isUploading || isPublishDisabled}
            className={`w-full py-3 font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition shadow-lg ${
              isPublishDisabled
                ? 'bg-zinc-800 text-zinc-500 border border-zinc-700/50 cursor-not-allowed'
                : 'bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-zinc-950 shadow-emerald-950/40'
            } disabled:opacity-60`}
          >
            <Upload className={`w-4 h-4 ${isUploading ? 'animate-bounce' : ''}`} />
            {isUploading ? 'Sedang Memproses Upload...' : publishBtnText}
          </button>
          {remainingPlatforms.length > 0 && remainingPlatforms.length < connectedPlatforms.length && (
            <p className="text-[10px] text-zinc-400 text-center px-1 leading-tight">
              ℹ️ Platform yang sudah terbit ({connectedPlatforms.filter((p) => p.isUploaded).map((p) => p.name).join(', ')}) otomatis dilewati.
            </p>
          )}
        </div>
      )}

      {/* 2. Individual Platform Publish Buttons (3 Platforms: TikTok, Instagram, Facebook Fanspage) */}
      <div className="grid grid-cols-3 gap-2">
        {/* 1. Publish TikTok Button */}
        <button
          type="button"
          onClick={() => handleUploadItem(selectedItem, 'tiktok')}
          disabled={isUploading || !currentAccData.tiktok_active}
          className={`py-2 px-2 rounded-xl border text-[11px] font-semibold flex items-center justify-center gap-1 transition ${
            currentAccData.tiktok_active
              ? hasTiktok
                ? 'bg-cyan-950/20 hover:bg-cyan-950/40 border-cyan-800/40 text-cyan-400/80 active:scale-[0.98]'
                : 'bg-cyan-950/50 hover:bg-cyan-950/80 border-cyan-700/80 text-cyan-200 active:scale-[0.98]'
              : 'bg-zinc-900/50 border-zinc-800/80 text-zinc-600 cursor-not-allowed'
          } disabled:opacity-50`}
          title={hasTiktok ? 'Posting ulang ke TikTok Studio' : 'Upload ke platform TikTok Studio'}
        >
          <Upload className="w-3 h-3 text-cyan-400 shrink-0" />
          <span className="truncate">{hasTiktok ? 'Re-Publish TT' : 'Publish TikTok'}</span>
        </button>

        {/* 2. Publish Instagram Button */}
        <button
          type="button"
          onClick={() => handleUploadItem(selectedItem, 'instagram')}
          disabled={isUploading || !currentAccData.instagram_active}
          className={`py-2 px-2 rounded-xl border text-[11px] font-semibold flex items-center justify-center gap-1 transition ${
            currentAccData.instagram_active
              ? hasInstagram
                ? 'bg-pink-950/20 hover:bg-pink-950/40 border-pink-800/40 text-pink-400/80 active:scale-[0.98]'
                : 'bg-pink-950/50 hover:bg-pink-950/80 border-pink-700/80 text-pink-200 active:scale-[0.98]'
              : 'bg-zinc-900/50 border-zinc-800/80 text-zinc-600 cursor-not-allowed'
          } disabled:opacity-50`}
          title={hasInstagram ? 'Posting ulang ke Instagram' : 'Upload ke Instagram (Rasio Asli)'}
        >
          <Upload className="w-3 h-3 text-pink-400 shrink-0" />
          <span className="truncate">{hasInstagram ? 'Re-Publish IG' : 'Publish Instagram'}</span>
        </button>

        {/* 3. Publish Facebook Fanspage Button */}
        <button
          type="button"
          onClick={() => handleUploadItem(selectedItem, 'facebook')}
          disabled={isUploading || !currentAccData.facebook_active}
          className={`py-2 px-2 rounded-xl border text-[11px] font-semibold flex items-center justify-center gap-1 transition ${
            currentAccData.facebook_active
              ? hasFacebook
                ? 'bg-blue-950/20 hover:bg-blue-950/40 border-blue-800/40 text-blue-400/80 active:scale-[0.98]'
                : 'bg-blue-950/50 hover:bg-blue-950/80 border-blue-700/80 text-blue-200 active:scale-[0.98]'
              : 'bg-zinc-900/50 border-zinc-800/80 text-zinc-600 cursor-not-allowed'
          } disabled:opacity-50`}
          title={hasFacebook ? 'Posting ulang ke Halaman Fanspage Facebook' : 'Upload ke Halaman Fanspage Facebook (Reels & Feed)'}
        >
          <Upload className="w-3 h-3 text-blue-400 shrink-0" />
          <span className="truncate">{hasFacebook ? 'Re-Publish FB' : 'Publish Facebook'}</span>
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
