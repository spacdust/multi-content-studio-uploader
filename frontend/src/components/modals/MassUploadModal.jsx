import React, { useState, useEffect, useMemo } from 'react';
import {
  Zap,
  X,
  Play,
  Film,
  Image as ImageIcon,
  Layers,
  Sparkles,
  ArrowDownUp,
  Clock,
  Calendar,
  CalendarClock,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  CalendarRange,
  ShoppingBag,
} from 'lucide-react';
import {
  getLocalTodayDate,
  addMinutesToIso,
  formatScheduleShort,
  formatDateDisplay,
  formatTimeDisplay
} from '../../utils/dateUtils';

const INTERVAL_PRESETS = [
  { label: '15 Mnt', minutes: 15 },
  { label: '30 Mnt', minutes: 30 },
  { label: '1 Jam', minutes: 60 },
  { label: '2 Jam', minutes: 120 },
  { label: '3 Jam', minutes: 180 },
  { label: '6 Jam', minutes: 360 },
  { label: '12 Jam', minutes: 720 },
  { label: '1 Hari', minutes: 1440 },
  { label: 'Kustom', minutes: 'custom' },
];

function getDefaultStartTime() {
  const d = new Date();
  const mins = d.getMinutes();
  if (mins < 30) {
    d.setMinutes(30, 0, 0);
  } else {
    d.setHours(d.getHours() + 1, 0, 0, 0);
  }
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return {
    date: `${year}-${month}-${day}`,
    hour: hours,
    min: minutes,
  };
}

