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

  const isCarousel = item.category === 'Carousel';
  const slideUrls = item.slide_urls && item.slide_urls.length > 0
    ? item.slide_urls
    : (item.slides && item.slides.length > 0
      ? item.slides.map((s) => `/api/content/media/${encodeURIComponent(item.account)}/${encodeURIComponent(item.category)}/${encodeURIComponent(item.date)}/${encodeURIComponent(item.name.split(' (')[0])}/${encodeURIComponent(s)}`)
      : (item.media_url ? [item.media_url] : []));

  if (isCarousel && slideUrls.length > 0) {
    const totalSlides = slideUrls.length;
    const currentSlideIdx = Math.min(
      Math.max(0, carouselSlideIndices[item.item_key] || 0),
      totalSlides - 1
    );
    const activeSlideUrl = slideUrls[currentSlideIdx] || slideUrls[0];

    return (
      <div className="w-full aspect-video rounded-xl bg-black border border-zinc-800 overflow-hidden flex items-center justify-center relative shadow-inner group">
        <img
          key={activeSlideUrl}
          src={activeSlideUrl}
          alt={`Slide ${currentSlideIdx + 1}`}
          className="w-full h-full object-contain bg-zinc-950 transition-all duration-200"
        />

        {/* Carousel Slide Navigator Controls (Left / Right Buttons) */}
        {totalSlides > 1 && (
          <div className="absolute inset-x-2 top-1/2 -translate-y-1/2 flex items-center justify-between pointer-events-none z-10">
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
              title="Slide Sebelumnya"
              className="pointer-events-auto w-8 h-8 rounded-full bg-black/80 hover:bg-black text-white border border-zinc-700/80 flex items-center justify-center disabled:opacity-20 disabled:cursor-not-allowed transition shadow-lg hover:scale-105"
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
              title="Slide Berikutnya"
              className="pointer-events-auto w-8 h-8 rounded-full bg-black/80 hover:bg-black text-white border border-zinc-700/80 flex items-center justify-center disabled:opacity-20 disabled:cursor-not-allowed transition shadow-lg hover:scale-105"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Bottom Center Slide Dots Indicator */}
        {totalSlides > 1 && (
          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center gap-1.5 bg-black/70 backdrop-blur-xs px-2.5 py-1 rounded-full border border-zinc-800 z-10">
            {slideUrls.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setCarouselSlideIndices((prev) => ({
                    ...prev,
                    [item.item_key]: i,
                  }));
                }}
                className={`transition-all rounded-full ${
                  i === currentSlideIdx
                    ? 'w-4 h-1.5 bg-purple-400'
                    : 'w-1.5 h-1.5 bg-zinc-600 hover:bg-zinc-400'
                }`}
                title={`Buka Slide ${i + 1}`}
              />
            ))}
          </div>
        )}

        {/* Slide Counter Badge (Bottom Right) */}
        <div className="absolute bottom-2 right-2 bg-black/85 backdrop-blur-xs text-[10px] font-mono font-bold text-zinc-200 px-2 py-0.5 rounded-md border border-zinc-700 z-10">
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
        className="w-full h-full object-contain bg-zinc-950"
      />
    </div>
  );
}
