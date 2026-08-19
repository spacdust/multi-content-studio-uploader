import { useState, useEffect, useCallback, useRef } from 'react';
import {
  fetchContentApi,
  saveCaptionApi,
  generateCaptionApi,
  uploadItemApi,
  deleteContentItemApi,
  initDateFolderApi,
  uploadMediaFilesApi,
} from '../api/contentApi';
import { getLocalNowIso, getLocalTodayDate } from '../utils/dateUtils';

export function useContent(selectedAccount, currentAccData, showToast, setShowAccountManagerModal) {
  const [items, setItems] = useState([]);
  const [loadingContent, setLoadingContent] = useState(false);
  const [selectedItemKey, setSelectedItemKey] = useState(null);

  // Filters & Sorting
  const [filterCategory, setFilterCategory] = useState('All');
  const [filterDate, setFilterDate] = useState('TODAY');
  const [filterStatus, setFilterStatus] = useState('All');
  const [sortBy, setSortBy] = useState('date-desc');

  // Metadata Edits per Item
  const [editedItems, setEditedItems] = useState({});
  const [uploadingItem, setUploadingItem] = useState(null);
  const [generatingCaption, setGeneratingCaption] = useState(null);

  // Modals & Delete Action
  const [isDeleting, setIsDeleting] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  const [showDeleteConfirmModal, setShowDeleteConfirmModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showAddDateModal, setShowAddDateModal] = useState(false);
  const [newDateInput, setNewDateInput] = useState('');

  // Carousel interactive viewer index per item
  const [carouselSlideIndices, setCarouselSlideIndices] = useState({});

  // Upload Modal State
  const [singleMediaFile, setSingleMediaFile] = useState(null);
  const [singleMediaPreviewUrl, setSingleMediaPreviewUrl] = useState(null);
  const [carouselSlides, setCarouselSlides] = useState([]);
  const [isScheduledUpload, setIsScheduledUpload] = useState(false);
  const [uploadScheduleTime, setUploadScheduleTime] = useState(getLocalNowIso());
  const [uploadDate, setUploadDate] = useState(getLocalTodayDate());
  const [carouselNameInput, setCarouselNameInput] = useState('');
  const [uploadingFileState, setUploadingFileState] = useState(false);

  const fetchContent = useCallback(async (accountToFetch = selectedAccount) => {
    if (!accountToFetch) return;
    setLoadingContent(true);
    try {
      const data = await fetchContentApi(accountToFetch);
      const fetchedItems = data.items || [];
      setItems(fetchedItems);

      const initialEdits = {};
      fetchedItems.forEach((item) => {
        const defaultDb = item.category === 'Video' ? '-7' : '0';
        initialEdits[item.item_key] = {
          caption: item.caption,
          soundMode: item.meta?.sound_mode || 'search',
          soundQuery: item.meta?.sound_query ?? '',
          soundDb: item.meta?.sound_db !== undefined && item.meta?.sound_db !== null && item.meta?.sound_db !== '' ? item.meta.sound_db : defaultDb,
          scheduledTime: item.meta?.scheduled_time || '',
        };
      });
      setEditedItems((prev) => ({ ...initialEdits, ...prev }));
      return fetchedItems;
    } catch {
      showToast('Gagal memuat antrean konten', 'error');
    } finally {
      setLoadingContent(false);
    }
  }, [selectedAccount, showToast]);

  useEffect(() => {
    if (selectedAccount) {
      fetchContent(selectedAccount);
    }
  }, [selectedAccount, fetchContent]);

  // Auto-refresh when user focuses back on the tab
  useEffect(() => {
    const handleFocus = () => {
      if (selectedAccount) {
        fetchContent(selectedAccount);
      }
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [selectedAccount, fetchContent]);

  // Derived filtered and sorted items
  const availableDates = Array.from(new Set(items.map((i) => i.date))).sort();

  const sortedItems = [...items]
    .filter((item) => {
      if (filterCategory !== 'All' && item.category !== filterCategory) return false;
      if (filterStatus !== 'All') {
        const uploaded = item.uploaded_platforms || [];
        const hasTiktok = uploaded.includes('tiktok');
        const hasInstagram = uploaded.includes('instagram') || uploaded.includes('meta');
        const hasFacebook = uploaded.includes('facebook');
        if (filterStatus === 'PENDING' && uploaded.length > 0) return false;
        if (filterStatus === 'UPLOADED' && uploaded.length === 0) return false;
        if (filterStatus === 'TIKTOK_ONLY' && (!hasTiktok || hasInstagram || hasFacebook)) return false;
        if (filterStatus === 'INSTAGRAM_ONLY' && (!hasInstagram || hasTiktok || hasFacebook)) return false;
        if (filterStatus === 'FACEBOOK_ONLY' && (!hasFacebook || hasTiktok || hasInstagram)) return false;
        if (filterStatus === 'ALL_PLATFORMS' && (!hasTiktok || !hasInstagram || !hasFacebook)) return false;
      }
      if (filterDate === 'TODAY') {
        const todayStr = getLocalTodayDate();
        if (item.date !== todayStr) return false;
      } else if (filterDate !== 'All') {
        if (item.date !== filterDate) return false;
      }
      return true;
    })
    .sort((a, b) => {
      const timeA = a.created_at || a.mtime || 0;
      const timeB = b.created_at || b.mtime || 0;

      if (sortBy === 'date-desc') {
        if (timeA && timeB && timeA !== timeB) {
          return timeB - timeA;
        }
        return b.date.localeCompare(a.date) || b.name.localeCompare(a.name);
      }
      if (sortBy === 'date-asc') {
        if (timeA && timeB && timeA !== timeB) {
          return timeA - timeB;
        }
        return a.date.localeCompare(b.date) || a.name.localeCompare(b.name);
      }
      if (sortBy === 'name-asc') {
        return a.name.localeCompare(b.name);
      }
      if (sortBy === 'name-desc') {
        return b.name.localeCompare(a.name);
      }
      if (sortBy === 'status-pending') {
        if (a.status === 'PENDING' && b.status !== 'PENDING') return -1;
        if (a.status !== 'PENDING' && b.status === 'PENDING') return 1;
        if (timeA && timeB && timeA !== timeB) return timeB - timeA;
        return b.date.localeCompare(a.date);
      }
      return 0;
    });

  // Auto-select topmost item when items load, account changes, or filtered list updates
  useEffect(() => {
    if (sortedItems.length > 0) {
      if (!selectedItemKey || !sortedItems.some((i) => i.item_key === selectedItemKey)) {
        setSelectedItemKey(sortedItems[0].item_key);
      }
    } else {
      setSelectedItemKey(null);
    }
  }, [sortedItems, selectedItemKey]);

  useEffect(() => {
    setSelectedItemKey(null);
  }, [selectedAccount]);

  const selectedItem = (selectedItemKey && sortedItems.find((i) => i.item_key === selectedItemKey)) || sortedItems[0] || null;
  const currentEdit = selectedItem ? (editedItems[selectedItem.item_key] || {
    caption: selectedItem.caption,
    soundMode: selectedItem.meta?.sound_mode || 'search',
    soundQuery: selectedItem.meta?.sound_query ?? '',
    soundDb: selectedItem.meta?.sound_db !== undefined && selectedItem.meta?.sound_db !== null && selectedItem.meta?.sound_db !== '' ? selectedItem.meta.sound_db : (selectedItem.category === 'Video' ? '-7' : '0'),
    scheduledTime: selectedItem.meta?.scheduled_time || '',
  }) : null;

  const isInspectorScheduled = Boolean(currentEdit?.scheduledTime);
  const currentHashtags = currentEdit ? (currentEdit.caption?.match(/#[A-Za-z0-9_]+/g) || []) : [];

  // Active platforms computation
  const activePlatforms = [];
  if (currentAccData.tiktok_active) activePlatforms.push('TikTok');
  if (currentAccData.instagram_active) activePlatforms.push('Instagram');
  if (currentAccData.facebook_active) activePlatforms.push('Facebook');

  let publishBtnText = 'Publish Konten';
  const isPublishDisabled = activePlatforms.length === 0;

  if (activePlatforms.length === 0) {
    publishBtnText = 'Belum Ada Platform Terhubung (Hubungkan Akun)';
  } else if (activePlatforms.length === 1) {
    publishBtnText = `Publish to ${activePlatforms[0]}`;
  } else {
    publishBtnText = `Publish to ${activePlatforms.join(' & ')}`;
  }

  // Action: Save Caption & Metadata
  const handleSaveCaption = async (item) => {
    if (!item) return;
    const edit = editedItems[item.item_key] || {};
    const itemDefaultDb = item.category === 'Video' ? '-7' : '0';
    try {
      const data = await saveCaptionApi({
        account: item.account,
        category: item.category,
        date: item.date,
        item_name: item.name,
        caption: edit.caption || item.caption,
        sound_mode: edit.soundMode || item.meta?.sound_mode || 'search',
        sound_query: edit.soundQuery !== undefined ? edit.soundQuery : (item.meta?.sound_query ?? ''),
        sound_db: edit.soundDb !== undefined && edit.soundDb !== null && edit.soundDb !== '' ? edit.soundDb : itemDefaultDb,
        scheduled_time: edit.scheduledTime || null,
      });
      if (data.status === 'success') {
        showToast('Perubahan caption, jadwal & audio tersimpan!');
        fetchContent();
      }
    } catch {
      showToast('Gagal menyimpan metadata', 'error');
    }
  };

  // Action: Generate Caption with AI
  const handleGenerateCaption = async (item) => {
    if (!item) return;
    setGeneratingCaption(item.item_key);
    try {
      const data = await generateCaptionApi({
        item_name: item.name,
        topic: item.name,
        category: item.category,
        account: item.account,
        item_path: item.path || '',
      });
      if (data?.status === 'success' && data?.caption) {
        setEditedItems((prev) => ({
          ...prev,
          [item.item_key]: {
            ...prev[item.item_key],
            caption: data.caption,
          },
        }));
        showToast(`✓ AI berhasil merumuskan caption untuk '${item.name}'`);
      } else {
        const errorMsg = typeof data?.detail === 'string'
          ? data.detail
          : (data?.message || 'Gagal menghasilkan caption');
        showToast(errorMsg, 'error');
      }
    } catch {
      showToast('Gagal menghubungi service AI Caption', 'error');
    } finally {
      setGeneratingCaption(null);
    }
  };

  // Action: Trigger Upload
  const pollingRef = useRef(null);

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const handleUploadItem = async (item, platformTarget = 'all') => {
    if (!item) return;
    
    if (platformTarget === 'all' && isPublishDisabled) {
      showToast('Harap hubungkan akun ke minimal satu platform (TikTok, Instagram, atau Facebook)', 'error');
      setShowAccountManagerModal(true);
      return;
    }
    if (platformTarget === 'tiktok' && !currentAccData.tiktok_active) {
      showToast('Sesi login TikTok belum terhubung. Silakan hubungkan akun TikTok terlebih dahulu.', 'error');
      setShowAccountManagerModal(true);
      return;
    }
    if (platformTarget === 'instagram' && !currentAccData.instagram_active) {
      showToast('Sesi login Instagram belum terhubung. Silakan hubungkan akun Instagram terlebih dahulu.', 'error');
      setShowAccountManagerModal(true);
      return;
    }
    if (platformTarget === 'facebook' && !currentAccData.facebook_active) {
      showToast('Sesi login Facebook belum terhubung. Silakan hubungkan akun Facebook terlebih dahulu.', 'error');
      setShowAccountManagerModal(true);
      return;
    }

    await handleSaveCaption(item);
    setUploadingItem(item.item_key);

    const targetLabel = platformTarget === 'all'
      ? activePlatforms.join(' & ')
      : (platformTarget === 'tiktok' ? 'TikTok Studio' : (platformTarget === 'instagram' ? 'Instagram Web' : 'Facebook Fanspage'));

    showToast(`Memulai proses upload ${item.name} ke ${targetLabel}...`, 'info');

    try {
      const data = await uploadItemApi({
        account: item.account,
        item_key: item.item_key,
        platform: platformTarget,
        headless: false,
      });
      if (data.status === 'started') {
        showToast(`Browser terbuka. Otomatis memantau & memperbarui status saat upload selesai...`, 'info');
        
        // Polling setiap 3 detik untuk memperbarui status upload secara real-time
        if (pollingRef.current) clearInterval(pollingRef.current);
        const initialPlatforms = [...(item.uploaded_platforms || [])];
        let pollCount = 0;

        pollingRef.current = setInterval(async () => {
          pollCount += 1;
          try {
            const res = await fetchContentApi(selectedAccount);
            if (res?.items) {
              setItems(res.items);
              const updatedItem = res.items.find((i) => i.item_key === item.item_key);
              const newPlatforms = updatedItem?.uploaded_platforms || [];

              // Cek apakah platform target telah selesai diunggah secara penuh
              let isTargetCompleted = false;
              if (platformTarget === 'tiktok') {
                isTargetCompleted = newPlatforms.includes('tiktok') && (!initialPlatforms.includes('tiktok') || pollCount >= 5);
              } else if (platformTarget === 'instagram') {
                isTargetCompleted = (newPlatforms.includes('instagram') || newPlatforms.includes('meta')) && (!initialPlatforms.includes('instagram') || pollCount >= 5);
              } else if (platformTarget === 'facebook') {
                isTargetCompleted = newPlatforms.includes('facebook') && (!initialPlatforms.includes('facebook') || pollCount >= 5);
              } else if (platformTarget === 'all') {
                // Mode Master: Tunggu hingga SEMUA platform aktif (TikTok, Instagram, Facebook) selesai terposting
                const hasAllActive = activePlatforms.length > 0 && activePlatforms.every((p) => {
                  const pLower = p.toLowerCase();
                  if (pLower === 'instagram') return newPlatforms.includes('instagram') || newPlatforms.includes('meta');
                  return newPlatforms.includes(pLower);
                });
                isTargetCompleted = hasAllActive || (newPlatforms.includes('tiktok') && newPlatforms.includes('instagram') && newPlatforms.includes('facebook'));
              }

              if (isTargetCompleted) {
                clearInterval(pollingRef.current);
                pollingRef.current = null;
                setUploadingItem(null);
                showToast(`✓ Berhasil! Status ${item.name} otomatis diperbarui: Terposting ke ${targetLabel}!`, 'success');
                return;
              }
            }
          } catch {
            // Abaikan temporary error saat polling
          }

          // Timeout aman setelah 90x polling (270 detik / 4.5 menit) agar cukup waktu untuk 3 platform berurutan
          if (pollCount >= 90) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
            setUploadingItem(null);
            fetchContent();
          }
        }, 3000);
      }
    } catch {
      showToast('Gagal memulai proses upload', 'error');
      setUploadingItem(null);
    }
  };

  // Action: Confirm Delete
  const handleConfirmDelete = async () => {
    if (!itemToDelete) return;
    setIsDeleting(true);
    try {
      const data = await deleteContentItemApi({
        account: itemToDelete.account,
        category: itemToDelete.category,
        date: itemToDelete.date,
        item_name: itemToDelete.name,
      });
      if (data.status === 'success') {
        showToast(`Berhasil menghapus ${itemToDelete.name}`);
        setShowDeleteConfirmModal(false);
        setItemToDelete(null);
        await fetchContent();
      } else {
        showToast(data.detail || 'Gagal menghapus media', 'error');
      }
    } catch {
      showToast('Gagal menghapus file media', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  // Action: Create Date Folder
  const handleCreateDateFolder = async (e) => {
    if (e) e.preventDefault();
    if (!newDateInput) return;
    try {
      const data = await initDateFolderApi(selectedAccount, newDateInput);
      if (data.status === 'success') {
        showToast(`Folder tanggal ${newDateInput} siap digunakan`);
        setShowAddDateModal(false);
        setNewDateInput('');
        fetchContent();
      } else {
        showToast(data.detail || 'Gagal membuat folder tanggal', 'error');
      }
    } catch {
      showToast('Gagal membuat folder tanggal', 'error');
    }
  };

  // Action: Upload Media Files
  const handleMediaFileUpload = async (category, date, targetCarouselName = null) => {
    if (!selectedAccount) return;
    setUploadingFileState(true);
    showToast(`Mengunggah file media ke antrean ${category}...`, 'info');

    try {
      const formData = new FormData();
      formData.append('account', selectedAccount);
      formData.append('category', category);
      formData.append('date', date);

      if (category === 'Carousel') {
        const finalCarouselName = targetCarouselName || carouselNameInput || `Carousel ${Date.now()}`;
        formData.append('carousel_name', finalCarouselName);
        carouselSlides.forEach((slide) => {
          formData.append('files', slide.file ? slide.file : slide);
        });
      } else if (singleMediaFile) {
        formData.append('files', singleMediaFile.file ? singleMediaFile.file : singleMediaFile);
      }

      if (isScheduledUpload && uploadScheduleTime) {
        formData.append('scheduled_time', uploadScheduleTime);
      }

      const data = await uploadMediaFilesApi(formData);
      if (data.status === 'success') {
        showToast(data.message || 'Media berhasil ditambahkan ke antrean!');
        setShowUploadModal(false);
        setSingleMediaFile(null);
        setSingleMediaPreviewUrl(null);
        setCarouselSlides([]);
        setIsScheduledUpload(false);
        setUploadScheduleTime(getLocalNowIso());
        fetchContent();
      } else {
        showToast(data.detail || 'Gagal mengunggah media', 'error');
      }
    } catch {
      showToast('Gagal memproses upload media', 'error');
    } finally {
      setUploadingFileState(false);
    }
  };

  return {
    items,
    loadingContent,
    selectedItemKey,
    setSelectedItemKey,
    selectedItem,
    sortedItems,
    availableDates,
    filterCategory,
    setFilterCategory,
    filterDate,
    setFilterDate,
    filterStatus,
    setFilterStatus,
    sortBy,
    setSortBy,
    editedItems,
    setEditedItems,
    currentEdit,
    isInspectorScheduled,
    currentHashtags,
    activePlatforms,
    publishBtnText,
    isPublishDisabled,
    uploadingItem,
    generatingCaption,
    isDeleting,
    itemToDelete,
    setItemToDelete,
    showDeleteConfirmModal,
    setShowDeleteConfirmModal,
    showUploadModal,
    setShowUploadModal,
    showAddDateModal,
    setShowAddDateModal,
    newDateInput,
    setNewDateInput,
    carouselSlideIndices,
    setCarouselSlideIndices,
    singleMediaFile,
    setSingleMediaFile,
    singleMediaPreviewUrl,
    setSingleMediaPreviewUrl,
    carouselSlides,
    setCarouselSlides,
    isScheduledUpload,
    setIsScheduledUpload,
    uploadScheduleTime,
    setUploadScheduleTime,
    uploadDate,
    setUploadDate,
    carouselNameInput,
    setCarouselNameInput,
    uploadingFileState,
    fetchContent,
    handleSaveCaption,
    handleGenerateCaption,
    handleUploadItem,
    handleConfirmDelete,
    handleCreateDateFolder,
    handleMediaFileUpload,
  };
}
