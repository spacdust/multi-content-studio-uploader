import React from 'react';
import { Users, RefreshCw, LogIn, ExternalLink } from 'lucide-react';

export default function AccountManagerModal({
  show,
  onClose,
  accounts,
  selectedAccount,
  newAccountName,
  setNewAccountName,
  handleCreateAccount,
  handleAccountChange,
  handleTriggerLogin,
  handleOpenTikTokStudioBrowser,
  handleOpenMetaBusinessBrowser,
  fetchAccounts,
  loggingInPlatform,
  showToast,
}) {
  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl flex flex-col gap-5 max-h-[90vh] overflow-y-auto animate-fadeIn">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
              <Users className="w-4 h-4 text-emerald-400" /> Manajemen Akun & Sesi Login
            </h3>
            <p className="text-xs text-zinc-400">
              Pantau status koneksi platform dan buka browser visual untuk menghubungkan akun.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchAccounts()}
              title="Segarkan Status"
              className="p-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => {
                onClose();
                fetchAccounts();
              }}
              className="text-zinc-400 hover:text-zinc-100 text-xs p-1"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Polling Alert if Browser is open */}
        {loggingInPlatform && (
          <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-800/80 text-emerald-300 text-xs flex items-start gap-3">
            <RefreshCw className="w-4 h-4 animate-spin flex-shrink-0 text-emerald-400 mt-0.5" />
            <div>
              <p className="font-semibold text-emerald-200">
                Jendela browser visual sedang aktif untuk akun '{loggingInPlatform.account}' ({loggingInPlatform.platform.toUpperCase()})
              </p>
              <p className="text-[11px] text-emerald-400/80 mt-0.5">
                Silakan masukkan username/password di browser yang terbuka. Dashboard otomatis mendeteksi ketika login selesai dan memperbarui status menjadi Terhubung.
              </p>
            </div>
          </div>
        )}

        {/* List of Registered Accounts */}
        <div className="flex flex-col gap-3">
          {accounts.map((acc) => {
            const isSelected = acc.name === selectedAccount;
            return (
              <div
                key={acc.name}
                className={`p-4 rounded-xl border transition flex flex-col gap-3 ${
                  isSelected
                    ? 'bg-zinc-950 border-zinc-700 ring-1 ring-zinc-700'
                    : 'bg-zinc-950/60 border-zinc-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {acc.avatar_url ? (
                      <img
                        src={acc.avatar_url}
                        alt={acc.name}
                        className="w-10 h-10 rounded-full object-cover border-2 border-emerald-500/40 shadow-sm"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center font-bold text-sm text-zinc-300">
                        {acc.name.slice(0, 1).toUpperCase()}
                      </div>
                    )}

                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-zinc-100">{acc.name}</span>
                        {isSelected && (
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            AKTIF
                          </span>
                        )}
                      </div>

                      {acc.tiktok_profile?.username && (
                        <div className="flex items-center gap-2 text-[11px] text-zinc-400 font-mono">
                          <span className="text-cyan-400 font-semibold">@{acc.tiktok_profile.username}</span>
                          {acc.tiktok_profile.followers > 0 && (
                            <>
                              <span>•</span>
                              <span className="text-zinc-300">
                                {(acc.tiktok_profile.followers / 1000).toFixed(1)}K Pengikut
                              </span>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {!isSelected && (
                    <button
                      onClick={() => {
                        handleAccountChange(acc.name);
                        showToast(`Beralih ke akun ${acc.name}`);
                      }}
                      className="text-xs px-2.5 py-1 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 transition"
                    >
                      Pilih Akun Ini
                    </button>
                  )}
                </div>

                {/* Platform Connection Cards Grid (2 Platforms: TikTok Studio & Meta Business Suite) */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {/* 1. TikTok Card */}
                  <div className="bg-zinc-900 border border-zinc-800 p-3.5 rounded-xl flex flex-col justify-between gap-3 shadow-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {acc.avatar_url && (
                          <img
                            src={acc.avatar_url}
                            alt="TT"
                            className="w-5 h-5 rounded-full object-cover border border-cyan-500/40"
                          />
                        )}
                        <span className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
                          <span className="text-cyan-400 font-mono text-[11px] font-bold">TT</span> TikTok Studio
                        </span>
                      </div>

                      <span
                        className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded-full flex items-center gap-1 ${
                          acc.tiktok_active
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            acc.tiktok_active ? 'bg-emerald-400' : 'bg-amber-400'
                          }`}
                        />
                        {acc.tiktok_active ? 'TERHUBUNG' : 'BELUM LOGIN'}
                      </span>
                    </div>

                    <p className="text-[10px] text-zinc-400 truncate">
                      {acc.tiktok_profile?.username
                        ? `Akun @${acc.tiktok_profile.username} (${acc.tiktok_profile.nickname || 'Kreator'})`
                        : (acc.tiktok_message || (acc.tiktok_active ? 'Sesi aktif & siap posting otomatis' : 'Belum ada sesi login'))}
                    </p>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleTriggerLogin(acc.name, 'tiktok')}
                        className={`flex-1 py-1.5 text-xs font-medium rounded-lg flex items-center justify-center gap-1.5 transition ${
                          acc.tiktok_active
                            ? 'bg-zinc-800 hover:bg-zinc-750 text-zinc-300 border border-zinc-700'
                            : 'bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-bold'
                        }`}
                      >
                        <LogIn className="w-3.5 h-3.5" />
                        {acc.tiktok_active ? 'Login Ulang' : 'Hubungkan TikTok'}
                      </button>

                      {acc.tiktok_active && (
                        <button
                          onClick={() => handleOpenTikTokStudioBrowser(acc.name)}
                          title="Buka TikTok Studio dengan sesi akun ini di browser visual"
                          className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-750 text-cyan-400 hover:text-cyan-300 border border-zinc-700 rounded-lg text-xs font-medium flex items-center gap-1 transition"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Studio</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* 2. Meta Business Suite Card (Instagram & Facebook Cross-Posting) */}
                  <div className="bg-zinc-900 border border-zinc-800 p-3.5 rounded-xl flex flex-col justify-between gap-3 shadow-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
                        <span className="text-blue-400 font-mono text-[11px] font-bold">META</span> Meta Suite (IG & FB)
                      </span>
                      <span
                        className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded-full flex items-center gap-1 ${
                          acc.meta_active
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            acc.meta_active ? 'bg-emerald-400' : 'bg-amber-400'
                          }`}
                        />
                        {acc.meta_active ? 'TERHUBUNG' : 'BELUM LOGIN'}
                      </span>
                    </div>

                    <p className="text-[10px] text-zinc-400 truncate">
                      {acc.meta_message || (acc.meta_active ? 'Sesi aktif (Cross-Post Reels/Feed IG & Fanspage FB)' : 'Posting paralel IG & FB')}
                    </p>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleTriggerLogin(acc.name, 'meta')}
                        className={`flex-1 py-1.5 text-xs font-medium rounded-lg flex items-center justify-center gap-1.5 transition ${
                          acc.meta_active
                            ? 'bg-zinc-800 hover:bg-zinc-750 text-zinc-300 border border-zinc-700'
                            : 'bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-bold'
                        }`}
                      >
                        <LogIn className="w-3.5 h-3.5" />
                        {acc.meta_active ? 'Login Ulang' : 'Hubungkan Meta'}
                      </button>

                      {acc.meta_active && (
                        <button
                          onClick={() => handleOpenMetaBusinessBrowser(acc.name)}
                          title="Buka Meta Business Suite dengan sesi akun ini di browser visual"
                          className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-750 text-blue-400 hover:text-blue-300 border border-zinc-700 rounded-lg text-xs font-medium flex items-center gap-1 transition"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Suite</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Form Daftarkan Akun Baru */}
        <div className="border-t border-zinc-800 pt-4">
          <span className="text-xs font-semibold text-zinc-300 block mb-2">Daftarkan Akun Baru:</span>
          <form onSubmit={handleCreateAccount} className="flex items-center gap-2">
            <input
              type="text"
              required
              placeholder="Nama Akun / Brand (Misal: Yayasan Bina Bangsa)"
              value={newAccountName}
              onChange={(e) => setNewAccountName(e.target.value)}
              className="flex-1 bg-zinc-950 border border-zinc-800 px-3 py-2 rounded-lg text-xs text-zinc-100 outline-none focus:border-zinc-600"
            />
            <button
              type="submit"
              className="px-4 py-2 bg-zinc-100 hover:bg-white text-zinc-950 font-bold text-xs rounded-lg transition"
            >
              Daftarkan
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
