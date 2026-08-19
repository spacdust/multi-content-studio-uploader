import React from 'react';
import { CalendarClock } from 'lucide-react';
import FriendlyDateTimePicker from '../common/FriendlyDateTimePicker';
import { getLocalNowIso } from '../../utils/dateUtils';

export default function ScheduleSettingCard({
  selectedItem,
  currentEdit,
  isInspectorScheduled,
  setEditedItems,
}) {
  return (
    <div className="bg-zinc-950/70 p-3 rounded-xl border border-zinc-800 flex flex-col gap-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CalendarClock className="w-4 h-4 text-cyan-400 flex-shrink-0" />
          <div>
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-zinc-200 block">Jadwalkan Publikasi Konten</label>
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                Semua Platform
              </span>
            </div>
            <p className="text-[10px] text-zinc-400">Atur tanggal dan waktu otomatis posting</p>
          </div>
        </div>

        {/* Toggle ON/OFF Switch */}
        <button
          type="button"
          onClick={() => {
            if (isInspectorScheduled) {
              setEditedItems((prev) => ({
                ...prev,
                [selectedItem.item_key]: {
                  ...prev[selectedItem.item_key],
                  scheduledTime: '',
                },
              }));
            } else {
              setEditedItems((prev) => ({
                ...prev,
                [selectedItem.item_key]: {
                  ...prev[selectedItem.item_key],
                  scheduledTime: getLocalNowIso(),
                },
              }));
            }
          }}
          className={`relative inline-flex h-5 w-10 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
            isInspectorScheduled ? 'bg-emerald-600' : 'bg-zinc-800'
          }`}
        >
          <span
            className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
              isInspectorScheduled ? 'translate-x-5' : 'translate-x-0'
            }`}
          />
        </button>
      </div>

      {/* If ON: Show Bespoke Friendly Dark Mode DateTime Picker */}
      {isInspectorScheduled && (
        <div className="pt-2 border-t border-zinc-800/60 animate-fadeIn">
          <FriendlyDateTimePicker
            value={currentEdit?.scheduledTime || getLocalNowIso()}
            onChange={(newVal) =>
              setEditedItems((prev) => ({
                ...prev,
                [selectedItem.item_key]: {
                  ...prev[selectedItem.item_key],
                  scheduledTime: newVal,
                },
              }))
            }
          />
        </div>
      )}
    </div>
  );
}
