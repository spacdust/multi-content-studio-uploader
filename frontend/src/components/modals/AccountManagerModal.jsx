import React, { useState } from 'react';
import { Users, RefreshCw, LogIn, ExternalLink, ShieldCheck, Cookie, Info, Check, Zap } from 'lucide-react';
import { importTikTokSessionApi, refreshTikTokSessionApi } from '../../api/accountApi';

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
  handleOpenInstagramBrowser,
  handleOpenFacebookBrowser,
  fetchAccounts,
  loggingInPlatform,
  showToast,
}) {
  const [cookieModalAccount, setCookieModalAccount] = useState(null);
  const [cookieDataInput, setCookieDataInput] = useState('');
  const [importingCookie, setImportingCookie] = useState(false);
  const [refreshingAccount, setRefreshingAccount] = useState(null);

  const handleImportTikTokCookie = async (e) => {
    e.preventDefault();
    if (!cookieModalAccount || !cookieDataInput.trim()) return;
    setImportingCookie(true);
    try {
      const res = await importTikTokSessionApi(cookieModalAccount, cookieDataInput.trim());
      if (showToast) {
        showToast(res.message || '✓ Sesi TikTok berhasil diverifikasi & terhubung!', 'success');
      }
      setCookieModalAccount(null);
      setCookieDataInput('');
      fetchAccounts();
    } catch (err) {
      if (showToast) {
        showToast('Gagal mengimpor cookie: ' + err.message, 'error');
      }
    } finally {
      setImportingCookie(false);
    }
  };

  const handleRefreshTikTokSession = async (accountName) => {
    setRefreshingAccount(accountName);
    try {
      const res = await refreshTikTokSessionApi(accountName);
      if (showToast) {
        showToast(res.message || `✓ Sesi TikTok '${accountName}' aktif & diperbarui!`, 'success');
      }
      fetchAccounts();
    } catch (err) {
      if (showToast) {
        showToast(`Gagal refresh sesi TikTok: ${err.message}`, 'error');
      }
    } finally {
      setRefreshingAccount(null);
    }
  };

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-3xl w-full p-6 shadow-2xl flex flex-col gap-5 max-h-[90vh] overflow-y-auto animate-fadeIn">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
              <Users className="w-4 h-4 text-emerald-400" /> Manajemen Akun & Sesi Login Platform
            </h3>
            <p className="text-xs text-zinc-400">
              Hubungkan akun TikTok Studio, Instagram, dan Halaman Facebook Fanspage untuk publikasi otomatis.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchAccounts()}
              title="Segarkan Status"
              className="p-1.5 bg-zinc-800 hover:bg-zinc-750 text-zinc-300 rounded-lg transition"
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

        {/* Daftar Akun */}
        <div className="flex flex-col gap-4">
          {accounts.map((acc) => {
            const isSelected = selectedAccount === acc.name;
            const isCurrentlyLoggingIn = loggingInPlatform?.account === acc.name;

            return (
              <div
                key={acc.slug}
                className={`p-4 rounded-xl border transition flex flex-col gap-3.5 ${
                  isSelected
                    ? 'bg-zinc-950/80 border-emerald-500/40 ring-1 ring-emerald-500/30'
                    : 'bg-zinc-950/40 border-zinc-800/80 hover:border-zinc-700'
                }`}
              >
                {/* Header Akun */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center font-bold text-xs text-zinc-300 border border-zinc-700 uppercase">
                      {acc.name.slice(0, 2)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-zinc-100">{acc.name}</span>
                        {isSelected && (
                          <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full font-bold">
                            AKTIF
                          </span>
                        )}
                      </div>
                      {acc.description && (
                        <p className="text-xs text-zinc-400">{acc.description}</p>
                      )}
                      {isCurrentlyLoggingIn && (
                        <div className="flex items-center gap-1.5 mt-1 text-[11px] text-amber-400 animate-pulse font-medium">
                          <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                          <span>Browser visual {loggingInPlatform.platform} sedang dibuka. Silakan login...</span>
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

                {/* 3 Platform Connection Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {/* 1. TikTok Studio Card */}
                  <div className="bg-zinc-900 border border-zinc-800 p-3 rounded-xl flex flex-col justify-between gap-2.5 shadow-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        {acc.avatar_url && (
                          <img
                            src={acc.avatar_url}
                            alt="TT"
                            className="w-4 h-4 rounded-full object-cover border border-cyan-500/40"
                          />
                        )}
                        <span className="text-xs font-semibold text-zinc-200 flex items-center gap-1">
                          <span className="text-cyan-400 font-mono text-[11px] font-bold">TT</span> TikTok
                        </span>
                      </div>

                      <span
                        className={`text-[9px] font-mono font-medium px-1.5 py-0.5 rounded-full flex items-center gap-1 ${
                          acc.tiktok_active
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        <span
                          className={`w-1 h-1 rounded-full ${
                            acc.tiktok_active ? 'bg-emerald-400' : 'bg-amber-400'
                          }`}
                        />
                        {acc.tiktok_active ? 'TERHUBUNG' : 'BELUM'}
                      </span>
                    </div>

                    <p className="text-[10px] text-zinc-400 truncate">
                      {acc.tiktok_profile?.username
                        ? `@${acc.tiktok_profile.username}`
                        : (acc.tiktok_active ? 'Sesi aktif' : 'Belum login')}
                    </p>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleTriggerLogin(acc.name, 'tiktok')}
                        className={`flex-1 py-1.5 text-[11px] font-medium rounded-lg flex items-center justify-center gap-1 transition ${
                          acc.tiktok_active
                            ? 'bg-zinc-800 hover:bg-zinc-750 text-zinc-300 border border-zinc-700'
                            : 'bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-bold'
                        }`}
                      >
                        <LogIn className="w-3 h-3" />
                        {acc.tiktok_active ? 'Login Ulang' : 'Hubungkan'}
                      </button>

                      <button
                        onClick={() => {
                          setCookieModalAccount(acc.name);
                          setCookieDataInput('');
                        }}
                        title="Tempel Cookie SessionID (Bypass scan QR)"
                        className="px-2 py-1.5 bg-zinc-800 hover:bg-zinc-750 text-amber-400 hover:text-amber-300 border border-zinc-700 rounded-lg text-[11px] font-medium flex items-center gap-1 transition"
                      >
                        <Cookie className="w-3.5 h-3.5" />
                      </button>

                      {acc.tiktok_active && (
                        <button
                          onClick={() => handleRefreshTikTokSession(acc.name)}
                          disabled={refreshingAccount === acc.name}
                          title="Validasi & Perbarui Sesi TikTok Secara Live"
                          className="px-2 py-1.5 bg-zinc-800 hover:bg-zinc-750 text-emerald-400 hover:text-emerald-300 border border-zinc-700 rounded-lg text-[11px] font-medium flex items-center gap-1 transition"
                        >
                          <RefreshCw className={`w-3 h-3 ${refreshingAccount === acc.name ? 'animate-spin' : ''}`} />
                        </button>
                      )}

                      {acc.tiktok_active && (
                        <button
                          onClick={() => handleOpenTikTokStudioBrowser(acc.name)}
                          title="Buka TikTok Studio di browser visual"
                          className="px-2 py-1.5 bg-zinc-800 hover:bg-zinc-750 text-cyan-400 hover:text-cyan-300 border border-zinc-700 rounded-lg text-[11px] font-medium flex items-center gap-1 transition"
                        >
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* 2. Instagram Direct Card */}
                  <div className="bg-zinc-900 border border-zinc-800 p-3 rounded-xl flex flex-col justify-between gap-2.5 shadow-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-200 flex items-center gap-1">
                        <span className="text-pink-400 font-mono text-[11px] font-bold">IG</span> Instagram
                      </span>
                      <span
                        className={`text-[9px] font-mono font-medium px-1.5 py-0.5 rounded-full flex items-center gap-1 ${
                          acc.instagram_active
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        <span
                          className={`w-1 h-1 rounded-full ${
                            acc.instagram_active ? 'bg-emerald-400' : 'bg-amber-400'
                          }`}
                        />
                        {acc.instagram_active ? 'TERHUBUNG' : 'BELUM'}
                      </span>
                    </div>

                    <p className="text-[10px] text-zinc-400 truncate">
                      {acc.instagram_active ? 'Sesi aktif' : 'Belum login'}
                    </p>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleTriggerLogin(acc.name, 'instagram')}
                        className={`flex-1 py-1.5 text-[11px] font-medium rounded-lg flex items-center justify-center gap-1 transition ${
                          acc.instagram_active
                            ? 'bg-zinc-800 hover:bg-zinc-750 text-zinc-300 border border-zinc-700'
                            : 'bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-bold'
                        }`}
                      >
                        <LogIn className="w-3 h-3" />
                        {acc.instagram_active ? 'Login Ulang' : 'Hubungkan'}
                      </button>

                      {acc.instagram_active && (
                        <button
                          onClick={() => handleOpenInstagramBrowser(acc.name)}
                          title="Buka Instagram di browser visual"
                          className="px-2 py-1.5 bg-zinc-800 hover:bg-zinc-750 text-pink-400 hover:text-pink-300 border border-zinc-700 rounded-lg text-[11px] font-medium flex items-center gap-1 transition"
                        >
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* 3. Facebook Fanspage Direct Card */}
                  <div className="bg-zinc-900 border border-zinc-800 p-3 rounded-xl flex flex-col justify-between gap-2.5 shadow-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-200 flex items-center gap-1">
                        <span className="text-blue-400 font-mono text-[11px] font-bold">FB</span> Facebook
                      </span>
                      <span
                        className={`text-[9px] font-mono font-medium px-1.5 py-0.5 rounded-full flex items-center gap-1 ${
                          acc.facebook_active
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        <span
                          className={`w-1 h-1 rounded-full ${
                            acc.facebook_active ? 'bg-emerald-400' : 'bg-amber-400'
                          }`}
                        />
                        {acc.facebook_active ? 'TERHUBUNG' : 'BELUM'}
                      </span>
                    </div>

                    <p className="text-[10px] text-zinc-400 truncate">
                      {acc.facebook_active ? 'Sesi aktif' : 'Belum login'}
                    </p>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleTriggerLogin(acc.name, 'facebook')}
                        className={`flex-1 py-1.5 text-[11px] font-medium rounded-lg flex items-center justify-center gap-1 transition ${
                          acc.facebook_active
                            ? 'bg-zinc-800 hover:bg-zinc-750 text-zinc-300 border border-zinc-700'
                            : 'bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-bold'
                        }`}
                      >
                        <LogIn className="w-3 h-3" />
                        {acc.facebook_active ? 'Login Ulang' : 'Hubungkan'}
                      </button>

                      {acc.facebook_active && (
                        <button
                          onClick={() => handleOpenFacebookBrowser(acc.name)}
                          title="Buka Facebook di browser visual"
                          className="px-2 py-1.5 bg-zinc-800 hover:bg-zinc-750 text-blue-400 hover:text-blue-300 border border-zinc-700 rounded-lg text-[11px] font-medium flex items-center gap-1 transition"
                        >
                          <ExternalLink className="w-3 h-3" />
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

        {/* Sub-Modal: Impor Cookie SessionID TikTok */}
        {cookieModalAccount && (
          <div className="fixed inset-0 z-60 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-zinc-900 border border-amber-500/40 rounded-2xl max-w-xl w-full p-5 shadow-2xl flex flex-col gap-4 animate-scaleUp">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/30">
                    <Cookie className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-zinc-100">Impor Cookie Sesi TikTok (Safe & Auto-Refresh)</h4>
                    <span className="text-[11px] text-amber-400 font-mono font-medium">Target Akun: {cookieModalAccount}</span>
                  </div>
                </div>
                <button
                  onClick={() => setCookieModalAccount(null)}
                  className="text-zinc-400 hover:text-zinc-100 text-xs p-1"
                >
                  ✕
                </button>
              </div>

              {/* Petunjuk Praktis */}
              <div className="bg-zinc-950/80 border border-zinc-800 rounded-xl p-3 text-[11px] text-zinc-300 flex flex-col gap-2">
                <span className="font-semibold text-emerald-400 flex items-center gap-1">
                  <Info className="w-3.5 h-3.5" /> Mendukung 4 Format Cookie:
                </span>
                <div className="space-y-1.5 text-zinc-400 leading-relaxed text-[11px]">
                  <p>
                    <strong className="text-zinc-200">1. JSON Cookie-Editor (Sangat Direkomendasikan & Paling Stabil):</strong><br />
                    Buka ekstensi <em>Cookie-Editor</em> di Chrome tempat akun aktif login $\rightarrow$ klik <strong>Export</strong> $\rightarrow$ <strong>Export as JSON</strong> $\rightarrow$ tempel di sini. (Semua token keamanan <code className="text-cyan-400">ttwid</code>, <code className="text-cyan-400">odin_tt</code> otomatis tersinkron & anti-logout).
                  </p>
                  <p>
                    <strong className="text-zinc-200">2. Header String / Full Cookie:</strong> <code className="text-amber-400">sessionid=xxx; sid_tt=yyy; ...</code>
                  </p>
                  <p>
                    <strong className="text-zinc-200">3. Nilai sessionid Tunggal:</strong> Nilai token <code className="text-amber-400">sessionid</code> dari DevTools (F12 $\rightarrow$ Application $\rightarrow$ Cookies).
                  </p>
                </div>
                <div className="text-[10px] text-emerald-400/90 bg-emerald-950/30 border border-emerald-500/20 p-2 rounded-lg">
                  ⚡ Sistem akan otomatis melakukan <strong>verifikasi live ke TikTok Studio</strong>, mengunduh profil, dan memperbarui sesi secara berkala tanpa pernah menimpa sesi valid Anda.
                </div>
              </div>

              <form onSubmit={handleImportTikTokCookie} className="flex flex-col gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-zinc-300 block mb-1">
                    Tempel Cookie (JSON Cookie-Editor / Header String / SessionID):
                  </label>
                  <textarea
                    required
                    rows={4}
                    placeholder="Tempel JSON [{...}], Header String 'sessionid=xxx; sid_tt=yyy', atau nilai sessionid di sini..."
                    value={cookieDataInput}
                    onChange={(e) => setCookieDataInput(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-2.5 text-xs font-mono text-zinc-100 placeholder-zinc-600 outline-none focus:border-amber-500/60 transition resize-none"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-1 border-t border-zinc-800">
                  <button
                    type="button"
                    onClick={() => setCookieModalAccount(null)}
                    className="px-3.5 py-1.5 bg-zinc-800 hover:bg-zinc-750 text-zinc-300 rounded-lg text-xs font-medium transition"
                  >
                    Batal
                  </button>
                  <button
                    type="submit"
                    disabled={importingCookie || !cookieDataInput.trim()}
                    className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-zinc-950 font-bold rounded-lg text-xs flex items-center gap-1.5 transition shadow-lg shadow-amber-500/20"
                  >
                    {importingCookie ? 'Memverifikasi Sesi Live...' : '⚡ Verifikasi & Hubungkan Sesi'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
