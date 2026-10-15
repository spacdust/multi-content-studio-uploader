import React, { useState, useMemo } from 'react';
import {
  CalendarClock,
  Clock,
  Calendar,
  CalendarX,
  Film,
  Layers,
  Image as ImageIcon,
  CheckCircle2,
  RotateCw,
  Search,
  X,
  AlertTriangle,
  Trash2,
  Tag,
  Building2,
} from 'lucide-react';
import { formatScheduleShort, formatDateDisplay, formatTimeDisplay } from '../../utils/dateUtils';

const PLATFORM_BADGES = {
  tiktok: {
    name: 'TikTok',
    color: 'bg-cyan-950/40 text-cyan-300 border-cyan-800/50',
    dot: 'bg-cyan-400',
  },
  instagram: {
    name: 'Instagram',
    color: 'bg-pink-950/40 text-pink-300 border-pink-800/50',
    dot: 'bg-pink-400',
  },
  facebook: {
    name: 'Facebook',
    color: 'bg-blue-950/40 text-blue-300 border-blue-800/50',
    dot: 'bg-blue-400',
  },
};

function formatCountdown(diffSeconds) {
  if (diffSeconds === undefined || diffSeconds === null) return '-';
  if (diffSeconds <= 0) return 'Jatuh tempo (segera)';
  if (diffSeconds < 60) return '< 1 menit lagi';
  const mins = Math.floor(diffSeconds / 60);
  if (mins < 60) return `${mins} mnt lagi`;
  const hours = Math.floor(mins / 60);
  const remMins = mins % 60;
  if (hours < 24) {
    return remMins > 0 ? `${hours} jam ${remMins} mnt lagi` : `${hours} jam lagi`;
  }
  const days = Math.floor(hours / 24);
  const remHours = hours % 24;
  return remHours > 0 ? `${days} hari ${remHours} jam lagi` : `${days} hari lagi`;
}

