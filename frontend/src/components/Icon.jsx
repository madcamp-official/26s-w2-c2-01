// 공통 아이콘 래퍼. 대부분은 children으로 <path>/<circle>을 직접 넘기고,
// PRESETS처럼 목록을 순회하며 그리는 경우엔 shapes(data.js의 PRESET_ICON) prop을 사용한다.
export default function Icon({ size = 17, children, shapes }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {shapes
        ? shapes.map((s, i) =>
            s.type === 'circle'
              ? <circle key={i} cx={s.cx} cy={s.cy} r={s.r} />
              : <path key={i} d={s.d} />
          )
        : children}
    </svg>
  );
}
