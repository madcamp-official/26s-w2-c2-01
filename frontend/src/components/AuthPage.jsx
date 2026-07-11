import { useState } from 'react';
import Icon from './Icon.jsx';
import { register, login, ApiError } from '../api.js';

export default function AuthPage({ onAuthed }) {
  const [mode, setMode] = useState('login'); // login | register
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [nickname, setNickname] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = mode === 'login'
        ? await login(email, password)
        : await register(email, password, nickname);
      onAuthed(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="layout" style={{ alignItems: 'center', justifyContent: 'center' }}>
      <div className="block" style={{ width: 360, maxWidth: '90vw' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
          <div className="mk" style={{ width: 34, height: 34, borderRadius: 10, background: 'var(--accent)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon size={20}><path d="M3 17l6-6 4 4 8-8" /><path d="M17 7h4v4" /></Icon>
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700 }}>TRADE CHASER</div>
            <div style={{ fontSize: 11, color: 'var(--t3)' }}>AI 미장 브리핑</div>
          </div>
        </div>

        <div className="ptabs" style={{ marginBottom: 18 }}>
          <button className={mode === 'login' ? 'on' : ''} onClick={() => { setMode('login'); setError(''); }}>로그인</button>
          <button className={mode === 'register' ? 'on' : ''} onClick={() => { setMode('register'); setError(''); }}>회원가입</button>
        </div>

        <form onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="group">
              <div className="group-t">닉네임</div>
              <input className="field" style={{ maxWidth: 'none' }} value={nickname} onChange={(e) => setNickname(e.target.value)} required />
            </div>
          )}
          <div className="group">
            <div className="group-t">이메일</div>
            <input className="field" style={{ maxWidth: 'none' }} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="group">
            <div className="group-t">비밀번호</div>
            <input className="field" style={{ maxWidth: 'none' }} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={4} />
          </div>

          {error && (
            <div className="strip" style={{ background: 'var(--neg-bg)', color: 'var(--neg)' }}>{error}</div>
          )}

          <button className="btn primary" type="submit" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
            {loading ? '처리 중…' : mode === 'login' ? '로그인' : '회원가입'}
          </button>
        </form>
      </div>
    </div>
  );
}
