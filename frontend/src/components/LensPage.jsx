import { CATS, CATLABEL, PRESETS, PRESET_ICON, recFor, buildPreview } from '../data.js';
import Icon from './Icon.jsx';

function CategoryGroup({ group, lens, isOpen, query, onToggleChip, onOpenSearch, onCloseSearch, onQueryChange, onPick }) {
  const selected = group.items.filter(([c]) => lens.cats.has(c));
  const q = query.trim().toLowerCase();
  const avail = group.items.filter(([c]) => !lens.cats.has(c));
  const filtered = q ? avail.filter(([c, l]) => c.toLowerCase().includes(q) || l.toLowerCase().includes(q)) : avail;

  return (
    <div className="group">
      <div className="group-t">{group.label}</div>
      <div className="chips">
        {selected.length === 0 && <span className="hint2" style={{ margin: '0 4px 0 0' }}>선택된 항목이 없습니다.</span>}
        {selected.map(([c, l]) => (
          <span key={c} className="chip on" onClick={() => onToggleChip(c)}>{l}</span>
        ))}
        <span
          className={`chip addchip${isOpen ? ' on' : ''}`}
          title={`${group.label} 추가`}
          onClick={onOpenSearch}
        >
          <Icon size={13}><path d="M12 5v14M5 12h14" /></Icon>
        </span>
      </div>

      {isOpen && (
        <div className="catsearch">
          <div className="searchbox" style={{ padding: '8px 12px' }}>
            <Icon size={14}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></Icon>
            <input
              type="text"
              placeholder={`${group.label} 검색`}
              value={query}
              autoComplete="off"
              autoFocus
              onChange={(e) => onQueryChange(e.target.value)}
            />
            <span className="closex" title="닫기" onClick={onCloseSearch}>
              <Icon size={13}><path d="M18 6L6 18M6 6l12 12" /></Icon>
            </span>
          </div>
          <div className="searchresults" style={{ marginTop: 6 }}>
            {!avail.length && <div className="hint2" style={{ padding: '6px 2px' }}>모든 항목을 추가했습니다.</div>}
            {avail.length > 0 && !filtered.length && <div className="hint2" style={{ padding: '6px 2px' }}>검색 결과가 없습니다.</div>}
            {filtered.map(([c, l]) => (
              <div key={c} className="searchrow" onClick={() => onPick(c)}>
                <div className="sm"><span className="sym">{l}</span></div>
                <span className="addbtn"><Icon size={13}><path d="M12 5v14M5 12h14" /></Icon></span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function LensPage({
  ticker, stock, lens, updateLens, onBack,
  catSearchOpen, setCatSearchOpen, catSearchQuery, setCatSearchQuery,
}) {
  const rec = recFor(ticker);
  const preview = buildPreview(lens);

  function toggleChip(code) {
    updateLens((l) => {
      const cats = new Set(l.cats);
      cats.has(code) ? cats.delete(code) : cats.add(code);
      return { ...l, cats, whyKey: null };
    });
  }
  function pickChip(groupKey, code) {
    updateLens((l) => {
      const cats = new Set(l.cats);
      cats.add(code);
      return { ...l, cats, whyKey: null };
    });
    setCatSearchQuery((q) => ({ ...q, [groupKey]: '' }));
  }
  function setPreset(code) {
    updateLens((l) => ({ ...l, preset: code, whyKey: null }));
  }
  function setDepth(val) {
    updateLens((l) => ({ ...l, depth: val, whyKey: null }));
  }
  function setNote(val) {
    updateLens((l) => ({ ...l, note: val }));
  }
  function applyRec(key) {
    updateLens((l) => {
      const r = rec[key];
      return { cats: new Set(r.cats), preset: r.preset, depth: 'standard', note: l.note, whyKey: key };
    });
  }

  return (
    <div className="lens-grid">
      <div>
        <div className="backlink" onClick={onBack}>
          <Icon size={15}><path d="M15 18l-6-6 6-6" /></Icon> 마이페이지로
        </div>
        <div className="crumbline">{ticker} · {stock.name} 분석 렌즈</div>

        <div className="recbox">
          <div className="rt">
            <Icon size={14}><path d="M12 2l3 6.5 7 .9-5 4.8 1.3 7L12 18l-6.6 3.2L6.7 14l-5-4.8 7-.9z" /></Icon>
            {stock.name}({stock.sector}) 추천 렌즈
          </div>
          <div className="rechips">
            <div className="rechip" onClick={() => applyRec('primary')}>
              <b>기본 추천</b>{rec.primary.cats.map((c) => CATLABEL[c]).join(' · ')} + {PRESETS[rec.primary.preset].name}
            </div>
            <div className="rechip alt" onClick={() => applyRec('alt')}>
              <b>대안 추천</b>{rec.alt.cats.map((c) => CATLABEL[c]).join(' · ')} + {PRESETS[rec.alt.preset].name}
            </div>
          </div>
        </div>

        <div className="block">
          <div className="block-h"><span className="num">1</span><h2>분석 카테고리</h2><span className="hint">그룹별 + 로 추가</span></div>
          {CATS.map((g) => (
            <CategoryGroup
              key={g.key}
              group={g}
              lens={lens}
              isOpen={!!catSearchOpen[g.key]}
              query={catSearchQuery[g.key] || ''}
              onToggleChip={toggleChip}
              onOpenSearch={() => {
                setCatSearchOpen((s) => ({ ...s, [g.key]: !s[g.key] }));
                setCatSearchQuery((q) => ({ ...q, [g.key]: '' }));
              }}
              onCloseSearch={() => setCatSearchOpen((s) => ({ ...s, [g.key]: false }))}
              onQueryChange={(val) => setCatSearchQuery((q) => ({ ...q, [g.key]: val }))}
              onPick={(code) => pickChip(g.key, code)}
            />
          ))}
        </div>

        <div className="block">
          <div className="block-h"><span className="num">2</span><h2>분석 성향</h2><span className="hint">하나 선택</span></div>
          <div className="cards">
            {Object.entries(PRESETS).map(([code, p]) => (
              <div key={code} className={`pcard ${lens.preset === code ? 'on' : ''}`} onClick={() => setPreset(code)}>
                <div className="chk"><Icon size={12}><path d="M20 6L9 17l-5-5" /></Icon></div>
                <div className="pi"><Icon size={17} shapes={PRESET_ICON[code]} /></div>
                <div className="pn">{p.name}</div>
                <div className="pd">{p.desc}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="block">
          <div className="block-h"><span className="num">3</span><h2>심층도</h2></div>
          <div className="seg" style={{ maxWidth: 280 }}>
            {[['brief', '요약'], ['standard', '표준'], ['deep', '심층']].map(([v, l]) => (
              <button key={v} className={lens.depth === v ? 'on' : ''} onClick={() => setDepth(v)}>{l}</button>
            ))}
          </div>
        </div>

        <div className="block">
          <div className="block-h"><h2>참고 리포트 · 메모</h2><span className="hint">선택</span></div>
          <p className="hint2">기본적으로 이 종목 관련 뉴스 스니펫을 근거로 분석합니다. 증권사 리포트나 메모를 붙여넣으면 지수·지표 해석에 함께 반영됩니다.</p>
          <textarea
            className="ta"
            placeholder="예: OO증권 리포트 요약, 실적 메모 등을 붙여넣으세요 (선택)"
            value={lens.note}
            onChange={(e) => setNote(e.target.value)}
          />
        </div>
      </div>

      <div className="rail">
        <div className="preview">
          <div className="pv-h"><Icon size={15}><path d="M9 6l-6 6 6 6M15 6l6 6-6 6" /></Icon> 조립된 렌즈 프롬프트</div>
          <code>
            {preview.placeholder ? preview.text : (
              <>
                이 문서를 <span className="hl">[{preview.catStr}]</span> 관점에서,{'\n'}
                <span className="hl">{preview.presetName}</span> 성향({preview.persona})으로{'\n'}
                <span className="hl">{preview.depth}</span> 분석해줘.{preview.noteLine}
              </>
            )}
          </code>
          <div className="lock">
            <Icon size={12}><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></Icon>
            근거 인용 필수 · 매매 지시 금지 (고정)
          </div>
        </div>

        {lens.whyKey && (
          <div className="whybox">
            <div className="wh">
              <Icon size={14}><circle cx="12" cy="12" r="10" /><path d="M12 16v-4" /><path d="M12 8h.01" /></Icon>
              왜 {lens.whyKey === 'primary' ? '기본 추천' : '대안 추천'}인가요?
            </div>
            <p className="wt">{rec[lens.whyKey].why}</p>
          </div>
        )}
      </div>
    </div>
  );
}
