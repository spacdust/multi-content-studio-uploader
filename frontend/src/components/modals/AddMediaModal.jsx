import React, { useState, useRef } from 'react';
import {
  Upload,
  Layers,
  Film,
  Image as ImageIcon,
  ArrowUp,
  ArrowDown,
  Trash2,
  Plus,
  X,
  Sparkles,
} from 'lucide-react';
import { getLocalNowIso, getLocalTodayDate } from '../../utils/dateUtils';

export default function AddMediaModal({
  show,
  onClose,
  selectedAccount,
  availableDates,
  singleMediaFile,
  setSingleMediaFile,
  singleMediaPreviewUrl,
  setSingleMediaPreviewUrl,
  selectedMediaFiles = [],
  setSelectedMediaFiles,
  carouselSlides,
  setCarouselSlides,
  isScheduledUpload,
  setIsScheduledUpload,
  uploadScheduleTime,
  setUploadScheduleTime,
  uploadDate,
  setUploadDate,
  carouselNameInput,
  setCarouselNameInput,
  uploadingFileState,
  handleMediaFileUpload,
}) {
  const [activeTab, setActiveTab] = useState('Video'); // 'Video' | 'Poster' | 'Carousel'
  const fileInputRef = useRef(null);
  const carouselInputRef = useRef(null);

  if (!show) return null;

  // Multi-file picker for Video & Poster
  const handleMediaFilesChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    const newMediaItems = files.map((file, idx) => ({
      id: `${Date.now()}_${idx}_${Math.random().toString(36).substr(2, 5)}`,
      file,
      previewUrl: URL.createObjectURL(file),
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2),
      type: file.type || (activeTab === 'Video' ? 'video/mp4' : 'image/jpeg'),
    }));

    const updated = [...(selectedMediaFiles || []), ...newMediaItems];
    if (setSelectedMediaFiles) setSelectedMediaFiles(updated);

    if (updated.length > 0) {
      setSingleMediaFile(updated[0].file);
      setSingleMediaPreviewUrl(updated[0].previewUrl);
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeMediaFile = (index) => {
    const updated = (selectedMediaFiles || []).filter((_, i) => i !== index);
    if (setSelectedMediaFiles) setSelectedMediaFiles(updated);

    if (updated.length > 0) {
      setSingleMediaFile(updated[0].file);
      setSingleMediaPreviewUrl(updated[0].previewUrl);
    } else {
      setSingleMediaFile(null);
      setSingleMediaPreviewUrl(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const clearAllMediaFiles = () => {
    if (setSelectedMediaFiles) setSelectedMediaFiles([]);
    setSingleMediaFile(null);
    setSingleMediaPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleClose = () => {
    clearAllMediaFiles();
    setCarouselSlides([]);
    onClose();
  };

  // Multi-file picker for Carousel (appends new files)
  const handleCarouselFilesChange = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    const newSlides = files.map((file, idx) => ({
      id: `${Date.now()}_${idx}_${Math.random().toString(36).substr(2, 5)}`,
      file,
      previewUrl: URL.createObjectURL(file),
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2),
    }));

    setCarouselSlides((prev) => [...prev, ...newSlides]);
    if (carouselInputRef.current) {
      carouselInputRef.current.value = '';
    }
  };

  // Move slide up / down to rearrange order
  const moveSlide = (index, direction) => {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= carouselSlides.length) return;
    const updated = [...carouselSlides];
    const temp = updated[index];
    updated[index] = updated[targetIndex];
    updated[targetIndex] = temp;
    setCarouselSlides(updated);
  };

  // Remove individual slide
  const removeSlide = (index) => {
    const updated = carouselSlides.filter((_, i) => i !== index);
    setCarouselSlides(updated);
  };

  // Clear all carousel slides
  const clearAllSlides = () => {
    setCarouselSlides([]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleMediaFileUpload(activeTab, uploadDate, carouselNameInput);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-3xl w-full p-6 shadow-2xl flex flex-col gap-4 max-h-[90vh] overflow-y-auto animate-fadeIn custom-scrollbar">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
              <Upload className="w-4 h-4 text-emerald-400" /> Tambah Media ke Antrean
            </h3>
            <p className="text-xs text-zinc-400">
              Akun Target: <strong className="text-zinc-200">{selectedAccount}</strong>
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="p-1 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Category Tabs */}
          <div className="grid grid-cols-3 gap-2 bg-zinc-950 p-1 rounded-xl border border-zinc-800 text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setActiveTab('Video');
                clearAllMediaFiles();
                setCarouselSlides([]);
              }}
              className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition ${
                activeTab === 'Video'
                  ? 'bg-zinc-800 text-emerald-400 shadow-sm border border-zinc-700/60'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Film className="w-3.5 h-3.5" />
              <span>Video (Reels/TikTok)</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveTab('Poster');
                clearAllMediaFiles();
                setCarouselSlides([]);
              }}
              className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition ${
                activeTab === 'Poster'
                  ? 'bg-zinc-800 text-blue-400 shadow-sm border border-zinc-700/60'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <ImageIcon className="w-3.5 h-3.5" />
              <span>Poster (Single)</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveTab('Carousel');
                clearAllMediaFiles();
                setCarouselSlides([]);
              }}
              className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition ${
                activeTab === 'Carousel'
                  ? 'bg-zinc-800 text-purple-400 shadow-sm border border-zinc-700/60'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Carousel (Multi-Slide)</span>
            </button>
          </div>

          {/* Date Selector */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-zinc-300 font-medium">Tanggal Folder Konten:</label>
            <input
              type="date"
              required
              value={uploadDate}
              onChange={(e) => setUploadDate(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 px-3 py-2 rounded-xl text-xs text-zinc-100 outline-none focus:border-zinc-600 font-medium"
            />
          </div>

          {/* Section: File Picker & Multi-Video/Poster Selection */}
          {activeTab !== 'Carousel' ? (
            <div className="flex flex-col gap-2.5">
              <div>
                <label className="text-xs text-zinc-200 font-semibold flex items-center gap-1.5">
                  {activeTab === 'Video' ? <Film className="w-3.5 h-3.5 text-emerald-400" /> : <ImageIcon className="w-3.5 h-3.5 text-blue-400" />}
                  Pilih File {activeTab === 'Video' ? 'Video (.mp4, .mov, .webm)' : 'Gambar Poster (.jpg, .png, .webp)'}:
                </label>
                <p className="text-[11px] text-zinc-400 mt-0.5">
                  💡 <strong>Bisa pilih banyak file sekaligus</strong> (misal 5 video). Setiap video akan otomatis diunggah menjadi Reel / Video terpisah di antrean!
                </p>
              </div>

              {/* Multi-File Upload Input (if no files chosen yet) */}
              {(!selectedMediaFiles || selectedMediaFiles.length === 0) && (
                <div className="flex items-center gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    required
                    accept={
                      activeTab === 'Video'
                        ? 'video/mp4,video/quicktime,video/webm'
                        : 'image/jpeg,image/png,image/webp'
                    }
                    onChange={handleMediaFilesChange}
                    className="w-full text-xs text-zinc-400 file:mr-3 file:py-2 file:px-3.5 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-700 cursor-pointer border border-zinc-800 rounded-xl bg-zinc-950/60 p-1"
                  />
                </div>
              )}

              {/* Hidden input to allow adding more files when list is active */}
              {selectedMediaFiles && selectedMediaFiles.length > 0 && (
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept={
                    activeTab === 'Video'
                      ? 'video/mp4,video/quicktime,video/webm'
                      : 'image/jpeg,image/png,image/webp'
                  }
                  onChange={handleMediaFilesChange}
                  className="hidden"
                />
              )}

              {/* Single File Preview Mode (if exactly 1 file selected) */}
              {selectedMediaFiles && selectedMediaFiles.length === 1 && (
                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between bg-zinc-950/60 p-2.5 rounded-xl border border-zinc-800 text-xs">
                    <span className="text-zinc-300 font-medium truncate flex-1 pr-2">
                      {selectedMediaFiles[0].name} ({selectedMediaFiles[0].size} MB)
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="text-[11px] font-medium text-emerald-400 hover:text-emerald-300 bg-emerald-950/40 px-2 py-1 rounded-lg border border-emerald-800/40 flex items-center gap-1 transition"
                      >
                        <Plus className="w-3 h-3" /> Tambah Video Lagi
                      </button>
                      <button
                        type="button"
                        onClick={clearAllMediaFiles}
                        className="text-[11px] font-medium text-red-400 hover:text-red-300 px-2 py-1 transition"
                      >
                        Ganti File
                      </button>
                    </div>
                  </div>

                  <div className="w-full aspect-video rounded-xl bg-black overflow-hidden flex items-center justify-center border border-zinc-800 shadow-inner relative">
                    {activeTab === 'Video' ? (
                      <video
                        src={selectedMediaFiles[0].previewUrl}
                        controls
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <img
                        src={selectedMediaFiles[0].previewUrl}
                        alt="Preview"
                        className="w-full h-full object-contain"
                      />
                    )}
                    <div className="absolute top-2 left-2 bg-black/80 px-2 py-0.5 rounded text-[10px] font-mono text-zinc-300">
                      {selectedMediaFiles[0].name}
                    </div>
                  </div>
                </div>
              )}

              {/* Multi-Files List Mode (if 2 or more files selected) */}
              {selectedMediaFiles && selectedMediaFiles.length > 1 && (
                <div className="flex flex-col gap-2.5">
                  <div className="flex items-center justify-between bg-emerald-950/40 border border-emerald-800/50 p-3 rounded-xl">
                    <div className="flex items-center gap-2.5">
                      <Film className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      <div>
                        <span className="text-xs font-bold text-emerald-300">
                          {selectedMediaFiles.length} {activeTab === 'Video' ? 'Video Dipilih' : 'Poster Dipilih'}
                        </span>
                        <p className="text-[11px] text-emerald-400/80">
                          Otomatis menjadi {selectedMediaFiles.length} {activeTab === 'Video' ? 'Reel/Video terpisah di antrean' : 'Poster terpisah'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="text-xs font-medium text-zinc-200 hover:text-white bg-zinc-800 hover:bg-zinc-700 px-2.5 py-1.5 rounded-lg border border-zinc-700 flex items-center gap-1 transition shadow-sm"
                      >
                        <Plus className="w-3.5 h-3.5" /> Tambah Lagi
                      </button>
                      <button
                        type="button"
                        onClick={clearAllMediaFiles}
                        className="text-xs font-medium text-red-400 hover:text-red-300 px-2 py-1.5 transition"
                      >
                        Hapus Semua
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto p-1.5 bg-zinc-950/80 rounded-xl border border-zinc-800 custom-scrollbar">
                    {selectedMediaFiles.map((m, idx) => (
                      <div
                        key={m.id || idx}
                        className="p-2.5 bg-zinc-900 border border-zinc-800/80 hover:border-zinc-700 rounded-xl flex items-center justify-between gap-3 transition"
                      >
                        <div className="flex items-center gap-3 min-w-0 flex-1">
                          <div className="w-12 h-12 rounded-lg bg-black border border-zinc-800 overflow-hidden flex items-center justify-center flex-shrink-0 relative">
                            {activeTab === 'Video' ? (
                              <video src={m.previewUrl} className="w-full h-full object-cover" />
                            ) : (
                              <img src={m.previewUrl} alt={m.name} className="w-full h-full object-cover" />
                            )}
                            <span className="absolute bottom-0.5 right-0.5 bg-black/80 text-[9px] font-mono font-bold text-zinc-300 px-1 rounded">
                              #{idx + 1}
                            </span>
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-medium text-zinc-200 truncate">{m.name}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-[10px] text-zinc-400">{m.size} MB</span>
                              <span className="text-[10px] text-emerald-400/90 bg-emerald-950/60 px-1.5 py-0.2 rounded border border-emerald-800/40">
                                {activeTab === 'Video' ? `Reel #${idx + 1}` : `Poster #${idx + 1}`}
                              </span>
                            </div>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeMediaFile(idx)}
                          className="p-1.5 text-zinc-400 hover:text-red-400 hover:bg-red-950/40 rounded-lg transition"
                          title="Hapus file ini"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Multi-Slide Carousel with Full Reordering & Multi-Select */
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-xs text-zinc-200 font-semibold flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-purple-400" /> Pilih & Atur Urutan Slide Carousel:
                  </label>
                  <p className="text-[11px] text-zinc-400">
                    Bisa memilih banyak gambar sekaligus. Urutan slide dapat digeser naik/turun sesuai susunan cerita.
                  </p>
                </div>

                {carouselSlides.length > 0 && (
                  <button
                    type="button"
                    onClick={clearAllSlides}
                    className="text-[11px] text-red-400 hover:text-red-300 font-medium transition"
                  >
                    Hapus Semua ({carouselSlides.length})
                  </button>
                )}
              </div>

              {/* Multi-File Upload Input (Supports Multiple & Append) */}
              <div className="flex items-center gap-2">
                <input
                  ref={carouselInputRef}
                  type="file"
                  multiple
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleCarouselFilesChange}
                  className="w-full text-xs text-zinc-400 file:mr-3 file:py-2 file:px-3.5 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-purple-950/60 file:text-purple-300 hover:file:bg-purple-900/60 cursor-pointer border border-zinc-800 rounded-xl bg-zinc-950/60 p-1"
                />
              </div>

              {/* Interactive Carousel Slide Reordering List with Large Thumbnails */}
              {carouselSlides.length > 0 ? (
                <div className="flex flex-col gap-2.5 max-h-[420px] overflow-y-auto p-2 bg-zinc-950/80 rounded-xl border border-zinc-800/90 custom-scrollbar">
                  {carouselSlides.map((slide, idx) => (
                    <div
                      key={slide.id || idx}
                      className="p-3 bg-zinc-900/90 hover:bg-zinc-850 border border-zinc-800 rounded-xl flex items-center justify-between gap-4 transition shadow-sm"
                    >
                      {/* Left: Big Thumbnail + Slide Number Badge + Details */}
                      <div className="flex items-center gap-3.5 min-w-0 flex-1">
                        {/* Slide Thumbnail Preview (Large & Clear) */}
                        <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-xl bg-black border border-zinc-700/80 overflow-hidden flex items-center justify-center relative flex-shrink-0 shadow-md">
                          <img
                            src={slide.previewUrl}
                            alt={`Slide ${idx + 1}`}
                            className="w-full h-full object-contain bg-zinc-950"
                          />
                          {/* Slide Number Badge */}
                          <div className="absolute top-1.5 left-1.5 px-2 py-0.5 rounded-md bg-purple-600/90 backdrop-blur-xs text-white font-mono font-extrabold text-[11px] shadow-sm">
                            #{idx + 1}
                          </div>
                        </div>

                        {/* File Details */}
                        <div className="flex flex-col gap-1 min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-purple-950/80 border border-purple-800/60 text-purple-300">
                              Urutan ke-{idx + 1}
                            </span>
                            <span className="text-[11px] font-mono text-zinc-400">
                              {slide.size ? `${slide.size} MB` : 'Gambar'}
                            </span>
                          </div>
                          <span className="text-xs font-semibold text-zinc-100 truncate">
                            {slide.name}
                          </span>
                          <span className="text-[11px] text-zinc-400">
                            Gunakan tombol panah di kanan untuk memindahkan urutan slide cerita.
                          </span>
                        </div>
                      </div>

                      {/* Right: Reordering Actions (Up, Down, Delete) */}
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <button
                          type="button"
                          disabled={idx === 0}
                          onClick={() => moveSlide(idx, -1)}
                          title="Geser ke Atas / Urutan Lebih Awal"
                          className="p-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700/60 disabled:opacity-25 disabled:cursor-not-allowed transition flex items-center gap-1 text-xs font-medium"
                        >
                          <ArrowUp className="w-4 h-4 text-purple-400" />
                          <span className="hidden sm:inline">Naik</span>
                        </button>

                        <button
                          type="button"
                          disabled={idx === carouselSlides.length - 1}
                          onClick={() => moveSlide(idx, 1)}
                          title="Geser ke Bawah / Urutan Berikutnya"
                          className="p-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700/60 disabled:opacity-25 disabled:cursor-not-allowed transition flex items-center gap-1 text-xs font-medium"
                        >
                          <ArrowDown className="w-4 h-4 text-purple-400" />
                          <span className="hidden sm:inline">Turun</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => removeSlide(idx)}
                          title="Hapus Slide Ini"
                          className="p-2 rounded-xl bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-800/50 transition ml-1"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 px-4 rounded-xl border border-dashed border-zinc-800 text-center flex flex-col items-center justify-center gap-1 bg-zinc-950/40">
                  <Layers className="w-6 h-6 text-zinc-600 mb-1" />
                  <p className="text-xs text-zinc-400 font-medium">Belum ada slide gambar yang dipilih</p>
                  <p className="text-[11px] text-zinc-500">
                    Pilih beberapa foto di atas untuk mulai menyusun carousel slide.
                  </p>
                </div>
              )}
            </div>
          )}


          {/* Submit Button */}
          <button
            type="submit"
            disabled={
              uploadingFileState ||
              (activeTab === 'Carousel'
                ? carouselSlides.length === 0
                : (!selectedMediaFiles || selectedMediaFiles.length === 0) && !singleMediaFile)
            }
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-zinc-950 font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-lg shadow-emerald-950/40"
          >
            <Upload className={`w-4 h-4 ${uploadingFileState ? 'animate-bounce' : ''}`} />
            {uploadingFileState
              ? 'Mengunggah File Media...'
              : activeTab === 'Carousel'
              ? `Tambahkan ${carouselSlides.length} Slide ke Antrean`
              : (selectedMediaFiles && selectedMediaFiles.length > 1)
              ? `Tambahkan ${selectedMediaFiles.length} ${activeTab === 'Video' ? 'Reel/Video Terpisah' : 'Poster Terpisah'} ke Antrean`
              : 'Tambahkan ke Antrean'}
          </button>
        </form>
      </div>
    </div>
  );
}
