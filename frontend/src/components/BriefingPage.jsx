import { useDeferredValue, useMemo } from 'react';
import { SENT_LABEL } from '../data.js';
import Icon from './Icon.jsx';

function RowActions({ label, refreshing, removing, onRefresh, onRemove }) {
  const busy = refreshing || removing;
  return (
    <div style={{ display: 'flex', gap: 6, marginTop: 7 }} onClick={(event) => event.stopPropagation()}>
      <button
        type="button"
        className="btn"
        style={{ padding: '6px 9px', fontSize: 12 }}
        disabled={busy}
        aria-busy={refreshing}
        title={`${label} 브리핑 새로고침`}
        aria-label={`${label} 브리핑 새로고침`}
        onClick={onRefresh}
      >
        <span className={refreshing ? 'briefing-refresh-icon spinning' : 'briefing-refresh-icon'}>
          <Icon size={14}><path d="M4 4v6h6M20 20v-6h-6" /><path d="M20 8a8 8 0 0 0-14.9-3M4 16a8 8 0 0 0 14.9 3" /></Icon>
        </span>
      </button>
      {onRemove && (
        <button
          type="button"
          className="btn"
          style={{ padding: '6px 8px', lineHeight: 0 }}
          disabled={busy}
          title={`관심 ${label}에서 삭제`}
          aria-label={`관심 ${label}에서 삭제`}
          onClick={onRemove}
        >
          <Icon size={14}><path d="M18 6L6 18M6 6l12 12" /></Icon>
        </button>
      )}
    </div>
  );
}

function StockCard({ stock, briefing, missing, onOpenDetail, onRefresh, onRemove, refreshing, removing }) {
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
      <div className="chg">
        {briefing && <div className="cnt">이슈 {(briefing.positive_factors?.length ?? 0) + (briefing.negative_factors?.length ?? 0)}건</div>}
        <RowActions
          label="종목"
          refreshing={refreshing}
          removing={removing}
          onRefresh={onRefresh}
          onRemove={onRemove}
        />
      </div>
    </div>
  );
}

function SectorCard({ sector, briefing, missing, onOpenDetail, onRefresh, onRemove, refreshing, removing }) {
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
      <div className="chg">
        {briefing && <div className="cnt">이슈 {(briefing.positive_factors?.length ?? 0) + (briefing.negative_factors?.length ?? 0)}건</div>}
        <RowActions
          label="섹터"
          refreshing={refreshing}
          removing={removing}
          onRefresh={onRefresh}
          onRemove={onRemove}
        />
      </div>
    </div>
  );
}

