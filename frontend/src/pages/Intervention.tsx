import { useState } from "react";
import { activatePlan, fetchPlanDraft, sendAction } from "../api/endpoints";
import PlanAskModal from "../components/PlanAskModal";
import SleepPrepModal, { type SleepContentChoice } from "../components/SleepPrepModal";
import type { AppState } from "../types";

interface Props {
  view: AppState;
  run: (fn: () => Promise<AppState>) => Promise<boolean>;
  notify: (msg: string, kind?: "ok" | "err") => void;
}

const TOMORROW_PLAN = [
  { time: "07:30", item: "起床 · 拉开窗帘晒太阳" },
  { time: "09:00", item: "工作 · 深度专注 2 小时" },
  { time: "12:30", item: "午餐 · 散步 20 分钟" },
  { time: "19:30", item: "运动 · 慢跑 / 拉伸" },
];

/** 页面 3：Intervention —— AI 提醒、阶段状态、用户操作（三阶段干预）。
 *  任意阶段点「好了，去休息」：先询问是否启动深夜计划（是/否），再选择助眠模式。
 */
export default function Intervention({ view, run, notify }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const [askPlan, setAskPlan] = useState(false);
  const [askSleep, setAskSleep] = useState(false);
  const [planCount, setPlanCount] = useState<number | null>(null);
  const session = view.session!;
  const stage = session.stage ?? 1;
  const isStage3 = session.state === "STAGE_3";
  const msg = session.message;

  async function act(action: string) {
    setBusy(action);
    const ok = await run(() => sendAction(action));
    if (!ok) setBusy(null);
  }

  /** 点击「好了，去休息」：第一步弹「是否启动深夜计划」。 */
  async function requestSleep() {
    setBusy("open");
    try {
      const draft = await fetchPlanDraft();
      setPlanCount(draft.tasks.length);
      setAskPlan(true);
    } catch (e) {
      notify(e instanceof Error ? e.message : "打开失败", "err");
    } finally {
      setBusy(null);
    }
  }

  async function chooseNoPlan() {
    setAskPlan(false);
    setAskSleep(true);
  }

  async function chooseYesPlan() {
    setAskPlan(false);
    setBusy("activate");
    try {
      await activatePlan(session.session_id);
      notify("深夜计划已启动 🌙 任务已交给 Agent", "ok");
      setAskSleep(true);
    } catch (e) {
      notify(e instanceof Error ? e.message : "启动失败", "err");
    } finally {
      setBusy(null);
    }
  }

  /** 第二步：选择助眠模式（音乐 / 故事 / 安静）后正式入睡。 */
  async function confirmSleep(choice: SleepContentChoice) {
    setAskSleep(false);
    setBusy("prepare_sleep");
    const ok = await run(() => sendAction("prepare_sleep", choice));
    if (!ok) setBusy(null);
  }

  return (
    <div className="page">
      {/* 场景与阶段提示 */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span className="chip" style={{ fontSize: 13 }}>
          {session.scenario_icon} {session.scenario_name}
        </span>
        <span className="chip">{session.stage_label || "干预中"}</span>
      </div>

      {/* 阶段步骤条 */}
      <section className="card" style={{ marginTop: 14, padding: "18px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {[1, 2, 3].map((n, idx) => (
            <div key={n} style={{ flex: 1, display: "flex", alignItems: "center", gap: 6 }}>
              <div
                style={{
                  flex: 1,
                  textAlign: "center",
                  padding: "9px 4px",
                  borderRadius: 12,
                  fontSize: 12.5,
                  fontWeight: 600,
                  background:
                    n <= stage ? "rgba(142,168,255,.16)" : "rgba(255,255,255,.04)",
                  border:
                    n === stage
                      ? "1px solid rgba(142,168,255,.6)"
                      : "1px solid rgba(255,255,255,.07)",
                  color: n <= stage ? "#dbe4ff" : "var(--ink-faint)",
                }}
              >
                {n <= stage ? "●" : "○"} Stage {n}
              </div>
              {idx < 2 && (
                <div
                  style={{
                    width: 8,
                    height: 1,
                    background: n < stage ? "rgba(142,168,255,.6)" : "rgba(255,255,255,.12)",
                    flexShrink: 0,
                  }}
                />
              )}
            </div>
          ))}
        </div>
        <p className="muted" style={{ textAlign: "center", marginTop: 10 }}>
          {isStage3
            ? "这是最后一次温和提醒 —— 是时候把今晚交给睡眠了"
            : "循循善诱，不会说教；每次「再等等」都会换来更合适的提醒"}
        </p>
      </section>

      {/* AI 消息气泡 */}
      <section className="card" style={{ marginTop: 16 }}>
        <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: 14,
              display: "grid",
              placeItems: "center",
              fontSize: 21,
              background: "linear-gradient(140deg, rgba(142,168,255,.3), rgba(185,168,255,.18))",
              border: "1px solid rgba(142,168,255,.35)",
              flexShrink: 0,
            }}
          >
            🌙
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <b style={{ fontSize: 13.5 }}>OKSleep Agent</b>
              <span className="tag">{msg.source === "llm" ? "AI 实时生成" : "智能策略 · Mock"}</span>
            </div>
            <p style={{ fontSize: 15.5, lineHeight: 1.85 }}>{msg.text}</p>
            {msg.suggestion && (
              <div
                style={{
                  marginTop: 12,
                  padding: "10px 14px",
                  borderRadius: 12,
                  background: "rgba(255,217,138,.08)",
                  border: "1px solid rgba(255,217,138,.22)",
                  fontSize: 13,
                  color: "#ffe6b3",
                }}
              >
                💡 {msg.suggestion}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Stage 3：明日日程提醒（现实信息提醒） */}
      {isStage3 && (
        <section className="card" style={{ marginTop: 16 }}>
          <div className="h2" style={{ fontSize: 16 }}>
            📅 明日日程
          </div>
          <p className="muted" style={{ marginTop: 4 }}>
            醒来后这些事在等你 —— 睡饱了才接得住
          </p>
          <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
            {TOMORROW_PLAN.map((t) => (
              <div key={t.time} style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <span
                  style={{
                    fontVariantNumeric: "tabular-nums",
                    fontSize: 12.5,
                    color: "var(--gold)",
                    minWidth: 46,
                  }}
                >
                  {t.time}
                </span>
                <span style={{ fontSize: 14 }}>{t.item}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 用户操作 */}
      <section className="card" style={{ marginTop: 16 }}>
        <div className="h2" style={{ textAlign: "center", fontSize: 15, marginBottom: 4 }}>
          接下来你打算怎么做？
        </div>
        <div className="btn-row">
          {session.can_act.includes("continue") && (
            <button className="btn ghost" disabled={!!busy} onClick={() => act("continue")}>
              {busy === "continue" ? "● 处理中…" : "📱 再刷一会儿"}
            </button>
          )}
          {session.can_act.includes("prepare_sleep") && (
            <button className="btn gold" disabled={!!busy} onClick={requestSleep}>
              {busy === "prepare_sleep" || busy === "open" || busy === "activate"
                ? "● 处理中…"
                : "🌙 好了，去休息"}
            </button>
          )}
        </div>
        {session.can_act.length === 0 && (
          <p className="sub" style={{ textAlign: "center" }}>
            交互已锁定 —— 该休息啦
          </p>
        )}
      </section>

      <div className="ai-note" style={{ marginTop: 16 }}>
        ✨ <b>AI 能力（规划中）：</b>当前提醒由策略引擎生成；接入 LLM 后，
        每一步提醒与推荐内容（音乐 / 睡前故事）都将结合你的作息、场景与历史行为
        <b>个性化生成</b>。
      </div>

      {/* 第一步：是否启动深夜计划 */}
      {askPlan && (
        <PlanAskModal
          busy={busy === "activate"}
          taskCount={planCount}
          onYes={chooseYesPlan}
          onNo={chooseNoPlan}
          onClose={() => setAskPlan(false)}
        />
      )}

      {/* 第二步：选择助眠模式 */}
      {askSleep && (
        <SleepPrepModal
          title="准备休息"
          subtitle="需要一点声音陪你入睡吗？（不会再自动播放）"
          busy={busy === "prepare_sleep"}
          onConfirm={confirmSleep}
          onCancel={() => setAskSleep(false)}
        />
      )}
    </div>
  );
}
