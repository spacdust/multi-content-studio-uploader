import React from 'react';
import { Music, Search, Star, Shuffle } from 'lucide-react';

export default function TikTokSoundCard({
  selectedItem,
  currentEdit,
  setEditedItems,
}) {
  const soundMode = currentEdit?.soundMode || 'favorite';
  const defaultDb = selectedItem?.category === 'Video' ? '-7' : '0';
  const soundDbValue = currentEdit?.soundDb !== undefined && currentEdit?.soundDb !== null ? currentEdit.soundDb : defaultDb;

  return (
    <div className="bg-zinc-950/70 p-3.5 rounded-xl border border-zinc-800 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold text-zinc-300 flex items-center gap-1.5">
            <Music className="w-3.5 h-3.5 text-cyan-400" /> Mode Audio / Sound TikTok
          </span>
          <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-cyan-950/80 border border-cyan-800/60 text-cyan-300 font-semibold">
            Khusus TikTok
          </span>
        </div>

        {/* Segmented Mode Selector: Search Query vs Random Favorite */}
        <div className="flex items-center p-0.5 rounded-lg bg-zinc-900 border border-zinc-800 text-[10px] font-medium">
          <button
            type="button"
            onClick={() =>
              setEditedItems((prev) => ({
                ...prev,
                [selectedItem.item_key]: {
                  ...prev[selectedItem.item_key],
                  soundMode: 'search',
                },
              }))
            }
            className={`px-2.5 py-1 rounded-md transition flex items-center gap-1 ${
              soundMode === 'search'
                ? 'bg-cyan-500/20 text-cyan-300 font-semibold shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Search className="w-2.5 h-2.5" />
            <span>Cari Sound</span>
          </button>

          <button
            type="button"
            onClick={() =>
              setEditedItems((prev) => ({
                ...prev,
                [selectedItem.item_key]: {
                  ...prev[selectedItem.item_key],
                  soundMode: 'favorite',
                },
              }))
            }
            className={`px-2.5 py-1 rounded-md transition flex items-center gap-1 ${
              soundMode === 'favorite'
                ? 'bg-amber-500/20 text-amber-300 font-semibold shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Star className="w-2.5 h-2.5" />
            <span>Favorite (Random)</span>
          </button>
        </div>
      </div>

      {/* Mode 1: Search Query Input */}
      {soundMode === 'search' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="text-[10px] text-zinc-400 font-medium block mb-1">
              Kata Kunci Pencarian Sound:
            </label>
            <input
              type="text"
              value={currentEdit?.soundQuery || ''}
              onChange={(e) =>
                setEditedItems((prev) => ({
                  ...prev,
                  [selectedItem.item_key]: {
                    ...prev[selectedItem.item_key],
                    soundQuery: e.target.value,
                  },
                }))
              }
              placeholder="Opsional: misal nasyid, santri, dll"
              className="w-full bg-zinc-900 border border-zinc-800 px-2.5 py-1.5 rounded-lg text-xs text-cyan-300 outline-none font-mono placeholder:text-zinc-600 focus:border-cyan-500/50"
            />
          </div>

          <div>
            <label className="text-[10px] text-zinc-400 font-medium block mb-1">
              Pengaturan Volume (dB):
            </label>
            <input
              type="text"
              value={soundDbValue}
              onChange={(e) =>
                setEditedItems((prev) => ({
                  ...prev,
                  [selectedItem.item_key]: {
                    ...prev[selectedItem.item_key],
                    soundDb: e.target.value,
                  },
                }))
              }
              placeholder={defaultDb}
              className="w-full bg-zinc-900 border border-zinc-800 px-2.5 py-1.5 rounded-lg text-xs text-amber-300 outline-none font-mono placeholder:text-zinc-600 focus:border-amber-500/50"
            />
          </div>
        </div>
      ) : (
        /* Mode 2: Random Favorite Sound */
        <div className="flex flex-col gap-2.5">
          <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-800/40 flex items-start gap-2.5">
            <div className="p-1 rounded-md bg-amber-500/10 text-amber-400 flex-shrink-0 mt-0.5">
              <Shuffle className="w-3.5 h-3.5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[11px] font-semibold text-amber-200">
                Mode Pustaka Suara Favorit (Randomizer)
              </p>
              <p className="text-[10px] text-zinc-400 leading-relaxed mt-0.5">
                Bot otomatis masuk ke tab <strong>Favorites</strong> di TikTok Studio akun ini dan memilih salah satu musik favorit Anda secara <strong>acak (random)</strong> agar sound tiap postingan bervariasi.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 pt-1">
            <span className="text-[10px] text-zinc-400">Pengaturan Volume Latar Belakang:</span>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-mono text-zinc-500">dB:</span>
              <input
                type="text"
                value={soundDbValue}
                onChange={(e) =>
                  setEditedItems((prev) => ({
                    ...prev,
                    [selectedItem.item_key]: {
                      ...prev[selectedItem.item_key],
                      soundDb: e.target.value,
                    },
                  }))
                }
                placeholder={defaultDb}
                className="w-20 bg-zinc-900 border border-zinc-800 px-2 py-1 rounded-lg text-xs text-amber-300 text-center font-mono outline-none focus:border-amber-500/50"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
