import React from 'react';
import { Sparkles, AtSign } from 'lucide-react';

export default function CaptionEditorCard({
  selectedItem,
  currentEdit,
  currentHashtags,
  setEditedItems,
}) {
  return (
    <div className="flex flex-col gap-3">
      {/* 1. Main Shared Caption & Hashtags */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" /> Narasi Caption & Hashtags
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
              Semua Platform
            </span>
          </div>

          <span
            className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${
              currentHashtags.length <= 4
                ? 'bg-zinc-800 text-emerald-400 border border-zinc-700'
                : 'bg-red-950 text-red-400 border border-red-800'
            }`}
          >
            {currentHashtags.length}/4 Hashtags
          </span>
        </div>

        <textarea
          rows={3}
          value={currentEdit?.caption || ''}
          onChange={(e) =>
            setEditedItems((prev) => ({
              ...prev,
              [selectedItem.item_key]: {
                ...prev[selectedItem.item_key],
                caption: e.target.value,
              },
            }))
          }
          className="w-full bg-zinc-950 border border-zinc-800 focus:border-zinc-600 rounded-xl p-3 text-xs text-zinc-200 outline-none resize-none leading-relaxed transition font-sans font-normal placeholder-zinc-600"
          placeholder="Ketik atau edit narasi caption utama di sini..."
        />

        {/* Hashtag Pills Badge */}
        {currentHashtags.length > 0 && (
          <div className="flex items-center flex-wrap gap-1.5 pt-0.5">
            {currentHashtags.map((tag, idx) => (
              <span
                key={idx}
                className="text-[11px] font-mono bg-zinc-950 border border-zinc-800 text-zinc-300 px-2 py-0.5 rounded-md"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 2. Independent Tag / Mention Form (TikTok & Instagram) */}
      <div className="p-3 bg-zinc-950/70 border border-zinc-800/80 rounded-xl space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-zinc-300 flex items-center gap-1.5">
            <AtSign className="w-3.5 h-3.5 text-cyan-400" /> Tag / Mention Akun Independen
          </span>
          <span className="text-[9px] font-mono text-zinc-500">
            Username spesifik platform
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {/* TikTok Tag / Mention */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-medium text-zinc-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
              <span>Tag TikTok:</span>
            </label>
            <input
              type="text"
              value={currentEdit?.tiktokMentions || ''}
              onChange={(e) =>
                setEditedItems((prev) => ({
                  ...prev,
                  [selectedItem.item_key]: {
                    ...prev[selectedItem.item_key],
                    tiktokMentions: e.target.value,
                  },
                }))
              }
              placeholder="@username_tt @partner"
              className="w-full bg-zinc-900/90 border border-zinc-800 focus:border-cyan-500/70 rounded-lg px-2.5 py-1.5 text-xs text-cyan-200 outline-none transition placeholder-zinc-600 font-mono"
            />
          </div>

          {/* Instagram Tag / Mention */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-medium text-zinc-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-pink-400"></span>
              <span>Tag Instagram:</span>
            </label>
            <input
              type="text"
              value={currentEdit?.instagramMentions || ''}
              onChange={(e) =>
                setEditedItems((prev) => ({
                  ...prev,
                  [selectedItem.item_key]: {
                    ...prev[selectedItem.item_key],
                    instagramMentions: e.target.value,
                  },
                }))
              }
              placeholder="@username_ig @partner"
              className="w-full bg-zinc-900/90 border border-zinc-800 focus:border-pink-500/70 rounded-lg px-2.5 py-1.5 text-xs text-pink-200 outline-none transition placeholder-zinc-600 font-mono"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
