/** 夜空背景（星星 + 星云光晕）。 */
export default function Sky() {
  return (
    <div className="sky" aria-hidden>
      <div className="stars" />
      <div className="stars two" />
      <div className="glow glow-violet" />
      <div className="glow glow-moon" />
    </div>
  );
}
