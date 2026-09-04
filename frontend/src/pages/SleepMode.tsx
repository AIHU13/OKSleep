import { useEffect, useRef, useState } from "react";
import { demoAdvance, demoNextDay, settleReward } from "../api/endpoints";
import type { AppState, RewardData } from "../types";
import { formatSec, sleepProgress } from "../utils/format";

interface Props {
  view: AppState;
  run: (fn: () => Promise<AppState>) => Promise<boolean>;
  /** 静默刷新（不改变当前页面）。 */
  silentRefresh: () => Promise<void>;
  /** 领取奖励成功 -> 展示 Reward 页。 */
  onReward: (data: RewardData) => void;
  notify: (msg: string, kind?: "ok" | "err") => void;
}

/** 页面 4：Sleep Mode —— 模拟播放器 / 安静休息 + 入睡倒计时 / 睡眠成功。 */
export default function SleepMode({ view, run, silentRefresh, onReward, notify }: Props) {
  const session = view.session!;
  const success = session.state === "SLEEP_SUCCESS" || session.reward_ready;
  const content = session.content;
  const quiet = !content;
  const [busy, setBusy] = useState<string | null>(null);
  const [localSec, setLocalSec] = useState<number | null>(session.sleep.remaining_sec);

  // 服务端剩余时间变化时同步到本地
  useEffect(() => {
    setLocalSec(session.sleep.remaining_sec);
  }, [session.sleep.remaining_sec, session.state]);

  // 本地 1 秒倒计时（纯视觉）
  const timerRef = useRef<number | null>(null);
  useEffect(() => {
    if (success) return;
    timerRef.current = window.setInterval(() => {
      setLocalSec((s) => {
        if (s == null || s <= 0) {
          if (timerRef.current) window.clearInterval(timerRef.current);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [success, session.state]);

  // 服务端自动判定（模拟 1 小时真实流逝时由后端转为成功）
  useEffect(() => {
    if (success) return;
    const poll = window.setInterval(() => {
      void silentRefresh();
    }, 5000);
    return () => window.clearInterval(poll);
  }, [success, silentRefresh]);

  async function advance60() {
    setBusy("adv60");
    const ok = await run(() => demoAdvance(60));
    if (!ok) setBusy(null);
  }

  async function collect() {
    setBusy("collect");
    try {
      await demoNextDay(); // 模拟第二天
      const reward = await settleReward(session.session_id);
      onReward(reward);
      notify("奖励已到账 🎉", "ok");
    } catch (e) {
      notify(e instanceof Error ? e.message : "领取失败", "err");
    } finally {
      setBusy(null);
    }
  }

  /* ---------------- 睡眠成功 ---------------- */
  if (success) {
    return (
      <div className="page" style={{ textAlign: "center" }}>
        <section className="card">
          <div style={{ fontSize: 62, animation: "breathe 4s ease-in-out infinite" }}>😴</div>
          <h1 className="h1" style={{ marginTop: 12 }}>
            睡眠成功！
          </h1>
          <p className="sub" style={{ marginTop: 10 }}>
            已经 {session.sleep.elapsed_min ?? 60} 分钟没有使用手机
            <br />
            昨晚的睡前计划完成了，身体和精神都在好好充电
          </p>
          <div style={{ marginTop: 24 }}>
            <button className="btn gold block" disabled={!!busy} onClick={collect}>
              {busy === "collect" ? "● 处理中…" : "☀️ 模拟第二天 · 领取奖励"}
            </button>
          </div>
        </section>
        <p className="muted" style={{ marginTop: 16 }}>
          次日早晨将结算：+10 Sleep Coins 与连续打卡 +1
        </p>
        <div className="ai-note" style={{ marginTop: 16, textAlign: "left" }}>
          ✨ <b>AI 能力（规划中）：</b>接入 LLM 后，次日晨报将结合本次睡眠过程，
          为你生成<b>个性化睡眠小结与建议</b>。
        </div>
      </div>
    );
  }

  /* ---------------- 助眠播放中 / 安静休息 ---------------- */
  const progress = sleepProgress(localSec ?? session.sleep.remaining_sec);
  const isMusic = content?.type === "music" || content?.type === "noise";

  return (
    <div className="page">
      <div style={{ textAlign: "center" }}>
        <h1 className="h1" style={{ fontSize: 24 }}>
          🌙 Sleep Mode
        </h1>
        <p className="sub" style={{ marginTop: 6 }}>
          放下手机，接下来的 60 分钟交给{quiet ? "呼吸与安静" : "声音与呼吸"}
        </p>
      </div>

      {/* 播放器 / 安静模式 */}
      <section className="card" style={{ marginTop: 18, textAlign: "center" }}>
        {quiet ? (
          <>
            <div
              style={{
                width: 92,
                height: 92,
                margin: "6px auto 0",
                borderRadius: "50%",
                display: "grid",
                placeItems: "center",
                fontSize: 44,
                background: "radial-gradient(circle, rgba(142,168,255,.22), transparent 70%)",
                animation: "breathe 5s ease-in-out infinite",
              }}
            >
              🤫
            </div>
            <div style={{ fontSize: 18, fontWeight: 700, marginTop: 12 }}>安静休息模式</div>
            <div className="muted" style={{ marginTop: 4 }}>
              没有选择播放内容 · 跟随呼吸，慢慢入睡
            </div>
          </>
        ) : (
          <>
            <div style={{ fontSize: 46 }}>{content?.icon ?? "🎧"}</div>
            <div style={{ fontSize: 18, fontWeight: 700, marginTop: 10 }}>
              {content?.title ?? "未选择内容"}
            </div>
            <div className="muted" style={{ marginTop: 4 }}>
              {content?.subtitle ?? "助眠内容"}
              {content && ` · ${content.duration_min} 分钟`}
            </div>

            {/* 播放指示动画 */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 5,
                height: 44,
                marginTop: 14,
              }}
            >
              {[0, 1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  style={{
                    width: 5,
                    borderRadius: 3,
                    background: isMusic ? "var(--accent)" : "rgba(255,217,138,.85)",
                    height: "100%",
                    animation: `eq ${1 + (i % 3) * 0.25}s ease-in-out ${i * 0.12}s infinite alternate`,
                  }}
                />
              ))}
            </div>
          </>
        )}

        {/* 剩余时间 */}
        <div
          style={{
            marginTop: 16,
            padding: "14px 18px",
            borderRadius: 16,
            background: "rgba(255,255,255,.05)",
            border: "1px solid rgba(255,255,255,.07)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <span className="muted">模拟睡眠进行中</span>
            <span style={{ fontSize: 26, fontWeight: 800, fontVariantNumeric: "tabular-nums" }}>
              {formatSec(localSec)}
            </span>
          </div>
          <div
            style={{
              marginTop: 10,
              height: 8,
              borderRadius: 999,
              background: "rgba(255,255,255,.08)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${progress * 100}%`,
                height: "100%",
                borderRadius: 999,
                background: "linear-gradient(90deg, #8ea8ff, #b9a8ff, #ffd98a)",
                transition: "width .5s linear",
              }}
            />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
            <span className="muted" style={{ fontSize: 11 }}>
              已模拟 {session.sleep.elapsed_min ?? 0} / 60 分钟
            </span>
            <span className="muted" style={{ fontSize: 11 }}>
              连续 1 小时不使用手机即视为入睡
            </span>
          </div>
        </div>
      </section>

      {/* 操作 */}
      <section className="card" style={{ marginTop: 16 }}>
        <p className="sub" style={{ textAlign: "center" }}>
          MVP 使用模拟播放器；点击下方按钮模拟时间的流逝
        </p>
        <div className="btn-row">
          <button className="btn ghost" disabled={!!busy} onClick={() => void run(() => demoAdvance(6))}>
            ⏱️ 快进 6 分钟
          </button>
          <button className="btn" disabled={!!busy} onClick={advance60}>
            {busy === "adv60" ? "● 模拟中…" : "😴 模拟 1 小时未使用手机"}
          </button>
        </div>
        {!view.clock.demo_active && (
          <p className="muted" style={{ textAlign: "center", marginTop: 10 }}>
            未开启 Demo 时间时，请用上方按钮模拟等待
          </p>
        )}
      </section>

      <div className="ai-note" style={{ marginTop: 16 }}>
        ✨ <b>AI 能力（规划中）：</b>接入 LLM 后，助眠内容与入睡前的温馨提示，
        将结合你的作息规律与偏好由 AI <b>个性化生成与推荐</b>。
      </div>
    </div>
  );
}
