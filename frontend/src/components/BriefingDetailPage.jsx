import { SENT_LABEL } from '../data.js';
import Icon from './Icon.jsx';

export default function BriefingDetailPage({
  detail, stocks, watch, onBack, onOpenDetail, onOpenLens, onToggleWatch,
  briefingByTicker, missingTickers, marketOverview,
  sectorsById, sectorWatch, onOpenSectorLens, onToggleSectorWatch,
  sectorBriefingBySectorId, missingSectorIds,
}) {
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
    const indexEntries = marketOverview?.indices ? Object.entries(marketOverview.indices) : [];
    return (
      <div className="maxw">
        {BackLink}
        <div className="block">
          <div className="block-h"><h2>전체 시황</h2></div>
          {marketOverview ? (
            <>
              {indexEntries.length > 0 && (
                <div className="idxgrid" style={{ marginBottom: 16 }}>
                  {indexEntries.map(([name, v]) => (
                    <div key={name} className="idxcard"><div className="l">{name}</div><div className="v">{String(v)}</div></div>
                  ))}
                </div>
              )}
              <p style={{ fontSize: 13.5, color: 'var(--t2)', lineHeight: 1.7 }}>{marketOverview.summary}</p>
            </>
          ) : (
            <div className="strip">아직 전체 시황 브리핑이 생성되지 않았습니다. 뉴스 수집·분석 파이프라인이 연결되면 이곳에 표시됩니다.</div>
          )}
        </div>
        <div style={{ fontSize: 11, color: 'var(--t3)' }}>본 브리핑은 정보 제공 목적이며 투자 권유가 아닙니다.</div>
      </div>
    );
  }

  if (detail.type === 'sector-briefing') {
    const sectorId = detail.sectorId;
    const sector = sectorsById[sectorId];
    if (!sector) {
      return <div className="maxw">{BackLink}섹터 정보를 찾을 수 없습니다.</div>;
    }
    const b = sectorBriefingBySectorId[sectorId];
    const inWatch = sectorWatch.includes(sectorId);
    const [lbl, cls] = b?.sentiment ? SENT_LABEL[b.sentiment] : [null, null];

    return (
      <div className="maxw">
        {BackLink}
        <div className="block">
          <div className="block-h">
            <h2>{sector.name_ko} 섹터</h2>
            {lbl && <span className={`tag ${cls}`} style={{ marginLeft: 'auto' }}>{lbl}</span>}
          </div>

          {b ? (
            <>
              {b.summary && <p style={{ fontSize: 13.5, color: 'var(--t2)', lineHeight: 1.7 }}>{b.summary}</p>}
              <div className="factgrid">
                {b.positive_factors?.length > 0 && (
                  <div className="factbox pos"><div className="ft">긍정 요인</div>{b.positive_factors.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
                )}
                {b.negative_factors?.length > 0 && (
                  <div className="factbox neg"><div className="ft">부정 요인</div>{b.negative_factors.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
                )}
                {b.watch_issues?.length > 0 && (
                  <div className="factbox neu"><div className="ft">확인할 것</div>{b.watch_issues.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
                )}
              </div>
              {b.reasons?.length > 0 && (
                <div className="citelist">
                  {b.reasons.map((r, i) => (
                    <div key={i} className="citerow">
                      <Icon size={13}>
                        <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
                        <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
                      </Icon>
                      {r.source_url ? (
                        <a href={r.source_url} target="_blank" rel="noreferrer">{r.factor ?? r.explain ?? r.source_url}</a>
                      ) : (
                        <span>{r.factor ?? r.explain ?? JSON.stringify(r)}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="strip" style={{ marginTop: 4 }}>
              {missingSectorIds.has(sectorId) ? '아직 이 섹터의 브리핑이 생성되지 않았습니다.' : '브리핑 데이터가 없습니다.'}
            </div>
          )}

          <div style={{ display: 'flex', gap: 10, marginTop: 18, flexWrap: 'wrap' }}>
            <button className="btn primary" onClick={() => onOpenSectorLens(sectorId)}>
              <Icon size={15}><path d="M4 6h16M7 12h10M10 18h4" /></Icon> 분석렌즈 편집
            </button>
            <button className="btn" onClick={() => onToggleSectorWatch(sectorId)}>{inWatch ? '관심 섹터에서 제거' : '관심 섹터에 추가'}</button>
          </div>
        </div>
      </div>
    );
  }

  // detail.type === 'stock'
  const t = detail.ticker;
  const s = stocks.find((x) => x.ticker === t);
  if (!s) {
    return <div className="maxw">{BackLink}종목 정보를 찾을 수 없습니다.</div>;
  }
  const b = briefingByTicker[t];
  const inWatch = watch.includes(t);
  const [lbl, cls] = b?.sentiment ? SENT_LABEL[b.sentiment] : [null, null];

  return (
    <div className="maxw">
      {BackLink}
      <div className="block">
        <div className="block-h">
          <h2>{t} · {s.name_ko || s.name_en}</h2>
          {lbl && <span className={`tag ${cls}`} style={{ marginLeft: 'auto' }}>{lbl}</span>}
        </div>
        <p style={{ fontSize: 13, color: 'var(--t3)', marginBottom: 12 }}>{s.sector?.name_ko ?? '섹터 미지정'} · {s.exchange}</p>

        {b ? (
          <>
            {b.summary && <p style={{ fontSize: 13.5, color: 'var(--t2)', lineHeight: 1.7 }}>{b.summary}</p>}
            <div className="factgrid">
              {b.positive_factors?.length > 0 && (
                <div className="factbox pos"><div className="ft">긍정 요인</div>{b.positive_factors.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
              )}
              {b.negative_factors?.length > 0 && (
                <div className="factbox neg"><div className="ft">부정 요인</div>{b.negative_factors.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
              )}
              {b.watch_issues?.length > 0 && (
                <div className="factbox neu"><div className="ft">확인할 것</div>{b.watch_issues.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
              )}
            </div>
            {b.reasons?.length > 0 && (
              <div className="citelist">
                {b.reasons.map((r, i) => (
                  <div key={i} className="citerow">
                    <Icon size={13}>
                      <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
                      <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
                    </Icon>
                    {r.source_url ? (
                      <a href={r.source_url} target="_blank" rel="noreferrer">{r.factor ?? r.explain ?? r.source_url}</a>
                    ) : (
                      <span>{r.factor ?? r.explain ?? JSON.stringify(r)}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="strip" style={{ marginTop: 4 }}>
            {missingTickers.has(t) ? '아직 이 종목의 브리핑이 생성되지 않았습니다.' : '브리핑 데이터가 없습니다.'}
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
