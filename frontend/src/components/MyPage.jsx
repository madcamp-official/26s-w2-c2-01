import { useState, useEffect } from 'react';
import { INVESTOR_TYPES } from '../data.js';
import { updateMe, ApiError } from '../api.js';
import Icon from './Icon.jsx';

export default function MyPage({ user, onUserUpdated, watch, stocksByTicker, getLens, presetsByCode, onRemove, onOpenLens, onNav }) {
  const [nickname, setNickname] = useState(user.nickname);
  const [investorType, setInvestorType] = useState(user.investor_type);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setNickname(user.nickname);
    setInvestorType(user.investor_type);
  }, [user]);

  async function handleSave() {
    setError('');
    setSaving(true);
    try {
      const updated = await updateMe({ nickname, investor_type: investorType });
      onUserUpdated(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 1200);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : '저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="maxw">
      <div className="block">
        <div className="block-h"><h2>프로필</h2></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <div className="avatarlg">{(nickname || '?').slice(0, 2)}</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>{nickname}</div>
            <div style={{ fontSize: 12, color: 'var(--t3)' }}>{user.email}</div>
          </div>
        </div>
        <div className="group">
          <div className="group-t">닉네임</div>
          <input className="field" value={nickname} onChange={(e) => setNickname(e.target.value)} />
        </div>
        <div className="group">
          <div className="group-t">투자 성향</div>
          <div className="chips">
            {Object.entries(INVESTOR_TYPES).map(([k, v]) => (
              <span key={k} className={`chip ${investorType === k ? 'on' : ''}`} onClick={() => setInvestorType(k)}>{v.name}</span>
            ))}
          </div>
          <p className="hint2" style={{ marginTop: 8 }}>{INVESTOR_TYPES[investorType]?.desc}</p>
        </div>
        {error && <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)' }}>{error}</div>}
        <button className="btn primary" onClick={handleSave} disabled={saving}>
          {saving ? '저장 중…' : saved ? '저장됨 ✓' : '프로필 저장'}
        </button>
      </div>

      <div className="block">
        <div className="block-h"><h2>관심종목</h2><span className="hint">{watch.length}개</span></div>
        <div className="rows">
          {watch.length ? watch.map((t) => {
            const s = stocksByTicker[t];
            if (!s) return null;
            const lens = getLens(t);
            const preset = lens.preset ? presetsByCode[lens.preset] : null;
            return (
              <div key={t} className="srow" style={{ cursor: 'pointer' }} onClick={() => onOpenLens(t)}>
                <div className="m">
                  <div className="tk">
                    <span className="sym">{t}</span>
                    <span className="sec">{s.name_ko || s.name_en} · {s.sector?.name_ko ?? '섹터 미지정'}</span>
                  </div>
                  <div className="lensbadge">
                    <Icon size={12}><path d="M4 6h16M7 12h10M10 18h4" /></Icon> {preset ? preset.name_ko : '미설정'} · 카테고리 {lens.cats.size}개
                  </div>
                </div>
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
