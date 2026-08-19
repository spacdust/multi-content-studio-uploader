import { useState, useEffect, useCallback } from 'react';
import { fetchSettingsApi, saveSettingsApi, testLlmApi } from '../api/settingsApi';

export function useSettings(showToast) {
  const [llmBaseUrl, setLlmBaseUrl] = useState('');
  const [llmApiKey, setLlmApiKey] = useState('');
  const [llmModel, setLlmModel] = useState('');
  const [savingSettings, setSavingSettings] = useState(false);
  const [testingLlm, setTestingLlm] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      const data = await fetchSettingsApi();
      setLlmBaseUrl(data.llm_base_url || '');
      setLlmApiKey(data.llm_api_key || '');
      setLlmModel(data.llm_model || '');
    } catch {
      // Ignored on initial load
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSaveSettings = async (e) => {
    if (e) e.preventDefault();
    setSavingSettings(true);
    try {
      const data = await saveSettingsApi({
        llm_base_url: llmBaseUrl,
        llm_api_key: llmApiKey,
        llm_model: llmModel,
      });
      if (data.status === 'success') {
        showToast('Konfigurasi LLM berhasil disimpan');
        setShowSettingsModal(false);
      }
    } catch {
      showToast('Gagal menyimpan konfigurasi LLM', 'error');
    } finally {
      setSavingSettings(false);
    }
  };

  const handleTestLlmConnection = async () => {
    setTestingLlm(true);
    setTestResult(null);
    try {
      const data = await testLlmApi({
        llm_base_url: llmBaseUrl,
        llm_api_key: llmApiKey,
        llm_model: llmModel,
      });
      setTestResult(data);
      if (data.status === 'success') {
        showToast(`Koneksi LLM Berhasil! Model '${data.model}' merespons.`);
      } else {
        showToast(`Tes gagal: ${data.message}`, 'error');
      }
    } catch (err) {
      setTestResult({ status: 'error', message: err.message });
      showToast('Koneksi endpoint gagal. Periksa Base URL & API Key.', 'error');
    } finally {
      setTestingLlm(false);
    }
  };

  return {
    llmBaseUrl,
    setLlmBaseUrl,
    llmApiKey,
    setLlmApiKey,
    llmModel,
    setLlmModel,
    savingSettings,
    testingLlm,
    testResult,
    setTestResult,
    showSettingsModal,
    setShowSettingsModal,
    fetchSettings,
    handleSaveSettings,
    handleTestLlmConnection,
  };
}
