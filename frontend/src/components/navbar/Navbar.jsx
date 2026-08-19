import React from 'react';
import { Sparkles, Settings } from 'lucide-react';
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
  handleOpenMetaBusinessBrowser,
  setShowSettingsModal,
  setTestResult,
  showToast,
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
              <span className="text-sm font-semibold tracking-tight text-zinc-100">Content Studio</span>
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
            handleOpenMetaBusinessBrowser={handleOpenMetaBusinessBrowser}
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
