export default function TopBar({ crumb, title, children }) {
  return (
    <div className="topbar">
      <div>
        <div className="crumb">{crumb}</div>
        <h1>{title}</h1>
      </div>
      <div className="actions">{children}</div>
    </div>
  );
}
