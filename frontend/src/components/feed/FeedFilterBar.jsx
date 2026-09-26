import React, { useRef } from 'react';
import { Zap } from 'lucide-react';
import { getLocalTodayDate } from '../../utils/dateUtils';

export default function FeedFilterBar({
  filterCategory,
  setFilterCategory,
  filterDate,
  setFilterDate,
  filterStatus,
  setFilterStatus,
  sortBy,
  setSortBy,
  availableDates,
  unuploadedCount = 0,
  onOpenMassUpload,
  batchPublishing = false,
}) {
  const todayStr = getLocalTodayDate();
  const datePickerRef = useRef(null);

  const handleDateSelectChange = (e) => {
    const val = e.target.value;
    if (val === 'CUSTOM_PICKER') {
      if (datePickerRef.current) {
        if (typeof datePickerRef.current.showPicker === 'function') {
          datePickerRef.current.showPicker();
        } else {
          datePickerRef.current.focus();
        }
      }
    } else {
      setFilterDate(val);
    }
  };

  return (
    <div className="flex items-center justify-between gap-3 bg-zinc-900/70 border border-zinc-800/80 p-2.5 rounded-xl flex-wrap">
      {/* Category Tabs */}
      <div className="flex items-center gap-1">
        {['All', 'Video', 'Poster', 'Carousel'].map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              filterCategory === cat
                ? 'bg-zinc-800 text-zinc-100 font-semibold border border-zinc-700/60'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {cat === 'All' ? 'Semua' : cat}
          </button>
        ))}
      </div>

      {/* Date, Status & Sort Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Sort Selector */}
        <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-1">
          <span className="text-[10px] text-zinc-500 font-medium">Sort:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-transparent text-xs text-cyan-300 font-medium outline-none cursor-pointer"
          >
            <option value="custom" className="bg-zinc-900 text-emerald-300 font-semibold">
              🔀 Urutan Manual (Kustom)
            </option>
            <option value="date-desc" className="bg-zinc-900 text-zinc-200">
              📅 Tanggal (Terbaru)
            </option>
            <option value="date-asc" className="bg-zinc-900 text-zinc-200">
              ⏳ Tanggal (Terlama)
            </option>
            <option value="name-asc" className="bg-zinc-900 text-zinc-200">
              🔤 Nama (A - Z)
            </option>
            <option value="name-desc" className="bg-zinc-900 text-zinc-200">
              🔤 Nama (Z - A)
            </option>
            <option value="status-pending" className="bg-zinc-900 text-zinc-200">
              ⚡ Status (Pending Dulu)
            </option>
          </select>
        </div>

        {/* Single Unified Date Selector */}
        <div className="relative flex items-center">
          <select
            value={filterDate}
            onChange={handleDateSelectChange}
            className="bg-zinc-900 border border-zinc-800 text-xs text-zinc-200 font-medium px-2.5 py-1.5 rounded-lg outline-none cursor-pointer focus:border-zinc-700"
          >
            <option value="TODAY" className="bg-zinc-900 text-emerald-400 font-semibold">
              📅 Hari Ini ({todayStr})
            </option>
            <option value="All" className="bg-zinc-900 text-zinc-200">
              🌐 Semua Tanggal
            </option>
            {availableDates
              .filter((d) => d !== todayStr)
              .map((d) => (
                <option key={d} value={d} className="bg-zinc-900 text-zinc-300">
                  📁 {d}
                </option>
              ))}
            {/* Opsi jika user memilih tanggal kustom */}
            {filterDate !== 'TODAY' && filterDate !== 'All' && !availableDates.includes(filterDate) && (
              <option value={filterDate} className="bg-zinc-900 text-cyan-300 font-semibold">
                🗓️ {filterDate} (Kustom)
              </option>
            )}
            <option value="CUSTOM_PICKER" className="bg-zinc-900 text-indigo-300 font-medium">
              🗓️ Pilih Tanggal Lain...
            </option>
          </select>

          {/* Hidden Date Input triggered by 'Pilih Tanggal Lain...' */}
          <input
            ref={datePickerRef}
            type="date"
            onChange={(e) => {
              if (e.target.value) {
                setFilterDate(e.target.value === todayStr ? 'TODAY' : e.target.value);
              }
            }}
            className="sr-only absolute pointer-events-none"
            tabIndex={-1}
            aria-hidden="true"
          />
        </div>

        {/* Status Filter */}
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="bg-zinc-900 border border-zinc-800 text-xs text-zinc-300 px-2 py-1.5 rounded-lg outline-none cursor-pointer focus:border-zinc-700"
        >
          <option value="All">Semua Status</option>
          <option value="PENDING">⚡ Belum Diposting (Pending)</option>
          <option value="TIKTOK_ONLY">🎬 TikTok Saja</option>
          <option value="INSTAGRAM_ONLY">📸 Instagram Saja</option>
          <option value="FACEBOOK_ONLY">📘 Facebook Saja</option>
          <option value="ALL_PLATFORMS">✅ Semua Platform (TT · IG · FB)</option>
        </select>

        {/* Upload Massal Button (Far Right of Sort & Filter Box) */}
        <button
          type="button"
          onClick={onOpenMassUpload}
          disabled={unuploadedCount === 0 || batchPublishing}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition shadow-sm select-none ${
            unuploadedCount > 0 && !batchPublishing
              ? 'bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white cursor-pointer active:scale-95 shadow-emerald-950/50'
              : 'bg-zinc-900 border border-zinc-800 text-zinc-500 cursor-not-allowed opacity-60'
          }`}
          title={
            unuploadedCount > 0
              ? `Upload massal ${unuploadedCount} media pending berurutan dari bawah ke atas`
              : 'Semua media pada filter ini sudah terupload'
          }
        >
          <Zap className={`w-3.5 h-3.5 ${unuploadedCount > 0 && !batchPublishing ? 'text-amber-300 fill-amber-300' : 'text-zinc-500'}`} />
          <span>Upload Massal</span>
          {unuploadedCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-700/60 font-extrabold">
              {unuploadedCount}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
