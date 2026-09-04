import type { AppState } from "../types";
import { formatClock } from "../utils/format";

/** 顶栏：品牌 + 时钟徽章 + 积分/连续打卡。 */
export default function TopBar({ view }: { view: AppState }) {
  const clock = formatClock(view.clock.demo_active ? view.clock.virtual_now : view.clock.real_now);

  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-logo">🌙</div>
        <div>
          <div className="brand-name">
            Sleep<span className="grad-text">Flow</span>
          </div>
          <div className="brand-sub">睡前 30 分钟智能助眠 Agent</div>
        </div>
      </div>
      <div className="top-chips">
        {clock && (
          <span className="chip" title={view.clock.demo_active ? "Demo 虚拟时间" : "当前时间"}>
            {view.clock.demo_active ? "🧪" : "🕐"} {clock.time}
          </span>
        )}
        <span className="chip gold" title="累计 Sleep Coins">
          🪙 {view.profile.total_coins}
        </span>
        <span className="chip" title="连续规律作息天数">
          🔥 {view.profile.streak_days} 天
        </span>
      </div>
    </header>
  );
}
