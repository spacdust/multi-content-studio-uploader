import React from 'react';
import { FolderPlus } from 'lucide-react';

export default function AddDateModal({
  show,
  onClose,
  selectedAccount,
  newDateInput,
  setNewDateInput,
  handleCreateDateFolder,
}) {
  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-md w-full p-6 shadow-2xl flex flex-col gap-4 animate-fadeIn">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
            <FolderPlus className="w-4 h-4 text-emerald-400" /> Buat Tanggal Konten Baru
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-100 text-xs p-1"
          >
            ✕
          </button>
        </div>
        <p className="text-xs text-zinc-400">
          Folder <code className="text-zinc-200">Video/</code>, <code className="text-zinc-200">Poster/</code>, dan <code className="text-zinc-200">Carousel/</code> akan otomatis diinisialisasi untuk akun <strong>{selectedAccount}</strong>.
        </p>
        <form onSubmit={handleCreateDateFolder} className="flex flex-col gap-3">
          <div>
            <label className="text-xs font-medium text-zinc-300 block mb-1">Tanggal (YYYY-MM-DD):</label>
            <input
              type="date"
              required
              value={newDateInput}
              onChange={(e) => setNewDateInput(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 px-3 py-2 rounded-lg text-xs text-zinc-100 outline-none focus:border-zinc-600 font-medium"
            />
          </div>
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 bg-zinc-800 text-zinc-300 rounded-lg text-xs font-medium hover:bg-zinc-700 transition"
            >
              Batal
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 bg-zinc-100 hover:bg-white text-zinc-950 rounded-lg text-xs font-bold transition"
            >
              Buat Folder
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
