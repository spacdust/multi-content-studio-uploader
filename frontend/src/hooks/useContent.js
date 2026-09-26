import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  fetchContentApi,
  saveCaptionApi,
  generateCaptionApi,
  uploadItemApi,
  deleteContentItemApi,
  initDateFolderApi,
  uploadMediaFilesApi,
  fetchPublishProgressApi,
  getPublishStreamUrl,
  fetchSchedulerStatusApi,
  reorderQueueApi,
  batchScheduleContentApi,
  batchClearScheduleApi,
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
  const [sortBy, setSortBy] = useState('custom');

  // Metadata Edits per Item
  const [editedItems, setEditedItems] = useState({});
  const [uploadingItem, setUploadingItem] = useState(null);
  const [generatingCaption, setGeneratingCaption] = useState(null);

  // Interactive Real-Time Publishing Modal State
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [publishSessionData, setPublishSessionData] = useState(null);
  const [publishMinimized, setPublishMinimized] = useState(false);
  const eventSourceRef = useRef(null);
  const itemsRef = useRef([]);

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

  // Batch / Mass Upload & Polling State
  const [batchPublishing, setBatchPublishing] = useState(false);
  const [showMassUploadModal, setShowMassUploadModal] = useState(false);
  const batchAbortRef = useRef(false);
  const pollingRef = useRef(null);

  // Background Auto-Scheduler & Content Auto-Sync Polling
  const [schedulerStatus, setSchedulerStatus] = useState(null);

  const fetchContent = useCallback(async (accountToFetch = selectedAccount, isSilent = false) => {
    if (!accountToFetch) return;
    if (!isSilent) {
      setLoadingContent((prev) => (itemsRef.current && itemsRef.current.length > 0 ? false : true));
    }
    try {
      const data = await fetchContentApi(accountToFetch);
      const fetchedItems = data.items || [];
      itemsRef.current = fetchedItems;
      setItems(fetchedItems);

      setEditedItems((prevEdits) => {
        const nextEdits = { ...prevEdits };
        fetchedItems.forEach((item) => {
          const defaultDb = item.category === 'Video' ? '-7' : '0';
          if (!nextEdits[item.item_key]) {
            nextEdits[item.item_key] = {
              caption: item.caption || '',
              tiktokMentions: item.meta?.tiktok_mentions || '',
              instagramMentions: item.meta?.instagram_mentions || '',
              soundMode: item.meta?.sound_mode || 'favorite',
              soundQuery: item.meta?.sound_query ?? '',
              soundDb: item.meta?.sound_db !== undefined && item.meta?.sound_db !== null && item.meta?.sound_db !== '' ? item.meta.sound_db : defaultDb,
              scheduledTime: item.meta?.scheduled_time || '',
              tiktokProduct: item.meta?.tiktok_product || { enabled: false },
            };
          } else {
            if (!nextEdits[item.item_key].caption && item.caption) {
              nextEdits[item.item_key].caption = item.caption;
            }
            if (nextEdits[item.item_key].tiktokMentions === undefined && item.meta?.tiktok_mentions) {
              nextEdits[item.item_key].tiktokMentions = item.meta.tiktok_mentions;
            }
            if (nextEdits[item.item_key].instagramMentions === undefined && item.meta?.instagram_mentions) {
              nextEdits[item.item_key].instagramMentions = item.meta.instagram_mentions;
            }
          }
        });
        return nextEdits;
      });
      return fetchedItems;
    } catch {
      if (!isSilent) {
        showToast('Gagal memuat antrean konten', 'error');
      }
    } finally {
      setLoadingContent(false);
    }
  }, [selectedAccount, showToast]);

  useEffect(() => {
    if (selectedAccount) {
      fetchContent(selectedAccount);
    }
  }, [selectedAccount, fetchContent]);

  const refreshSchedulerStatus = useCallback(async () => {
    try {
      const data = await fetchSchedulerStatusApi();
      if (data) setSchedulerStatus(data);
    } catch {
      // Ignore network jitter
    }
  }, []);

  // Continuous background auto-sync every 5 seconds for instant status updates
  useEffect(() => {
    refreshSchedulerStatus();
    const interval = setInterval(() => {
      refreshSchedulerStatus();
      if (selectedAccount && !batchPublishing) {
        fetchContent(selectedAccount, true);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [selectedAccount, batchPublishing, fetchContent, refreshSchedulerStatus]);

  // Auto-refresh when user focuses back on the tab
  useEffect(() => {
    const handleFocus = () => {
      if (selectedAccount) {
        fetchContent(selectedAccount, false);
        refreshSchedulerStatus();
      }
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [selectedAccount, fetchContent, refreshSchedulerStatus]);

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

      if (sortBy === 'custom') {
        const ordA = a.custom_order !== undefined && a.custom_order !== null ? a.custom_order : 999999;
        const ordB = b.custom_order !== undefined && b.custom_order !== null ? b.custom_order : 999999;
        if (ordA !== ordB) {
          return ordA - ordB;
        }
        return (
          a.date.localeCompare(b.date) ||
          a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' })
        );
      }
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

  // Unuploaded / Pending items from currently filtered list
  const unuploadedSortedItems = useMemo(() => {
    return sortedItems.filter((item) => {
      const uploaded = item.uploaded_platforms || [];
      return uploaded.length === 0;
    });
  }, [sortedItems]);

  // Mass upload queue: executes strictly in the exact order shown on screen (#1 -> #2 -> #3 -> ...)
  const massUploadQueue = useMemo(() => {
    return [...unuploadedSortedItems];
  }, [unuploadedSortedItems]);

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
    setEditedItems({});
  }, [selectedAccount]);

  const selectedItem = (selectedItemKey && sortedItems.find((i) => i.item_key === selectedItemKey)) || sortedItems[0] || null;
  const currentEdit = selectedItem ? (editedItems[selectedItem.item_key] || {
    caption: selectedItem.caption,
    soundMode: selectedItem.meta?.sound_mode || 'favorite',
    soundQuery: selectedItem.meta?.sound_query ?? '',
    soundDb: selectedItem.meta?.sound_db !== undefined && selectedItem.meta?.sound_db !== null && selectedItem.meta?.sound_db !== '' ? selectedItem.meta.sound_db : (selectedItem.category === 'Video' ? '-7' : '0'),
    scheduledTime: selectedItem.meta?.scheduled_time || '',
    tiktokProduct: selectedItem.meta?.tiktok_product || { enabled: false },
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

  // Action: Reorder items (Move Up, Down, Top, Bottom)
  const handleMoveItem = useCallback(
    async (itemKey, direction) => {
      if (!itemKey || !selectedAccount) return;

      const currentSortedKeys = sortedItems.map((it) => it.item_key);
      const currentIndex = currentSortedKeys.indexOf(itemKey);
      if (currentIndex === -1) return;

      let targetIndex = currentIndex;
      if (direction === 'up' && currentIndex > 0) {
        targetIndex = currentIndex - 1;
      } else if (direction === 'down' && currentIndex < currentSortedKeys.length - 1) {
        targetIndex = currentIndex + 1;
      } else if (direction === 'top' && currentIndex > 0) {
        targetIndex = 0;
      } else if (direction === 'bottom' && currentIndex < currentSortedKeys.length - 1) {
        targetIndex = currentSortedKeys.length - 1;
      } else {
        return; // No change needed
      }

      const newSortedKeys = [...currentSortedKeys];
      const [movedKey] = newSortedKeys.splice(currentIndex, 1);
      newSortedKeys.splice(targetIndex, 0, movedKey);

      // Preserve any unlisted items for this account
      const allAccountKeys = items.map((it) => it.item_key);
      const remainingKeys = allAccountKeys.filter((k) => !newSortedKeys.includes(k));
      const fullOrderedKeys = [...newSortedKeys, ...remainingKeys];

      // Optimistically update local items state
      const orderLookup = {};
      fullOrderedKeys.forEach((k, idx) => {
        orderLookup[k] = idx;
      });

      setItems((prevItems) =>
        prevItems.map((it) => ({
          ...it,
          custom_order: orderLookup[it.item_key] !== undefined ? orderLookup[it.item_key] : 999999,
        }))
      );

      setSortBy('custom');
      showToast(
        direction === 'top'
          ? '✓ Dipindahkan ke urutan teratas (#1)'
          : direction === 'bottom'
          ? '✓ Dipindahkan ke urutan terbawah'
          : direction === 'up'
          ? '✓ Urutan antrean dinaikkan'
          : '✓ Urutan antrean diturunkan'
      );

      try {
        await reorderQueueApi(selectedAccount, fullOrderedKeys);
      } catch {
        // Silently catch
      }
    },
    [sortedItems, selectedAccount, items, showToast]
  );

  // Action: Drag and Drop Reorder
  const handleDragReorder = useCallback(
    async (sourceKey, targetKey) => {
      if (!sourceKey || !targetKey || sourceKey === targetKey || !selectedAccount) return;

      const currentSortedKeys = sortedItems.map((it) => it.item_key);
      const sourceIndex = currentSortedKeys.indexOf(sourceKey);
      const targetIndex = currentSortedKeys.indexOf(targetKey);
      if (sourceIndex === -1 || targetIndex === -1) return;

      const newSortedKeys = [...currentSortedKeys];
      const [movedKey] = newSortedKeys.splice(sourceIndex, 1);
      newSortedKeys.splice(targetIndex, 0, movedKey);

      const allAccountKeys = items.map((it) => it.item_key);
      const remainingKeys = allAccountKeys.filter((k) => !newSortedKeys.includes(k));
      const fullOrderedKeys = [...newSortedKeys, ...remainingKeys];

      const orderLookup = {};
      fullOrderedKeys.forEach((k, idx) => {
        orderLookup[k] = idx;
      });

      setItems((prevItems) =>
        prevItems.map((it) => ({
          ...it,
          custom_order: orderLookup[it.item_key] !== undefined ? orderLookup[it.item_key] : 999999,
        }))
      );

      setSortBy('custom');
      showToast('✓ Urutan antrean berhasil diubah');

      try {
        await reorderQueueApi(selectedAccount, fullOrderedKeys);
      } catch {
        // Silently catch
      }
    },
    [sortedItems, selectedAccount, items, showToast]
  );

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
        tiktok_mentions: edit.tiktokMentions !== undefined ? edit.tiktokMentions : (item.meta?.tiktok_mentions || ''),
        instagram_mentions: edit.instagramMentions !== undefined ? edit.instagramMentions : (item.meta?.instagram_mentions || ''),
        sound_mode: edit.soundMode !== undefined ? edit.soundMode : (item.meta?.sound_mode || 'favorite'),
        sound_query: edit.soundQuery !== undefined ? edit.soundQuery : (item.meta?.sound_query ?? ''),
        sound_db: edit.soundDb !== undefined && edit.soundDb !== null && edit.soundDb !== '' ? edit.soundDb : itemDefaultDb,
        scheduled_time: edit.scheduledTime || null,
        tiktok_product: edit.tiktokProduct !== undefined ? edit.tiktokProduct : (item.meta?.tiktok_product || { enabled: false }),
      });
      if (data.status === 'success') {
        showToast('Perubahan caption, tag platform & jadwal tersimpan!');
        const updatedTiktokProduct = edit.tiktokProduct !== undefined ? edit.tiktokProduct : (item.meta?.tiktok_product || { enabled: false });
        setItems((prevItems) => {
          const nextItems = prevItems.map((it) => {
            if (it.item_key === item.item_key) {
              return {
                ...it,
                caption: edit.caption !== undefined ? edit.caption : it.caption,
                meta: {
                  ...(it.meta || {}),
                  tiktok_mentions: edit.tiktokMentions !== undefined ? edit.tiktokMentions : (it.meta?.tiktok_mentions || ''),
                  instagram_mentions: edit.instagramMentions !== undefined ? edit.instagramMentions : (it.meta?.instagram_mentions || ''),
                  sound_mode: edit.soundMode !== undefined ? edit.soundMode : (it.meta?.sound_mode || 'favorite'),
                  sound_query: edit.soundQuery !== undefined ? edit.soundQuery : (it.meta?.sound_query ?? ''),
                  sound_db: edit.soundDb !== undefined && edit.soundDb !== null && edit.soundDb !== '' ? edit.soundDb : itemDefaultDb,
                  scheduled_time: edit.scheduledTime || null,
                  tiktok_product: updatedTiktokProduct,
                },
              };
            }
            return it;
          });
          itemsRef.current = nextItems;
          return nextItems;
        });
        fetchContent(selectedAccount, true);
        refreshSchedulerStatus();
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
  // Helper: Promisified Single Item Upload with SSE & Polling Fallback
  const uploadSingleItemPromise = (item, platformTarget = 'all', batchInfo = null) => {
    return new Promise(async (resolve) => {
      if (!item) return resolve({ success: false, error: 'Item tidak valid' });

      try {
        await handleSaveCaption(item);
        setUploadingItem(item.item_key);

        const data = await uploadItemApi({
          account: item.account,
          item_key: item.item_key,
          platform: platformTarget,
          headless: false,
        });

        if (!data || data.status !== 'started' || !data.session_id) {
          setUploadingItem(null);
          return resolve({ success: false, error: data?.message || 'Gagal memulai proses upload' });
        }

        const initialPlatforms = {};
        (data.target_platforms || activePlatforms || ['tiktok']).forEach((p) => {
          initialPlatforms[p] = {
            status: 'pending',
            percent: 0,
            current_step: 'Menunggu antrean...',
            post_url: null,
          };
        });

        setPublishSessionData({
          session_id: data.session_id,
          account: item.account,
          item_key: item.item_key,
          item_name: item.name,
          category: item.category,
          status: 'running',
          percent: 5,
          current_step: 'Membuka antrean publish & browser visual...',
          platforms: initialPlatforms,
          batchInfo: batchInfo,
          logs: [
            {
              timestamp: new Date().toLocaleTimeString('id-ID', { hour12: false }),
              platform: 'SYS',
              message: `Memulai pipeline publish untuk '${item.name}' [${(data.target_platforms || []).join(', ').toUpperCase()}]`,
              type: 'info',
            },
          ],
        });

        setPublishModalOpen(true);
        setPublishMinimized(false);

        // Tutup EventSource lama jika ada
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }

        const sseUrl = getPublishStreamUrl(data.session_id);
        const es = new EventSource(sseUrl);
        eventSourceRef.current = es;

        let hasResolved = false;

        const cleanupAndResolve = (result) => {
          if (hasResolved) return;
          hasResolved = true;
          if (es) es.close();
          if (eventSourceRef.current === es) eventSourceRef.current = null;
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          setUploadingItem(null);
          fetchContent(selectedAccount, true); // silent refresh
          resolve(result);
        };

        es.onmessage = (e) => {
          try {
            const parsed = JSON.parse(e.data);
            if (parsed && parsed.session_id) {
              setPublishSessionData({
                ...parsed,
                batchInfo: batchInfo,
              });

              if (parsed.status === 'completed') {
                cleanupAndResolve({ success: true, session: parsed });
              } else if (parsed.status === 'failed') {
                cleanupAndResolve({ success: false, session: parsed, error: parsed.error_msg });
              }
            }
          } catch (err) {
            console.error('Error parsing SSE publish data:', err);
          }
        };

        es.onerror = () => {
          // Fallback polling jika EventSource terputus
          if (pollingRef.current) clearInterval(pollingRef.current);
          pollingRef.current = setInterval(async () => {
            try {
              const prog = await fetchPublishProgressApi(data.session_id);
              if (prog) {
                setPublishSessionData({
                  ...prog,
                  batchInfo: batchInfo,
                });
                if (prog.status === 'completed') {
                  cleanupAndResolve({ success: true, session: prog });
                } else if (prog.status === 'failed') {
                  cleanupAndResolve({ success: false, session: prog, error: prog.error_msg });
                }
              }
            } catch {
              // Network jitter
            }
          }, 1500);
        };
      } catch (err) {
        setUploadingItem(null);
        resolve({ success: false, error: err.message });
      }
    });
  };

  // Action: Single Upload
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

    const targetLabel = platformTarget === 'all'
      ? activePlatforms.join(' & ')
      : (platformTarget === 'tiktok' ? 'TikTok Studio' : (platformTarget === 'instagram' ? 'Instagram Web' : 'Facebook Fanspage'));

    showToast(`Memulai proses upload ${item.name} ke ${targetLabel}...`, 'info');

    const result = await uploadSingleItemPromise(item, platformTarget, null);
    if (result.success) {
      showToast(`✓ Berhasil! ${item.name} berhasil terposting ke ${targetLabel}!`, 'success');
    } else {
      showToast(`Upload ${item.name} mengalami kendala: ${result.error || 'Gagal'}`, 'error');
    }
  };

  // Action: Stop Mass Upload
  const handleStopMassUpload = () => {
    batchAbortRef.current = true;
    showToast('Menghentikan antrean upload massal...', 'warn');
  };

  // Action: Start Sequential Mass Upload (from bottom to top)
  const handleStartMassUpload = async () => {
    if (isPublishDisabled) {
      showToast('Harap hubungkan akun ke minimal satu platform terlebih dahulu', 'error');
      setShowAccountManagerModal(true);
      return;
    }

    const queueToProcess = [...massUploadQueue];
    if (queueToProcess.length === 0) {
      showToast('Tidak ada media pending untuk diupload', 'info');
      return;
    }

    setShowMassUploadModal(false);
    setBatchPublishing(true);
    batchAbortRef.current = false;

    showToast(`🚀 Memulai upload massal ${queueToProcess.length} media secara berurutan (dari bawah ke atas)...`, 'info');

    let successCount = 0;
    let failedCount = 0;

    for (let i = 0; i < queueToProcess.length; i++) {
      if (batchAbortRef.current) {
        showToast(`Upload massal dihentikan pada item ${i + 1}/${queueToProcess.length}.`, 'warn');
        break;
      }

      const currentItem = queueToProcess[i];
      const batchInfo = {
        current: i + 1,
        total: queueToProcess.length,
        item: currentItem,
      };

      const result = await uploadSingleItemPromise(currentItem, 'all', batchInfo);
      if (result.success) {
        successCount++;
        showToast(`✓ (${i + 1}/${queueToProcess.length}) ${currentItem.name} selesai terposting!`, 'success');
      } else {
        failedCount++;
        showToast(`⚠️ (${i + 1}/${queueToProcess.length}) ${currentItem.name} gagal: ${result.error || 'Kendala'}`, 'error');
      }

      // Jeda 2 detik sebelum berpindah ke item berikutnya jika masih ada antrean
      if (i < queueToProcess.length - 1 && !batchAbortRef.current) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    }

    setBatchPublishing(false);
    await fetchContent(selectedAccount);

    if (!batchAbortRef.current) {
      showToast(
        `🎉 Upload massal selesai! Berhasil: ${successCount}, Gagal: ${failedCount}`,
        successCount > 0 ? 'success' : 'warn'
      );
    }
  };

  const handleBatchSchedule = async (scheduledItems) => {
    if (!selectedAccount) {
      showToast('Pilih akun terlebih dahulu', 'error');
      return;
    }
    if (!scheduledItems || scheduledItems.length === 0) {
      showToast('Tidak ada media untuk dijadwalkan', 'info');
      return;
    }

    try {
      const itemsPayload = scheduledItems.map((item) => ({
        category: item.category,
        date: item.date,
        item_name: item.name,
        scheduled_time: item.scheduled_time,
      }));

      const res = await batchScheduleContentApi(selectedAccount, itemsPayload);
      if (res.status === 'success') {
        showToast(res.message || `Berhasil menjadwalkan ${itemsPayload.length} konten!`, 'success');
        await fetchContent(selectedAccount);
        refreshSchedulerStatus();
      } else {
        showToast(res.message || 'Gagal menyimpan jadwal antrean', 'error');
      }
    } catch (err) {
      console.error('Error batch scheduling:', err);
      showToast(`Gagal menyimpan jadwal: ${err.message}`, 'error');
    }
  };

  const handleBatchClearSchedule = async (itemsToClear) => {
    if (!selectedAccount) {
      showToast('Pilih akun terlebih dahulu', 'error');
      return;
    }

    try {
      const itemsPayload = (itemsToClear || []).map((item) => ({
        category: item.category,
        date: item.date,
        item_name: item.name,
      }));

      const res = await batchClearScheduleApi(selectedAccount, itemsPayload);
      if (res.status === 'success') {
        showToast(res.message || 'Berhasil menghapus semua jadwal antrean!', 'success');
        await fetchContent(selectedAccount);
        refreshSchedulerStatus();
      } else {
        showToast(res.message || 'Gagal menghapus jadwal antrean', 'error');
      }
    } catch (err) {
      console.error('Error clearing batch schedule:', err);
      showToast(`Gagal menghapus jadwal: ${err.message}`, 'error');
    }
  };

  const closePublishModal = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    setPublishModalOpen(false);
    setPublishMinimized(false);
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
        showToast(data.message || 'Media berhasil ditambahkan ke antrean! AI sedang membuat caption otomatis di latar belakang...');
        setShowUploadModal(false);
        setSingleMediaFile(null);
        setSingleMediaPreviewUrl(null);
        setCarouselSlides([]);
        setIsScheduledUpload(false);
        setUploadScheduleTime(getLocalNowIso());
        fetchContent();

        // Background auto-refresh to seamlessly populate AI-generated caption
        setTimeout(() => fetchContent(), 3000);
        setTimeout(() => fetchContent(), 7000);
        setTimeout(() => fetchContent(), 12000);
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
    publishModalOpen,
    setPublishModalOpen,
    publishSessionData,
    setPublishSessionData,
    publishMinimized,
    setPublishMinimized,
    closePublishModal,
    fetchContent,
    handleSaveCaption,
    handleGenerateCaption,
    handleUploadItem,
    handleConfirmDelete,
    handleCreateDateFolder,
    handleMediaFileUpload,
    unuploadedSortedItems,
    massUploadQueue,
    batchPublishing,
    showMassUploadModal,
    setShowMassUploadModal,
    handleStartMassUpload,
    handleStopMassUpload,
    handleBatchSchedule,
    handleBatchClearSchedule,
    schedulerStatus,
    refreshSchedulerStatus,
    handleMoveItem,
    handleDragReorder,
  };
}
