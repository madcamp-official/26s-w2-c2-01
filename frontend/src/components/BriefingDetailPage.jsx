import { STOCKS, DETAILS, SECTORS, OVERVIEW, SENT, genericDetail, chgClass } from '../data.js';
import Icon from './Icon.jsx';

export default function BriefingDetailPage({ detail, watch, onBack, onOpenDetail, onOpenLens, onToggleWatch }) {
  if (!detail) {
    return (
      <div className="maxw">
        잘못된 접근입니다. <span style={{ color: 'var(--accent)', cursor: 'pointer' }} onClick={onBack}>돌아가기</span>
      </div>
    );
  }

  const BackLink = (
    <div className="backlink" onClick={onBack}>
      <Icon size={15}><path d="M15 18l-6-6 6-6" /></Icon> 오늘의 브리핑으로
    </div>
  );

  if (detail.type === 'overview') {
    return (
      <div className="maxw">
        {BackLink}
        <div className="block">
          <div className="block-h"><h2>전체 시황</h2></div>
          <div className="idxgrid" style={{ marginBottom: 16 }}>
            {OVERVIEW.indices.map((i) => (
              <div key={i.name} className="idxcard">
                <div className="l">{i.name}</div>
                <div className={`v ${chgClass(i.chg)}`}>{i.chg}</div>
              </div>
            ))}
          </div>
          <p style={{ fontSize: 13.5, color: 'var(--t2)', lineHeight: 1.7 }}>{OVERVIEW.summary}</p>
        </div>
        <div className="block">
          <div className="block-h"><h2>오늘 확인할 것</h2></div>
          {OVERVIEW.actions.map((a, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, fontSize: 13, color: 'var(--t2)', lineHeight: 1.6, marginBottom: 7 }}>
              <Icon size={15}><path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="9" /></Icon>{a}
            </div>
          ))}
          <div style={{ fontSize: 11, color: 'var(--t3)', marginTop: 10 }}>본 브리핑은 정보 제공 목적이며 투자 권유가 아닙니다.</div>
        </div>
      </div>
    );
  }

  if (detail.type === 'sector') {
    const s = SECTORS[detail.id];
    const rows = Object.entries(STOCKS).filter(([, v]) => v.sector === detail.id);
    return (
      <div className="maxw">
        {BackLink}
        <div className="block">
          <div className="block-h"><h2>{detail.id}</h2><span className="hint">{s.chg}</span></div>
          <p style={{ fontSize: 13.5, color: 'var(--t2)', lineHeight: 1.7, marginBottom: 14 }}>{s.desc}</p>
          <div className="rows">
            {rows.map(([t, v]) => (
              <div key={t} className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenDetail({ type: 'stock', ticker: t })}>
                <div className="m"><div className="tk"><span className="sym">{t}</span><span className="sec">{v.name}</span></div></div>
                <div className="chg"><div className={`pct ${chgClass(v.chg)}`}>{v.chg}</div></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // detail.type === 'stock'
  const t = detail.ticker;
  const s = STOCKS[t];
  const det = DETAILS[t] || genericDetail(t);
  const [lbl, cls] = SENT[s.sent];
  const inWatch = watch.includes(t);

  return (
    <div className="maxw">
      {BackLink}
      <div className="block">
        <div className="block-h"><h2>{t} · {s.name}</h2><span className={`tag ${cls}`} style={{ marginLeft: 'auto' }}>{lbl}</span></div>
        <p style={{ fontSize: 13, color: 'var(--t3)', marginBottom: 12 }}>{s.sector} · {s.chg}</p>
        <p style={{ fontSize: 13.5, color: 'var(--t2)', lineHeight: 1.7 }}>{s.desc}</p>
        <div className="factgrid">
          {det.pos.length > 0 && (
            <div className="factbox pos"><div className="ft">긍정 요인</div>{det.pos.map((x, i) => <div key={i}>{x}</div>)}</div>
          )}
          {det.neg.length > 0 && (
            <div className="factbox neg"><div className="ft">부정 요인</div>{det.neg.map((x, i) => <div key={i}>{x}</div>)}</div>
          )}
          {det.watch.length > 0 && (
            <div className="factbox neu"><div className="ft">확인할 것</div>{det.watch.map((x, i) => <div key={i}>{x}</div>)}</div>
          )}
        </div>
        {det.cites.length > 0 && (
          <div className="citelist">
            {det.cites.map((c, i) => (
              <div key={i} className="citerow">
                <Icon size={13}>
                  <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
                  <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
                </Icon>{c}
              </div>
            ))}
          </div>
        )}
        <div style={{ display: 'flex', gap: 10, marginTop: 18, flexWrap: 'wrap' }}>
          <button className="btn primary" onClick={() => onOpenLens(t)}>
            <Icon size={15}><path d="M4 6h16M7 12h10M10 18h4" /></Icon> 분석렌즈 편집
          </button>
          <button className="btn" onClick={() => onToggleWatch(t)}>{inWatch ? '관심종목에서 제거' : '관심종목에 추가'}</button>
        </div>
      </div>
    </div>
  );
}
