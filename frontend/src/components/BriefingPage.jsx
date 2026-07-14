import { useDeferredValue, useMemo } from 'react';
import { SENT_LABEL } from '../data.js';
import Icon from './Icon.jsx';

function HistoryRow({ row, stocksByTicker, onOpenDetail }) {
  const stock = stocksByTicker[row.ticker];
  const [lbl, cls] = row.sentiment ? SENT_LABEL[row.sentiment] : [null, null];
  return (
    <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'stock', ticker: row.ticker })}>
      <div className="m">
        <div className="tk">
          <span className="sym">{row.briefing_date}</span>
          <span className="sym">{row.ticker}</span>
          {lbl && <span className={`tag ${cls}`}>{lbl}</span>}
          <span className="sec">{stock?.name_ko || stock?.name_en || row.ticker}</span>
        </div>
        <div className="desc">{row.summary ?? ''}</div>
      </div>
    </div>
  );
}

function OverviewHistoryRow({ row, onOpenDetail }) {
  return (
    <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'overview' })}>
      <div className="m">
        <div className="tk"><span className="sym">{row.briefing_date}</span><span className="sym">전체 시황</span></div>
        <div className="desc">{row.summary ?? ''}</div>
      </div>
    </div>
  );
}

function SectorHistoryRow({ row, sectorsById, onOpenDetail }) {
  const sector = sectorsById[row.sector_id];
  const [lbl, cls] = row.sentiment ? SENT_LABEL[row.sentiment] : [null, null];
  return (
    <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'sector-briefing', sectorId: row.sector_id })}>
      <div className="m">
        <div className="tk">
          <span className="sym">{row.briefing_date}</span>
          {lbl && <span className={`tag ${cls}`}>{lbl}</span>}
          <span className="sec">{sector?.name_ko ?? `섹터 #${row.sector_id}`}</span>
        </div>
        <div className="desc">{row.summary ?? ''}</div>
      </div>
    </div>
  );
}

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

