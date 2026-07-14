import { useState } from 'react';
import Icon from './Icon.jsx';

function formatNumber(value, digits = 1) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : '-';
}

function formatSigned(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '-';
  return `${number > 0 ? '+' : ''}${number.toFixed(1)}%`;
}

function formatMarketCap(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) return '시총 정보 없음';
  if (number >= 1_000_000_000_000) return `$${(number / 1_000_000_000_000).toFixed(2)}T`;
  if (number >= 1_000_000_000) return `$${(number / 1_000_000_000).toFixed(1)}B`;
  return `$${(number / 1_000_000).toFixed(0)}M`;
}

function formatUpdatedAt(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat('ko-KR', {
    month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Seoul',
  }).format(date);
}

function VolatilityRow({ rank, metrics, stock, inWatch, adding, onAddOrOpen }) {
  const ticker = metrics.ticker;
  return (
    <div className="vol-row">
      <span className="vol-rank">{rank}</span>
      <span className="vol-company">
        <span className="vol-ticker">{ticker}</span>
        <span className="vol-name">{stock?.name_ko || stock?.name_en || ticker}</span>
        {metrics.news_catalyst_confirmed && <span className="vol-news">뉴스 {metrics.news_catalyst_count}건</span>}
      </span>
      <span className="vol-primary">
        <span className="vol-score">{formatNumber(metrics.volatility_attention_score, 0)}</span>
        <span className="vol-label">주목 점수</span>
      </span>
      <span className="vol-stat">
        <b className={metrics.premarket_direction === 'down' ? 'down' : 'up'}>{formatSigned(metrics.premarket_gap_pct)}</b>
        <span>프리마켓 갭</span>
      </span>
      <span className="vol-stat">
        <b>{formatNumber(metrics.high_low_spread_pct)}%</b>
        <span>전일 변동폭</span>
      </span>
      <span className="vol-stat vol-cap">
        <b>{formatMarketCap(metrics.market_cap_usd)}</b>
        <span>시가총액</span>
      </span>
      <button
        type="button"
        className={`vol-add ${inWatch ? 'on' : ''}`}
        disabled={adding}
        title={inWatch ? `${ticker} 브리핑 상세 보기` : `${ticker} 관심 종목에 추가`}
        aria-label={inWatch ? `${ticker} 브리핑 상세 보기` : `${ticker} 관심 종목에 추가하고 브리핑 상세 보기`}
        onClick={() => onAddOrOpen(ticker)}
      >
        {adding ? (
          <span className="vol-spinner" />
        ) : inWatch ? (
          <Icon size={17}><path d="M5 12l4 4L19 6" /></Icon>
        ) : (
          <Icon size={17}><path d="M12 5v14M5 12h14" /></Icon>
        )}
      </button>
    </div>
  );
}

export default function VolatilityPage({ data, loading, error, stocksByTicker, watch, addingTicker, actionError, onRetry, onAddOrOpen }) {
  const [tab, setTab] = useState('blue_chip');
  const tabData = data?.[tab];
  const items = (tabData?.tickers ?? [])
    .map((ticker) => tabData?.metrics?.[ticker])
    .filter(Boolean)
    .slice(0, 5);
  const threshold = Number(data?.criteria?.blue_chip_market_cap_usd ?? 2_000_000_000);
  const allLiquidity = Number(data?.criteria?.all_stock_min_dollar_volume ?? 1_000_000);
  const updatedAt = formatUpdatedAt(data?.generated_at);

  return (
    <div className="vol-page">
      <div className="vol-hero">
        <div>
          <div className="vol-kicker"><span className="live-dot" /> PRE-MARKET SCANNER</div>
          <h2>오늘 움직임이 큰 종목</h2>
          <p>상승과 하락을 함께 탐지하고, 5개 지표를 합산한 변동성 주목 점수로 순위를 매깁니다.</p>
        </div>
        {updatedAt && <div className="vol-updated">{updatedAt} 기준</div>}
      </div>

      <div className="vol-tabs" role="tablist" aria-label="변동성 종목 범위">
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'blue_chip'}
          className={tab === 'blue_chip' ? 'on' : ''}
          onClick={() => setTab('blue_chip')}
        >
          우량·중대형주
          <span>시총 ${Math.round(threshold / 1_000_000_000)}B 이상 · 유동성 적용</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'all'}
          className={tab === 'all' ? 'on' : ''}
          onClick={() => setTab('all')}
        >
          전체 종목
          <span>시총 제한 없음 · 일평균 거래대금 ${(allLiquidity / 1_000_000).toFixed(0)}M 이상</span>
        </button>
      </div>

      {actionError && (
        <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)', marginBottom: 12 }}>
          {actionError}
        </div>
      )}

      <div className="vol-panel">
        <div className="vol-panel-head">
          <span>{data?.score_name ?? '변동성 주목 점수'} 상위 종목</span>
          <span>최대 5개 · 100점 만점</span>
        </div>

        {loading && <div className="vol-state"><span className="vol-spinner" />종목을 불러오는 중입니다.</div>}
        {!loading && error && (
          <div className="vol-state vol-error">
            <Icon size={20}><circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" /></Icon>
            <div><b>아직 오늘의 스캔 결과가 없습니다.</b><span>{error}</span></div>
            <button type="button" className="btn" onClick={onRetry}>다시 불러오기</button>
          </div>
        )}
        {!loading && !error && !items.length && (
          <div className="vol-state">
            <Icon size={22}><path d="M3 18l4-5 4 3 5-9 5 4" /></Icon>
            <div><b>표시할 종목이 없습니다.</b><span>장 시작 전 다음 스캔 결과를 기다려 주세요.</span></div>
          </div>
        )}
        {!loading && !error && items.length > 0 && (
          <div className="vol-list">
            {items.map((metrics, index) => (
              <VolatilityRow
                key={metrics.ticker}
                rank={index + 1}
                metrics={metrics}
                stock={stocksByTicker[metrics.ticker]}
                inWatch={watch.includes(metrics.ticker)}
                adding={addingTicker === metrics.ticker}
                onAddOrOpen={onAddOrOpen}
              />
            ))}
          </div>
        )}
      </div>

      <p className="vol-footnote">{data?.score_disclaimer ?? '이 점수는 투자 추천이나 미래 수익률 예측이 아닙니다.'} 프리마켓 가격은 정규장 시가와 다를 수 있습니다.</p>
    </div>
  );
}
