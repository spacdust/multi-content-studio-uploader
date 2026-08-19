import React from 'react';
import { Calendar } from 'lucide-react';

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
  setShowAddDateModal,
}) {
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

      {/* Date, Status & Sort Dropdowns */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Sort Selector */}
        <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-1">
          <span className="text-[10px] text-zinc-500 font-medium">Sort:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-transparent text-xs text-cyan-300 font-medium outline-none cursor-pointer"
          >
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

        {/* Date Filter */}
        <select
          value={filterDate}
          onChange={(e) => setFilterDate(e.target.value)}
          className="bg-zinc-900 border border-zinc-800 text-xs text-zinc-300 px-2 py-1 rounded-lg outline-none cursor-pointer"
        >
          <option value="All">Semua Tanggal</option>
          {availableDates.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>

        {/* Status Filter */}
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="bg-zinc-900 border border-zinc-800 text-xs text-zinc-300 px-2 py-1 rounded-lg outline-none cursor-pointer"
        >
          <option value="All">Semua Status</option>
          <option value="PENDING">⚡ Belum Diposting (Pending)</option>
          <option value="TIKTOK_ONLY">🎬 TikTok Saja</option>
          <option value="META_ONLY">⚡ Meta Suite Saja</option>
          <option value="ALL_PLATFORMS">✅ Semua Platform (TT & Meta)</option>
        </select>

        {/* Add Date Folder Button */}
        <button
          onClick={() => setShowAddDateModal(true)}
          title="Inisialisasi Tanggal Baru"
          className="p-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 rounded-lg transition"
        >
          <Calendar className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
