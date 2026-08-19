import { useState, useEffect, useCallback } from 'react';
import {
  fetchAccountsApi,
  createAccountApi,
  triggerLoginApi,
  openTikTokStudioApi,
  openInstagramApi,
  openFacebookApi,
  loginInstagramMobileApi,
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
              const isIGActive = loggingInPlatform.platform === 'instagram' && targetAcc.instagram_active;

              if (isTTActive || isIGActive) {
                showToast(`Sesi login ${loggingInPlatform.platform === 'tiktok' ? 'TikTok' : 'Instagram'} untuk '${loggingInPlatform.account}' berhasil terhubung!`);
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
    const platformLabel = platform === 'tiktok' ? 'TikTok' : 'Instagram';
    showToast(`Membuka browser visual untuk login ${platformLabel} akun '${accName}'...`);
    setLoggingInPlatform({ account: accName, platform });
    try {
      const data = await triggerLoginApi(accName, platform);
      if (data.status === 'started') {
        showToast(`Jendela browser visual terbuka. Silakan login di browser.`);
      }
    } catch {
      showToast(`Gagal memulai sesi login ${platformLabel}`, 'error');
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

  const handleOpenInstagramBrowser = async (accName) => {
    if (!accName) return;
    showToast(`Membuka Instagram Web akun '${accName}' di browser penuh...`);
    try {
      const data = await openInstagramApi(accName);
      if (data.status === 'started') {
        showToast(`Browser Instagram terbuka untuk akun '${accName}'`);
      }
    } catch {
      showToast('Gagal membuka Instagram', 'error');
    }
  };

  const handleOpenFacebookBrowser = async (accName) => {
    if (!accName) return;
    showToast(`Membuka Facebook Fanspage akun '${accName}' di browser penuh...`);
    try {
      const data = await openFacebookApi(accName);
      if (data.status === 'started') {
        showToast(`Browser Facebook terbuka untuk akun '${accName}'`);
      }
    } catch {
      showToast('Gagal membuka Facebook', 'error');
    }
  };

  const handleLoginInstagramMobile = async (accName, username, password, verificationCode = null) => {
    if (!accName || !username || !password) {
      showToast('Username dan Password Instagram wajib diisi', 'error');
      return { status: 'error', message: 'Username dan Password wajib diisi' };
    }
    showToast(`Menghubungkan Instagram Mobile untuk '${accName}'...`);
    try {
      const res = await loginInstagramMobileApi(accName, username, password, verificationCode);
      if (res.status === 'success') {
        showToast(`✓ Berhasil terhubung ke Instagram Mobile (@${username})!`, 'success');
        await fetchAccounts();
        return res;
      } else if (res.status === '2fa_required') {
        showToast('Verifikasi 2FA diperlukan. Masukkan kode OTP / Authenticator.', 'warning');
        return res;
      } else {
        showToast(res.message || 'Gagal login Instagram Mobile', 'error');
        return res;
      }
    } catch {
      showToast('Terjadi kesalahan saat menghubungkan Instagram Mobile', 'error');
      return { status: 'error', message: 'Gagal menghubungkan Instagram Mobile' };
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
    handleLoginInstagramMobile,
    handleOpenTikTokStudioBrowser,
    handleOpenInstagramBrowser,
    handleOpenFacebookBrowser,
  };
}
