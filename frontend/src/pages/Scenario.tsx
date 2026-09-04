import { useState } from "react";
import { activatePlan, chooseScenario, fetchPlanDraft } from "../api/endpoints";
import PlanAskModal from "../components/PlanAskModal";
import SleepPrepModal, { type SleepContentChoice } from "../components/SleepPrepModal";
import type { AppState } from "../types";

interface Props {
  run: (fn: () => Promise<AppState>) => Promise<boolean>;
  sessionId: number;
  notify: (msg: string, kind?: "ok" | "err") => void;
}

const SCENARIOS = [
  {
    key: "shorts",
    icon: "📱",
    name: "正在刷短视频",
    desc: "越刷越清醒，大脑被多巴胺牵着走",
    tip: "三阶段循循善诱，帮你从被动刷切换到主动听",
    prompt: "稍作休息？还是继续沉浸一会儿？",
  },
  {
    key: "working",
    icon: "💻",
    name: "仍在工作 / 加班",
    desc: "大脑高速运转，还没切换到休息状态",
    tip: "帮你收尾、关机，给大脑一个休息仪式",
    prompt: "给大脑一个关机仪式吧",
  },
  {
    key: "ready",
    icon: "🛏️",
    name: "已准备休息",
    desc: "洗漱完毕，已经躺好准备入睡",
    tip: "选择一段喜欢的声音陪你入睡（可选）",
    prompt: "选一段喜欢的声音陪你入睡",
  },
];

/** 页面 2：Scenario —— 当前状态选择（Mock 模拟真实手机环境）。
 *  选择「已准备休息」也走：深夜计划询问（是/否）→ 助眠模式选择。
 */
export default function Scenario({ run, sessionId, notify }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const [askPlan, setAskPlan] = useState(false);
  const [askSleep, setAskSleep] = useState(false);
  const [planCount, setPlanCount] = useState<number | null>(null);

  async function pick(key: string) {
    // 「已准备休息」直接入睡：先询问深夜计划，再选择助眠声音
    if (key === "ready") {
      setBusy("open");
      try {
        const draft = await fetchPlanDraft();
        setPlanCount(draft.tasks.length);
        setAskPlan(true);
      } catch (e) {
        setBusy(null);
        return;
      }
      setBusy(null);
      return;
    }
    setBusy(key);
    const ok = await run(() => chooseScenario(key));
    if (!ok) setBusy(null);
  }

  async function chooseNoPlan() {
    setAskPlan(false);
    setAskSleep(true);
  }

  async function chooseYesPlan() {
    setAskPlan(false);
    setBusy("activate");
    try {
      await activatePlan(sessionId);
      notify("深夜计划已启动 🌙 任务已交给 Agent", "ok");
      setAskSleep(true);
    } catch (e) {
      notify(e instanceof Error ? e.message : "启动失败", "err");
    } finally {
      setBusy(null);
    }
  }

  async function confirmSleep(choice: SleepContentChoice) {
    setAskSleep(false);
    setBusy("ready");
    const ok = await run(() => chooseScenario("ready", choice));
    if (!ok) setBusy(null);
  }

  return (
    <div className="page">
      <div style={{ textAlign: "center", marginBottom: 18 }}>
        <h1 className="h1">你现在处于什么状态？</h1>
        <p className="sub" style={{ marginTop: 8 }}>
          为了给出更合适的引导，告诉我此刻的你 —— 请如实选择
        </p>
      </div>

      {SCENARIOS.map((s) => (
        <button
          key={s.key}
          className="card"
          onClick={() => pick(s.key)}
          disabled={busy !== null || askPlan || askSleep}
          style={{
            display: "block",
            width: "100%",
            textAlign: "left",
            color: "var(--ink)",
            fontFamily: "inherit",
            cursor: "pointer",
            transition: "transform .18s ease, border-color .18s ease, background .18s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-3px)";
            e.currentTarget.style.borderColor = "rgba(142,168,255,.5)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "none";
            e.currentTarget.style.borderColor = "";
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: 16,
                display: "grid",
                placeItems: "center",
                fontSize: 28,
                background: "rgba(255,255,255,.07)",
                border: "1px solid rgba(255,255,255,.1)",
                flexShrink: 0,
              }}
            >
              {s.icon}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 17, fontWeight: 700 }}>
                {s.name}
                {busy === s.key && (
                  <span style={{ marginLeft: 10, fontSize: 13, color: "var(--accent)" }}>
                    ● 处理中…
                  </span>
                )}
              </div>
              <div className="sub" style={{ marginTop: 3 }}>
                {s.desc}
              </div>
              <div className="muted" style={{ marginTop: 5 }}>
                💡 {s.tip}
              </div>
            </div>
            <div style={{ fontSize: 20, color: "var(--accent)" }}>›</div>
          </div>
        </button>
      ))}

      <div className="ai-note" style={{ marginTop: 18 }}>
        ✨ <b>AI 能力（规划中）：</b>接入 LLM 后，将根据此刻场景与历史行为，
        智能判断你的状态并选择更合适的引导策略。
      </div>

      <p className="muted" style={{ textAlign: "center", marginTop: 14 }}>
        MVP 阶段以 Mock 模拟真实手机环境，后续将接入真实设备数据
      </p>

      {askPlan && (
        <PlanAskModal
          busy={busy === "activate"}
          taskCount={planCount}
          onYes={chooseYesPlan}
          onNo={chooseNoPlan}
          onClose={() => setAskPlan(false)}
        />
      )}

      {askSleep && (
        <SleepPrepModal
          title="准备休息"
          subtitle="需要一点声音陪你入睡吗？（不会再自动播放）"
          busy={busy === "ready"}
          onConfirm={confirmSleep}
          onCancel={() => setAskSleep(false)}
        />
      )}
    </div>
  );
}