export default function MassUploadModal({
  isOpen,
  onClose,
  queue = [],
  activePlatforms = [],
  onConfirm,
  onConfirmSchedule,
  onClearSchedule,
  isPublishDisabled = false,
  accountName = 'Akun'
}) {
  const [activeTab, setActiveTab] = useState('schedule'); // 'schedule' | 'immediate'

  // Scheduling state
  const [startDate, setStartDate] = useState(getLocalTodayDate());
  const [startHour, setStartHour] = useState('14');
  const [startMin, setStartMin] = useState('00');
  const [selectedInterval, setSelectedInterval] = useState(60); // minutes or 'custom'
  const [customIntervalMins, setCustomIntervalMins] = useState(45);
  const [isApplyingSchedule, setIsApplyingSchedule] = useState(false);

  // Initialize start time when modal opens
  useEffect(() => {
    if (isOpen) {
      // If queue has an item with schedule already, use it as starting point
      const firstScheduled = queue.find((i) => i.meta?.scheduled_time);
      if (firstScheduled && firstScheduled.meta.scheduled_time.includes('T')) {
        const [dPart, tPart] = firstScheduled.meta.scheduled_time.split('T');
        if (dPart) setStartDate(dPart);
        if (tPart) {
          const [h, m] = tPart.split(':');
          if (h) setStartHour(h.padStart(2, '0'));
          if (m) setStartMin(m.padStart(2, '0'));
        }
      } else {
        const def = getDefaultStartTime();
        setStartDate(def.date);
        setStartHour(def.hour);
        setStartMin(def.min);
      }
    }
  }, [isOpen, queue]);

  const effectiveIntervalMinutes = useMemo(() => {
    if (selectedInterval === 'custom') {
      const parsed = parseInt(customIntervalMins, 10);
      return isNaN(parsed) || parsed < 1 ? 60 : parsed;
    }
    return selectedInterval;
  }, [selectedInterval, customIntervalMins]);

  const startIso = `${startDate}T${startHour}:${startMin}:00`;

  // Calculate progressive schedule for each item in the queue
  const scheduledQueueItems = useMemo(() => {
    return queue.map((item, idx) => {
      const addedMinutes = idx * effectiveIntervalMinutes;
      const targetIso = addMinutesToIso(startIso, addedMinutes);
      return {
        ...item,
        scheduled_time: targetIso,
        offset_minutes: addedMinutes,
        relative_display: formatScheduleShort(targetIso),
      };
    });
  }, [queue, startIso, effectiveIntervalMinutes]);

  const hasExistingScheduleInQueue = useMemo(() => {
    return queue.some((i) => Boolean(i.meta?.scheduled_time));
  }, [queue]);

  if (!isOpen) return null;

  const hoursList = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'));
  const minutesList = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'));

  const getCategoryIcon = (cat) => {
    switch (cat?.toLowerCase()) {
      case 'video':
        return <Film className="w-3.5 h-3.5 text-cyan-400" />;
      case 'poster':
        return <ImageIcon className="w-3.5 h-3.5 text-pink-400" />;
      case 'carousel':
        return <Layers className="w-3.5 h-3.5 text-amber-400" />;
      default:
        return <Sparkles className="w-3.5 h-3.5 text-emerald-400" />;
    }
  };

  const applyQuickPreset = (type) => {
    const d = new Date();
    if (type === 'plus30m') {
      d.setMinutes(d.getMinutes() + 30);
    } else if (type === 'plus1h') {
      d.setHours(d.getHours() + 1);
    } else if (type === 'tonight') {
      d.setHours(19, 30, 0, 0);
    } else if (type === 'tomorrow_morning') {
      d.setDate(d.getDate() + 1);
      d.setHours(8, 0, 0, 0);
    } else if (type === 'tomorrow_night') {
      d.setDate(d.getDate() + 1);
      d.setHours(19, 30, 0, 0);
    }

    const yr = d.getFullYear();
    const mo = String(d.getMonth() + 1).padStart(2, '0');
    const dy = String(d.getDate()).padStart(2, '0');
    setStartDate(`${yr}-${mo}-${dy}`);
    setStartHour(String(d.getHours()).padStart(2, '0'));
    setStartMin(String(d.getMinutes()).padStart(2, '0'));
  };

  const handleApplyScheduleClick = async () => {
    if (!onConfirmSchedule) return;
    setIsApplyingSchedule(true);
    try {
      await onConfirmSchedule(scheduledQueueItems);
      onClose();
    } finally {
      setIsApplyingSchedule(false);
    }
  };

  const handleClearScheduleClick = async () => {
    if (!onClearSchedule) return;
    setIsApplyingSchedule(true);
    try {
      await onClearSchedule(queue);
      onClose();
    } finally {
      setIsApplyingSchedule(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs transition-all duration-300 animate-fadeIn">
      <div className="relative w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Accent Top Border */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500" />

        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-950/70">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 shadow-inner">
              <CalendarRange className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-zinc-100 tracking-wide">
                  Upload & Penjadwalan Massal
                </h3>
                <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-emerald-950 text-emerald-300 border border-emerald-700/60 font-mono">
                  {queue.length} Media
                </span>
              </div>
              <p className="text-xs text-zinc-400">
                Akun: <span className="text-zinc-200 font-medium">{accountName}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-800 transition cursor-pointer"
            title="Tutup Modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="px-6 pt-3 pb-0 bg-zinc-950/40 border-b border-zinc-800/80">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveTab('schedule')}
              className={`flex-1 pb-3 pt-1 text-xs font-semibold flex items-center justify-center gap-2 border-b-2 transition cursor-pointer ${
                activeTab === 'schedule'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <CalendarClock className="w-4 h-4" />
              <span>Jadwalkan Bertahap (Staggered)</span>
              <span className="px-1.5 py-0.2 text-[9px] rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800/80">
                Otomatis
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('immediate')}
              className={`flex-1 pb-3 pt-1 text-xs font-semibold flex items-center justify-center gap-2 border-b-2 transition cursor-pointer ${
                activeTab === 'immediate'
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Upload Sekarang (Langsung)</span>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 custom-scrollbar bg-zinc-900">
          {activeTab === 'schedule' ? (
            /* =================== TAB 1: STAGGERED SCHEDULING =================== */
            <div className="space-y-4 animate-fadeIn">
              {/* Scheduling Settings Card */}
              <div className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 space-y-3.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-cyan-400" />
                    <h4 className="text-xs font-bold text-zinc-200">
                      1. Atur Waktu Mulai Postingan Pertama (#1)
                    </h4>
                  </div>
                  <span className="text-[10px] text-zinc-400 font-mono">Format 24 Jam</span>
                </div>

                {/* Date & Time Input Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
                  <div className="sm:col-span-6 flex flex-col gap-1">
                    <label className="text-[10px] text-zinc-400 font-mono uppercase tracking-wider">
                      Tanggal Mulai:
                    </label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs text-zinc-100 outline-none focus:border-zinc-600 font-medium"
                    />
                  </div>

                  <div className="sm:col-span-6 flex flex-col gap-1">
                    <label className="text-[10px] text-zinc-400 font-mono uppercase tracking-wider flex items-center gap-1">
                      Jam Tayang Pertama:
                    </label>
                    <div className="flex items-center gap-1.5">
                      <select
                        value={startHour}
                        onChange={(e) => setStartHour(e.target.value)}
                        className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-1.5 text-xs text-zinc-100 font-mono font-bold outline-none focus:border-zinc-600 cursor-pointer"
                      >
                        {hoursList.map((h) => (
                          <option key={h} value={h} className="bg-zinc-900 text-zinc-100">
                            {h}
                          </option>
                        ))}
                      </select>
                      <span className="text-zinc-500 font-bold font-mono">:</span>
                      <select
                        value={startMin}
                        onChange={(e) => setStartMin(e.target.value)}
                        className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-1.5 text-xs text-zinc-100 font-mono font-bold outline-none focus:border-zinc-600 cursor-pointer"
                      >
                        {minutesList.map((m) => (
                          <option key={m} value={m} className="bg-zinc-900 text-zinc-100">
                            {m}
                          </option>
                        ))}
                      </select>
                      <span className="text-xs text-zinc-400 font-mono px-1">WIB</span>
                    </div>
                  </div>
                </div>

                {/* Quick Presets */}
                <div className="flex items-center gap-1.5 flex-wrap pt-1">
                  <span className="text-[10px] text-zinc-500 font-medium mr-1">Preset Cepat:</span>
                  <button
                    type="button"
                    onClick={() => applyQuickPreset('plus30m')}
                    className="px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[10px] text-zinc-300 transition cursor-pointer"
                  >
                    +30 Mnt
                  </button>
                  <button
                    type="button"
                    onClick={() => applyQuickPreset('plus1h')}
                    className="px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[10px] text-zinc-300 transition cursor-pointer"
                  >
                    +1 Jam
                  </button>
                  <button
                    type="button"
                    onClick={() => applyQuickPreset('tonight')}
                    className="px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[10px] text-cyan-300 transition cursor-pointer"
                  >
                    Malam Ini (19:30)
                  </button>
                  <button
                    type="button"
                    onClick={() => applyQuickPreset('tomorrow_morning')}
                    className="px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[10px] text-amber-300 transition cursor-pointer"
                  >
                    Besok Pagi (08:00)
                  </button>
                  <button
                    type="button"
                    onClick={() => applyQuickPreset('tomorrow_night')}
                    className="px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[10px] text-purple-300 transition cursor-pointer"
                  >
                    Besok Malam (19:30)
                  </button>
                </div>

                {/* Interval / Jeda Waktu Section */}
                <div className="pt-3 border-t border-zinc-800/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-zinc-200 flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-amber-400" />
                      2. Pilih Jeda Waktu Upload Antar Postingan
                    </label>
                    <span className="text-[11px] font-mono font-semibold text-emerald-400">
                      Tiap {effectiveIntervalMinutes} Menit
                      {effectiveIntervalMinutes >= 60 && ` (${(effectiveIntervalMinutes / 60).toFixed(1).replace('.0', '')} Jam)`}
                    </span>
                  </div>

                  {/* Interval Presets Pill Row */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {INTERVAL_PRESETS.map((preset) => {
                      const isSel = selectedInterval === preset.minutes;
                      return (
                        <button
                          key={preset.label}
                          type="button"
                          onClick={() => setSelectedInterval(preset.minutes)}
                          className={`px-2.5 py-1 text-xs rounded-lg font-medium transition cursor-pointer border ${
                            isSel
                              ? 'bg-emerald-950/80 border-emerald-500 text-emerald-300 font-bold shadow-xs'
                              : 'bg-zinc-900/90 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-850'
                          }`}
                        >
                          {preset.label}
                        </button>
                      );
                    })}
                  </div>

                  {/* Custom Interval Input if selected */}
                  {selectedInterval === 'custom' && (
                    <div className="flex items-center gap-2 pt-1 animate-fadeIn">
                      <label className="text-xs text-zinc-400">Masukkan Menit Jeda:</label>
                      <input
                        type="number"
                        min="1"
                        max="10080"
                        value={customIntervalMins}
                        onChange={(e) => setCustomIntervalMins(Math.max(1, parseInt(e.target.value) || 1))}
                        className="w-24 bg-zinc-900 border border-zinc-700 rounded-lg px-2.5 py-1 text-xs text-zinc-100 font-mono font-bold outline-none focus:border-emerald-500"
                      />
                      <span className="text-xs text-zinc-500">menit</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Schedule Summary Banner */}
              {queue.length > 0 && (
                <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-800/40 flex items-start gap-2.5">
                  <div className="p-1 rounded-md bg-cyan-500/20 text-cyan-400 flex-shrink-0 mt-0.5">
                    <CalendarClock className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-cyan-200">
                      Ringkasan Penjadwalan ({queue.length} Postingan)
                    </p>
                    <p className="text-[11px] text-zinc-400 leading-relaxed mt-0.5">
                      Postingan #1 dijadwalkan pada{' '}
                      <strong className="text-cyan-300">{scheduledQueueItems[0]?.relative_display}</strong>, dan
                      postingan terakhir (#{queue.length}) pada{' '}
                      <strong className="text-cyan-300">
                        {scheduledQueueItems[queue.length - 1]?.relative_display}
                      </strong>
                      . Auto-Scheduler akan otomatis mengunggah tepat pada jadwal masing-masing.
                    </p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* =================== TAB 2: IMMEDIATE UPLOAD =================== */
            <div className="space-y-4 animate-fadeIn">
              {/* Info Banner */}
              <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-800/40 flex items-start gap-2.5">
                <div className="p-1 rounded-md bg-emerald-500/20 text-emerald-400 flex-shrink-0 mt-0.5">
                  <ArrowDownUp className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-emerald-200">
                    Urutan Upload: Sesuai Antrean (#1 &rarr; #{queue.length})
                  </p>
                  <p className="text-[11px] text-zinc-400 leading-relaxed mt-0.5">
                    Bot akan memproses dan mengunggah {queue.length} konten secara berurutan mulai dari antrean nomor #1 hingga #{queue.length} saat ini juga. Anda dapat memantau progres tiap postingan secara langsung.
                  </p>
                </div>
              </div>

              {/* Active Platforms Badge */}
              <div className="p-3 bg-zinc-950/70 border border-zinc-800 rounded-xl space-y-2">
                <span className="text-[11px] font-semibold text-zinc-400 block uppercase tracking-wider">
                  Target Platform Aktif:
                </span>
                <div className="flex items-center gap-2 flex-wrap">
                  {activePlatforms.map((p) => (
                    <span
                      key={p}
                      className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-200 flex items-center gap-1.5"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      {p === 'tiktok' ? 'TikTok Studio' : p === 'instagram' ? 'Instagram' : 'Facebook Fanpage'}
                    </span>
                  ))}
                  {activePlatforms.length === 0 && (
                    <span className="text-xs text-rose-400 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> Belum ada akun terhubung
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Queue List Preview (Always visible for both tabs) */}
          <div className="space-y-2 pt-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Daftar Antrean Upload ({queue.length} Item)
              </span>
              <span className="text-[10px] text-zinc-500 font-mono">
                {activeTab === 'schedule' ? 'Waktu Publikasi Bertahap' : 'Urutan Eksekusi'}
              </span>
            </div>

            <div className="space-y-1.5 max-h-56 overflow-y-auto custom-scrollbar pr-1">
              {(activeTab === 'schedule' ? scheduledQueueItems : queue).map((item, idx) => {
                const isFirst = idx === 0;
                const isLast = idx === queue.length - 1;

                return (
                  <div
                    key={item.item_key || idx}
                    className={`p-2.5 rounded-xl border flex items-center justify-between gap-3 transition ${
                      isFirst
                        ? 'bg-emerald-950/20 border-emerald-800/60 text-zinc-200'
                        : 'bg-zinc-950/50 border-zinc-800/80 text-zinc-300'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span
                        className={`w-5 h-5 flex items-center justify-center rounded-full text-[10px] font-mono font-bold flex-shrink-0 ${
                          isFirst
                            ? 'bg-emerald-500 text-black'
                            : 'bg-zinc-800 text-zinc-400'
                        }`}
                      >
                        {idx + 1}
                      </span>
                      <div className="p-1 rounded-md bg-zinc-900 border border-zinc-800 flex-shrink-0">
                        {getCategoryIcon(item.category)}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-zinc-200 truncate">
                          {item.name}
                        </p>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <p className="text-[10px] text-zinc-500 font-mono">
                            {item.category} • {formatDateDisplay(item.date)}
                          </p>
                          {Boolean(item.meta?.tiktok_product?.enabled) && (
                            <span
                              title={item.meta?.tiktok_product?.custom_title || item.meta?.tiktok_product?.title || 'Keranjang Kuning Aktif'}
                              className="text-[9px] px-1.5 py-0.2 rounded bg-amber-950/80 border border-amber-800/60 text-amber-300 font-mono font-semibold flex items-center gap-0.5"
                            >
                              <ShoppingBag className="w-2.5 h-2.5 text-amber-400" />
                              <span>Keranjang Kuning</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex-shrink-0 text-right">
                      {activeTab === 'schedule' ? (
                        <div className="flex flex-col items-end gap-0.5">
                          <span className="px-2 py-0.5 text-[10px] font-mono font-semibold rounded-md bg-cyan-950 border border-cyan-800/80 text-cyan-300 flex items-center gap-1">
                            <Clock className="w-2.5 h-2.5 text-cyan-400" />
                            {item.relative_display}
                          </span>
                          <span className="text-[9px] text-zinc-500 font-mono">
                            {isFirst ? (
                              <span className="text-emerald-400 font-semibold">Mulai Tayang</span>
                            ) : (
                              `+${item.offset_minutes}m`
                            )}
                          </span>
                        </div>
                      ) : (
                        <div>
                          {isFirst && (
                            <span className="px-2 py-0.5 text-[9px] font-bold rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase">
                              Mulai Pertama (#1)
                            </span>
                          )}
                          {isLast && queue.length > 1 && (
                            <span className="px-2 py-0.5 text-[9px] font-semibold rounded-md bg-zinc-800 text-zinc-400 border border-zinc-700 uppercase">
                              Terakhir (#{queue.length})
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-zinc-800 bg-zinc-950/80">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-zinc-400 hover:text-white bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-xl transition cursor-pointer"
            >
              Batal
            </button>

            {/* Clear All Schedule Button (if queue has scheduled items) */}
            {activeTab === 'schedule' && hasExistingScheduleInQueue && (
              <button
                type="button"
                onClick={handleClearScheduleClick}
                disabled={isApplyingSchedule}
                title="Hapus semua waktu jadwal pada antrean ini"
                className="px-3 py-2 text-xs font-medium text-rose-400 hover:text-rose-300 bg-rose-950/30 hover:bg-rose-950/50 border border-rose-800/40 rounded-xl transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Hapus Semua Jadwal</span>
              </button>
            )}
          </div>

          {activeTab === 'schedule' ? (
            <button
              type="button"
              onClick={handleApplyScheduleClick}
              disabled={queue.length === 0 || isApplyingSchedule}
              className={`px-5 py-2 text-xs font-bold rounded-xl flex items-center gap-2 transition shadow-lg ${
                queue.length === 0 || isApplyingSchedule
                  ? 'bg-zinc-800 text-zinc-500 border border-zinc-700/50 cursor-not-allowed opacity-60'
                  : 'bg-gradient-to-r from-cyan-600 via-teal-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white cursor-pointer active:scale-95 shadow-cyan-950/50'
              }`}
            >
              <CalendarClock className="w-3.5 h-3.5" />
              <span>
                {isApplyingSchedule
                  ? 'Menyimpan Jadwal...'
                  : `Terapkan Jadwal (${queue.length} Konten Bertahap)`}
              </span>
            </button>
          ) : (
            <button
              type="button"
              onClick={onConfirm}
              disabled={isPublishDisabled || queue.length === 0}
              className={`px-5 py-2 text-xs font-bold rounded-xl flex items-center gap-2 transition shadow-lg ${
                isPublishDisabled || queue.length === 0
                  ? 'bg-zinc-800 text-zinc-500 border border-zinc-700/50 cursor-not-allowed opacity-60'
                  : 'bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white cursor-pointer active:scale-95 shadow-emerald-950/50'
              }`}
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Mulai Upload Massal ({queue.length} Media)</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
