import React from 'react';
import { Sparkles } from 'lucide-react';

export default function CaptionEditorCard({
  selectedItem,
  currentEdit,
  currentHashtags,
  setEditedItems,
}) {
  return (
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
        rows={4}
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
        placeholder="Ketik atau edit caption di sini..."
      />

      {/* Hashtag Pills Badge */}
      {currentHashtags.length > 0 && (
        <div className="flex items-center flex-wrap gap-1.5 pt-1">
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
  );
}
