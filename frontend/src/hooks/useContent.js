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
  const [filterDate, setFilterDate] = useState('All');
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

      if (fetchedItems.length > 0) {
        setSelectedItemKey((prev) => {
          const stillExists = fetchedItems.some((i) => i.item_key === prev);
          return stillExists ? prev : fetchedItems[0].item_key;
        });
      } else {
        setSelectedItemKey(null);
      }

      const initialEdits = {};
      fetchedItems.forEach((item) => {
        initialEdits[item.item_key] = {
          caption: item.caption,
          soundMode: item.meta?.sound_mode || 'search',
          soundQuery: item.meta?.sound_query || 'school',
          soundDb: item.meta?.sound_db || '-7',
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

  // Derived filtered and sorted items
  const availableDates = Array.from(new Set(items.map((i) => i.date))).sort();

  const sortedItems = [...items]
    .filter((item) => {
      if (filterCategory !== 'All' && item.category !== filterCategory) return false;
      if (filterStatus !== 'All') {
        const uploaded = item.uploaded_platforms || [];
        const hasTiktok = uploaded.includes('tiktok');
        const hasMeta = uploaded.includes('meta') || uploaded.includes('instagram');
        if (filterStatus === 'PENDING' && uploaded.length > 0) return false;
        if (filterStatus === 'UPLOADED' && uploaded.length === 0) return false;
        if (filterStatus === 'TIKTOK_ONLY' && (!hasTiktok || hasMeta)) return false;
        if (filterStatus === 'META_ONLY' && (!hasMeta || hasTiktok)) return false;
        if (filterStatus === 'ALL_PLATFORMS' && (!hasTiktok || !hasMeta)) return false;
      }
      if (filterDate !== 'All' && item.date !== filterDate) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'date-desc') {
        return b.date.localeCompare(a.date) || b.name.localeCompare(a.name);
      }
      if (sortBy === 'date-asc') {
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
        return b.date.localeCompare(a.date);
      }
      return 0;
    });

  const selectedItem = items.find((i) => i.item_key === selectedItemKey) || sortedItems[0] || null;
  const currentEdit = selectedItem ? (editedItems[selectedItem.item_key] || {
    caption: selectedItem.caption,
    soundMode: selectedItem.meta?.sound_mode || 'search',
    soundQuery: selectedItem.meta?.sound_query || 'school',
    soundDb: selectedItem.meta?.sound_db || '-7',
    scheduledTime: selectedItem.meta?.scheduled_time || '',
  }) : null;

  const isInspectorScheduled = Boolean(currentEdit?.scheduledTime);
  const currentHashtags = currentEdit ? (currentEdit.caption?.match(/#[A-Za-z0-9_]+/g) || []) : [];

  // Active platforms computation
  const activePlatforms = [];
  if (currentAccData.tiktok_active) activePlatforms.push('TikTok');
  if (currentAccData.meta_active) activePlatforms.push('Meta Suite');

  let publishBtnText = 'Publish Konten';
  const isPublishDisabled = activePlatforms.length === 0;

  if (activePlatforms.length === 0) {
    publishBtnText = 'Belum Ada Platform Terhubung (Hubungkan Akun)';
  } else if (activePlatforms.length === 1) {
    publishBtnText = `Publish to ${activePlatforms[0]}`;
  } else {
    publishBtnText = `Publish to TikTok & Meta Suite`;
  }

  // Action: Save Caption & Metadata
  const handleSaveCaption = async (item) => {
    if (!item) return;
    const edit = editedItems[item.item_key] || {};
    try {
      const data = await saveCaptionApi({
        account: item.account,
        category: item.category,
        date: item.date,
        item_name: item.name,
        caption: edit.caption || item.caption,
        sound_mode: edit.soundMode || item.meta?.sound_mode || 'search',
        sound_query: edit.soundQuery || 'school',
        sound_db: edit.soundDb || '-7',
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
        topic: item.name,
        category: item.category,
        account: item.account,
      });
      if (data.status === 'success') {
        setEditedItems((prev) => ({
          ...prev,
          [item.item_key]: {
            ...prev[item.item_key],
            caption: data.caption,
          },
        }));
        showToast(`AI berhasil merumuskan caption untuk '${item.name}'`);
      } else {
        showToast(data.detail || 'Gagal menghasilkan caption', 'error');
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
      showToast('Harap hubungkan akun ke minimal satu platform (TikTok atau Meta Suite)', 'error');
      setShowAccountManagerModal(true);
      return;
    }
    if (platformTarget === 'tiktok' && !currentAccData.tiktok_active) {
      showToast('Sesi login TikTok belum terhubung. Silakan hubungkan akun TikTok terlebih dahulu.', 'error');
      setShowAccountManagerModal(true);
      return;
    }
    if (platformTarget === 'meta' && !currentAccData.meta_active) {
      showToast('Sesi login Meta Suite belum terhubung. Silakan hubungkan akun Meta terlebih dahulu.', 'error');
      setShowAccountManagerModal(true);
      return;
    }

    await handleSaveCaption(item);
    setUploadingItem(item.item_key);

    const targetLabel = platformTarget === 'all'
      ? activePlatforms.join(' & ')
      : (platformTarget === 'tiktok' ? 'TikTok Studio' : 'Meta Business Suite');

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
        
        // Polling setiap 4 detik untuk memperbarui status upload secara real-time
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

              // Cek apakah ada platform baru yang berhasil terposting
              const hasNewUpload = newPlatforms.length > initialPlatforms.length ||
                (platformTarget === 'tiktok' && newPlatforms.includes('tiktok') && !initialPlatforms.includes('tiktok')) ||
                (platformTarget === 'meta' && (newPlatforms.includes('meta') || newPlatforms.includes('instagram')) && !(initialPlatforms.includes('meta') || initialPlatforms.includes('instagram')));

              if (hasNewUpload) {
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

          // Timeout setelah 2.5 menit (35 x 4s) jika user menutup browser manual
          if (pollCount >= 35) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
            setUploadingItem(null);
            fetchContent();
          }
        }, 4000);
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
