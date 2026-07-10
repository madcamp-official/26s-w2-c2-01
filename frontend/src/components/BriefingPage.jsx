import { PERIODS, STOCKS, SENT, SECTORS, OVERVIEW, chgClass } from '../data.js';
import Icon from './Icon.jsx';

function StockCard({ ticker, period, onOpenDetail }) {
  const s = STOCKS[ticker];
  const iss = Math.round(s.issues * PERIODS[period].mult);
  const [lbl, cls] = SENT[s.sent];
  return (
    <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'stock', ticker })}>
      <div className="m">
        <div className="tk">
          <span className="sym">{ticker}</span>
          <span className={`tag ${cls}`}>{lbl}</span>
          <span className="sec">{s.name} · {s.sector}</span>
        </div>
        <div className="desc">{s.desc}</div>
      </div>
      <div className="chg">
        <div className={`pct ${chgClass(s.chg)}`}>{s.chg}</div>
        <div className="cnt">이슈 {iss}건</div>
      </div>
    </div>
  );
}

export default function BriefingPage({
  period, setPeriod, briefingTab, setBriefingTab,
  watch, stockSearch, setStockSearch, onOpenDetail, onAddStock,
}) {
  const P = PERIODS[period];

  const avail = Object.keys(STOCKS).filter((t) => !watch.includes(t));
  const q = stockSearch.trim().toLowerCase();
  const filtered = q
    ? avail.filter((t) => t.toLowerCase().includes(q) || STOCKS[t].name.toLowerCase().includes(q))
    : avail;

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
        {[['mine', '내 종목'], ['sector', '섹터'], ['overview', '전체']].map(([k, l]) => (
          <span key={k} className={`chip ${briefingTab === k ? 'on' : ''}`} onClick={() => setBriefingTab(k)}>{l}</span>
        ))}
      </div>

      {briefingTab === 'overview' && (
        <div className="rows">
          <div className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'overview' })}>
            <div className="m">
              <div className="tk"><span className="sym">전체 시황</span><span className="tag neu">{P.label}</span></div>
              <div className="desc">{OVERVIEW.summary}</div>
            </div>
            <div className="chg">
              <div className="pct up">{OVERVIEW.indices[0].chg}</div>
              <div className="cnt">나스닥</div>
            </div>
          </div>
        </div>
      )}

      {briefingTab === 'sector' && (
        <div className="rows">
          {Object.entries(SECTORS).map(([name, s]) => (
            <div key={name} className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'sector', id: name })}>
              <div className="m">
                <div className="tk"><span className="sym">{name}</span></div>
                <div className="desc">{s.desc}</div>
              </div>
              <div className="chg"><div className={`pct ${chgClass(s.chg)}`}>{s.chg}</div></div>
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
            />
          </div>
          <div className="searchresults">
            {!avail.length && <div className="hint2" style={{ padding: '8px 2px' }}>모든 종목을 이미 관심종목에 추가했습니다.</div>}
            {avail.length > 0 && !filtered.length && <div className="hint2" style={{ padding: '8px 2px' }}>검색 결과가 없습니다.</div>}
            {filtered.map((t) => (
              <div key={t} className="searchrow" onClick={() => onAddStock(t)}>
                <div className="sm"><span className="sym">{t}</span><span className="sec">{STOCKS[t].name} · {STOCKS[t].sector}</span></div>
                <span className="addbtn"><Icon size={14}><path d="M12 5v14M5 12h14" /></Icon></span>
              </div>
            ))}
          </div>

          {watch.length ? (
            <div className="rows" style={{ marginTop: 16 }}>
              {watch.map((t) => <StockCard key={t} ticker={t} period={period} onOpenDetail={onOpenDetail} />)}
            </div>
          ) : (
            <div className="strip" style={{ marginTop: 14 }}>검색해서 관심종목을 추가하면 여기 브리핑이 생성됩니다.</div>
          )}
        </>
      )}
    </div>
  );
}
