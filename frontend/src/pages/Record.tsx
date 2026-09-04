import { useEffect, useState } from "react";
import { fetchHistory } from "../api/endpoints";
import type { AppState, HistoryItem } from "../types";
import { formatClock } from "../utils/format";

interface Props {
  view: AppState;
  onBack: () => void;
  notify: (msg: string, kind?: "ok" | "err") => void;
}

/** 页面 6：睡眠记录与 AI 睡眠建议。 */
export default function Record({ view, onBack, notify }: Props) {
  const [history, setHistory] = useState<HistoryItem[] | null>(null);
  const p = view.profile;
  const demoMode = view.clock.demo_active;

  useEffect(() => {
    fetchHistory()
      .then((r) => setHistory(r.items))
      .catch((e) => notify(e instanceof Error ? e.message : "加载失败", "err"));
  }, [notify]);

  return (
    <div className="page">
      {/* 顶部 */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button className="btn ghost sm" onClick={onBack}>
          ‹ 返回
        </button>
        <h1 className="h1" style={{ fontSize: 22 }}>
          📊 睡眠记录与建议
        </h1>
      </div>

      {/* 统计 */}
      <section className="card" style={{ marginTop: 16 }}>
        <div className="stats">
          <div className="stat">
            <div className="num grad-text">{p.streak_days}</div>
            <div className="lbl">连续打卡（天）</div>
          </div>
          <div className="stat">
            <div className="num grad-text">{p.completed_nights}</div>
            <div className="lbl">累计完成（晚）</div>
          </div>
          <div className="stat">
            <div className="num grad-text">{p.total_coins}</div>
            <div className="lbl">Sleep Coins 🪙</div>
          </div>
        </div>
        <div className="muted" style={{ marginTop: 12, textAlign: "center", fontSize: 11.5 }}>
          积分按累计完成晚数发放（每晚安睡 +10，断签不清零）；连续打卡为最近不间断天数 ——
          两者独立统计，明细见下方记录
        </div>
      </section>

      {/* AI 睡眠建议 */}
      <section className="card" style={{ marginTop: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 18 }}>🤖</span>
          <b style={{ fontSize: 16 }}>AI 睡眠建议</b>
          <span className="tag ai">AI · 规划中</span>
        </div>
        <p className="muted" style={{ marginTop: 6 }}>
          当前为规则引擎生成的通用建议；接入 LLM 后将结合你的作息记录生成个性化分析
        </p>
        <ul style={{ marginTop: 12, display: "grid", gap: 9, listStyle: "none" }}>
          <Suggestion
            icon="⏰"
            text={
              demoMode
                ? `固定作息优先：目标 ${p.weekday_bedtime} 入睡 / ${p.weekday_wake} 起床，误差尽量控制在 30 分钟内`
                : `固定作息优先：目标 ${p.weekday_bedtime} 入睡 / ${p.weekday_wake} 起床`
            }
          />
          <Suggestion
            icon="📵"
            text="睡前 1 小时关闭短视频 / 工作消息，蓝光会抑制褪黑素分泌"
          />
          <Suggestion
            icon="🧘"
            text="入睡困难时，尝试 4-7-8 呼吸法：吸气 4s — 屏息 7s — 呼气 8s"
          />
          <Suggestion
            icon="📈"
            text="记录周平均入睡偏差，若连续 3 天晚于 24:00，AI 将提醒你调整节奏（接入后生效）"
          />
        </ul>
      </section>

      {/* 历史列表 */}
      <section className="card" style={{ marginTop: 16 }}>
        <div className="h2" style={{ fontSize: 16 }}>
          📜 睡眠历史
        </div>
        {history === null ? (
          <p className="muted" style={{ marginTop: 12, textAlign: "center" }}>
            加载中…
          </p>
        ) : history.length === 0 ? (
          <p className="muted" style={{ marginTop: 16, textAlign: "center" }}>
            还没有睡眠记录 —— 完成一次「睡前 30 分钟」流程后，这里会展示历史
          </p>
        ) : (
          <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
            {history.map((h) => {
              const isMiss = h.kind === "miss";
              const deduct = isMiss && h.coins != null && h.coins < 0;
              return (
                <div
                  key={h.session_id ?? `miss-${h.date}-${h.reward_message}`}
                  style={{
                    padding: "13px 14px",
                    borderRadius: 14,
                    background: "rgba(255,255,255,.045)",
                    border: "1px solid rgba(255,255,255,.08)",
                    display: "flex",
                    gap: 12,
                    alignItems: "center",
                  }}
                >
                  <div style={{ fontSize: 24 }}>{isMiss ? "🚫" : h.scenario_icon || "🌙"}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 650 }}>
                      {formatClock(`${h.date} 08:00:00`)?.date ?? h.date}
                      <span className="muted" style={{ marginLeft: 8, fontSize: 12 }}>
                        {isMiss ? "助眠失败" : h.scenario_name || "未选场景"}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: "var(--ink-dim)", marginTop: 3 }}>
                      {isMiss ? h.reward_message ?? h.result : h.result}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    {h.coins != null ? (
                      deduct ? (
                        <div style={{ fontSize: 16, fontWeight: 800, color: "var(--danger)" }}>
                          {h.coins} 🪙
                        </div>
                      ) : (
                        <>
                          <div style={{ fontSize: 16, fontWeight: 800, color: "var(--gold)" }}>
                            +{h.coins} 🪙
                          </div>
                          <div className="muted" style={{ fontSize: 11 }}>
                            累计 {h.total_coins}
                          </div>
                        </>
                      )
                    ) : (
                      <div className="muted" style={{ fontSize: 12 }}>—</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function Suggestion({ icon, text }: { icon: string; text: string }) {
  return (
    <li style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
      <span style={{ fontSize: 17, flexShrink: 0 }}>{icon}</span>
      <span style={{ fontSize: 13.5, color: "var(--ink)", lineHeight: 1.7 }}>{text}</span>
    </li>
  );
}
