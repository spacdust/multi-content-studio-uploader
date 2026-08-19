import React from 'react';
import { Check, ShieldAlert } from 'lucide-react';

export default function Toast({ toast }) {
  if (!toast) return null;

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg shadow-xl border flex items-center gap-3 transition-all duration-200 animate-fadeIn ${
        toast.type === 'error'
          ? 'bg-red-950/90 border-red-800/80 text-red-200'
          : 'bg-zinc-900 border-zinc-700 text-zinc-100'
      }`}
    >
      {toast.type === 'error' ? (
        <ShieldAlert className="w-4 h-4 text-red-400" />
      ) : (
        <Check className="w-4 h-4 text-emerald-400" />
      )}
      <span className="text-xs font-medium tracking-tight">{toast.message}</span>
    </div>
  );
}
