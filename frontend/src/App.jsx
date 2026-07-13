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
  getMe, listStocks, listSectors, listAnalysisCategories, listAnalysisPresets,
  listWatchlist, addWatchlist, removeWatchlist, getTodayBriefing,
  listSectorWatchlist, addSectorWatchlist, removeSectorWatchlist,
  refreshBriefing, getBriefingHistory, getMarketOverviewHistory, getSectorBriefingHistory,
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
  const [sectors, setSectors] = useState([]);
  const [categories, setCategories] = useState([]);
  const [presets, setPresets] = useState([]);
  const [watchItems, setWatchItems] = useState([]); // WatchlistRead[] (id, ticker, stock)
  const [sectorWatchItems, setSectorWatchItems] = useState([]); // SectorWatchlistRead[] (id, sector_id, sector)
  const [briefing, setBriefing] = useState(null); // TodayBriefingResponse
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState('');

  const loadAll = useCallback(() => {
    setDataLoading(true);
    setDataError('');
    Promise.all([
      listStocks(),
      listSectors(),
      listAnalysisCategories(),
      listAnalysisPresets(),
      listWatchlist(),
      listSectorWatchlist(),
      getTodayBriefing(),
    ])
      .then(([s, sec, c, p, w, sw, b]) => {
        setStocks(s);
        setSectors(sec);
        setCategories(c);
        setPresets(p);
        setWatchItems(w);
        setSectorWatchItems(sw);
        setBriefing(b);
      })
      .catch((err) => setDataError(err instanceof ApiError ? err.detail : '데이터를 불러오지 못했습니다.'))
      .finally(() => setDataLoading(false));
  }, []);

  useEffect(() => {
    if (user) loadAll();
  }, [user, loadAll]);

  const stocksByTicker = useMemo(() => Object.fromEntries(stocks.map((s) => [s.ticker, s])), [stocks]);
  const sectorsById = useMemo(() => Object.fromEntries(sectors.map((s) => [s.id, s])), [sectors]);
  const catLabel = useMemo(() => Object.fromEntries(categories.map((c) => [c.code, c.name_ko])), [categories]);
  const presetsByCode = useMemo(() => Object.fromEntries(presets.map((p) => [p.code, p])), [presets]);
  const catGroups = useMemo(() => ([
    { key: 'idx', label: '지수', items: categories.filter((c) => c.type === 'index').map((c) => [c.code, c.name_ko]) },
    { key: 'ind', label: '지표', items: categories.filter((c) => c.type === 'indicator').map((c) => [c.code, c.name_ko]) },
    { key: 'sec', label: '섹터 · 테마', items: categories.filter((c) => c.type === 'sector' || c.type === 'theme').map((c) => [c.code, c.name_ko]) },
  ]), [categories]);
  const watch = useMemo(() => watchItems.map((w) => w.ticker), [watchItems]);
  const sectorWatch = useMemo(() => sectorWatchItems.map((w) => w.sector_id), [sectorWatchItems]);
  const briefingByTicker = useMemo(
    () => Object.fromEntries((briefing?.stocks ?? []).map((b) => [b.ticker, b])),
    [briefing]
  );
  const missingTickers = useMemo(() => new Set(briefing?.missing_tickers ?? []), [briefing]);
  const sectorBriefingBySectorId = useMemo(
    () => Object.fromEntries((briefing?.sector_briefings ?? []).map((b) => [b.sector_id, b])),
    [briefing]
  );
  const missingSectorIds = useMemo(() => new Set(briefing?.missing_sectors ?? []), [briefing]);

  // ── 화면 상태 ──
  const [view, setView] = useState('briefing'); // briefing | briefing-detail | mypage | lens
  const [timeMode, setTimeMode] = useState('today'); // today | history
  const [briefingTab, setBriefingTab] = useState('mine');
  const [detail, setDetail] = useState(null);
  const [stockSearch, setStockSearch] = useState('');
  const [sectorSearch, setSectorSearch] = useState('');
  const [lensTicker, setLensTicker] = useState(null);
  const [lensByTicker, setLensByTicker] = useState({});
  const [lensSectorId, setLensSectorId] = useState(null);
  const [lensBySector, setLensBySector] = useState({});
  const [catSearchOpen, setCatSearchOpen] = useState({});
  const [catSearchQuery, setCatSearchQuery] = useState({});
  const [watchBusy, setWatchBusy] = useState(false);
  const [watchError, setWatchError] = useState('');
  const [sectorWatchBusy, setSectorWatchBusy] = useState(false);
  const [sectorWatchError, setSectorWatchError] = useState('');

  // ── 하루 1회 수동 새로고침 ──
  const [refreshBusy, setRefreshBusy] = useState(false);
  const [refreshError, setRefreshError] = useState('');

  // ── 이전 기록(오늘/이전 기록 탭) ──
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [overviewHistory, setOverviewHistory] = useState([]);
  const [overviewHistoryLoading, setOverviewHistoryLoading] = useState(false);
  const [overviewHistoryError, setOverviewHistoryError] = useState('');
  const [sectorHistory, setSectorHistory] = useState([]);
  const [sectorHistoryLoading, setSectorHistoryLoading] = useState(false);
  const [sectorHistoryError, setSectorHistoryError] = useState('');
  useEffect(() => {
    if (view !== 'briefing' || timeMode !== 'history') return;
    setHistoryLoading(true);
    setHistoryError('');
    getBriefingHistory()
      .then(setHistory)
      .catch((err) => setHistoryError(err instanceof ApiError ? err.detail : '이전 기록을 불러오지 못했습니다.'))
      .finally(() => setHistoryLoading(false));

    setOverviewHistoryLoading(true);
    setOverviewHistoryError('');
    getMarketOverviewHistory()
      .then(setOverviewHistory)
      .catch((err) => setOverviewHistoryError(err instanceof ApiError ? err.detail : '이전 기록을 불러오지 못했습니다.'))
      .finally(() => setOverviewHistoryLoading(false));

    setSectorHistoryLoading(true);
    setSectorHistoryError('');
    getSectorBriefingHistory()
      .then(setSectorHistory)
      .catch((err) => setSectorHistoryError(err instanceof ApiError ? err.detail : '이전 기록을 불러오지 못했습니다.'))
      .finally(() => setSectorHistoryLoading(false));
  }, [view, timeMode]);

  async function handleRefreshBriefing() {
    setRefreshError('');
    setRefreshBusy(true);
    try {
      const b = await refreshBriefing();
      setBriefing(b);
    } catch (err) {
      setRefreshError(err instanceof ApiError ? err.detail : '새로고침에 실패했습니다.');
    } finally {
      setRefreshBusy(false);
    }
  }

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
  function sectorCodeOfSector(sectorId) {
    const name = sectorsById[sectorId]?.name_ko;
    return name ? (SECTOR_NAME_TO_CODE[name] ?? null) : null;
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

  const getSectorLens = useCallback(
    (sid) => lensBySector[sid] || defaultLens(sectorCodeOfSector(sid)),
    [lensBySector, sectorsById, categories]
  );
  const updateSectorLensFor = useCallback((sectorId, updater) => {
    setLensBySector((prev) => {
      const cur = prev[sectorId] || defaultLens(sectorCodeOfSector(sectorId));
      return { ...prev, [sectorId]: updater(cur) };
    });
  }, [sectorsById, categories]);

  const openLens = useCallback((t) => {
    setLensTicker(t);
    setView('lens');
    setCatSearchOpen({});
    setCatSearchQuery({});
  }, []);
  const openSectorLens = useCallback((sid) => {
    setLensSectorId(sid);
    setView('sector-lens');
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

  // 관심종목과 동일한 패턴 — 섹터를 관심 등록하면 소속 종목 뉴스 수집 + 섹터 단위
  // LLM 브리핑 생성 대상이 된다(백엔드 app/services/sector_briefing_pipeline.py).
  async function handleAddSector(sectorId) {
    setSectorWatchError('');
    setSectorWatchBusy(true);
    try {
      const item = await addSectorWatchlist(sectorId);
      setSectorWatchItems((prev) => [...prev, item]);
      setSectorSearch('');
      openSectorLens(sectorId);
    } catch (err) {
      setSectorWatchError(err instanceof ApiError ? err.detail : '관심 섹터 추가에 실패했습니다.');
    } finally {
      setSectorWatchBusy(false);
    }
  }
  async function handleRemoveSector(sectorId) {
    setSectorWatchError('');
    try {
      await removeSectorWatchlist(sectorId);
      setSectorWatchItems((prev) => prev.filter((w) => w.sector_id !== sectorId));
    } catch (err) {
      setSectorWatchError(err instanceof ApiError ? err.detail : '삭제에 실패했습니다.');
    }
  }
  async function handleToggleSectorWatch(sectorId) {
    if (sectorWatch.includes(sectorId)) {
      await handleRemoveSector(sectorId);
    } else {
      await handleAddSector(sectorId);
    }
  }

  function handleLensReset() {
    if (view === 'sector-lens') {
      updateSectorLensFor(lensSectorId, (l) => ({ ...blankLens(), note: l.note }));
    } else {
      updateLensFor(lensTicker, (l) => ({ ...blankLens(), note: l.note }));
    }
  }
  function handleLensRecommend() {
    if (view === 'sector-lens') {
      updateSectorLensFor(lensSectorId, (l) => {
        const r = recFor(sectorCodeOfSector(lensSectorId)).primary;
        return { cats: new Set(r.cats), preset: r.preset, depth: 'standard', note: l.note, whyKey: 'primary' };
      });
    } else {
      updateLensFor(lensTicker, (l) => {
        const r = recFor(sectorCodeOf(lensTicker)).primary;
        return { cats: new Set(r.cats), preset: r.preset, depth: 'standard', note: l.note, whyKey: 'primary' };
      });
    }
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
          : detail.type === 'sector-briefing'
          ? sectorsById[detail.sectorId]?.name_ko ?? '섹터'
          : `${detail.ticker} · ${stocksByTicker[detail.ticker]?.name_ko ?? detail.ticker}`;
        return { crumb: '오늘의 브리핑 / 상세', title: label };
      }
      case 'mypage':
        return { crumb: '홈 / 마이페이지', title: '마이페이지' };
      case 'lens':
        return { crumb: '마이페이지 / 분석 렌즈', title: lensTicker ? `${lensTicker} 분석 렌즈` : '분석 렌즈' };
      case 'sector-lens':
        return {
          crumb: '오늘의 브리핑 / 분석 렌즈',
          title: lensSectorId ? `${sectorsById[lensSectorId]?.name_ko ?? ''} 분석 렌즈` : '분석 렌즈',
        };
      default:
        return { crumb: '', title: '' };
    }
  }
  const navActiveMap = {
    briefing: 'briefing', 'briefing-detail': 'briefing', mypage: 'mypage', lens: 'mypage', 'sector-lens': 'briefing',
  };

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
          {((view === 'lens' && lensTicker) || (view === 'sector-lens' && lensSectorId)) && (
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
                  timeMode={timeMode}
                  setTimeMode={setTimeMode}
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
                  onRefresh={handleRefreshBriefing}
                  refreshBusy={refreshBusy}
                  refreshError={refreshError}
                  history={history}
                  historyLoading={historyLoading}
                  historyError={historyError}
                  overviewHistory={overviewHistory}
                  overviewHistoryLoading={overviewHistoryLoading}
                  overviewHistoryError={overviewHistoryError}
                  sectors={sectors}
                  sectorWatch={sectorWatch}
                  sectorWatchBusy={sectorWatchBusy}
                  sectorWatchError={sectorWatchError}
                  sectorSearch={sectorSearch}
                  setSectorSearch={setSectorSearch}
                  onAddSector={handleAddSector}
                  sectorBriefingBySectorId={sectorBriefingBySectorId}
                  missingSectorIds={missingSectorIds}
                  sectorHistory={sectorHistory}
                  sectorHistoryLoading={sectorHistoryLoading}
                  sectorHistoryError={sectorHistoryError}
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
                  sectorsById={sectorsById}
                  sectorWatch={sectorWatch}
                  onOpenSectorLens={openSectorLens}
                  onToggleSectorWatch={handleToggleSectorWatch}
                  sectorBriefingBySectorId={sectorBriefingBySectorId}
                  missingSectorIds={missingSectorIds}
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

              {view === 'sector-lens' && (
                lensSectorId && sectorsById[lensSectorId] ? (
                  <LensPage
                    kind="sector"
                    backLabel="오늘의 브리핑으로"
                    ticker={sectorsById[lensSectorId].name_ko}
                    stock={sectorsById[lensSectorId]}
                    lens={getSectorLens(lensSectorId)}
                    updateLens={(fn) => updateSectorLensFor(lensSectorId, fn)}
                    onBack={() => setView('briefing')}
                    catGroups={catGroups}
                    catLabel={catLabel}
                    presets={presets}
                    presetsByCode={presetsByCode}
                    rec={recFor(sectorCodeOfSector(lensSectorId))}
                    catSearchOpen={catSearchOpen}
                    setCatSearchOpen={setCatSearchOpen}
                    catSearchQuery={catSearchQuery}
                    setCatSearchQuery={setCatSearchQuery}
                  />
                ) : (
                  <div className="maxw">
                    섹터를 먼저 선택하세요.{' '}
                    <span style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={() => setView('briefing')}>오늘의 브리핑으로 →</span>
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
