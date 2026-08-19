// Account & Authentication API endpoints

export async function fetchAccountsApi() {
  const res = await fetch('/api/accounts');
  return await res.json();
}

export async function createAccountApi(name) {
  const res = await fetch('/api/accounts/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  return await res.json();
}

export async function triggerLoginApi(account, platform, timeout = 300) {
  const res = await fetch('/api/accounts/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account, platform, timeout }),
  });
  return await res.json();
}

export async function openTikTokStudioApi(account) {
  const res = await fetch('/api/accounts/open-tiktok-studio', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account }),
  });
  return await res.json();
}

export async function openInstagramApi(account) {
  const res = await fetch('/api/accounts/open-instagram', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account }),
  });
  return await res.json();
}

export async function openFacebookApi(account) {
  const res = await fetch('/api/accounts/open-facebook', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account }),
  });
  return await res.json();
}

export async function loginInstagramMobileApi(account, username, password, verification_code = null) {
  const res = await fetch('/api/accounts/login-instagram-mobile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      account,
      username,
      password,
      verification_code: verification_code || null,
    }),
  });
  return await res.json();
}

