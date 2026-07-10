// ── 유틸 ──
export const chgClass = (c) => (c.startsWith('+') ? 'up' : c.startsWith('-') ? 'down' : 'flat');

// ── 분석 카테고리 마스터 (지수 / 지표 / 섹터·테마) ──
export const CATS = [
  { key: 'idx', label: '지수', items: [
    ['NASDAQ', '나스닥'], ['SP500', 'S&P 500'], ['SOX', '필라델피아 반도체(SOX)'],
    ['VIX', 'VIX 변동성'], ['DXY', '달러 인덱스'], ['DJI', '다우존스'], ['RUT', '러셀 2000'],
  ] },
  { key: 'ind', label: '지표', items: [
    ['FFR', '기준금리'], ['US10Y', '미 국채 10년물'], ['CPI', 'CPI'], ['NFP', '고용·실업률'],
    ['PMI', 'PMI'], ['PCE', 'PCE 물가'], ['GDP', 'GDP 성장률'], ['FOMC', 'FOMC 회의'],
  ] },
  { key: 'sec', label: '섹터 · 테마', items: [
    ['SEMI', '반도체·AI'], ['BIGTECH', '빅테크'], ['EV', '전기차'],
    ['AI_DC', 'AI·데이터센터'], ['DIVIDEND', '배당'], ['EARNINGS', '실적·밸류에이션'],
  ] },
];

export const CATLABEL = {};
CATS.forEach((g) => g.items.forEach(([c, l]) => { CATLABEL[c] = l; }));

