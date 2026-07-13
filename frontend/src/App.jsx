import { useState, useEffect, useCallback, useMemo } from 'react';
import Sidebar from './components/Sidebar.jsx';
import TopBar from './components/TopBar.jsx';
import LensTopActions from './components/LensTopActions.jsx';
import AuthPage from './components/AuthPage.jsx';
import BriefingPage from './components/BriefingPage.jsx';
import BriefingDetailPage from './components/BriefingDetailPage.jsx';
import MyPage from './components/MyPage.jsx';
import LensPage from './components/LensPage.jsx';
import { defaultLens, blankLens, recFor } from './data.js';
import {
  getToken, setToken, ApiError,
  getMe, listStocks, listAnalysisCategories, listAnalysisPresets,
  listWatchlist, addWatchlist, removeWatchlist, getTodayBriefing,
} from './api.js';

export default function App() {
  // ── 인증 ──
  const [authChecked, setAuthChecked] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = getToken();
    if (!token) { setAuthChecked(true); return; }
    getMe()
      .then((u) => setUser(u))
      .catch(() => setToken(null))
      .finally(() => setAuthChecked(true));
  }, []);

  function handleAuthed(data) {
    setToken(data.access_token);
    setUser(data.user);
  }
  function handleLogout() {
    setToken(null);
    setUser(null);
  }

  // ── 서버 데이터 ──
  const [stocks, setStocks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [presets, setPresets] = useState([]);
  const [watchItems, setWatchItems] = useState([]); // WatchlistRead[] (id, ticker, stock)
  const [briefing, setBriefing] = useState(null); // TodayBriefingResponse
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState('');

  const loadAll = useCallback(() => {
    setDataLoading(true);
    setDataError('');
    Promise.all([
      listStocks(),
      listAnalysisCategories(),
      listAnalysisPresets(),
      listWatchlist(),
      getTodayBriefing(),
    ])
      .then(([s, c, p, w, b]) => {
        setStocks(s);
        setCategories(c);
        setPresets(p);
        setWatchItems(w);
        setBriefing(b);
      })
      .catch((err) => setDataError(err instanceof ApiError ? err.detail : '데이터를 불러오지 못했습니다.'))
      .finally(() => setDataLoading(false));
  }, []);

  useEffect(() => {
    if (user) loadAll();
  }, [user, loadAll]);

  const stocksByTicker = useMemo(() => Object.fromEntries(stocks.map((s) => [s.ticker, s])), [stocks]);
  const catLabel = useMemo(() => Object.fromEntries(categories.map((c) => [c.code, c.name_ko])), [categories]);
  const presetsByCode = useMemo(() => Object.fromEntries(presets.map((p) => [p.code, p])), [presets]);
  const catGroups = useMemo(() => ([
    { key: 'idx', label: '지수', items: categories.filter((c) => c.type === 'index').map((c) => [c.code, c.name_ko]) },
    { key: 'ind', label: '지표', items: categories.filter((c) => c.type === 'indicator').map((c) => [c.code, c.name_ko]) },
    { key: 'sec', label: '섹터 · 테마', items: categories.filter((c) => c.type === 'sector' || c.type === 'theme').map((c) => [c.code, c.name_ko]) },
  ]), [categories]);
  const watch = useMemo(() => watchItems.map((w) => w.ticker), [watchItems]);
  const briefingByTicker = useMemo(
    () => Object.fromEntries((briefing?.stocks ?? []).map((b) => [b.ticker, b])),
    [briefing]
  );
  const missingTickers = useMemo(() => new Set(briefing?.missing_tickers ?? []), [briefing]);

  // ── 화면 상태 ──
  const [view, setView] = useState('briefing'); // briefing | briefing-detail | mypage | lens
  const [period, setPeriod] = useState('3d');
  const [briefingTab, setBriefingTab] = useState('mine');
  const [detail, setDetail] = useState(null);
  const [stockSearch, setStockSearch] = useState('');
  const [lensTicker, setLensTicker] = useState(null);
  const [lensByTicker, setLensByTicker] = useState({});
  const [catSearchOpen, setCatSearchOpen] = useState({});
  const [catSearchQuery, setCatSearchQuery] = useState({});
  const [watchBusy, setWatchBusy] = useState(false);
  const [watchError, setWatchError] = useState('');

  // ── 테마 ──
  const [theme, setTheme] = useState(null);
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
  );
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => setSystemDark(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);
  useEffect(() => {
    if (theme) document.documentElement.setAttribute('data-theme', theme);
    else document.documentElement.removeAttribute('data-theme');
  }, [theme]);
  const effectiveTheme = theme || (systemDark ? 'dark' : 'light');
  const toggleTheme = () => setTheme(effectiveTheme === 'dark' ? 'light' : 'dark');

  // ── 렌즈 헬퍼 (로컬 전용 — 백엔드에 저장 API 없음) ──
  // sectors 테이블(종목 소속 섹터)과 analysis_categories의 sector 타입은 별개로 시딩되어
  // name_ko 표기가 정확히 일치하지 않는다(예: "반도체·AI" vs "반도체·AI 하드웨어").
  // REC_LENS 매핑용으로 섹터명 -> 카테고리 code를 명시적으로 연결한다.
  const SECTOR_NAME_TO_CODE = {
    '반도체·AI': 'SEMI',
    '테크·소프트웨어': 'TECH',
    '미디어·인터넷': 'MEDIA',
    '소비재·유통': 'CONSUMER',
    '자동차': 'AUTO',
    '금융': 'FIN',
    '헬스케어': 'HEALTH',
    '에너지': 'ENERGY',
    '산업재': 'INDUST',
    '통신': 'TELECOM',
    '부동산': 'REALESTATE',
    '소재': 'MATERIALS',
    '유틸리티': 'UTIL',
  };
  function sectorCodeOf(ticker) {
    const s = stocksByTicker[ticker]?.sector;
    return s ? (SECTOR_NAME_TO_CODE[s.name_ko] ?? null) : null;
  }
  const getLens = useCallback(
    (t) => lensByTicker[t] || defaultLens(sectorCodeOf(t)),
    [lensByTicker, stocksByTicker, categories]
  );
  const updateLensFor = useCallback((ticker, updater) => {
    setLensByTicker((prev) => {
      const cur = prev[ticker] || defaultLens(sectorCodeOf(ticker));
      return { ...prev, [ticker]: updater(cur) };
    });
  }, [stocksByTicker, categories]);

  const openLens = useCallback((t) => {
    setLensTicker(t);
    setView('lens');
    setCatSearchOpen({});
    setCatSearchQuery({});
  }, []);
  const openDetail = useCallback((d) => {
    setDetail(d);
    setView('briefing-detail');
  }, []);

  async function handleAddStock(ticker) {
    setWatchError('');
    setWatchBusy(true);
    try {
      const item = await addWatchlist(ticker);
      setWatchItems((prev) => [...prev, item]);
      // 관심종목 추가 시점에 백엔드가 섹터를 지연 분류하므로(classify_and_save),
      // 응답에 담긴 최신 stock(섹터 포함)으로 stocks 목록도 갱신해야
      // 방금 연 렌즈 화면이 "섹터 미지정" 같은 오래된 값을 보지 않는다.
      if (item.stock) {
        setStocks((prev) => prev.map((s) => (s.ticker === item.stock.ticker ? item.stock : s)));
      }
      setStockSearch('');
      openLens(ticker);
    } catch (err) {
      setWatchError(err instanceof ApiError ? err.detail : '관심종목 추가에 실패했습니다.');
    } finally {
      setWatchBusy(false);
    }
  }
  async function handleRemoveWatch(ticker) {
    setWatchError('');
    try {
      await removeWatchlist(ticker);
      setWatchItems((prev) => prev.filter((w) => w.ticker !== ticker));
    } catch (err) {
      setWatchError(err instanceof ApiError ? err.detail : '삭제에 실패했습니다.');
    }
  }
  async function handleToggleWatch(ticker) {
    if (watch.includes(ticker)) {
      await handleRemoveWatch(ticker);
    } else {
      await handleAddStock(ticker);
    }
  }

  function handleLensReset() {
    updateLensFor(lensTicker, (l) => ({ ...blankLens(), note: l.note }));
  }
  function handleLensRecommend() {
    updateLensFor(lensTicker, (l) => {
      const r = recFor(sectorCodeOf(lensTicker)).primary;
      return { cats: new Set(r.cats), preset: r.preset, depth: 'standard', note: l.note, whyKey: 'primary' };
    });
  }

  function handleUserUpdated(updated) {
    setUser(updated);
  }

  // ── 헤더 정보 ──
  function headerInfo() {
    switch (view) {
      case 'briefing':
        return { crumb: '홈 / 오늘의 브리핑', title: '오늘의 브리핑' };
      case 'briefing-detail': {
        const label = !detail
          ? '상세'
          : detail.type === 'overview'
          ? '전체 시황'
          : detail.type === 'sector'
          ? detail.id
          : `${detail.ticker} · ${stocksByTicker[detail.ticker]?.name_ko ?? detail.ticker}`;
        return { crumb: '오늘의 브리핑 / 상세', title: label };
      }
      case 'mypage':
        return { crumb: '홈 / 마이페이지', title: '마이페이지' };
      case 'lens':
        return { crumb: '마이페이지 / 분석 렌즈', title: lensTicker ? `${lensTicker} 분석 렌즈` : '분석 렌즈' };
      default:
        return { crumb: '', title: '' };
    }
  }
  const navActiveMap = { briefing: 'briefing', 'briefing-detail': 'briefing', mypage: 'mypage', lens: 'mypage' };

  if (!authChecked) return null;
  if (!user) return <AuthPage onAuthed={handleAuthed} />;

  const h = headerInfo();
  const lensStock = lensTicker ? stocksByTicker[lensTicker] : null;

  return (
    <div className="layout">
      <Sidebar
        active={navActiveMap[view]}
        onNav={setView}
        theme={effectiveTheme}
        onToggleTheme={toggleTheme}
        nickname={user.nickname}
        email={user.email}
        onLogout={handleLogout}
      />

      <div className="main">
        <TopBar crumb={h.crumb} title={h.title}>
          {view === 'lens' && lensTicker && (
            <LensTopActions onReset={handleLensReset} onRecommend={handleLensRecommend} />
          )}
        </TopBar>

        <div id="view">
          {dataLoading && !stocks.length ? (
            <div className="maxw"><div className="strip">불러오는 중…</div></div>
          ) : dataError ? (
            <div className="maxw">
              <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)' }}>{dataError}</div>
              <button className="btn" onClick={loadAll}>다시 시도</button>
            </div>
          ) : (
            <>
              {view === 'briefing' && (
                <BriefingPage
                  period={period}
                  setPeriod={setPeriod}
                  briefingTab={briefingTab}
                  setBriefingTab={setBriefingTab}
                  stocks={stocks}
                  watch={watch}
                  watchBusy={watchBusy}
                  watchError={watchError}
                  stockSearch={stockSearch}
                  setStockSearch={setStockSearch}
                  onOpenDetail={openDetail}
                  onAddStock={handleAddStock}
                  briefingByTicker={briefingByTicker}
                  missingTickers={missingTickers}
                  marketOverview={briefing?.market_overview ?? null}
                />
              )}

              {view === 'briefing-detail' && (
                <BriefingDetailPage
                  detail={detail}
                  stocks={stocks}
                  watch={watch}
                  onBack={() => setView('briefing')}
                  onOpenDetail={openDetail}
                  onOpenLens={openLens}
                  onToggleWatch={handleToggleWatch}
                  briefingByTicker={briefingByTicker}
                  missingTickers={missingTickers}
                  marketOverview={briefing?.market_overview ?? null}
                />
              )}

              {view === 'mypage' && (
                <MyPage
                  user={user}
                  onUserUpdated={handleUserUpdated}
                  watch={watch}
                  stocksByTicker={stocksByTicker}
                  getLens={getLens}
                  presetsByCode={presetsByCode}
                  onRemove={handleRemoveWatch}
                  onOpenLens={openLens}
                  onNav={setView}
                />
              )}

              {view === 'lens' && (
                lensTicker && lensStock ? (
                  <LensPage
                    ticker={lensTicker}
                    stock={lensStock}
                    lens={getLens(lensTicker)}
                    updateLens={(fn) => updateLensFor(lensTicker, fn)}
                    onBack={() => setView('mypage')}
                    catGroups={catGroups}
                    catLabel={catLabel}
                    presets={presets}
                    presetsByCode={presetsByCode}
                    rec={recFor(sectorCodeOf(lensTicker))}
                    catSearchOpen={catSearchOpen}
                    setCatSearchOpen={setCatSearchOpen}
                    catSearchQuery={catSearchQuery}
                    setCatSearchQuery={setCatSearchQuery}
                  />
                ) : (
                  <div className="maxw">
                    종목을 먼저 선택하세요.{' '}
                    <span style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => setView('mypage')}>마이페이지로 →</span>
                  </div>
                )
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
