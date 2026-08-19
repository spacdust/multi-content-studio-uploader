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
  const res = await fetch('/api/caption/generate', {
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