export default function BriefingPage({
  briefingTab, setBriefingTab,
  searchOpen, setSearchOpen,
  stocks, popularStocks, stockSearchResults, stockSearchLoading,
  watch, watchBusy, watchError, stockSearch, setStockSearch, onOpenDetail, onAddStock,
  briefingByTicker, missingTickers, marketOverview,
  onRefreshStock, onRemoveStock, refreshingTicker, removingTicker,
  onRefreshSector, onRemoveSector, refreshingSectorId, removingSectorId, actionError,
  onRefreshOverview, refreshingOverview,
  sectors, sectorWatch, sectorWatchBusy, sectorWatchError, sectorSearch, setSectorSearch, onAddSector,
  sectorBriefingBySectorId, missingSectorIds,
}) {
  const deferredStockSearch = useDeferredValue(stockSearch);
  const deferredSectorSearch = useDeferredValue(sectorSearch);
  const [overviewLabel, overviewClass] = marketOverview?.sentiment
    ? SENT_LABEL[marketOverview.sentiment]
    : [null, null];
  const overviewHasIssueFields = Array.isArray(marketOverview?.positive_factors)
    && Array.isArray(marketOverview?.negative_factors);
  const overviewIssueCount = overviewHasIssueFields
    ? marketOverview.positive_factors.length + marketOverview.negative_factors.length
    : null;

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
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 4 }}>
        <p className="hint2" style={{ fontSize: 13, margin: 0 }}>안 본 사이 있었던 일만 간단히 정리했습니다. 장시작·장중·장마감·휴장 중 하루 4번 자동으로 갱신됩니다.</p>
        <span className="hint2" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, margin: 0, whiteSpace: 'nowrap' }}>
          <Icon size={14}><path d="M4 4v6h6M20 20v-6h-6" /><path d="M20 8a8 8 0 0 0-14.9-3M4 16a8 8 0 0 0 14.9 3" /></Icon>
          새로고침
        </span>
      </div>
      {actionError && <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)', marginBottom: 10 }}>{actionError}</div>}

      <div className="chips" style={{ marginBottom: 14 }}>
        {[['mine', '관심 종목'], ['sector', '관심 섹터'], ['overview', '전체']].map(([k, l]) => (
          <span
            key={k}
            className={`chip ${briefingTab === k ? 'on' : ''}`}
            onClick={() => {
              setBriefingTab(k);
              if (k === 'overview') setSearchOpen(false);
            }}
          >{l}</span>
        ))}
        <span
          className={`chip ${searchOpen ? 'on' : ''}`}
          style={{
            marginLeft: 'auto',
            opacity: briefingTab === 'overview' ? 0.45 : 1,
            cursor: briefingTab === 'overview' ? 'not-allowed' : 'pointer',
          }}
          aria-disabled={briefingTab === 'overview'}
          onClick={() => {
            if (briefingTab !== 'overview') setSearchOpen((open) => !open);
          }}
        >검색</span>
      </div>

      {searchOpen && briefingTab === 'sector' && (
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
        </>
      )}

      {searchOpen && briefingTab !== 'sector' && (
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

      {briefingTab === 'overview' && (
        <div className="rows">
          <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'overview' })}>
            <div className="m">
              <div className="tk">
                <span className="sym">전체 시황</span>
                {overviewLabel && <span className={`tag ${overviewClass}`}>{overviewLabel}</span>}
              </div>
              <div className="desc">{marketOverview?.summary ?? '아직 전체 시황 브리핑이 생성되지 않았습니다.'}</div>
            </div>
            <div className="chg">
              {overviewIssueCount > 0 && <div className="cnt">이슈 {overviewIssueCount}건</div>}
              <RowActions
                label="전체 시황"
                refreshing={refreshingOverview}
                onRefresh={onRefreshOverview}
              />
            </div>
          </div>
        </div>
      )}

      {briefingTab === 'sector' && (
        <>
          {watchSectors.length ? (
            <div className="rows" style={{ marginTop: searchOpen ? 16 : 0 }}>
              {watchSectors.map((s) => (
                <SectorCard
                  key={s.id}
                  sector={s}
                  briefing={sectorBriefingBySectorId[s.id]}
                  missing={missingSectorIds.has(s.id)}
                  onOpenDetail={onOpenDetail}
                  onRefresh={() => onRefreshSector(s.id)}
                  onRemove={() => onRemoveSector(s.id)}
                  refreshing={refreshingSectorId === s.id}
                  removing={removingSectorId === s.id}
                />
              ))}
            </div>
          ) : (
            <div className="strip" style={{ marginTop: 14 }}>검색해서 관심 섹터를 추가하면 여기 섹터 브리핑이 생성됩니다.</div>
          )}
        </>
      )}

      {briefingTab === 'mine' && (
        <>
          {watchStocks.length ? (
            <div className="rows" style={{ marginTop: searchOpen ? 16 : 0 }}>
              {watchStocks.map((s) => (
                <StockCard
                  key={s.ticker}
                  stock={s}
                  briefing={briefingByTicker[s.ticker]}
                  missing={missingTickers.has(s.ticker)}
                  onOpenDetail={onOpenDetail}
                  onRefresh={() => onRefreshStock(s.ticker)}
                  onRemove={() => onRemoveStock(s.ticker)}
                  refreshing={refreshingTicker === s.ticker}
                  removing={removingTicker === s.ticker}
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
