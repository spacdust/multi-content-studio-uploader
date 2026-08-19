// Category visual configuration & presets

export const CATEGORY_COLORS = {
  Video: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  Poster: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  Carousel: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
};

export const CATEGORY_BADGES = {
  Video: '🎬 Video',
  Poster: '🖼️ Poster',
  Carousel: '📑 Carousel',
};

export const QUICK_PRESETS = [
  { label: 'Hari Ini (19:30)', hours: 19, mins: 30, dayOffset: 0 },
  { label: 'Hari Ini (21:00)', hours: 21, mins: 0, dayOffset: 0 },
  { label: 'Besok (12:00)', hours: 12, mins: 0, dayOffset: 1 },
  { label: 'Besok (19:30)', hours: 19, mins: 30, dayOffset: 1 },
];
