import React from 'react';
import { Film, Image as ImageIcon, Layers, Sparkles, Save, Check } from 'lucide-react';
import MediaPreviewer from './MediaPreviewer';
import ScheduleSettingCard from './ScheduleSettingCard';
import CaptionEditorCard from './CaptionEditorCard';
import TikTokSoundCard from './TikTokSoundCard';
import PublishActionCenter from './PublishActionCenter';
import { CATEGORY_COLORS } from '../../utils/constants';
import { formatDateDisplay } from '../../utils/dateUtils';

export default function StudioInspector({
  selectedItem,
  currentEdit,
  isInspectorScheduled,
  currentHashtags,
  carouselSlideIndices,
  setCarouselSlideIndices,
  setEditedItems,
  generatingCaption,
  handleGenerateCaption,
  handleSaveCaption,
  uploadingItem,
  isPublishDisabled,
  publishBtnText,
  activePlatforms,
  currentAccData,
  handleUploadItem,
}) {
  if (!selectedItem) {
    return (
      <aside className="lg:col-span-5 bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-5 flex flex-col gap-4 sticky top-20 shadow-xl">
        <div className="py-24 text-center text-zinc-500 text-xs font-medium">
          Pilih salah satu konten di panel kiri untuk membuka Studio Inspector.
        </div>
      </aside>
    );
  }

  return (
    <aside className="lg:col-span-5 bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-5 flex flex-col gap-4 sticky top-20 shadow-xl backdrop-blur-xs">
      {/* Inspector Header */}
      <div className="flex items-start justify-between gap-3 border-b border-zinc-800/80 pb-3.5">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span
              className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md border flex items-center gap-1 ${
                CATEGORY_COLORS[selectedItem.category] || 'bg-zinc-800 text-zinc-300'
              }`}
            >
              {selectedItem.category === 'Video' && <Film className="w-2.5 h-2.5" />}
              {selectedItem.category === 'Poster' && <ImageIcon className="w-2.5 h-2.5" />}
              {selectedItem.category === 'Carousel' && <Layers className="w-2.5 h-2.5" />}
              <span>{selectedItem.category}</span>
            </span>

            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-zinc-950 border border-zinc-800 text-zinc-400">
              📅 {formatDateDisplay(selectedItem.date)}
            </span>
          </div>

          <h2 className="text-sm font-bold text-zinc-100 truncate" title={selectedItem.name}>
            {selectedItem.name}
          </h2>
        </div>

        {/* AI Generator & Quick Save Actions */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <button
            type="button"
            onClick={() => handleGenerateCaption(selectedItem)}
            disabled={generatingCaption === selectedItem.item_key}
            title="Generate AI Caption & Hashtags"
            className="px-2.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-750 text-emerald-400 border border-zinc-700 rounded-xl text-xs font-semibold flex items-center gap-1 transition shadow-xs disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${generatingCaption === selectedItem.item_key ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">AI Caption</span>
          </button>

          <button
            type="button"
            onClick={() => handleSaveCaption(selectedItem)}
            title="Simpan Perubahan Metadata & Caption"
            className="px-2.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-750 text-zinc-200 border border-zinc-700 rounded-xl text-xs font-semibold flex items-center gap-1 transition shadow-xs"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Simpan</span>
          </button>
        </div>
      </div>

      {/* 1. Media Preview Area (Video, Poster, Carousel) */}
      <MediaPreviewer
        item={selectedItem}
        carouselSlideIndices={carouselSlideIndices}
        setCarouselSlideIndices={setCarouselSlideIndices}
      />

      {/* 2. Schedule Setting Card */}
      <ScheduleSettingCard
        selectedItem={selectedItem}
        currentEdit={currentEdit}
        isInspectorScheduled={isInspectorScheduled}
        setEditedItems={setEditedItems}
      />

      {/* 3. AI Caption & Hashtags Editor */}
      <CaptionEditorCard
        selectedItem={selectedItem}
        currentEdit={currentEdit}
        currentHashtags={currentHashtags}
        setEditedItems={setEditedItems}
      />

      {/* 4. TikTok Audio / Sound Controller */}
      <TikTokSoundCard
        selectedItem={selectedItem}
        currentEdit={currentEdit}
        setEditedItems={setEditedItems}
      />

      {/* 5. Publish Action Center */}
      <PublishActionCenter
        selectedItem={selectedItem}
        uploadingItem={uploadingItem}
        isPublishDisabled={isPublishDisabled}
        publishBtnText={publishBtnText}
        activePlatforms={activePlatforms}
        currentAccData={currentAccData}
        handleUploadItem={handleUploadItem}
      />
    </aside>
  );
}
