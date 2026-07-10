import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar.jsx';
import TopBar from './components/TopBar.jsx';
import LensTopActions from './components/LensTopActions.jsx';
import BriefingPage from './components/BriefingPage.jsx';
import BriefingDetailPage from './components/BriefingDetailPage.jsx';
import MyPage from './components/MyPage.jsx';
import LensPage from './components/LensPage.jsx';
import { STOCKS, defaultLens, blankLens, recFor } from './data.js';

export default function App() {
  // ── 화면 상태 ──
  const [view, setView] = useState('briefing'); // briefing | briefing-detail | mypage | lens
  const [period, setPeriod] = useState('3d');
  const [briefingTab, setBriefingTab] = useState('mine'); // mine | sector | overview
  const [detail, setDetail] = useState(null); // {type:'overview'} | {type:'sector',id} | {type:'stock',ticker}
  const [watch, setWatch] = useState(['NVDA', 'TSLA', 'AAPL']);
  const [stockSearch, setStockSearch] = useState('');
  const [lensTicker, setLensTicker] = useState(null);
  const [lensByTicker, setLensByTicker] = useState({});
  const [catSearchOpen, setCatSearchOpen] = useState({});
  const [catSearchQuery, setCatSearchQuery] = useState({});
  const [profile, setProfile] = useState({ nickname: '원건희', email: 'gunhui@kaist.ac.kr', investorType: 'balanced' });

  // ── 테마 (명시 토글 우선, 없으면 시스템 설정) ──
  const [theme, setTheme] = useState(null); // null | 'light' | 'dark'
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

  // ── 렌즈 헬퍼 ──
  const getLens = useCallback((t) => lensByTicker[t] || defaultLens(t), [lensByTicker]);

  const updateLensFor = useCallback((ticker, updater) => {
    setLensByTicker((prev) => {
      const cur = prev[ticker] || defaultLens(ticker);
      return { ...prev, [ticker]: updater(cur) };
    });
  }, []);

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

  // 검색해서 추가하면 바로 그 종목의 분석렌즈로 이동
  const handleAddStock = useCallback((t) => {
    setWatch((prev) => (prev.includes(t) ? prev : [...prev, t]));
    setStockSearch('');
    openLens(t);
  }, [openLens]);

  const removeFromWatch = useCallback((t) => {
    setWatch((prev) => prev.filter((x) => x !== t));
  }, []);

  // 종목 상세의 "관심종목에 추가/제거" 토글 — 추가일 때만 렌즈로 이동
  function handleToggleWatch(t) {
    const wasWatching = watch.includes(t);
    if (wasWatching) {
      removeFromWatch(t);
    } else {
      setWatch((prev) => [...prev, t]);
      openLens(t);
    }
  }

  function handleLensReset() {
    updateLensFor(lensTicker, (l) => ({ ...blankLens(), note: l.note }));
  }
  function handleLensRecommend() {
    updateLensFor(lensTicker, (l) => {
      const r = recFor(lensTicker).primary;
      return { cats: new Set(r.cats), preset: r.preset, depth: 'standard', note: l.note, whyKey: 'primary' };
    });
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
          : `${detail.ticker} · ${STOCKS[detail.ticker].name}`;
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
  const h = headerInfo();

  return (
    <div className="layout">
      <Sidebar
        active={navActiveMap[view]}
        onNav={setView}
        theme={effectiveTheme}
        onToggleTheme={toggleTheme}
        nickname={profile.nickname}
        email={profile.email}
      />

      <div className="main">
        <TopBar crumb={h.crumb} title={h.title}>
          {view === 'lens' && lensTicker && (
            <LensTopActions onReset={handleLensReset} onRecommend={handleLensRecommend} />
          )}
        </TopBar>

        <div id="view">
          {view === 'briefing' && (
            <BriefingPage
              period={period}
              setPeriod={setPeriod}
              briefingTab={briefingTab}
              setBriefingTab={setBriefingTab}
              watch={watch}
              stockSearch={stockSearch}
              setStockSearch={setStockSearch}
              onOpenDetail={openDetail}
              onAddStock={handleAddStock}
            />
          )}

          {view === 'briefing-detail' && (
            <BriefingDetailPage
              detail={detail}
              watch={watch}
              onBack={() => setView('briefing')}
              onOpenDetail={openDetail}
              onOpenLens={openLens}
              onToggleWatch={handleToggleWatch}
            />
          )}

          {view === 'mypage' && (
            <MyPage
              profile={profile}
              setProfile={setProfile}
              watch={watch}
              getLens={getLens}
              onRemove={removeFromWatch}
              onOpenLens={openLens}
              onNav={setView}
            />
          )}

          {view === 'lens' && (
            lensTicker ? (
              <LensPage
                ticker={lensTicker}
                stock={STOCKS[lensTicker]}
                lens={getLens(lensTicker)}
                updateLens={(fn) => updateLensFor(lensTicker, fn)}
                onBack={() => setView('mypage')}
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
        </div>
      </div>
    </div>
  );
}
