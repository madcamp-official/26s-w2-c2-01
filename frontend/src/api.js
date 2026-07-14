// 백엔드 API 클라이언트. 인증 토큰은 localStorage에 저장하고 매 요청에 Authorization 헤더로 실어 보낸다.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const TOKEN_KEY = 'trade_chaser_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

// FastAPI 422(RequestValidationError)의 detail은 문자열이 아니라
// [{loc, msg, type}, ...] 배열로 온다. 그대로 React에 렌더링하면
// "Objects are not valid as a React child"로 깨지므로 사람이 읽을 문자열로 정규화한다.
function normalizeDetail(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        if (typeof e === 'string') return e;
        const field = Array.isArray(e?.loc) ? e.loc[e.loc.length - 1] : null;
        return field ? `${field}: ${e.msg}` : e.msg;
      })
      .filter(Boolean)
      .join(' / ') || '요청이 올바르지 않습니다.';
  }
  if (detail && typeof detail === 'object') return detail.msg || JSON.stringify(detail);
  return '알 수 없는 오류가 발생했습니다.';
}

export class ApiError extends Error {
  constructor(status, detail) {
    const message = normalizeDetail(detail);
    super(message);
    this.status = status;
    this.detail = message;
  }
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

  const isJson = (res.headers.get('content-type') || '').includes('application/json');
  const data = isJson ? await res.json().catch(() => null) : null;

  if (!res.ok) {
    throw new ApiError(res.status, data?.detail ?? `요청이 실패했습니다 (${res.status})`);
  }
  return data;
}

// ── 인증 ──
export const register = (email, password, nickname) =>
  request('/auth/register', { method: 'POST', body: { email, password, nickname }, auth: false });

export const login = (email, password) =>
  request('/auth/login', { method: 'POST', body: { email, password }, auth: false });

// ── 사용자 ──
export const getMe = () => request('/users/me');
export const updateMe = (data) => request('/users/me', { method: 'PATCH', body: data });

// ── 종목 ──
export const listStocks = (search = '') => {
  const query = search.trim() ? `?search=${encodeURIComponent(search.trim())}&limit=20` : '?limit=20';
  return request(`/stocks${query}`, { auth: false });
};
export const listSectors = () => request('/sectors', { auth: false });
export const getTodayVolatility = () => request('/stocks/volatility/today', { auth: false });

// ── 관심종목 ──
export const listWatchlist = () => request('/watchlist');
export const addWatchlist = (ticker) => request('/watchlist', { method: 'POST', body: { ticker } });
export const removeWatchlist = (ticker) => request(`/watchlist/${ticker}`, { method: 'DELETE' });
export const watchlistRanking = (limit = 10) => request(`/watchlist/ranking/top?limit=${limit}`, { auth: false });

// ── 관심 섹터 ──
export const listSectorWatchlist = () => request('/sector-watchlist');
export const addSectorWatchlist = (sectorId) =>
  request('/sector-watchlist', { method: 'POST', body: { sector_id: sectorId } });
export const removeSectorWatchlist = (sectorId) => request(`/sector-watchlist/${sectorId}`, { method: 'DELETE' });

// ── 분석 카테고리 / 성향 프리셋 ──
export const listAnalysisCategories = () => request('/analysis-categories', { auth: false });
export const listAnalysisPresets = () => request('/analysis-presets', { auth: false });

// ── 오늘의 브리핑 ──
export const getTodayBriefing = () => request('/briefings/today');
export const refreshBriefing = () => request('/briefings/refresh', { method: 'POST' });
export const getBriefingHistory = () => request('/briefings/history');
export const getMarketOverviewHistory = () => request('/briefings/history/overview');
export const getSectorBriefingHistory = () => request('/briefings/history/sectors');
