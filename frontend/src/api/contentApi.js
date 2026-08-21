// Content Queue & Upload API endpoints

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
