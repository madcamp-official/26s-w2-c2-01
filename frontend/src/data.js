// 순수 로컬 설정만 남긴다. 종목/카테고리/성향/브리핑 등 실제 데이터는 api.js를 통해 백엔드에서 가져온다.

export const chgClass = (c) => {
  if (c == null) return 'flat';
  const s = String(c);
  return s.startsWith('+') ? 'up' : s.startsWith('-') ? 'down' : 'flat';
};
export const fmtPct = (v) => (v == null ? null : `${v > 0 ? '+' : ''}${v.toFixed(1)}%`);

// 분석 성향(preset) 카드 아이콘 — code는 백엔드 analysis_presets.code와 동일 (MACRO/VALUE/MOMENTUM/FACT/BEGINNER)
export const PRESET_ICON = {
  MACRO: [{ type: 'path', d: 'M3 3v18h18' }, { type: 'path', d: 'M7 14l4-4 3 3 5-6' }],
  VALUE: [{ type: 'path', d: 'M12 2v20' }, { type: 'path', d: 'M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6' }],
  MOMENTUM: [{ type: 'path', d: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z' }],
  FACT: [{ type: 'path', d: 'M9 12l2 2 4-4' }, { type: 'circle', cx: 12, cy: 12, r: 9 }],
  BEGINNER: [{ type: 'path', d: 'M12 20h9' }, { type: 'path', d: 'M12 4a4 4 0 0 1 4 4c0 2-2 3-2 5' }],
};

export const INVESTOR_TYPES = {
  stable: { name: '안정형', desc: '변동성보다 안정적인 수익을 선호합니다.' },
  balanced: { name: '균형형', desc: '수익과 안정의 균형을 추구합니다.' },
  aggressive: { name: '공격형', desc: '높은 변동성을 감수하고 수익을 추구합니다.' },
};

// 백엔드 sentiment: "positive" | "neutral" | "negative" | null
export const SENT_LABEL = {
  positive: ['긍정', 'pos'],
  negative: ['주의', 'warn'],
  neutral: ['중립', 'neu'],
};

// 섹터 상세에서 빠르게 비교할 수 있는 미국 상장 대표 ETF.
// 백엔드의 sectors.name_en을 키로 사용해 화면 문구가 바뀌어도 매핑을 유지한다.
export const SECTOR_ETFS = {
  'Semiconductors & AI': ['SOXX', 'SMH', 'BOTZ'],
  'Technology & Software': ['XLK', 'VGT', 'IGV'],
  'Media & Internet': ['XLC', 'VOX', 'FDN'],
  'Consumer & Retail': ['XLY', 'XLP', 'XRT'],
  Automobiles: ['CARZ', 'DRIV', 'IDRV'],
  Financials: ['XLF', 'VFH', 'KRE'],
  'Health Care': ['XLV', 'VHT', 'XBI'],
  Energy: ['XLE', 'VDE', 'OIH'],
  Industrials: ['XLI', 'VIS', 'IYT'],
  Telecommunications: ['XLC', 'VOX', 'IYZ'],
  'Real Estate': ['XLRE', 'VNQ', 'IYR'],
  Materials: ['XLB', 'VAW', 'GDX'],
  Utilities: ['XLU', 'VPU', 'FUTY'],
};

// ── 종목별 추천 렌즈 (프론트 전용 휴리스틱 — 백엔드에 대응 엔드포인트 없음) ──
// cats는 실제 analysis_categories.code, preset은 실제 analysis_presets.code 기준
export const REC_LENS = {
  SEMI: {
    primary: { cats: ['SOX', 'US10Y', 'SEMI'], preset: 'VALUE',
      why: '반도체·AI 종목은 금리에 민감한 성장주 성격이 강해 미 국채 10년물과 반도체 지수(SOX)를 함께 보는 것이 중요하고, 업황 사이클이 길어 장기 가치투자 관점이 잘 맞습니다.' },
    alt: { cats: ['SOX', 'SEMI'], preset: 'MOMENTUM',
      why: '반도체는 실적 서프라이즈와 수급에 따라 단기 변동성이 크기 때문에, 촉매 이벤트를 빠르게 포착하는 모멘텀 관점도 유효합니다.' },
  },
  TECH: {
    primary: { cats: ['IXIC', 'US10Y', 'TECH'], preset: 'MACRO',
      why: '테크·소프트웨어 종목은 나스닥 지수와 동조화가 강하고 금리 변화에 밸류에이션이 민감해, 거시 지표를 함께 보는 냉정한 시각이 유리합니다.' },
    alt: { cats: ['IXIC', 'TECH'], preset: 'FACT',
      why: '해석보다 실적·발표 사실 자체를 빠르게 확인하고 싶다면 팩트 브리핑이 더 적합합니다.' },
  },
  MEDIA: {
    primary: { cats: ['IXIC', 'MEDIA', 'EARNINGS'], preset: 'FACT',
      why: '미디어·인터넷 종목은 광고 매출·이용자 지표 등 실적 발표에 따른 변동이 커 사실 위주로 확인하는 것이 유용합니다.' },
    alt: { cats: ['IXIC', 'MEDIA'], preset: 'MACRO',
      why: '나스닥 지수와 동조화되고 금리에 밸류에이션이 민감한 성장주 성격도 있어 거시 관점도 함께 참고할 만합니다.' },
  },
  AUTO: {
    primary: { cats: ['RUT', 'FFR', 'AUTO'], preset: 'MOMENTUM',
      why: '자동차 섹터는 인도량·정책 변화에 따른 단기 변동성이 크고 중소형주 지수(러셀2000)·금리 흐름의 영향을 함께 받아 모멘텀 관점이 유효합니다.' },
    alt: { cats: ['AUTO'], preset: 'BEGINNER',
      why: '산업 배경 지식이 아직 낯설다면 용어를 풀어 설명하는 입문자용 렌즈로 먼저 감을 잡는 것을 추천합니다.' },
  },
  INDUST: {
    primary: { cats: ['PMI', 'GDP', 'INDUST'], preset: 'MACRO',
      why: '산업재는 경기 사이클과 제조업 지표(PMI)에 밀접하게 연동돼 거시 흐름을 함께 보는 것이 중요합니다.' },
    alt: { cats: ['INDUST'], preset: 'VALUE',
      why: '경기 순환에도 불구하고 장기적으로는 펀더멘털에 수렴하는 경향이 있어 가치투자 관점도 유효합니다.' },
  },
  TELECOM: {
    primary: { cats: ['TELECOM', 'DIVIDEND'], preset: 'VALUE',
      why: '통신주는 안정적인 현금흐름과 배당 매력이 있어 장기 가치투자 관점이 잘 맞습니다.' },
    alt: { cats: ['TELECOM'], preset: 'FACT',
      why: '설비투자·요금제 변화 등 사실 자체를 빠르게 확인하고 싶다면 팩트 브리핑이 적합합니다.' },
  },
  REALESTATE: {
    primary: { cats: ['US10Y', 'REALESTATE'], preset: 'MACRO',
      why: '부동산(리츠 등)은 금리 변화에 밸류에이션이 직접적으로 반응해 거시 지표 위주로 보는 것이 효과적입니다.' },
    alt: { cats: ['REALESTATE', 'DIVIDEND'], preset: 'VALUE',
      why: '배당 매력이 있는 부동산 종목이라면 장기 가치투자 관점으로 접근하는 것도 유효합니다.' },
  },
  MATERIALS: {
    primary: { cats: ['MATERIALS', 'GEOPOL'], preset: 'MACRO',
      why: '소재 섹터는 원자재 가격과 지정학 이슈에 크게 좌우되어 거시 흐름을 함께 보는 것이 중요합니다.' },
    alt: { cats: ['MATERIALS'], preset: 'FACT',
      why: '원자재 가격·생산량 등 사실 위주로 빠르게 확인하고 싶다면 팩트 브리핑이 적합합니다.' },
  },
  UTIL: {
    primary: { cats: ['UTIL', 'US10Y'], preset: 'VALUE',
      why: '유틸리티는 안정적인 현금흐름과 배당이 특징이지만 금리에 밸류에이션이 민감해 장기 가치투자 관점이 유효합니다.' },
    alt: { cats: ['UTIL', 'DIVIDEND'], preset: 'MACRO',
      why: '금리 흐름에 따른 밸류에이션 변화를 함께 보고 싶다면 거시 분석 관점도 참고할 만합니다.' },
  },
  FIN: {
    primary: { cats: ['FFR', 'US10Y', 'FIN'], preset: 'MACRO',
      why: '금융주는 기준금리·장단기 금리차의 영향을 직접적으로 받아 거시 지표 위주로 보는 것이 효과적입니다.' },
    alt: { cats: ['FIN', 'EARNINGS'], preset: 'FACT',
      why: '분기 실적 발표에 따른 변동이 커 사실 위주로 확인하고 싶다면 팩트 브리핑이 적합합니다.' },
  },
  HEALTH: {
    primary: { cats: ['HEALTH', 'EARNINGS'], preset: 'VALUE',
      why: '헬스케어는 임상·승인 이슈로 변동이 있지만 장기적으로는 펀더멘털에 수렴하는 경향이 있어 가치투자 관점이 유효합니다.' },
    alt: { cats: ['HEALTH'], preset: 'BEGINNER',
      why: '의학·규제 용어가 낯설다면 입문자용 렌즈로 배경부터 이해하는 것을 추천합니다.' },
  },
  ENERGY: {
    primary: { cats: ['ENERGY', 'GEOPOL'], preset: 'MACRO',
      why: '에너지 섹터는 지정학 이슈와 원자재 가격에 크게 좌우되어 거시 흐름을 함께 보는 것이 중요합니다.' },
    alt: { cats: ['ENERGY', 'DIVIDEND'], preset: 'VALUE',
      why: '배당 매력이 있는 에너지주라면 장기 가치투자 관점으로 접근하는 것도 유효합니다.' },
  },
  CONSUMER: {
    primary: { cats: ['CONSUMER', 'CPI'], preset: 'FACT',
      why: '소비재는 물가·소비 지표와 직결되어 사실 위주로 빠르게 확인하는 것이 유용합니다.' },
    alt: { cats: ['CONSUMER'], preset: 'BEGINNER',
      why: '소비재 산업이 처음이라면 입문자용 렌즈로 배경부터 살펴보는 것을 추천합니다.' },
  },
  DEFAULT: {
    primary: { cats: ['IXIC', 'US10Y'], preset: 'FACT',
      why: '특정 섹터로 분류되지 않은 종목은 전체 시장 지수와 금리 흐름을 사실 위주로 참고하는 것이 무난합니다.' },
    alt: { cats: ['IXIC'], preset: 'BEGINNER',
      why: '생소한 종목이라면 입문자용 설명으로 배경부터 이해하는 것을 추천합니다.' },
  },
};

export function recFor(sectorCode) {
  return REC_LENS[sectorCode] || REC_LENS.DEFAULT;
}

export function defaultLens(sectorCode) {
  const r = recFor(sectorCode).primary;
  return { cats: new Set(r.cats), preset: r.preset, depth: 'standard', note: '', whyKey: 'primary' };
}

export function blankLens(note = '') {
  return { cats: new Set(), preset: null, depth: null, note, whyKey: null };
}

// 프롬프트 미리보기 — catLabel: {code -> name_ko} (fetch된 analysis_categories에서 구성), presets: {code -> {name_ko, persona_text}}
export function buildPreview(lens, catLabel, presets) {
  const cats = [...lens.cats].map((c) => catLabel[c] || c);
  const catStr = cats.length ? cats.join(' · ') : '(카테고리 미선택)';
  if (!lens.preset || !presets[lens.preset]) {
    return { placeholder: true, text: '카테고리와 성향을 선택하면\n프롬프트가 여기에 조립됩니다.' };
  }
  const p = presets[lens.preset];
  const depth = lens.depth ? { brief: '요약', standard: '표준', deep: '심층' }[lens.depth] : '(심층도 미선택)';
  const noteLine = lens.note && lens.note.trim() ? '\n(참고 리포트/메모 반영)' : '';
  return { placeholder: false, catStr, presetName: p.name_ko, persona: p.persona_text, depth, noteLine };
}
