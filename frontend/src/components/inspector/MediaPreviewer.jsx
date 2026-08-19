import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function MediaPreviewer({
  item,
  carouselSlideIndices,
  setCarouselSlideIndices,
}) {
  if (!item) return null;

  if (item.category === 'Video') {
    return (
      <div className="w-full aspect-video rounded-xl bg-black border border-zinc-800 overflow-hidden flex items-center justify-center relative shadow-inner">
        <video
          key={item.media_url}
          src={item.media_url}
          controls
          className="w-full h-full object-contain"
        />
      </div>
    );
  }

  if (item.category === 'Carousel' && item.slides && item.slides.length > 0) {
    const currentSlideIdx = carouselSlideIndices[item.item_key] || 0;
    const totalSlides = item.slides.length;
    const slideName = item.slides[currentSlideIdx];
    const slideCleanName = slideName ? slideName.replace(/^.*[\\/]/, '') : '';
    const activeSlideUrl = `/api/content/media/${encodeURIComponent(item.account)}/${encodeURIComponent(item.category)}/${encodeURIComponent(item.date)}/${encodeURIComponent(item.name)}/${encodeURIComponent(slideCleanName)}`;

    return (
      <div className="w-full aspect-video rounded-xl bg-black border border-zinc-800 overflow-hidden flex items-center justify-center relative shadow-inner group">
        <img
          src={activeSlideUrl}
          alt={`Slide ${currentSlideIdx + 1}`}
          className="w-full h-full object-contain"
        />

        {/* Carousel Slide Navigator Controls */}
        <div className="absolute inset-x-2 top-1/2 -translate-y-1/2 flex items-center justify-between pointer-events-none">
          <button
            type="button"
            disabled={currentSlideIdx === 0}
            onClick={(e) => {
              e.stopPropagation();
              setCarouselSlideIndices((prev) => ({
                ...prev,
                [item.item_key]: Math.max(0, currentSlideIdx - 1),
              }));
            }}
            className="pointer-events-auto p-1.5 rounded-full bg-black/70 hover:bg-black text-white border border-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <button
            type="button"
            disabled={currentSlideIdx === totalSlides - 1}
            onClick={(e) => {
              e.stopPropagation();
              setCarouselSlideIndices((prev) => ({
                ...prev,
                [item.item_key]: Math.min(totalSlides - 1, currentSlideIdx + 1),
              }));
            }}
            className="pointer-events-auto p-1.5 rounded-full bg-black/70 hover:bg-black text-white border border-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed transition"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Slide Counter Badge */}
        <div className="absolute bottom-2 right-2 bg-black/80 backdrop-blur-xs text-[10px] font-mono font-bold text-zinc-200 px-2 py-0.5 rounded-md border border-zinc-700">
          Slide {currentSlideIdx + 1} / {totalSlides}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full aspect-video rounded-xl bg-black border border-zinc-800 overflow-hidden flex items-center justify-center relative shadow-inner">
      <img
        src={item.media_url}
        alt={item.name}
        className="w-full h-full object-contain"
      />
    </div>
  );
}