// 분석 성향(preset) 카드 아이콘 — 여러 path/circle 조합을 데이터로 표현 (Icon 컴포넌트의 shapes prop과 짝)
export const PRESET_ICON = {
  MACRO: [{ type: 'path', d: 'M3 3v18h18' }, { type: 'path', d: 'M7 14l4-4 3 3 5-6' }],
  VALUE: [{ type: 'path', d: 'M12 2v20' }, { type: 'path', d: 'M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6' }],
  MOMENTUM: [{ type: 'path', d: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z' }],
  FACT: [{ type: 'path', d: 'M9 12l2 2 4-4' }, { type: 'circle', cx: 12, cy: 12, r: 9 }],
  BEGINNER: [{ type: 'path', d: 'M12 20h9' }, { type: 'path', d: 'M12 4a4 4 0 0 1 4 4c0 2-2 3-2 5' }],
};

export const PRESETS = {
  MACRO: { name: '냉정한 거시', desc: '금리·거시·수급 중심', persona: '금리·거시·수급 중심, 감정 배제' },
  VALUE: { name: '장기 가치투자', desc: '펀더멘털·밸류에이션 중심', persona: '펀더멘털·밸류에이션 중심, 단기 노이즈 무시' },
  MOMENTUM: { name: '단기 모멘텀', desc: '수급·촉매·변동성 주목', persona: '수급·촉매·단기 변동성 주목' },
  FACT: { name: '팩트 브리핑', desc: '사실·수치·인용만', persona: '해석 최소화, 사실·수치·인용만' },
  BEGINNER: { name: '입문자용', desc: '용어 풀이·비유로 설명', persona: '용어를 풀어주고 비유로 설명' },
};

export const INVESTOR_TYPES = {
  stable: { name: '안정형', desc: '변동성보다 안정적인 수익을 선호합니다.' },
  balanced: { name: '균형형', desc: '수익과 안정의 균형을 추구합니다.' },
  aggressive: { name: '공격형', desc: '높은 변동성을 감수하고 수익을 추구합니다.' },
};

// ── 종목 마스터 ──
export const STOCKS = {
  NVDA: { name: '엔비디아', sector: '반도체·AI', sectorCode: 'SEMI', sent: 'pos', chg: '+8.4%', issues: 2, desc: '데이터센터 실적 호조 · 반도체 섹터 강세' },
  AVGO: { name: '브로드컴', sector: '반도체·AI', sectorCode: 'SEMI', sent: 'pos', chg: '+4.1%', issues: 1, desc: 'AI 네트워킹 칩 수요 확대' },
  AMD: { name: 'AMD', sector: '반도체·AI', sectorCode: 'SEMI', sent: 'pos', chg: '+3.2%', issues: 2, desc: 'AI 가속기 수요 기대감' },
  AAPL: { name: '애플', sector: '빅테크', sectorCode: 'BIGTECH', sent: 'neu', chg: '+0.4%', issues: 1, desc: '신제품 출시 루머 · 특이 이슈 적음' },
  MSFT: { name: '마이크로소프트', sector: '빅테크', sectorCode: 'BIGTECH', sent: 'pos', chg: '+1.9%', issues: 1, desc: '클라우드 매출 견조 · AI 코파일럿 확대' },
  AMZN: { name: '아마존', sector: '빅테크', sectorCode: 'BIGTECH', sent: 'pos', chg: '+1.2%', issues: 1, desc: 'AWS 성장 재가속' },
  GOOGL: { name: '알파벳', sector: '빅테크', sectorCode: 'BIGTECH', sent: 'neu', chg: '+0.7%', issues: 1, desc: '광고 매출 회복 조짐' },
  NFLX: { name: '넷플릭스', sector: '빅테크', sectorCode: 'BIGTECH', sent: 'pos', chg: '+2.5%', issues: 1, desc: '광고요금제 가입자 확대' },
  META: { name: '메타', sector: '빅테크', sectorCode: 'BIGTECH', sent: 'warn', chg: '-1.4%', issues: 2, desc: 'AI 투자 비용 부담 우려' },
  TSLA: { name: '테슬라', sector: '전기차', sectorCode: 'EV', sent: 'warn', chg: '-3.1%', issues: 3, desc: '인도량 둔화 우려 · 가격 정책 변경' },
};

export const DETAILS = {
  NVDA: { pos: ['데이터센터 매출 전분기 대비 12% 증가', '금리 인하 시사로 밸류에이션 부담 완화 기대'], neg: [], watch: ['단기 밸류에이션 고평가 논란'],
    cites: ['Reuters — 엔비디아 데이터센터 실적 발표', 'CNBC — 반도체 섹터 강세 분석'] },
  TSLA: { pos: [], neg: ['4분기 인도량 컨센서스 하회 전망'], watch: ['주간 인도 데이터 발표', '가격 정책 변경 여부'],
    cites: ['Bloomberg — 테슬라 인도량 전망 하향'] },
  AAPL: { pos: [], neg: [], watch: ['신제품 출시 루머 검증 필요', '특이 이슈 적어 관망 구간'],
    cites: ['MacRumors — 신제품 루머 정리'] },
};

export function genericDetail(t) {
  const s = STOCKS[t];
  return {
    pos: s.sent === 'pos' ? [s.desc] : [],
    neg: s.sent === 'warn' ? [s.desc] : [],
    watch: s.sent === 'neu' ? [s.desc] : ['추가 뉴스 확인 필요'],
    cites: ['관련 뉴스 요약'],
  };
}

export const SECTORS = {
  '반도체·AI': { code: 'SEMI', chg: '+2.1%', desc: '반도체 업황 개선 기대감, 필라델피아 반도체지수(SOX) 동반 강세' },
  '빅테크': { code: 'BIGTECH', chg: '+0.9%', desc: '클라우드·광고 매출 견조, 대형주 전반 강세' },
  '전기차': { code: 'EV', chg: '-1.8%', desc: '인도량 둔화 우려로 섹터 전반 약세' },
};

export const OVERVIEW = {
  indices: [
    { name: '나스닥', chg: '+1.2%' }, { name: 'S&P 500', chg: '+0.8%' },
    { name: '필라델피아 반도체', chg: '+2.1%' }, { name: 'VIX 변동성', chg: '-3.4%' },
    { name: '미 국채 10년물', chg: '+0.05%p' },
  ],
  summary: '연준 위원의 금리 인하 시사 발언에 성장주가 강세로 마감했고, 반도체 섹터가 지수를 이끌었습니다. 변동성은 낮아졌습니다.',
  actions: ['반도체 섹터(SOX) 동반 흐름과 주요 종목 컨퍼런스콜 코멘트 확인', '미 국채 10년물 금리 방향 확인 (성장주 밸류에이션 영향)'],
};

export const PERIODS = {
  overnight: { label: '밤사이', since: '오늘 새벽 마감', mult: 1 },
  '3d': { label: '지난 3일', since: '7월 7일~10일', mult: 3 },
  week: { label: '지난주', since: '7월 3일~10일', mult: 5 },
};

export const SENT = { pos: ['긍정', 'pos'], warn: ['주의', 'warn'], neu: ['중립', 'neu'] };

// ── 종목별 추천 렌즈 (섹터 기반, 추천 이유 포함) ──
export const REC_LENS = {
  SEMI: {
    primary: { cats: ['SOX', 'US10Y', 'SEMI'], preset: 'VALUE',
      why: '반도체·AI 종목은 금리에 민감한 성장주 성격이 강해 미 국채 10년물과 반도체 지수(SOX)를 함께 보는 것이 중요하고, 업황 사이클이 길어 장기 가치투자 관점이 잘 맞습니다.' },
    alt: { cats: ['SOX', 'SEMI'], preset: 'MOMENTUM',
      why: '반도체는 실적 서프라이즈와 수급에 따라 단기 변동성이 크기 때문에, 촉매 이벤트를 빠르게 포착하는 모멘텀 관점도 유효합니다.' },
  },
  BIGTECH: {
    primary: { cats: ['NASDAQ', 'US10Y', 'BIGTECH'], preset: 'MACRO',
      why: '빅테크는 나스닥 지수와 동조화가 강하고 금리 변화에 밸류에이션이 민감해, 거시 지표를 함께 보는 냉정한 시각이 유리합니다.' },
    alt: { cats: ['NASDAQ', 'BIGTECH'], preset: 'FACT',
      why: '해석보다 실적·발표 사실 자체를 빠르게 확인하고 싶다면 팩트 브리핑이 더 적합합니다.' },
  },
  EV: {
    primary: { cats: ['RUT', 'FFR', 'EV'], preset: 'MOMENTUM',
      why: '전기차 섹터는 인도량·정책 변화에 따른 단기 변동성이 크고 중소형주 지수(러셀2000)·금리 흐름의 영향을 함께 받아 모멘텀 관점이 유효합니다.' },
    alt: { cats: ['EV'], preset: 'BEGINNER',
      why: '산업 배경 지식이 아직 낯설다면 용어를 풀어 설명하는 입문자용 렌즈로 먼저 감을 잡는 것을 추천합니다.' },
  },
  DEFAULT: {
    primary: { cats: ['NASDAQ', 'US10Y'], preset: 'FACT',
      why: '특정 섹터로 분류되지 않은 종목은 전체 시장 지수와 금리 흐름을 사실 위주로 참고하는 것이 무난합니다.' },
    alt: { cats: ['NASDAQ'], preset: 'BEGINNER',
      why: '생소한 종목이라면 입문자용 설명으로 배경부터 이해하는 것을 추천합니다.' },
  },
};

export function recFor(ticker) {
  return REC_LENS[STOCKS[ticker].sectorCode] || REC_LENS.DEFAULT;
}

export function defaultLens(ticker) {
  const r = recFor(ticker).primary;
  return { cats: new Set(r.cats), preset: r.preset, depth: 'standard', note: '', whyKey: 'primary' };
}

export function blankLens(note = '') {
  return { cats: new Set(), preset: null, depth: null, note, whyKey: null };
}

// 프롬프트 미리보기 — HTML 문자열 대신 구조화된 데이터로 반환하고 렌더링은 컴포넌트가 담당
export function buildPreview(lens) {
  const cats = [...lens.cats].map((c) => CATLABEL[c]);
  const catStr = cats.length ? cats.join(' · ') : '(카테고리 미선택)';
  if (!lens.preset) {
    return { placeholder: true, text: '카테고리와 성향을 선택하면\n프롬프트가 여기에 조립됩니다.' };
  }
  const p = PRESETS[lens.preset];
  const depth = lens.depth ? { brief: '요약', standard: '표준', deep: '심층' }[lens.depth] : '(심층도 미선택)';
  const noteLine = lens.note && lens.note.trim() ? '\n(참고 리포트/메모 반영)' : '';
  return { placeholder: false, catStr, presetName: p.name, persona: p.persona, depth, noteLine };
}
