import React from 'react';
import { Sparkles, Settings, CalendarClock } from 'lucide-react';
import AccountSwitcherPopover from './AccountSwitcherPopover';

export default function Navbar({
  llmModel,
  accounts,
  selectedAccount,
  currentAccData,
  isAccountDropdownOpen,
  setIsAccountDropdownOpen,
  handleAccountChange,
  setShowAccountManagerModal,
  handleOpenTikTokStudioBrowser,
  handleOpenInstagramBrowser,
  handleOpenFacebookBrowser,
  setShowSettingsModal,
  setTestResult,
  showToast,
  schedulerStatus,
  onOpenScheduledQueue,
}) {
  return (
    <header className="border-b border-zinc-800/80 bg-[#09090b]/80 backdrop-blur-md sticky top-0 z-30 px-6 py-3.5">
      <div className="max-w-[1600px] mx-auto flex items-center justify-between gap-4">
        {/* Logo & Identity */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-700/80 flex items-center justify-center text-emerald-400 shadow-sm">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-tight text-zinc-100">Content Uploader Studio</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 tracking-tight">
              Model: <span className="font-mono text-zinc-300">{llmModel || 'Memuat...'}</span>
            </p>
          </div>
        </div>

        {/* Account Selector & Settings */}
        <div className="flex items-center gap-2.5">
          {/* Live Auto-Scheduler Indicator */}
          {schedulerStatus && schedulerStatus.total_scheduled_pending > 0 ? (
            <button
              type="button"
              onClick={() => onOpenScheduledQueue && onOpenScheduledQueue()}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-800/60 hover:border-emerald-700/80 text-xs shadow-xs transition cursor-pointer group focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
              title={
                schedulerStatus.next_job
                  ? `Jadwal Berikutnya: ${schedulerStatus.next_job.item_name} (${schedulerStatus.next_job.scheduled_time}) - ${schedulerStatus.next_job.account}\nKlik untuk melihat detail & membatalkan jadwal`
                  : 'Klik untuk melihat daftar antrean konten terjadwal'
              }
            >
              <div className="relative flex items-center justify-center">
                <CalendarClock className="w-3.5 h-3.5 text-emerald-400 group-hover:scale-110 transition-transform" />
                <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
              </div>
              <span className="text-[11px] font-semibold text-emerald-300 font-mono group-hover:text-emerald-200">
                {schedulerStatus.total_scheduled_pending} Terjadwal
              </span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => onOpenScheduledQueue && onOpenScheduledQueue()}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-900/60 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 text-xs shadow-xs transition cursor-pointer group text-zinc-400 hover:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-zinc-600"
              title="Klik untuk melihat antrean jadwal upload"
            >
              <CalendarClock className="w-3.5 h-3.5 text-zinc-500 group-hover:text-zinc-300 transition" />
              <span className="text-[11px] font-mono font-medium text-zinc-400 group-hover:text-zinc-200">
                0 Terjadwal
              </span>
            </button>
          )}

          {/* Bespoke Pro Account Switcher Popover */}
          <AccountSwitcherPopover
            accounts={accounts}
            selectedAccount={selectedAccount}
            currentAccData={currentAccData}
            isAccountDropdownOpen={isAccountDropdownOpen}
            setIsAccountDropdownOpen={setIsAccountDropdownOpen}
            handleAccountChange={handleAccountChange}
            setShowAccountManagerModal={setShowAccountManagerModal}
            handleOpenTikTokStudioBrowser={handleOpenTikTokStudioBrowser}
            handleOpenInstagramBrowser={handleOpenInstagramBrowser}
            handleOpenFacebookBrowser={handleOpenFacebookBrowser}
            showToast={showToast}
          />

          {/* Settings Button */}
          <button
            onClick={() => {
              if (setTestResult) setTestResult(null);
              setShowSettingsModal(true);
            }}
            title="Konfigurasi Endpoint LLM & API Key"
            className="p-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-zinc-100 rounded-xl transition"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
