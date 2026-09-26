// Content Queue & Upload API endpoints

export async function getLivePostLinksApi(account) {
  const url = account ? `/api/content/links?account=${encodeURIComponent(account)}` : '/api/content/links';
  const res = await fetch(url);
  return await res.json();
}

export async function fetchSchedulerStatusApi() {
  const res = await fetch('/api/scheduler/status');
  return await res.json();
}

export async function toggleSchedulerApi() {
  const res = await fetch('/api/scheduler/toggle', { method: 'POST' });
  return await res.json();
}

export async function triggerSchedulerCheckApi() {
  const res = await fetch('/api/scheduler/check', { method: 'POST' });
  return await res.json();
}

export async function fetchContentApi(account) {
  const url = account ? `/api/content?account=${encodeURIComponent(account)}` : '/api/content';
  const res = await fetch(url);
  return await res.json();
}

export async function saveCaptionApi(payload) {
  const res = await fetch('/api/content/caption/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return await res.json();
}

export async function generateCaptionApi(payload) {
  const res = await fetch('/api/content/caption/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return await res.json();
}

export async function uploadMediaFilesApi(formData) {
  const res = await fetch('/api/content/upload-media', {
    method: 'POST',
    body: formData,
  });
  return await res.json();
}

export async function uploadItemApi(payload) {
  const res = await fetch('/api/content/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return await res.json();
}

export async function deleteContentItemApi(payload) {
  const res = await fetch('/api/content/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return await res.json();
}

export async function reorderQueueApi(account, orderedKeys) {
  const res = await fetch('/api/content/reorder', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account, ordered_keys: orderedKeys }),
  });
  return await res.json();
}

export async function batchScheduleContentApi(account, items) {
  const res = await fetch('/api/content/batch-schedule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account, items }),
  });
  return await res.json();
}

export async function batchClearScheduleApi(account, items = null) {
  const res = await fetch('/api/content/batch-clear-schedule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account, items }),
  });
  return await res.json();
}

export async function initDateFolderApi(account, date) {
  const res = await fetch('/api/content/init-date', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account, date }),
  });
  return await res.json();
}

export async function updatePostLinksApi(account, itemKey, postUrls) {
  const res = await fetch('/api/content/update-links', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account, item_key: itemKey, post_urls: postUrls }),
  });
  return await res.json();
}

export async function fetchPostLinksApi(account, itemKey, caption = '', category = '', platforms = null, forceRefresh = false) {
  const res = await fetch('/api/content/find-links', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      account,
      item_key: itemKey,
      caption,
      category,
      platforms,
      force_refresh: forceRefresh
    }),
  });
  return await res.json();
}

export async function fetchPublishProgressApi(sessionId) {
  const res = await fetch(`/api/content/upload/progress?session_id=${encodeURIComponent(sessionId)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch progress: ${res.statusText}`);
  }
  return await res.json();
}

export function getPublishStreamUrl(sessionId) {
  return `/api/content/upload/stream?session_id=${encodeURIComponent(sessionId)}`;
}

export async function searchTikTokProductsApi(account, keyword = '') {
  const url = `/api/tiktok/products?account=${encodeURIComponent(account)}&keyword=${encodeURIComponent(keyword)}`;
  const res = await fetch(url);
  return await res.json();
}