export default function ScheduledQueueModal({
  isOpen,
  onClose,
  schedulerStatus,
  accounts = [],
  selectedAccount,
  onClearSingleSchedule,
  onClearAllSchedule,
  onRefresh,
  showToast,
}) {
  const [filterAccount, setFilterAccount] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [clearingItemKey, setClearingItemKey] = useState(null);
  const [showConfirmClearAll, setShowConfirmClearAll] = useState(false);
  const [isClearingAll, setIsClearingAll] = useState(false);

  // Extract upcoming queue from scheduler status
  const queue = useMemo(() => {
    return schedulerStatus?.upcoming_queue || [];
  }, [schedulerStatus]);

  // Unique accounts present in the scheduled items
  const queueAccounts = useMemo(() => {
    const set = new Set();
    queue.forEach((item) => {
      if (item.account) set.add(item.account);
    });
    return Array.from(set);
  }, [queue]);

  // Filtered queue based on account and search query
  const filteredQueue = useMemo(() => {
    return queue.filter((item) => {
      if (filterAccount !== 'all' && item.account !== filterAccount) {
        return false;
      }
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const nameMatch = (item.item_name || '').toLowerCase().includes(query);
        const accMatch = (item.account || '').toLowerCase().includes(query);
        const dateMatch = (item.date || '').toLowerCase().includes(query);
        const captionMatch = (item.caption || '').toLowerCase().includes(query);
        if (!nameMatch && !accMatch && !dateMatch && !captionMatch) {
          return false;
        }
      }
      return true;
    });
  }, [queue, filterAccount, searchQuery]);

  if (!isOpen) return null;

  const handleManualRefresh = async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    try {
      if (onRefresh) await onRefresh();
    } finally {
      setTimeout(() => setIsRefreshing(false), 400);
    }
  };

  const handleCancelItem = async (item) => {
    const itemKey = item.item_key || `${item.account}:${item.item_name}`;
    setClearingItemKey(itemKey);
    try {
      if (onClearSingleSchedule) {
        await onClearSingleSchedule(item);
      }
    } catch (err) {
      console.error('Error canceling schedule:', err);
      if (showToast) showToast(`Gagal membatalkan jadwal: ${err.message}`, 'error');
    } finally {
      setClearingItemKey(null);
    }
  };

  const handleConfirmClearAll = async () => {
    setIsClearingAll(true);
    try {
      if (onClearAllSchedule) {
        const targetAcc = filterAccount === 'all' ? 'all' : filterAccount;
        await onClearAllSchedule(targetAcc);
      }
      setShowConfirmClearAll(false);
    } catch (err) {
      console.error('Error clearing all schedule:', err);
      if (showToast) showToast(`Gagal membatalkan semua jadwal: ${err.message}`, 'error');
    } finally {
      setIsClearingAll(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-3xl bg-[#0e0e11] border border-zinc-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-zinc-800/80 bg-zinc-900/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-950/60 border border-emerald-800/60 flex items-center justify-center text-emerald-400 shadow-xs">
              <CalendarClock className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-zinc-100 tracking-tight">
                  Daftar Konten Terjadwal
                </h2>
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-950/50 text-emerald-300 border border-emerald-800/50">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {queue.length} Antrean Aktif
                </span>
              </div>
              <p className="text-xs text-zinc-400">
                Postingan yang akan dipublikasikan otomatis oleh robot sesuai waktu yang ditentukan.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleManualRefresh}
              disabled={isRefreshing}
              title="Perbarui status antrean"
              className="p-2 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-xl border border-zinc-800/80 transition cursor-pointer disabled:opacity-50"
            >
              <RotateCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-xl border border-zinc-800/80 transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="px-6 py-3 border-b border-zinc-800/60 bg-zinc-900/20 flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Account Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto py-0.5 max-w-full">
            <span className="text-zinc-500 font-medium flex items-center gap-1 mr-1">
              <Building2 className="w-3.5 h-3.5" /> Akun:
            </span>
            <button
              type="button"
              onClick={() => setFilterAccount('all')}
              className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer ${
                filterAccount === 'all'
                  ? 'bg-emerald-950/70 border border-emerald-800 text-emerald-300'
                  : 'bg-zinc-900/80 border border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
              }`}
            >
              Semua ({queue.length})
            </button>
            {queueAccounts.map((acc) => {
              const count = queue.filter((i) => i.account === acc).length;
              const isSelected = filterAccount === acc;
              return (
                <button
                  key={acc}
                  type="button"
                  onClick={() => setFilterAccount(acc)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer whitespace-nowrap ${
                    isSelected
                      ? 'bg-emerald-950/70 border border-emerald-800 text-emerald-300'
                      : 'bg-zinc-900/80 border border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
                  }`}
                >
                  {acc} ({count})
                </button>
              );
            })}
          </div>

          {/* Search Box */}
          <div className="relative min-w-[200px] flex-1 sm:flex-initial">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Cari file, tanggal, teks..."
              className="w-full bg-zinc-900/90 border border-zinc-800/80 rounded-xl pl-8 pr-3 py-1 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700 transition"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Content Queue List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {filteredQueue.length === 0 ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-600 mb-3">
                <CheckCircle2 className="w-6 h-6 text-zinc-500" />
              </div>
              <h3 className="text-sm font-semibold text-zinc-300 mb-1">
                {searchQuery || filterAccount !== 'all'
                  ? 'Tidak ada konten terjadwal yang cocok'
                  : 'Tidak ada jadwal postingan aktif'}
              </h3>
              <p className="text-xs text-zinc-500 max-w-sm">
                {searchQuery || filterAccount !== 'all'
                  ? 'Coba ubah kata kunci pencarian atau pilih filter akun yang lain.'
                  : 'Semua postingan telah diterbitkan atau belum ada jadwal otomatis yang dibuat. Anda dapat mengatur jadwal melalui menu Upload Massal.'}
              </p>
            </div>
          ) : (
            filteredQueue.map((item, index) => {
              const itemKey = item.item_key || `${item.account}:${item.item_name}`;
              const isClearingThis = clearingItemKey === itemKey;
              const formattedDate = formatScheduleShort(item.scheduled_time);
              const countdown = formatCountdown(item.diff_seconds);
              const isDue = item.diff_seconds <= 0;

              return (
                <div
                  key={itemKey || index}
                  className="group relative bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-800/80 hover:border-zinc-700/80 rounded-xl p-3.5 transition flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs"
                >
                  {/* Left: Category Icon / Thumbnail + Info */}
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    {/* Media Thumbnail / Icon */}
                    <div className="relative w-12 h-12 rounded-lg bg-zinc-950 border border-zinc-800 flex-shrink-0 overflow-hidden flex items-center justify-center">
                      {item.media_url ? (
                        item.category === 'Video' ? (
                          <div className="relative w-full h-full flex items-center justify-center bg-zinc-950">
                            <Film className="w-5 h-5 text-cyan-400/80" />
                          </div>
                        ) : (
                          <img
                            src={item.media_url}
                            alt={item.item_name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        )
                      ) : item.category === 'Carousel' ? (
                        <Layers className="w-5 h-5 text-purple-400" />
                      ) : item.category === 'Poster' ? (
                        <ImageIcon className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <Film className="w-5 h-5 text-cyan-400" />
                      )}
                      <span className="absolute bottom-0 right-0 left-0 bg-black/70 text-[9px] font-mono text-center text-zinc-300 py-0.2">
                        {item.category === 'Carousel' ? 'Car' : item.category === 'Poster' ? 'Img' : 'Vid'}
                      </span>
                    </div>

                    {/* Meta info */}
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-1.5 mb-1">
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-zinc-800/90 text-zinc-300 border border-zinc-700/50">
                          {item.account}
                        </span>
                        <span className="text-[11px] font-semibold text-zinc-200 truncate max-w-[240px] sm:max-w-[320px]">
                          {item.item_name}
                        </span>
                        {item.date && (
                          <span className="text-[10px] text-zinc-500 font-mono">
                            ({item.date})
                          </span>
                        )}
                      </div>

                      {/* Scheduled Time & Countdown */}
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        <div className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                          <Calendar className="w-3.5 h-3.5 text-emerald-500" />
                          <span className="font-mono text-[11px]">{formattedDate}</span>
                        </div>

                        <span className="text-zinc-700">•</span>

                        <div
                          className={`inline-flex items-center gap-1 px-1.5 py-0.2 rounded font-mono text-[10px] ${
                            isDue
                              ? 'bg-amber-950/60 text-amber-300 border border-amber-800/50'
                              : 'bg-zinc-800/60 text-zinc-400 border border-zinc-700/40'
                          }`}
                        >
                          <Clock className="w-3 h-3" />
                          <span>{countdown}</span>
                        </div>
                      </div>

                      {/* Target Platforms */}
                      {item.remaining_platforms && item.remaining_platforms.length > 0 && (
                        <div className="flex items-center gap-1 mt-1.5">
                          <span className="text-[10px] text-zinc-500 mr-0.5">Target:</span>
                          {item.remaining_platforms.map((p) => {
                            const cfg = PLATFORM_BADGES[p.toLowerCase()] || {
                              name: p,
                              color: 'bg-zinc-800 text-zinc-300 border-zinc-700',
                              dot: 'bg-zinc-400',
                            };
                            return (
                              <span
                                key={p}
                                className={`inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[10px] font-medium border ${cfg.color}`}
                              >
                                <span className={`w-1 h-1 rounded-full ${cfg.dot}`} />
                                {cfg.name}
                              </span>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right: Action button to Cancel this schedule */}
                  <div className="flex items-center justify-end w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-t-0 border-zinc-800/40">
                    <button
                      type="button"
                      onClick={() => handleCancelItem(item)}
                      disabled={isClearingThis}
                      title="Batalkan jadwal postingan ini"
                      className="px-2.5 py-1.5 rounded-xl text-xs font-medium text-rose-400 hover:text-rose-200 bg-rose-950/20 hover:bg-rose-950/50 border border-rose-900/40 hover:border-rose-800/70 transition cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {isClearingThis ? (
                        <RotateCw className="w-3.5 h-3.5 animate-spin text-rose-400" />
                      ) : (
                        <CalendarX className="w-3.5 h-3.5 text-rose-400" />
                      )}
                      <span>Batalkan Jadwal</span>
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-zinc-800/80 bg-zinc-900/50 flex flex-wrap items-center justify-between gap-3">
          {/* Clear All Confirmation Dialog or Trigger */}
          {showConfirmClearAll ? (
            <div className="flex items-center gap-2 bg-rose-950/40 border border-rose-800/60 rounded-xl px-3 py-1.5 animate-fadeIn">
              <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span className="text-xs text-rose-200 font-medium">
                Batalkan {filteredQueue.length} jadwal {filterAccount === 'all' ? 'semua akun' : filterAccount}?
              </span>
              <button
                type="button"
                onClick={handleConfirmClearAll}
                disabled={isClearingAll}
                className="px-2.5 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold transition cursor-pointer disabled:opacity-50"
              >
                {isClearingAll ? 'Membatalkan...' : 'Ya, Batalkan Semua'}
              </button>
              <button
                type="button"
                onClick={() => setShowConfirmClearAll(false)}
                className="px-2 py-1 text-xs text-zinc-400 hover:text-zinc-200 rounded-lg hover:bg-zinc-800 transition cursor-pointer"
              >
                Batal
              </button>
            </div>
          ) : (
            filteredQueue.length > 0 && (
              <button
                type="button"
                onClick={() => setShowConfirmClearAll(true)}
                className="px-3 py-1.5 text-xs font-medium text-rose-400 hover:text-rose-300 bg-rose-950/30 hover:bg-rose-950/60 border border-rose-800/40 rounded-xl transition flex items-center gap-1.5 cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                <span>
                  Batalkan Semua Jadwal {filterAccount !== 'all' ? `(${filterAccount})` : `(${filteredQueue.length})`}
                </span>
              </button>
            )
          )}

          {/* Right: Close button */}
          <div className="flex items-center gap-2 ml-auto">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-xl border border-zinc-700/80 transition cursor-pointer"
            >
              Tutup
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
