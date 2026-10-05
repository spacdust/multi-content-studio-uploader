import React from 'react';
import { Settings, Sparkles, Save, RefreshCw, Check, ShieldAlert } from 'lucide-react';

export default function SettingsModal({
  show,
  onClose,
  llmBaseUrl,
  setLlmBaseUrl,
  llmApiKey,
  setLlmApiKey,
  llmModel,
  setLlmModel,
  availableModels = [],
  loadingModels = false,
  detectModels = () => {},
  isCustomModel = false,
  setIsCustomModel = () => {},
  savingSettings,
  testingLlm,
  testResult,
  handleSaveSettings,
  handleTestLlmConnection,
}) {
  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl flex flex-col gap-4 max-h-[90vh] overflow-y-auto animate-fadeIn">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
              <Settings className="w-4 h-4 text-emerald-400" /> Konfigurasi AI Engine (LLM)
            </h3>
            <p className="text-xs text-zinc-400">
              Pengaturan endpoint & API Key untuk pembuatan caption otomatis.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-100 text-xs p-1"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSaveSettings} className="flex flex-col gap-4">
          {/* Base URL */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-zinc-300 font-medium">LLM Base URL (OpenAI-compatible):</label>
            <input
              type="url"
              required
              placeholder="https://generativelanguage.googleapis.com/v1beta/openai/"
              value={llmBaseUrl}
              onChange={(e) => setLlmBaseUrl(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 px-3 py-2 rounded-xl text-xs text-zinc-100 outline-none focus:border-zinc-600 font-mono"
            />
          </div>

          {/* API Key */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-zinc-300 font-medium">LLM API Key:</label>
            <input
              type="password"
              placeholder="Masukkan API Key (cth: AIzaSy...)"
              value={llmApiKey}
              onChange={(e) => setLlmApiKey(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 px-3 py-2 rounded-xl text-xs text-zinc-100 outline-none focus:border-zinc-600 font-mono"
            />
          </div>

          {/* Model Name */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs text-zinc-300 font-medium flex items-center gap-1.5">
                Model Name:
                {availableModels && availableModels.length > 0 && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-700/50 text-emerald-400 font-normal">
                    {availableModels.length} terdeteksi
                  </span>
                )}
              </label>

              <div className="flex items-center gap-2">
                {availableModels && availableModels.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setIsCustomModel(!isCustomModel)}
                    className="text-[11px] text-cyan-400 hover:text-cyan-300 transition underline underline-offset-2"
                  >
                    {isCustomModel ? '← Pilih Dropdown' : 'Ketik Manual'}
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => detectModels(llmBaseUrl, llmApiKey, true)}
                  disabled={loadingModels || !llmBaseUrl}
                  title="Deteksi ulang model yang tersedia dari endpoint"
                  className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1 p-1 rounded hover:bg-zinc-800 transition disabled:opacity-40"
                >
                  <RefreshCw className={`w-3 h-3 ${loadingModels ? 'animate-spin text-emerald-400' : ''}`} />
                  <span className="text-[11px]">{loadingModels ? 'Mendeteksi...' : 'Deteksi Model'}</span>
                </button>
              </div>
            </div>

            {!isCustomModel && availableModels && availableModels.length > 0 ? (
              <div className="relative">
                <select
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 px-3 py-2 rounded-xl text-xs text-zinc-100 outline-none focus:border-zinc-600 font-mono appearance-none cursor-pointer pr-8"
                >
                  {llmModel && !availableModels.includes(llmModel) && (
                    <option value={llmModel}>{llmModel} (Model Aktif Saat Ini)</option>
                  )}
                  {availableModels.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500 text-[10px]">
                  ▼
                </div>
              </div>
            ) : (
              <input
                type="text"
                required
                placeholder="cth: gemini-2.5-flash, ag/gemini-3.7-flash, gpt-4o-mini"
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 px-3 py-2 rounded-xl text-xs text-zinc-100 outline-none focus:border-zinc-600 font-mono"
              />
            )}

            {availableModels && availableModels.length === 0 && (
              <p className="text-[11px] text-zinc-500">
                Belum ada model terdeteksi. Tekan tombol <strong className="text-zinc-400">Deteksi Model</strong> di atas untuk memuat daftar otomatis.
              </p>
            )}
          </div>

          {/* Live Test Result Alert */}
          {testResult && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
                testResult.status === 'success'
                  ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300'
                  : 'bg-red-950/40 border-red-800/80 text-red-300'
              }`}
            >
              {testResult.status === 'success' ? (
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              ) : (
                <ShieldAlert className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1 min-w-0">
                <p className="font-semibold">{testResult.message}</p>
                {testResult.reply && (
                  <p className="text-[11px] font-mono text-zinc-400 mt-1 truncate">
                    Respon: "{testResult.reply}"
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2 border-t border-zinc-800">
            <button
              type="button"
              onClick={handleTestLlmConnection}
              disabled={testingLlm}
              className="px-3.5 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-750 text-cyan-400 text-xs font-semibold flex items-center gap-1.5 transition border border-zinc-700 disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 ${testingLlm ? 'animate-spin' : ''}`} />
              <span>{testingLlm ? 'Menguji...' : 'Uji Koneksi'}</span>
            </button>

            <button
              type="submit"
              disabled={savingSettings}
              className="flex-1 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-zinc-950 text-xs font-bold flex items-center justify-center gap-1.5 transition disabled:opacity-50 shadow-md shadow-emerald-950/40"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{savingSettings ? 'Menyimpan...' : 'Simpan Pengaturan'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
