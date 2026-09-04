import { useState } from "react";

export type SleepContentChoice = "music" | "story" | "noise" | null;

interface Props {
  title: string;
  subtitle: string;
  busy: boolean;
  onConfirm: (choice: SleepContentChoice) => void;
  onCancel: () => void;
}

const OPTIONS: Array<{ type: SleepContentChoice; icon: string; title: string; desc: string }> = [
  { type: "music", icon: "🎵", title: "助眠音乐", desc: "钢琴 / 白噪音，舒缓身心" },
  { type: "story", icon: "📖", title: "睡前故事", desc: "温柔故事，转移注意力" },
  { type: null, icon: "🤫", title: "安静休息", desc: "不播放声音，跟随呼吸入睡" },
];

/**
 * 进入睡眠前的确认弹窗：询问是否开启助眠音乐 / 睡前故事（不自动播放）。
 * 底部注明：接入 AI 后，音乐与故事将结合作息与偏好做个性化推荐。
 */
export default function SleepPrepModal({ title, subtitle, busy, onConfirm, onCancel }: Props) {
  const [choice, setChoice] = useState<SleepContentChoice>("music");

  return (
    <div className="modal-mask" onClick={busy ? undefined : onCancel}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal>
        <h2 style={{ fontSize: 20, fontWeight: 700 }}>🌙 {title}</h2>
        <p className="sub" style={{ margin: "8px 0 16px" }}>
          {subtitle}
        </p>

        <div style={{ display: "grid", gap: 10 }}>
          {OPTIONS.map((opt) => (
            <button
              key={opt.type ?? "quiet"}
              type="button"
              className={`choice-card${choice === opt.type ? " sel" : ""}`}
              disabled={busy}
              onClick={() => setChoice(opt.type)}
            >
              <div className="choice-icon">{opt.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: 15 }}>{opt.title}</div>
                <div style={{ fontSize: 12.5, color: "var(--ink-dim)", marginTop: 2 }}>
                  {opt.desc}
                </div>
              </div>
              <span style={{ fontSize: 18, color: choice === opt.type ? "var(--gold)" : "var(--ink-faint)" }}>
                {choice === opt.type ? "◉" : "○"}
              </span>
            </button>
          ))}
        </div>

        <div className="ai-note" style={{ marginTop: 16 }}>
          ✨ <b>AI 能力（规划中）：</b>后续接入 LLM 后，将结合你的作息规律与历史偏好，
          为你<b>个性化推荐</b>最合适的助眠音乐与睡前故事。
        </div>

        <div className="btn-row" style={{ marginTop: 20 }}>
          <button className="btn ghost" disabled={busy} onClick={onCancel}>
            返回
          </button>
          <button className="btn gold" disabled={busy} onClick={() => onConfirm(choice)}>
            {busy ? "正在进入…" : "好，开始休息"}
          </button>
        </div>
      </div>
    </div>
  );
}