function SectorCard({ sector, briefing, missing, onOpenDetail }) {
  const [lbl, cls] = briefing?.sentiment ? SENT_LABEL[briefing.sentiment] : [null, null];
  return (
    <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'sector-briefing', sectorId: sector.id })}>
      <div className="m">
        <div className="tk">
          <span className="sym">{sector.name_ko}</span>
          {lbl && <span className={`tag ${cls}`}>{lbl}</span>}
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
  timeMode, setTimeMode, briefingTab, setBriefingTab,
  stocks, popularStocks, stockSearchResults, stockSearchLoading,
  watch, watchBusy, watchError, stockSearch, setStockSearch, onOpenDetail, onAddStock,
  briefingByTicker, missingTickers, marketOverview,
  onRefresh, refreshBusy, refreshError,
  history, historyLoading, historyError,
  overviewHistory, overviewHistoryLoading, overviewHistoryError,
  sectors, sectorWatch, sectorWatchBusy, sectorWatchError, sectorSearch, setSectorSearch, onAddSector,
  sectorBriefingBySectorId, missingSectorIds,
  sectorHistory, sectorHistoryLoading, sectorHistoryError,
}) {
  const deferredStockSearch = useDeferredValue(stockSearch);
  const deferredSectorSearch = useDeferredValue(sectorSearch);

  const stocksByTicker = useMemo(() => Object.fromEntries(stocks.map((s) => [s.ticker, s])), [stocks]);
  const sectorsById = useMemo(() => Object.fromEntries(sectors.map((s) => [s.id, s])), [sectors]);

  const avail = useMemo(() => {
    const watchSet = new Set(watch);
    const source = deferredStockSearch.trim() ? stockSearchResults : popularStocks;
    return source.filter((s) => !watchSet.has(s.ticker));
  }, [popularStocks, stockSearchResults, watch, deferredStockSearch]);

  const filtered = avail;

  const watchStocks = useMemo(
    () => watch.map((t) => stocksByTicker[t]).filter(Boolean),
    [watch, stocksByTicker]
  );

  const availSectors = useMemo(() => {
    const sectorWatchSet = new Set(sectorWatch);
    return sectors.filter((s) => !sectorWatchSet.has(s.id));
  }, [sectors, sectorWatch]);

  const filteredSectors = useMemo(() => {
    const sq = deferredSectorSearch.trim().toLowerCase();
    return sq
      ? availSectors.filter((s) => s.name_ko.toLowerCase().includes(sq) || s.name_en.toLowerCase().includes(sq))
      : availSectors;
  }, [availSectors, deferredSectorSearch]);

  const watchSectors = useMemo(
    () => sectorWatch.map((id) => sectorsById[id]).filter(Boolean),
    [sectorWatch, sectorsById]
  );

  return (
    <div className="maxw">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 4 }}>
        <p className="hint2" style={{ fontSize: 13, margin: 0 }}>안 본 사이 있었던 일만 간단히 정리했습니다. 장시작·장중·장마감·휴장 중 하루 4번 자동으로 갱신됩니다.</p>
        <button className="btn" style={{ flex: '0 0 auto' }} disabled={refreshBusy} onClick={onRefresh}>
          <Icon size={14}><path d="M4 4v6h6M20 20v-6h-6" /><path d="M20 8a8 8 0 0 0-14.9-3M4 16a8 8 0 0 0 14.9 3" /></Icon> {refreshBusy ? '새로고침 중…' : '새로고침 (하루 1회)'}
        </button>
      </div>
      {refreshError && <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)', marginBottom: 10 }}>{refreshError}</div>}

      <div className="ptabs">
        <button className={timeMode === 'today' ? 'on' : ''} onClick={() => setTimeMode('today')}>오늘</button>
        <button
          className={timeMode === 'history' ? 'on' : ''}
          onClick={() => { setTimeMode('history'); if (briefingTab === 'search') setBriefingTab('mine'); }}
        >이전 기록</button>
      </div>

      <div className="chips" style={{ marginBottom: 14 }}>
        {[['mine', '관심 종목'], ['sector', '관심 섹터'], ['overview', '전체']].map(([k, l]) => (
          <span key={k} className={`chip ${briefingTab === k ? 'on' : ''}`} onClick={() => setBriefingTab(k)}>{l}</span>
        ))}
        <span
          className={`chip ${briefingTab === 'search' ? 'on' : ''}`}
          style={{ marginLeft: 'auto' }}
          onClick={() => { setTimeMode('today'); setBriefingTab('search'); }}
        >검색</span>
      </div>

      {timeMode === 'today' && briefingTab === 'overview' && (
        <div className="rows">
          <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'overview' })}>
            <div className="m">
              <div className="tk"><span className="sym">전체 시황</span></div>
              <div className="desc">{marketOverview?.summary ?? '아직 전체 시황 브리핑이 생성되지 않았습니다.'}</div>
            </div>
          </div>
        </div>
      )}

      {timeMode === 'today' && briefingTab === 'sector' && (
        <>
          <div className="searchbox">
            <Icon size={16}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></Icon>
            <input
              type="text"
              placeholder="섹터명으로 검색해서 추가"
              value={sectorSearch}
              autoComplete="off"
              onChange={(e) => setSectorSearch(e.target.value)}
              disabled={sectorWatchBusy}
            />
          </div>
          {sectorWatchError && <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)', marginTop: 8 }}>{sectorWatchError}</div>}
          <div className="searchresults">
            {!availSectors.length && <div className="hint2" style={{ padding: '8px 2px' }}>모든 섹터를 이미 관심 섹터에 추가했습니다.</div>}
            {availSectors.length > 0 && !filteredSectors.length && <div className="hint2" style={{ padding: '8px 2px' }}>검색 결과가 없습니다.</div>}
            {filteredSectors.map((s) => (
              <div key={s.id} className="searchrow" onClick={() => !sectorWatchBusy && onAddSector(s.id)}>
                <div className="sm"><span className="sym">{s.name_ko}</span></div>
                <span className="addbtn"><Icon size={14}><path d="M12 5v14M5 12h14" /></Icon></span>
              </div>
            ))}
          </div>

          {watchSectors.length ? (
            <div className="rows" style={{ marginTop: 16 }}>
              {watchSectors.map((s) => (
                <SectorCard
                  key={s.id}
                  sector={s}
                  briefing={sectorBriefingBySectorId[s.id]}
                  missing={missingSectorIds.has(s.id)}
                  onOpenDetail={onOpenDetail}
                />
              ))}
            </div>
          ) : (
            <div className="strip" style={{ marginTop: 14 }}>검색해서 관심 섹터를 추가하면 여기 섹터 브리핑이 생성됩니다.</div>
          )}
        </>
      )}

      {timeMode === 'today' && briefingTab === 'search' && (
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
            {!deferredStockSearch.trim() && <div className="hint2" style={{ padding: '8px 2px' }}>오늘 거래량이 많은 인기 종목 20개입니다.</div>}
            {stockSearchLoading && <div className="hint2" style={{ padding: '8px 2px' }}>검색 중…</div>}
            {!stockSearchLoading && deferredStockSearch.trim() && !filtered.length && <div className="hint2" style={{ padding: '8px 2px' }}>검색 결과가 없습니다.</div>}
            {filtered.map((s) => (
              <div key={s.ticker} className="searchrow" onClick={() => !watchBusy && onAddStock(s.ticker)}>
                <div className="sm"><span className="sym">{s.ticker}</span><span className="sec">{s.name_ko || s.name_en} · {s.sector?.name_ko ?? '섹터 미지정'}</span></div>
                <span className="addbtn"><Icon size={14}><path d="M12 5v14M5 12h14" /></Icon></span>
              </div>
            ))}
          </div>
        </>
      )}

      {timeMode === 'today' && briefingTab === 'mine' && (
        <>
          {watchStocks.length ? (
            <div className="rows">
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

      {timeMode === 'history' && briefingTab === 'overview' && (
        <div className="rows">
          {overviewHistoryLoading && <div className="hint2" style={{ padding: '8px 2px' }}>불러오는 중…</div>}
          {overviewHistoryError && <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)' }}>{overviewHistoryError}</div>}
          {!overviewHistoryLoading && !overviewHistoryError && !overviewHistory.length && (
            <div className="strip">아직 생성된 전체 시황이 없습니다.</div>
          )}
          {overviewHistory.map((row) => (
            <OverviewHistoryRow key={row.briefing_date} row={row} onOpenDetail={onOpenDetail} />
          ))}
        </div>
      )}

      {timeMode === 'history' && briefingTab === 'sector' && (
        <div className="rows">
          {sectorHistoryLoading && <div className="hint2" style={{ padding: '8px 2px' }}>불러오는 중…</div>}
          {sectorHistoryError && <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)' }}>{sectorHistoryError}</div>}
          {!sectorHistoryLoading && !sectorHistoryError && !sectorHistory.length && (
            <div className="strip">아직 생성된 섹터 브리핑이 없습니다.</div>
          )}
          {sectorHistory.map((row) => (
            <SectorHistoryRow key={`${row.sector_id}-${row.briefing_date}`} row={row} sectorsById={sectorsById} onOpenDetail={onOpenDetail} />
          ))}
        </div>
      )}

      {timeMode === 'history' && briefingTab === 'mine' && (
        <div className="rows">
          {historyLoading && <div className="hint2" style={{ padding: '8px 2px' }}>불러오는 중…</div>}
          {historyError && <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)' }}>{historyError}</div>}
          {!historyLoading && !historyError && !history.length && (
            <div className="strip">아직 생성된 브리핑이 없습니다.</div>
          )}
          {history.map((row) => (
            <HistoryRow key={`${row.ticker}-${row.briefing_date}`} row={row} stocksByTicker={stocksByTicker} onOpenDetail={onOpenDetail} />
          ))}
        </div>
      )}
    </div>
  );
}
