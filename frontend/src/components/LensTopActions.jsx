import { useState } from 'react';
import Icon from './Icon.jsx';

export default function LensTopActions({ onReset, onRecommend }) {
  const [saved, setSaved] = useState(false);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 1200);
  }

  return (
    <>
      <button className="btn" onClick={onReset}>초기화</button>
      <button className="btn" onClick={onRecommend}>
        <Icon size={14}><path d="M12 2l3 6.5 7 .9-5 4.8 1.3 7L12 18l-6.6 3.2L6.7 14l-5-4.8 7-.9z" /></Icon>
        추천
      </button>
      <button className="btn primary" onClick={handleSave}>{saved ? '저장됨 ✓' : '저장'}</button>
    </>
  );
}
