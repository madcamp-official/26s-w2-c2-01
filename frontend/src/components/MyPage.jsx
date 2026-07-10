import { useState } from 'react';
import { STOCKS, PRESETS, SENT, INVESTOR_TYPES, chgClass } from '../data.js';
import Icon from './Icon.jsx';

export default function MyPage({ profile, setProfile, watch, getLens, onRemove, onOpenLens, onNav }) {
  const [saved, setSaved] = useState(false);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 1200);
  }

  return (
    <div className="maxw">
      <div className="block">
        <div className="block-h"><h2>프로필</h2></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <div className="avatarlg">GH</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>{profile.nickname}</div>
            <div style={{ fontSize: 12, color: 'var(--t3)' }}>{profile.email}</div>
          </div>
        </div>
        <div className="group">
          <div className="group-t">닉네임</div>
          <input
            className="field"
            value={profile.nickname}
            onChange={(e) => setProfile((p) => ({ ...p, nickname: e.target.value }))}
          />
        </div>
        <div className="group">
          <div className="group-t">투자 성향</div>
          <div className="chips">
            {Object.entries(INVESTOR_TYPES).map(([k, v]) => (
              <span
                key={k}
                className={`chip ${profile.investorType === k ? 'on' : ''}`}
                onClick={() => setProfile((p) => ({ ...p, investorType: k }))}
              >{v.name}</span>
            ))}
          </div>
          <p className="hint2" style={{ marginTop: 8 }}>{INVESTOR_TYPES[profile.investorType].desc}</p>
        </div>
        <button className="btn primary" onClick={handleSave}>{saved ? '저장됨 ✓' : '프로필 저장'}</button>
      </div>

      <div className="block">
        <div className="block-h"><h2>관심종목</h2><span className="hint">{watch.length}개</span></div>
        <div className="rows">
          {watch.length ? watch.map((t) => {
            const s = STOCKS[t];
            const [lbl, cls] = SENT[s.sent];
            const lens = getLens(t);
            const pname = lens.preset ? PRESETS[lens.preset].name : '미설정';
            return (
              <div key={t} className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenLens(t)}>
                <div className="m">
                  <div className="tk">
                    <span className="sym">{t}</span>
                    <span className={`tag ${cls}`}>{lbl}</span>
                    <span className="sec">{s.name} · {s.sector}</span>
                  </div>
                  <div className="desc">{s.desc}</div>
                  <div className="lensbadge">
                    <Icon size={12}><path d="M4 6h16M7 12h10M10 18h4" /></Icon> {pname} · 카테고리 {lens.cats.size}개
                  </div>
                </div>
                <div className="chg"><div className={`pct ${chgClass(s.chg)}`}>{s.chg}</div></div>
                <button
                  className="iconbtn"
                  title="삭제"
                  onClick={(e) => { e.stopPropagation(); onRemove(t); }}
                >
                  <Icon size={16}><path d="M18 6L6 18M6 6l12 12" /></Icon>
                </button>
              </div>
            );
          }) : <div className="strip">아직 관심종목이 없습니다.</div>}
        </div>
        <div className="hint2" style={{ marginTop: 14 }}>
          종목을 클릭하면 해당 종목의 분석 렌즈로 이동합니다. 종목 추가는{' '}
          <span
            style={{ color: 'var(--accent)', cursor: 'pointer', textDecoration: 'underline' }}
            onClick={() => onNav('briefing')}
          >오늘의 브리핑</span>
          에서 검색으로 할 수 있습니다.
        </div>
      </div>
    </div>
  );
}
