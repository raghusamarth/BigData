/** Central API client. Uses VITE_API_URL in docker, /api proxy in dev. */
const BASE = import.meta.env.VITE_API_URL || '/api';

async function get(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ''}`);
  if (!res.ok) throw new Error(`API ${res.status} on ${path}`);
  return res.json();
}

async function del(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ''}`, { method: 'DELETE' });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || `API ${res.status} on ${path}`);
  }
  return res.json();
}
async function post(path, params = {}, body = null) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ''}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : null,
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || `API ${res.status} on ${path}`);
  }
  return res.json();
}

export const api = {
  health: () => get('/'),
  volatility: (limit = 10) => get('/analytics/volatility', { limit }),
  sectors: () => get('/analytics/sectors'),
  topGainers: (start, end, limit = 10) => get('/analytics/top-gainers', { start, end, limit }),
  monthly: (symbol, limit = 24) => get(`/analytics/monthly/${symbol}`, { limit }),
  spikes: (symbol) => get(`/analytics/volume-spikes/${symbol}`),
  correlation: () => get('/analytics/correlation'),
  anomalies: (limit = 50) => get('/analytics/anomalies', { limit }),
  history: (symbol, limit = 500) => get(`/stocks/${symbol}/history`, { limit }),
  stats: () => get('/pipeline/stats'),
  register: (u, p) => post('/auth/register', { username: u, password: p }),
  login: (u, p) => post('/auth/login', { username: u, password: p }),
  portfolio: (uid) => get(`/auth/portfolio/${uid}`),
  buy: (uid, sym, qty) => post('/trade/buy', {}, { user_id: uid, stock_symbol: sym, quantity: qty }),
  sell: (uid, sym, qty) => post('/trade/sell', {}, { user_id: uid, stock_symbol: sym, quantity: qty }),
  mgmtUsers: () => get('/admin/users'),
  mgmtDeleteUser: (uid) => del(`/admin/users/${uid}`),
  mgmtStocks: () => get('/admin/stocks'),
  mgmtAddStock: (symbol, sector, exchange) => post('/admin/stocks', {}, { symbol, sector, exchange }),
  mgmtDeleteStock: (symbol, purge = true) => del(`/admin/stocks/${symbol}`, { purge }),
  mgmtAddBar: (bar) => post('/admin/bars', {}, bar),
  mgmtSchema: (collection, sample = 200) => get('/admin/schema', { collection, sample }),
  mgmtAddField: (collection, name, dtype, defVal, backfill) => post('/admin/fields', { collection, name, dtype, default: defVal, backfill }),
  mgmtDropField: (collection, name) => del('/admin/fields', { collection, name }),
};
