import React, { useState } from 'react';
import { Clock, Sparkles } from 'lucide-react';
import {
  formatDateDisplay,
  formatTimeDisplay,
  formatScheduleIsoForHuman,
  getLocalTodayDate,
} from '../../utils/dateUtils';
import { QUICK_PRESETS } from '../../utils/constants';

export default function FriendlyDateTimePicker({ value, onChange }) {
  let initialDate = getLocalTodayDate();
  let initialHour = '19';
  let initialMin = '30';

  if (value && value.includes('T')) {
    const [dPart, tPart] = value.split('T');
    if (dPart) initialDate = dPart;
    if (tPart) {
      const [h, m] = tPart.split(':');
      if (h) initialHour = h.padStart(2, '0');
      if (m) initialMin = m.padStart(2, '0');
    }
  }

  const [selDate, setSelDate] = useState(initialDate);
  const [selHour, setSelHour] = useState(initialHour);
  const [selMin, setSelMin] = useState(initialMin);

  const hoursList = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'));
  const minutesList = ['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55'];

  const emitChange = (d, h, m) => {
    const isoString = `${d}T${h}:${m}:00`;
    onChange(isoString);
  };

  const applyPreset = (preset) => {
    const d = new Date();
    d.setDate(d.getDate() + preset.dayOffset);
    const yr = d.getFullYear();
    const mo = String(d.getMonth() + 1).padStart(2, '0');
    const dy = String(d.getDate()).padStart(2, '0');
    const newD = `${yr}-${mo}-${dy}`;
    const newH = String(preset.hours).padStart(2, '0');
    const newM = String(preset.mins).padStart(2, '0');

    setSelDate(newD);
    setSelHour(newH);
    setSelMin(newM);
    emitChange(newD, newH, newM);
  };

  const currentIso = `${selDate}T${selHour}:${selMin}:00`;

  return (
    <div className="flex flex-col gap-3 bg-zinc-950 p-3.5 rounded-xl border border-zinc-800/90 text-xs">
      {/* Date & Time Selectors */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-2.5 items-center">
        {/* Date Picker Input */}
        <div className="sm:col-span-6 flex flex-col gap-1">
          <label className="text-[10px] text-zinc-400 font-mono uppercase tracking-wider">Tanggal Tayang:</label>
          <input
            type="date"
            value={selDate}
            onChange={(e) => {
              const newD = e.target.value;
              setSelDate(newD);
              emitChange(newD, selHour, selMin);
            }}
            className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs text-zinc-100 outline-none focus:border-zinc-600 font-medium"
          />
        </div>

        {/* 24-Hour Time Selectors */}
        <div className="sm:col-span-6 flex flex-col gap-1">
          <label className="text-[10px] text-zinc-400 font-mono uppercase tracking-wider flex items-center gap-1">
            <Clock className="w-3 h-3 text-cyan-400" /> Jam Tayang (24 Jam):
          </label>
          <div className="flex items-center gap-1.5">
            {/* Hour Select */}
            <select
              value={selHour}
              onChange={(e) => {
                const newH = e.target.value;
                setSelHour(newH);
                emitChange(selDate, newH, selMin);
              }}
              className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-1.5 text-xs text-zinc-100 font-mono font-bold outline-none focus:border-zinc-600 cursor-pointer"
            >
              {hoursList.map((h) => (
                <option key={h} value={h} className="bg-zinc-900 text-zinc-100">
                  {h}
                </option>
              ))}
            </select>
            <span className="text-zinc-500 font-bold font-mono">:</span>

            {/* Minute Select */}
            <select
              value={selMin}
              onChange={(e) => {
                const newM = e.target.value;
                setSelMin(newM);
                emitChange(selDate, selHour, newM);
              }}
              className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-1.5 text-xs text-zinc-100 font-mono font-bold outline-none focus:border-zinc-600 cursor-pointer"
            >
              {minutesList.map((m) => (
                <option key={m} value={m} className="bg-zinc-900 text-zinc-100">
                  {m}
                </option>
              ))}
            </select>
            <span className="text-[10px] text-zinc-500 font-mono font-semibold px-1">WIB</span>
          </div>
        </div>
      </div>

      {/* Quick Time Presets */}
      <div className="flex items-center gap-1.5 flex-wrap pt-1 border-t border-zinc-900">
        <span className="text-[10px] text-zinc-500 font-mono flex items-center gap-1">
          <Sparkles className="w-2.5 h-2.5 text-amber-400" /> Preset:
        </span>
        {QUICK_PRESETS.map((preset, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => applyPreset(preset)}
            className="px-2 py-0.5 rounded-md bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 text-[10px] text-zinc-300 hover:text-zinc-100 font-mono transition"
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Human-Readable Output Confirmation Badge */}
      <div className="p-2 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-[11px] text-emerald-400 font-mono flex items-center justify-between">
        <span className="truncate">
          🗓️ Terjadwal: <strong>{formatScheduleIsoForHuman(currentIso)}</strong>
        </span>
      </div>
    </div>
  );
}
