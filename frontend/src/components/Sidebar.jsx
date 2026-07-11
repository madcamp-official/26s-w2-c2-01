import Icon from './Icon.jsx';

export default function Sidebar({ active, onNav, theme, onToggleTheme, nickname, email, onLogout }) {
  return (
    <aside className="side">
      <div className="sidetop">
        <div className="brand">
          <div className="mk">
            <Icon size={20}>
              <path d="M3 17l6-6 4 4 8-8" />
              <path d="M17 7h4v4" />
            </Icon>
          </div>
          <div>
            <div className="nm">TRADE CHASER</div>
            <div className="sl">AI 미장 브리핑</div>
          </div>
        </div>
        <button
          className="themebtn"
          title={theme === 'dark' ? '라이트 모드로 전환' : '다크 모드로 전환'}
          onClick={onToggleTheme}
        >
          {theme === 'dark' ? (
            <Icon size={16}>
              <circle cx="12" cy="12" r="4" />
              <path d="M12 3v1M12 20v1M4.2 4.2l.7.7M19.1 19.1l.7.7M3 12h1M20 12h1M4.2 19.8l.7-.7M19.1 4.9l.7-.7" />
            </Icon>
          ) : (
            <Icon size={16}>
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </Icon>
          )}
        </button>
      </div>

      <nav className="nav">
        <a className={active === 'briefing' ? 'on' : ''} onClick={() => onNav('briefing')}>
          <Icon size={18}><path d="M3 12l2-2 4 4 5-6 7 8" /></Icon> 오늘의 브리핑
        </a>
        <a className={active === 'mypage' ? 'on' : ''} onClick={() => onNav('mypage')}>
          <Icon size={18}><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-7 8-7s8 3 8 7" /></Icon> 마이페이지
        </a>
      </nav>

      <div className="grow" />

      <div style={{ display: 'flex', gap: 8 }}>
        <div className="userbox" style={{ flex: 1 }} onClick={() => onNav('mypage')}>
          <div className="av">{(nickname || '?').slice(0, 2)}</div>
          <div>
            <div className="nm">{nickname}</div>
            <div className="em">{email}</div>
          </div>
        </div>
        <button className="iconbtn" title="로그아웃" onClick={onLogout}>
          <Icon size={16}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></Icon>
        </button>
      </div>
    </aside>
  );
}
