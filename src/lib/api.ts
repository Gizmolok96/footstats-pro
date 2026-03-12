const API_BASE_URL = 'https://api.sstats.net';
const API_KEY = 'gbi1ldi9446kastj';

export function getApiUrl(): string {
  return API_BASE_URL;
}

export async function apiFetch(path: string): Promise<Response> {
  const url = `${API_BASE_URL}${path}${path.includes('?') ? '&' : '?'}apikey=${API_KEY}`;
  return fetch(url, {
    headers: {
      'User-Agent': 'FootStats-Pro/1.0',
      Accept: 'application/json',
    },
  });
}
