import { useEffect, useMemo, useState } from 'react';
import { SENT_LABEL } from '../data.js';
import Icon from './Icon.jsx';

function DetailTimeTabs({ timeMode, setTimeMode }) {
  return (
    <div className="ptabs">
      <button className={timeMode === 'today' ? 'on' : ''} onClick={() => setTimeMode('today')}>오늘</button>
      <button className={timeMode === 'history' ? 'on' : ''} onClick={() => setTimeMode('history')}>이전 기록</button>
    </div>
  );
}

function formatUpdateTime(value) {
  if (!value) return null;
  // PostgreSQL의 timestamp without time zone은 배포 DB에서 UTC로 저장된다.
  const normalized = typeof value === 'string' && !/(Z|[+-]\d{2}:\d{2})$/.test(value)
    ? `${value}Z`
    : value;
  return new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul', hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(new Date(normalized));
}

function TodaySessionTabs({ sessions, selected, onSelect, getUpdatedAt }) {
  return (
    <div className="session-tabs" aria-label="오늘의 장 세션">
      {sessions.map((session) => {
        const updatedAt = getUpdatedAt(session.key);
        const time = formatUpdateTime(updatedAt || session.scheduled_at);
        return (
          <button
            key={session.key}
            type="button"
            className={selected === session.key ? 'on' : ''}
            disabled={!session.available}
            onClick={() => onSelect(session.key)}
          >
            <span>{session.label}</span>
            <small>{session.available
              ? (updatedAt ? `${time} 업데이트` : '업데이트 대기')
              : (session.historical ? '기록 없음' : `${time} 예정`)}</small>
          </button>
        );
      })}
    </div>
  );
}

