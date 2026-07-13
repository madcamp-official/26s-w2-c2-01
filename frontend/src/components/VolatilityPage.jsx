import { useState } from 'react';
import Icon from './Icon.jsx';

function formatNumber(value, digits = 1) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : '-';
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

function VolatilityRow({ rank, metrics, stock, onOpenDetail }) {
  const ticker = metrics.ticker;
  return (
    <button
      type="button"
      className="vol-row"
      onClick={() => onOpenDetail({ type: 'stock', ticker })}
      aria-label={`${ticker} 종목 상세 보기`}
    >
      <span className="vol-rank">{rank}</span>
      <span className="vol-company">
        <span className="vol-ticker">{ticker}</span>
        <span className="vol-name">{stock?.name_ko || stock?.name_en || ticker}</span>
      </span>
      <span className="vol-primary">
        <span className="vol-gap">+{formatNumber(metrics.premarket_gap_pct)}%</span>
        <span className="vol-label">프리마켓 갭</span>
      </span>
      <span className="vol-stat">
        <b>{formatNumber(metrics.intraday_range_pct)}%</b>
        <span>전일 변동폭</span>
      </span>
      <span className="vol-stat">
        <b>{formatNumber(metrics.volume_ratio)}배</b>
        <span>거래량</span>
      </span>
      <span className="vol-stat vol-cap">
        <b>{formatMarketCap(metrics.market_cap_usd)}</b>
        <span>시가총액</span>
      </span>
      <span className="vol-arrow"><Icon size={16}><path d="M9 18l6-6-6-6" /></Icon></span>
    </button>
  );
}

export default function VolatilityPage({ data, loading, error, stocksByTicker, onRetry, onOpenDetail }) {
  const [tab, setTab] = useState('blue_chip');
  const tabData = data?.[tab];
  const items = (tabData?.tickers ?? [])
    .map((ticker) => tabData?.metrics?.[ticker])
    .filter(Boolean)
    .slice(0, 5);
  const threshold = Number(data?.criteria?.blue_chip_market_cap_usd ?? 10_000_000_000);
  const updatedAt = formatUpdatedAt(data?.generated_at);

  return (
    <div className="vol-page">
      <div className="vol-hero">
        <div>
          <div className="vol-kicker"><span className="live-dot" /> PRE-MARKET SCANNER</div>
          <h2>오늘 움직임이 큰 종목</h2>
          <p>거래량, 장중 변동폭, 볼린저 밴드 돌파와 프리마켓 갭을 모두 충족한 종목입니다.</p>
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
          우량주
          <span>시총 ${Math.round(threshold / 1_000_000_000)}B 이상</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'all'}
          className={tab === 'all' ? 'on' : ''}
          onClick={() => setTab('all')}
        >
          전체 종목
          <span>시가총액 제한 없음</span>
        </button>
      </div>

      <div className="vol-panel">
        <div className="vol-panel-head">
          <span>변동성 상위 종목</span>
          <span>최대 5개 · 높은 순</span>
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
            <div><b>조건을 충족한 종목이 없습니다.</b><span>장 시작 전 다음 스캔 결과를 기다려 주세요.</span></div>
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
                onOpenDetail={onOpenDetail}
              />
            ))}
          </div>
        )}
      </div>

      <p className="vol-footnote">변동성 지표는 투자 추천이 아니며, 프리마켓 가격은 정규장 시가와 다를 수 있습니다.</p>
    </div>
  );
}
