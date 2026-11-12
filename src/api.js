// CRA proxies relative API and image URLs to Flask during development.
export async function api(path, options = {}) {
  const response = await fetch(path, { credentials: 'include', ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || 'Request failed');
  return data;
}
export function post(path, data) {
  return api(path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
}
