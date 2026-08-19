// Settings & LLM Endpoint API endpoints

export async function fetchSettingsApi() {
  const res = await fetch('/api/settings');
  return await res.json();
}

export async function saveSettingsApi(payload) {
  const res = await fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return await res.json();
}

export async function testLlmApi(payload) {
  const res = await fetch('/api/settings/test-llm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return await res.json();
}
