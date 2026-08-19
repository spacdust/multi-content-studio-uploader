import { useState, useEffect, useCallback } from 'react';
import {
  fetchAccountsApi,
  createAccountApi,
  triggerLoginApi,
  openTikTokStudioApi,
  openMetaBusinessApi,
} from '../api/accountApi';

const STORAGE_KEY_LAST_ACCOUNT = 'content_uploader_last_account';

export function useAccounts(showToast) {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(() => {
    return localStorage.getItem(STORAGE_KEY_LAST_ACCOUNT) || '';
  });
  const [newAccountName, setNewAccountName] = useState('');
  const [showAccountManagerModal, setShowAccountManagerModal] = useState(false);
  const [isAccountDropdownOpen, setIsAccountDropdownOpen] = useState(false);
  const [loggingInPlatform, setLoggingInPlatform] = useState(null);

  const fetchAccounts = useCallback(async () => {
    try {
      const data = await fetchAccountsApi();
      if (data && data.accounts) {
        setAccounts(data.accounts);

        const savedAccount = localStorage.getItem(STORAGE_KEY_LAST_ACCOUNT);
        const exists = data.accounts.some((a) => a.name === savedAccount);

        if (savedAccount && exists) {
          setSelectedAccount(savedAccount);
        } else if (data.accounts.length > 0) {
          const firstAcc = data.accounts[0].name;
          setSelectedAccount(firstAcc);
          localStorage.setItem(STORAGE_KEY_LAST_ACCOUNT, firstAcc);
        }
      }
    } catch {
      // Error handled silently on load
    }
  }, []);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  // Polling platform authentication status when browser is open for login
  useEffect(() => {
    let interval = null;
    if (loggingInPlatform) {
      interval = setInterval(async () => {
        try {
          const data = await fetchAccountsApi();
          if (data && data.accounts) {
            setAccounts(data.accounts);
            const targetAcc = data.accounts.find((a) => a.name === loggingInPlatform.account);
            if (targetAcc) {
              const isTTActive = loggingInPlatform.platform === 'tiktok' && targetAcc.tiktok_active;
              const isMetaActive = loggingInPlatform.platform === 'meta' && targetAcc.meta_active;

              if (isTTActive || isMetaActive) {
                showToast(`Sesi login ${loggingInPlatform.platform.toUpperCase()} untuk '${loggingInPlatform.account}' berhasil terhubung!`);
                setLoggingInPlatform(null);
              }
            }
          }
        } catch {
          // Ignored during polling
        }
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [loggingInPlatform, showToast]);

  const handleAccountChange = (accName) => {
    setSelectedAccount(accName);
    localStorage.setItem(STORAGE_KEY_LAST_ACCOUNT, accName);
  };

  const handleCreateAccount = async (e) => {
    if (e) e.preventDefault();
    if (!newAccountName.trim()) return;
    try {
      const data = await createAccountApi(newAccountName.trim());
      if (data.status === 'success') {
        showToast(`Akun '${newAccountName}' berhasil didaftarkan`);
        setNewAccountName('');
        await fetchAccounts();
        handleAccountChange(newAccountName.trim());
      } else {
        showToast(data.message || 'Gagal membuat akun', 'error');
      }
    } catch {
      showToast('Gagal membuat akun baru', 'error');
    }
  };

  const handleTriggerLogin = async (accName, platform) => {
    showToast(`Membuka browser visual untuk login ${platform.toUpperCase()} akun '${accName}'...`);
    setLoggingInPlatform({ account: accName, platform });
    try {
      const data = await triggerLoginApi(accName, platform);
      if (data.status === 'started') {
        showToast(`Jendela browser visual terbuka. Silakan login di browser.`);
      }
    } catch {
      showToast(`Gagal memulai sesi login ${platform}`, 'error');
      setLoggingInPlatform(null);
    }
  };

  const handleOpenTikTokStudioBrowser = async (accName) => {
    if (!accName) return;
    showToast(`Membuka TikTok Studio akun '${accName}' di jendela browser penuh...`);
    try {
      const data = await openTikTokStudioApi(accName);
      if (data.status === 'started') {
        showToast(`Browser TikTok Studio terbuka untuk akun '${accName}'`);
      }
    } catch {
      showToast('Gagal membuka TikTok Studio', 'error');
    }
  };

  const handleOpenMetaBusinessBrowser = async (accName) => {
    if (!accName) return;
    showToast(`Membuka Meta Business Suite akun '${accName}' di browser penuh...`);
    try {
      const data = await openMetaBusinessApi(accName);
      if (data.status === 'started') {
        showToast(`Browser Meta Business Suite terbuka untuk akun '${accName}'`);
      }
    } catch {
      showToast('Gagal membuka Meta Business Suite', 'error');
    }
  };

  const currentAccData = accounts.find((a) => a.name === selectedAccount) || {};

  return {
    accounts,
    selectedAccount,
    currentAccData,
    newAccountName,
    setNewAccountName,
    showAccountManagerModal,
    setShowAccountManagerModal,
    isAccountDropdownOpen,
    setIsAccountDropdownOpen,
    loggingInPlatform,
    fetchAccounts,
    handleAccountChange,
    handleCreateAccount,
    handleTriggerLogin,
    handleOpenTikTokStudioBrowser,
    handleOpenMetaBusinessBrowser,
  };
}