function BriefingBlock({ row }) {
  const [label, className] = row.sentiment ? SENT_LABEL[row.sentiment] : [null, null];
  return (
    <div className="block">
      <div className="block-h">
        <h2 style={{ fontSize: 15 }}>{row.briefing_date}</h2>
        {label && <span className={`tag ${className}`} style={{ marginLeft: 'auto' }}>{label}</span>}
      </div>
      {row.indices && Object.keys(row.indices).length > 0 && (
        <div className="idxgrid" style={{ marginBottom: 16 }}>
          {Object.entries(row.indices).map(([name, value]) => (
            <div key={name} className="idxcard"><div className="l">{name}</div><div className="v">{String(value)}</div></div>
          ))}
        </div>
      )}
      {row.summary && <p style={{ fontSize: 13.5, color: 'var(--t2)', lineHeight: 1.7 }}>{row.summary}</p>}
      <div className="factgrid">
        {row.positive_factors?.length > 0 && (
          <div className="factbox pos"><div className="ft">긍정 요인</div>{row.positive_factors.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
        )}
        {row.negative_factors?.length > 0 && (
          <div className="factbox neg"><div className="ft">부정 요인</div>{row.negative_factors.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
        )}
        {row.watch_issues?.length > 0 && (
          <div className="factbox neu"><div className="ft">확인할 것</div>{row.watch_issues.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
        )}
      </div>
      {row.reasons?.length > 0 && (
        <div className="citelist">
          {row.reasons.map((reason, i) => (
            <div key={i} className="citerow">
              <Icon size={13}>
                <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
                <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
              </Icon>
              {reason.source_url ? (
                <a href={reason.source_url} target="_blank" rel="noreferrer">{reason.factor ?? reason.explain ?? reason.source_url}</a>
              ) : (
                <span>{reason.factor ?? reason.explain ?? JSON.stringify(reason)}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function historySessionsFor(dateValue, dateRows) {
  const briefingDate = new Date(`${dateValue}T00:00:00Z`);
  const marketDate = new Date(briefingDate);
  marketDate.setUTCDate(marketDate.getUTCDate() - 1);
  const marketDay = marketDate.getUTCDate();
  const todayDay = briefingDate.getUTCDate();
  const definitions = [
    ['market_open', `${marketDay}일 장시작`],
    ['intraday', `${marketDay}일 장중`],
    ['market_close', `${marketDay}일 장마감`],
    ['after_hours', `${marketDay}~${todayDay}일 시간외`],
  ];
  const sessions = definitions.map(([key, label]) => {
    const row = dateRows.find((item) => item.briefing_session === key);
    return { key, label, available: Boolean(row), historical: true, scheduled_at: row?.generated_at };
  });
  const additional = dateRows.find((item) => item.briefing_session === 'additional');
  if (additional) {
    sessions.push({
      key: 'additional', label: '추가', available: true, historical: true,
      scheduled_at: additional.generated_at,
    });
  }
  return sessions;
}

function HistoryList({ rows = [], loading, error, emptyLabel }) {
  const dates = useMemo(
    () => [...new Set(rows.map((row) => row.briefing_date))].sort().reverse(),
    [rows]
  );
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedHistorySession, setSelectedHistorySession] = useState(null);

  useEffect(() => {
    if (!dates.includes(selectedDate)) setSelectedDate(dates[0] ?? null);
  }, [dates, selectedDate]);

  const dateRows = useMemo(
    () => rows.filter((row) => row.briefing_date === selectedDate),
    [rows, selectedDate]
  );
  const sessions = useMemo(
    () => selectedDate ? historySessionsFor(selectedDate, dateRows) : [],
    [selectedDate, dateRows]
  );

  useEffect(() => {
    const available = sessions.filter((session) => session.available);
    if (!available.some((session) => session.key === selectedHistorySession)) {
      setSelectedHistorySession(available[0]?.key ?? null);
    }
  }, [selectedDate, sessions, selectedHistorySession]);

  if (loading) return <div className="strip">불러오는 중…</div>;
  if (error) return <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)' }}>{error}</div>;
  if (!rows.length) return <div className="strip">{emptyLabel}</div>;

  const selectedRow = dateRows.find((row) => row.briefing_session === selectedHistorySession);
  return (
    <div className="history-archive">
      <div className="history-date-tabs" aria-label="브리핑 기록 날짜">
        {dates.map((date) => (
          <button
            type="button"
            key={date}
            className={selectedDate === date ? 'on' : ''}
            onClick={() => setSelectedDate(date)}
          >
            {date.replaceAll('-', '.')}
          </button>
        ))}
      </div>
      <TodaySessionTabs
        sessions={sessions}
        selected={selectedHistorySession}
        onSelect={setSelectedHistorySession}
        getUpdatedAt={(key) => dateRows.find((row) => row.briefing_session === key)?.generated_at}
      />
      {selectedRow ? <BriefingBlock row={selectedRow} /> : <div className="strip">해당 세션의 기록이 없습니다.</div>}
    </div>
  );
}

export default function BriefingDetailPage({
  detail, stocks, watch, onBack, onOpenLens, onToggleWatch,
  timeMode, setTimeMode,
  briefingByTicker, missingTickers, marketOverview: latestMarketOverview,
  marketOverviews = [], briefingSessions = [], briefingDate, stockBriefings = [],
  sectorsById, sectorWatch, onOpenSectorLens, onToggleSectorWatch,
  sectorBriefingBySectorId, sectorBriefings = [], missingSectorIds,
  history, historyLoading, historyError,
  overviewHistory, overviewHistoryLoading, overviewHistoryError,
  sectorHistory, sectorHistoryLoading, sectorHistoryError,
}) {
  const latestAvailableSession = [...briefingSessions].reverse().find((item) => item.available)?.key ?? null;
  const [selectedSession, setSelectedSession] = useState(latestAvailableSession);

  useEffect(() => {
    setSelectedSession(latestAvailableSession);
  }, [briefingDate, detail?.type, detail?.ticker, detail?.sectorId, latestAvailableSession]);

  const SessionTabs = ({ rows }) => {
    const additional = rows.find((row) => row.briefing_session === 'additional');
    const sessions = additional
      ? [...briefingSessions, {
        key: 'additional', label: '추가', available: true, scheduled_at: additional.generated_at,
      }]
      : briefingSessions;
    return (
      <TodaySessionTabs
        sessions={sessions}
        selected={selectedSession}
        onSelect={setSelectedSession}
        getUpdatedAt={(key) => rows.find((row) => row.briefing_session === key)?.generated_at}
      />
    );
  };

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
    const marketOverview = marketOverviews.find(
      (row) => row.briefing_session === selectedSession
    ) ?? (selectedSession === latestAvailableSession ? latestMarketOverview : null);
    const indexEntries = marketOverview?.indices ? Object.entries(marketOverview.indices) : [];
    const sectorMoveEntries = marketOverview?.sector_moves ? Object.entries(marketOverview.sector_moves) : [];
    const [overviewLabel, overviewClass] = marketOverview?.sentiment
      ? SENT_LABEL[marketOverview.sentiment]
      : [null, null];
    const previousOverviews = overviewHistory.filter(
      (row) => row.briefing_date !== briefingDate
    );
    return (
      <div className="maxw">
        {BackLink}
        <DetailTimeTabs timeMode={timeMode} setTimeMode={setTimeMode} />
        {timeMode === 'today' && <SessionTabs rows={marketOverviews} />}
        {timeMode === 'today' ? (
          <div className="block">
          <div className="block-h">
            <h2>전체 시황</h2>
            {overviewLabel && <span className={`tag ${overviewClass}`} style={{ marginLeft: 'auto' }}>{overviewLabel}</span>}
          </div>
          {marketOverview ? (
            <>
              {indexEntries.length > 0 && (
                <div className="idxgrid" style={{ marginBottom: 16 }}>
                  {indexEntries.map(([name, v]) => (
                    <div key={name} className="idxcard"><div className="l">{name}</div><div className="v">{String(v)}</div></div>
                  ))}
                </div>
              )}
              {sectorMoveEntries.length > 0 && (
                <div className="idxgrid" style={{ marginBottom: 16 }}>
                  {sectorMoveEntries.map(([name, value]) => (
                    <div key={name} className="idxcard"><div className="l">{name}</div><div className="v" style={{ fontSize: 13 }}>{String(value)}</div></div>
                  ))}
                </div>
              )}
              <p style={{ fontSize: 13.5, color: 'var(--t2)', lineHeight: 1.7 }}>{marketOverview.summary}</p>
              <div className="factgrid">
                {marketOverview.positive_factors?.length > 0 && (
                  <div className="factbox pos"><div className="ft">긍정 요인</div>{marketOverview.positive_factors.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
                )}
                {marketOverview.negative_factors?.length > 0 && (
                  <div className="factbox neg"><div className="ft">부정 요인</div>{marketOverview.negative_factors.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
                )}
                {marketOverview.watch_issues?.length > 0 && (
                  <div className="factbox neu"><div className="ft">확인할 것</div>{marketOverview.watch_issues.map((x, i) => <div key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</div>)}</div>
                )}
              </div>
              {marketOverview.reasons?.length > 0 && (
                <div className="citelist">
                  {marketOverview.reasons.map((reason, i) => (
                    <div key={i} className="citerow">
                      <Icon size={13}>
                        <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
                        <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
                      </Icon>
                      {reason.source_url ? (
                        <a href={reason.source_url} target="_blank" rel="noreferrer">{reason.factor ?? reason.explain ?? reason.source_url}</a>
                      ) : (
                        <span>{reason.factor ?? reason.explain ?? JSON.stringify(reason)}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="strip">아직 전체 시황 브리핑이 생성되지 않았습니다. 뉴스 수집·분석 파이프라인이 연결되면 이곳에 표시됩니다.</div>
          )}
          </div>
        ) : (
          <HistoryList
            rows={previousOverviews}
            loading={overviewHistoryLoading}
            error={overviewHistoryError}
            emptyLabel="이전 전체 시황 기록이 없습니다."
          />
        )}
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
    const sectorRows = sectorBriefings.filter((row) => row.sector_id === sectorId);
    const b = sectorRows.find((row) => row.briefing_session === selectedSession)
      ?? (selectedSession === latestAvailableSession ? sectorBriefingBySectorId[sectorId] : null);
    const inWatch = sectorWatch.includes(sectorId);
    const [lbl, cls] = b?.sentiment ? SENT_LABEL[b.sentiment] : [null, null];
    const previousBriefings = sectorHistory.filter(
      (row) => row.sector_id === sectorId && row.briefing_date !== briefingDate
    );

    return (
      <div className="maxw">
        {BackLink}
        <DetailTimeTabs timeMode={timeMode} setTimeMode={setTimeMode} />
        {timeMode === 'today' && <SessionTabs rows={sectorRows} />}
        {timeMode === 'today' ? (
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
        ) : (
          <HistoryList
            rows={previousBriefings}
            loading={sectorHistoryLoading}
            error={sectorHistoryError}
            emptyLabel="이 섹터의 이전 브리핑 기록이 없습니다."
          />
        )}
      </div>
    );
  }

  // detail.type === 'stock'
  const t = detail.ticker;
  const s = stocks.find((x) => x.ticker === t);
  if (!s) {
    return <div className="maxw">{BackLink}종목 정보를 찾을 수 없습니다.</div>;
  }
  const stockRows = stockBriefings.filter((row) => row.ticker === t);
  const b = stockRows.find((row) => row.briefing_session === selectedSession)
    ?? (selectedSession === latestAvailableSession ? briefingByTicker[t] : null);
  const inWatch = watch.includes(t);
  const [lbl, cls] = b?.sentiment ? SENT_LABEL[b.sentiment] : [null, null];
  const previousBriefings = history.filter(
    (row) => row.ticker === t && row.briefing_date !== briefingDate
  );

  return (
    <div className="maxw">
      {BackLink}
      <DetailTimeTabs timeMode={timeMode} setTimeMode={setTimeMode} />
      {timeMode === 'today' && <SessionTabs rows={stockRows} />}
      {timeMode === 'today' ? (
        <div className="block">
        <div className="block-h">
          <h2>{t} · {s.name_ko || s.name_en}</h2>
          {lbl && <span className={`tag ${cls}`} style={{ marginLeft: 'auto' }}>{lbl}</span>}
        </div>
        <p style={{ fontSize: 13, color: 'var(--t3)', marginBottom: 12 }}>
          섹터: {s.sector?.name_ko ?? '미지정'} · 거래소: {s.exchange?.toUpperCase() ?? '미지정'}
        </p>

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
      ) : (
        <HistoryList
          rows={previousBriefings}
          loading={historyLoading}
          error={historyError}
          emptyLabel="이 종목의 이전 브리핑 기록이 없습니다."
        />
      )}
    </div>
  );
}
