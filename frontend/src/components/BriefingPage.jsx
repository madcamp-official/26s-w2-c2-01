import { PERIODS, SENT_LABEL } from '../data.js';
import Icon from './Icon.jsx';

function StockCard({ stock, briefing, missing, onOpenDetail }) {
  const { ticker } = stock;
  const [lbl, cls] = briefing?.sentiment ? SENT_LABEL[briefing.sentiment] : [null, null];
  return (
    <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'stock', ticker })}>
      <div className="m">
        <div className="tk">
          <span className="sym">{ticker}</span>
          {lbl && <span className={`tag ${cls}`}>{lbl}</span>}
          <span className="sec">{stock.name_ko || stock.name_en} · {stock.sector?.name_ko ?? '섹터 미지정'}</span>
        </div>
        <div className="desc">
          {briefing?.summary ?? (missing ? '아직 브리핑이 생성되지 않았습니다.' : '')}
        </div>
      </div>
      {briefing && (
        <div className="chg">
          <div className="cnt">이슈 {(briefing.positive_factors?.length ?? 0) + (briefing.negative_factors?.length ?? 0)}건</div>
        </div>
      )}
    </div>
  );
}

export default function BriefingPage({
  period, setPeriod, briefingTab, setBriefingTab,
  stocks, watch, watchBusy, watchError, stockSearch, setStockSearch, onOpenDetail, onAddStock,
  briefingByTicker, missingTickers, marketOverview,
}) {
  const P = PERIODS[period];

  const watchSet = new Set(watch);
  const avail = stocks.filter((s) => !watchSet.has(s.ticker));
  const q = stockSearch.trim().toLowerCase();
  const filtered = q
    ? avail.filter((s) => s.ticker.toLowerCase().includes(q) || (s.name_ko || '').toLowerCase().includes(q) || s.name_en.toLowerCase().includes(q))
    : avail;

  const watchStocks = watch.map((t) => stocks.find((s) => s.ticker === t)).filter(Boolean);

  // "섹터" 탭은 전체 종목 카탈로그가 아니라 관심종목만 섹터별로 묶어 보여준다 —
  // 관심종목에 추가하는 순간 지연 분류가 되므로 자동으로 "관심 섹터" 목록이 된다.
  const sectorGroups = {};
  watchStocks.forEach((s) => {
    const name = s.sector?.name_ko ?? '섹터 미지정';
    (sectorGroups[name] ??= []).push(s);
  });

  return (
    <div className="maxw">
      <p className="hint2" style={{ fontSize: 13 }}>{P.since} 동안 안 본 사이 있었던 일만 간단히 정리했습니다.</p>

      <div className="ptabs">
        {Object.entries(PERIODS).map(([k, v]) => (
          <button key={k} className={period === k ? 'on' : ''} onClick={() => setPeriod(k)}>{v.label}</button>
        ))}
        <button style={{ flex: '0 0 auto', padding: '9px 16px' }} title="준비 중">직접 설정</button>
      </div>

      <div className="chips" style={{ marginBottom: 14 }}>
        {[['mine', '내 종목'], ['sector', '관심 섹터'], ['overview', '전체']].map(([k, l]) => (
          <span key={k} className={`chip ${briefingTab === k ? 'on' : ''}`} onClick={() => setBriefingTab(k)}>{l}</span>
        ))}
      </div>

      {briefingTab === 'overview' && (
        <div className="rows">
          <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'overview' })}>
            <div className="m">
              <div className="tk"><span className="sym">전체 시황</span><span className="tag neu">{P.label}</span></div>
              <div className="desc">{marketOverview?.summary ?? '아직 전체 시황 브리핑이 생성되지 않았습니다.'}</div>
            </div>
          </div>
        </div>
      )}

      {briefingTab === 'sector' && (
        <div className="rows">
          {!Object.keys(sectorGroups).length && (
            <div className="strip">관심종목을 추가하면 소속 섹터가 자동으로 여기 묶여서 나타납니다.</div>
          )}
          {Object.entries(sectorGroups).map(([name, list]) => (
            <div key={name} className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'sector', id: name })}>
              <div className="m">
                <div className="tk"><span className="sym">{name}</span></div>
                <div className="desc">{list.length}개 종목</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {briefingTab === 'mine' && (
        <>
          <div className="searchbox">
            <Icon size={16}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></Icon>
            <input
              type="text"
              placeholder="티커 또는 종목명으로 검색해서 추가"
              value={stockSearch}
              autoComplete="off"
              onChange={(e) => setStockSearch(e.target.value)}
              disabled={watchBusy}
            />
          </div>
          {watchError && <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)', marginTop: 8 }}>{watchError}</div>}
          <div className="searchresults">
            {!avail.length && <div className="hint2" style={{ padding: '8px 2px' }}>모든 종목을 이미 관심종목에 추가했습니다.</div>}
            {avail.length > 0 && !filtered.length && <div className="hint2" style={{ padding: '8px 2px' }}>검색 결과가 없습니다.</div>}
            {filtered.map((s) => (
              <div key={s.ticker} className="searchrow" onClick={() => !watchBusy && onAddStock(s.ticker)}>
                <div className="sm"><span className="sym">{s.ticker}</span><span className="sec">{s.name_ko || s.name_en} · {s.sector?.name_ko ?? '섹터 미지정'}</span></div>
                <span className="addbtn"><Icon size={14}><path d="M12 5v14M5 12h14" /></Icon></span>
              </div>
            ))}
          </div>

          {watchStocks.length ? (
            <div className="rows" style={{ marginTop: 16 }}>
              {watchStocks.map((s) => (
                <StockCard
                  key={s.ticker}
                  stock={s}
                  briefing={briefingByTicker[s.ticker]}
                  missing={missingTickers.has(s.ticker)}
                  onOpenDetail={onOpenDetail}
                />
              ))}
            </div>
          ) : (
            <div className="strip" style={{ marginTop: 14 }}>검색해서 관심종목을 추가하면 여기 브리핑이 생성됩니다.</div>
          )}
        </>
      )}
    </div>
  );
}
