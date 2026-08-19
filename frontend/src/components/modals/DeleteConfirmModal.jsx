import React from 'react';
import { Trash2, AlertTriangle } from 'lucide-react';

export default function DeleteConfirmModal({
  show,
  onClose,
  itemToDelete,
  isDeleting,
  handleConfirmDelete,
}) {
  if (!show || !itemToDelete) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-md w-full p-6 shadow-2xl flex flex-col gap-4 animate-fadeIn">
        <div className="flex items-center gap-3 text-red-400">
          <div className="p-2.5 rounded-xl bg-red-950/60 border border-red-900/80">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-zinc-100">Hapus Konten dari Antrean?</h3>
            <p className="text-xs text-zinc-400">Tindakan ini akan menghapus file fisik media & caption.</p>
          </div>
        </div>

        <div className="p-3 bg-zinc-950 rounded-xl border border-zinc-800 text-xs font-mono text-zinc-300">
          <p className="truncate">
            <strong>Nama:</strong> {itemToDelete.name}
          </p>
          <p>
            <strong>Kategori:</strong> {itemToDelete.category}
          </p>
          <p>
            <strong>Tanggal:</strong> {itemToDelete.date}
          </p>
        </div>

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-zinc-300 transition"
          >
            Batal
          </button>
          <button
            type="button"
            onClick={handleConfirmDelete}
            disabled={isDeleting}
            className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 active:bg-red-700 text-white text-xs font-bold flex items-center gap-1.5 transition disabled:opacity-50 shadow-md shadow-red-950/50"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{isDeleting ? 'Menghapus...' : 'Ya, Hapus File'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
