import React, { useRef, useEffect } from 'react';
import {
  ChevronsUpDown,
  Check,
  Users,
  ChevronRight,
  ExternalLink,
  ArrowUpRight,
} from 'lucide-react';

export default function AccountSwitcherPopover({
  accounts,
  selectedAccount,
  currentAccData,
  isAccountDropdownOpen,
  setIsAccountDropdownOpen,
  handleAccountChange,
  setShowAccountManagerModal,
  handleOpenTikTokStudioBrowser,
  handleOpenMetaBusinessBrowser,
  showToast,
}) {
  const accountDropdownRef = useRef(null);

  // Close dropdown on outside click or escape
  useEffect(() => {
    function handleClickOutside(e) {
      if (accountDropdownRef.current && !accountDropdownRef.current.contains(e.target)) {
        setIsAccountDropdownOpen(false);
      }
    }
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        setIsAccountDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [setIsAccountDropdownOpen]);

  return (
    <div className="relative" ref={accountDropdownRef}>
      {/* Account Selector Button */}
      <button
        type="button"
        onClick={() => setIsAccountDropdownOpen(!isAccountDropdownOpen)}
        className={`group flex items-center gap-2.5 px-3 py-1.5 rounded-xl border transition-all duration-150 ${
          isAccountDropdownOpen
            ? 'bg-zinc-900 border-zinc-700 ring-2 ring-emerald-500/20 shadow-lg'
            : 'bg-zinc-900/90 hover:bg-zinc-850 border-zinc-800 hover:border-zinc-700/80 shadow-sm'
        }`}
      >
        {/* Account Avatar with Active Dot */}
        <div className="relative flex-shrink-0">
          {currentAccData.avatar_url ? (
            <img
              src={currentAccData.avatar_url}
              alt={selectedAccount}
              className="w-7 h-7 rounded-full object-cover border border-cyan-500/40 ring-1 ring-black/40"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          ) : (
            <div className="w-7 h-7 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[11px] font-bold text-zinc-200">
              {selectedAccount ? selectedAccount.slice(0, 1).toUpperCase() : 'A'}
            </div>
          )}
          <span
            className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-zinc-900 ${
              currentAccData.tiktok_active ? 'bg-emerald-400 shadow-xs shadow-emerald-400/50' : 'bg-amber-400'
            }`}
          />
        </div>

        {/* Account Info (Name & Subtitle/Handle) */}
        <div className="flex flex-col text-left min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-zinc-100 tracking-tight truncate max-w-[130px] sm:max-w-[170px]">
              {selectedAccount || 'Pilih Akun'}
            </span>
          </div>
          <span className="text-[10px] font-mono text-cyan-400/90 truncate max-w-[130px] sm:max-w-[170px]">
            {currentAccData.tiktok_profile?.username
              ? `@${currentAccData.tiktok_profile.username}`
              : (currentAccData.tiktok_active ? '● TikTok Aktif' : '○ Belum Login')}
          </span>
        </div>

        {/* Platform Connection Status Chips */}
        <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 bg-zinc-950/60 rounded-md border border-zinc-800/80 text-[10px] font-mono text-zinc-400">
          <span className={`w-1.5 h-1.5 rounded-full ${currentAccData.tiktok_active ? 'bg-emerald-400' : 'bg-zinc-600'}`} />
          <span>TT</span>
          <span className="text-zinc-700">|</span>
          <span className={`w-1.5 h-1.5 rounded-full ${currentAccData.meta_active ? 'bg-emerald-400' : 'bg-zinc-600'}`} />
          <span>META</span>
        </div>

        {/* Dropdown Chevron */}
        <ChevronsUpDown
          className={`w-3.5 h-3.5 text-zinc-500 group-hover:text-zinc-300 transition-transform duration-200 ${
            isAccountDropdownOpen ? 'rotate-180 text-emerald-400' : ''
          }`}
        />
      </button>

      {/* Floating Pro Popover Dropdown Menu */}
      {isAccountDropdownOpen && (
        <div className="absolute top-full left-0 mt-2 z-50 w-80 sm:w-96 rounded-2xl bg-zinc-950/95 backdrop-blur-xl border border-zinc-800 shadow-2xl p-2 animate-fadeIn flex flex-col gap-1 ring-1 ring-white/5">
          {/* Popover Header */}
          <div className="px-3 py-2 flex items-center justify-between border-b border-zinc-800/80">
            <span className="text-[10px] font-mono font-bold tracking-wider text-zinc-400 uppercase flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-emerald-400" /> Pilih Akun Aktif
            </span>
            <span className="text-[10px] font-mono text-zinc-400 bg-zinc-900 px-2 py-0.5 rounded-full border border-zinc-800">
              {accounts.length} Akun
            </span>
          </div>

          {/* Account List */}
          <div className="flex flex-col gap-1 max-h-72 overflow-y-auto py-1 custom-scrollbar">
            {accounts.map((acc) => {
              const isSelected = acc.name === selectedAccount;
              return (
                <div
                  key={acc.name}
                  onClick={() => {
                    handleAccountChange(acc.name);
                    setIsAccountDropdownOpen(false);
                    showToast(`Beralih ke akun '${acc.name}'`);
                  }}
                  className={`group cursor-pointer p-2.5 rounded-xl border transition-all flex items-center justify-between gap-3 ${
                    isSelected
                      ? 'bg-zinc-900 border-zinc-700 ring-1 ring-zinc-700 shadow-xs'
                      : 'bg-transparent border-transparent hover:bg-zinc-900/60 hover:border-zinc-800/80'
                  }`}
                >
                  {/* Left: Avatar + Names */}
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="relative flex-shrink-0">
                      {acc.avatar_url ? (
                        <img
                          src={acc.avatar_url}
                          alt={acc.name}
                          className="w-8 h-8 rounded-full object-cover border border-cyan-500/40"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-bold text-zinc-200">
                          {acc.name.slice(0, 1).toUpperCase()}
                        </div>
                      )}
                      <span
                        className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-zinc-950 ${
                          acc.tiktok_active ? 'bg-emerald-400' : 'bg-amber-400'
                        }`}
                      />
                    </div>

                    <div className="flex flex-col min-w-0">
                      <span className="text-xs font-semibold text-zinc-100 truncate group-hover:text-emerald-400 transition-colors">
                        {acc.name}
                      </span>
                      <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-400 truncate">
                        {acc.tiktok_profile?.username ? (
                          <span className="text-cyan-400/90">@{acc.tiktok_profile.username}</span>
                        ) : (
                          <span>{acc.tiktok_active ? 'TikTok Siap' : 'Belum Login'}</span>
                        )}

                        {acc.tiktok_profile?.followers > 0 && (
                          <>
                            <span className="text-zinc-600">•</span>
                            <span className="text-zinc-400">{(acc.tiktok_profile.followers / 1000).toFixed(1)}K</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right: Active Badge or Platform Status */}
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {isSelected ? (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono font-bold flex items-center gap-1">
                        <Check className="w-3 h-3" /> AKTIF
                      </span>
                    ) : (
                      <div className="flex items-center gap-1 text-[10px] font-mono text-zinc-500 group-hover:text-zinc-300">
                        <span className={`w-1.5 h-1.5 rounded-full ${acc.tiktok_active ? 'bg-emerald-400' : 'bg-zinc-600'}`} />
                        <span>TT</span>
                        <span className="text-zinc-700">|</span>
                        <span className={`w-1.5 h-1.5 rounded-full ${acc.meta_active ? 'bg-emerald-400' : 'bg-zinc-600'}`} />
                        <span>META</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Popover Footer Action Links */}
          <div className="pt-2 border-t border-zinc-800/80 flex flex-col gap-1.5">
            <button
              type="button"
              onClick={() => {
                setIsAccountDropdownOpen(false);
                setShowAccountManagerModal(true);
              }}
              className="w-full px-3 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-850 border border-zinc-800/80 text-xs font-medium text-zinc-200 hover:text-white flex items-center justify-between transition"
            >
              <span className="flex items-center gap-2">
                <Users className="w-3.5 h-3.5 text-emerald-400" />
                <span>Kelola Akun & Login Platform</span>
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-zinc-500" />
            </button>

            <div className="grid grid-cols-2 gap-2 pt-0.5">
              <button
                type="button"
                onClick={() => {
                  setIsAccountDropdownOpen(false);
                  handleOpenTikTokStudioBrowser(selectedAccount);
                }}
                className="px-2.5 py-2 rounded-xl bg-cyan-950/30 hover:bg-cyan-950/50 border border-cyan-800/40 text-[11px] font-semibold text-cyan-300 flex items-center justify-between transition group/tt"
              >
                <span className="flex items-center gap-1.5 truncate">
                  <ExternalLink className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 group-hover/tt:scale-110 transition-transform" />
                  <span className="truncate">TikTok Studio</span>
                </span>
                <ArrowUpRight className="w-3 h-3 text-cyan-400 flex-shrink-0" />
              </button>

              <button
                type="button"
                onClick={() => {
                  setIsAccountDropdownOpen(false);
                  handleOpenMetaBusinessBrowser(selectedAccount);
                }}
                className="px-2.5 py-2 rounded-xl bg-blue-950/30 hover:bg-blue-950/50 border border-blue-800/40 text-[11px] font-semibold text-blue-300 flex items-center justify-between transition group/meta"
              >
                <span className="flex items-center gap-1.5 truncate">
                  <ExternalLink className="w-3.5 h-3.5 text-blue-400 flex-shrink-0 group-hover/meta:scale-110 transition-transform" />
                  <span className="truncate">Meta Suite (IG & FB)</span>
                </span>
                <ArrowUpRight className="w-3 h-3 text-blue-400 flex-shrink-0" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
