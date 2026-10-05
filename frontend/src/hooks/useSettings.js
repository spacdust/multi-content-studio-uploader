import { useState, useEffect, useCallback } from 'react';
import { fetchSettingsApi, saveSettingsApi, testLlmApi, fetchAvailableModelsApi } from '../api/settingsApi';

export function useSettings(showToast) {
  const [llmBaseUrl, setLlmBaseUrl] = useState('');
  const [llmApiKey, setLlmApiKey] = useState('');
  const [llmModel, setLlmModel] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [isCustomModel, setIsCustomModel] = useState(false);
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
      return data;
    } catch {
      // Ignored on initial load
      return null;
    }
  }, []);

  const detectModels = useCallback(async (customBaseUrl, customApiKey, notify = true) => {
    const targetUrl = customBaseUrl !== undefined ? customBaseUrl : llmBaseUrl;
    const targetKey = customApiKey !== undefined ? customApiKey : llmApiKey;

    if (!targetUrl || !targetUrl.trim()) {
      if (notify) showToast('LLM Base URL belum diisi.', 'error');
      return;
    }

    setLoadingModels(true);
    try {
      const data = await fetchAvailableModelsApi({
        llm_base_url: targetUrl.trim(),
        llm_api_key: targetKey ? targetKey.trim() : '',
      });

      if (data.status === 'success' && Array.isArray(data.models) && data.models.length > 0) {
        setAvailableModels(data.models);

        // If current model is already in the list, keep it and switch to dropdown
        if (llmModel && data.models.includes(llmModel)) {
          setIsCustomModel(false);
        } else if (!llmModel) {
          // If no model set, select the first available model
          setLlmModel(data.models[0]);
          setIsCustomModel(false);
        }

        if (notify) {
          showToast(`✨ Berhasil mendeteksi ${data.models.length} model AI!`);
        }
      } else {
        if (notify) {
          showToast(data.message || 'Tidak ada model yang ditemukan dari endpoint ini.', 'warning');
        }
      }
    } catch (err) {
      if (notify) {
        showToast('Gagal mendeteksi model: ' + err.message, 'error');
      }
    } finally {
      setLoadingModels(false);
    }
  }, [llmBaseUrl, llmApiKey, llmModel, showToast]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // When modal is opened, if models haven't been loaded yet, auto-detect silently
  useEffect(() => {
    if (showSettingsModal && availableModels.length === 0 && llmBaseUrl) {
      detectModels(llmBaseUrl, llmApiKey, false);
    }
  }, [showSettingsModal, availableModels.length, llmBaseUrl, llmApiKey, detectModels]);

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
        showToast(`Koneksi LLM Berhasil! Model '${data.model || llmModel}' merespons.`);
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
    availableModels,
    setAvailableModels,
    loadingModels,
    detectModels,
    isCustomModel,
    setIsCustomModel,
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
