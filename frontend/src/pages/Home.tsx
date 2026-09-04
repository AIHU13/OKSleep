import { useEffect, useState, type CSSProperties } from "react";
import { fetchPlanDraft, loadAppState, startSession, updateProfile } from "../api/endpoints";
import DeepNightConfig from "../components/DeepNightConfig";
import SetupWizard from "../components/SetupWizard";
import type { AppState } from "../types";

interface Props {
  view: AppState;
  run: (fn: () => Promise<AppState>) => Promise<boolean>;
  openPage: (page: "record" | "shop" | "phone") => void;
  notify: (msg: string, kind?: "ok" | "err") => void;
}

const tStyle: CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,.13)",
  background: "rgba(255,255,255,.06)",
  color: "var(--ink)",
  fontSize: 18,
  fontFamily: "inherit",
  outline: "none",
};

/** 页面 1：Home —— 单页紧凑展示（开始助眠 / 手机模拟并排、作息 / 深夜计划等入口集中）。 */
export default function Home({ view, run, openPage, notify }: Props) {
  const [busy, setBusy] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [dismissSetup, setDismissSetup] = useState(false);
  const [bed, setBed] = useState(view.profile.weekday_bedtime);
  const [wake, setWake] = useState(view.profile.weekday_wake);
  const [planCount, setPlanCount] = useState(0);
  const p = view.profile;
  const demo = view.clock.demo_active;

  const showSetup = (view.meta?.needs_setup ?? false) && !dismissSetup;
  useEffect(() => {
    if (view.meta && !view.meta.needs_setup) setDismissSetup(false);
  }, [view.meta]);

  // 深夜计划任务数
  useEffect(() => {
    let alive = true;
    fetchPlanDraft()
      .then((d) => {
        if (alive) setPlanCount(d.tasks.length);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);

  async function onStart() {
    setBusy(true);
    const ok = await run(() => startSession());
    setBusy(false);
    void ok;
  }

  function openEdit() {
    setBed(view.profile.weekday_bedtime);
    setWake(view.profile.weekday_wake);
    setShowEdit(true);
  }

  async function saveSchedule() {
    const ok = await run(async () => {
      await updateProfile({ weekday_bedtime: bed, weekday_wake: wake });
      return loadAppState();
    });
    if (ok) {
      setShowEdit(false);
      notify("作息已保存", "ok");
    }
  }

  return (
    <div className="page">
      {/* 主卡（单页展示） */}
      <section className="card" style={{ textAlign: "center", padding: "26px 22px 24px" }}>
        {/* 产品图标 */}
        <div style={{ display: "flex", justifyContent: "center" }}>
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: 20,
              display: "grid",
              placeItems: "center",
              fontSize: 34,
              background: "linear-gradient(140deg, rgba(142,168,255,.32), rgba(185,168,255,.16))",
              border: "1px solid rgba(255,255,255,.18)",
              boxShadow: "0 10px 30px rgba(120,140,255,.35), 0 0 46px rgba(185,168,255,.25)",
              marginBottom: 14,
            }}
          >
            🌙
          </div>
        </div>
        <div style={{ fontSize: 12.5, color: "var(--ink-dim)" }}>{view.home.phase_text}</div>
        <h1 className="h1" style={{ fontSize: 27, marginTop: 10, letterSpacing: 1 }}>
          健康作息，从这开始
        </h1>
        <p className="muted" style={{ fontSize: 12.5, marginTop: 8, lineHeight: 1.9 }}>
          {demo
            ? "当前为演示模式：使用模拟数据完整展示「睡前 30 分钟 → 奖励」闭环"
            : "根据你的作息，提前 30 分钟进入助眠流程"}
        </p>
        <p style={{ fontSize: 15, marginTop: 12 }}>
          目标入睡 <b style={{ color: "var(--moon)" }}>{p.weekday_bedtime}</b> · 起床{" "}
          <b style={{ color: "var(--gold)" }}>{p.weekday_wake}</b>
        </p>

        {/* 统计一行 */}
        <div style={{ marginTop: 16, display: "flex", justifyContent: "center", gap: 8, flexWrap: "wrap" }}>
          <span className="chip" style={{ fontSize: 13, padding: "7px 14px" }}>🔥 连续 {p.streak_days} 天</span>
          <span className="chip gold" style={{ fontSize: 13, padding: "7px 14px" }}>🪙 {p.total_coins}</span>
          <span className="chip" style={{ fontSize: 13, padding: "7px 14px" }}>🌙 完成 {p.completed_nights} 晚</span>
        </div>

        {/* 主操作并排：开始助眠 / 模拟手机 */}
        <div style={{ marginTop: 22, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <button className="btn gold" style={{ padding: "15px 10px", fontSize: 16 }} disabled={busy} onClick={onStart}>
            {busy ? "● 处理中…" : "🌙 开始助眠"}
          </button>
          <button className="btn" style={{ padding: "15px 10px", fontSize: 16 }} disabled={busy} onClick={() => openPage("phone")}>
            📱 模拟手机
          </button>
        </div>

        {/* 次级入口 2×2：作息时间 / 深夜计划 / 睡眠记录 / 奖品兑换 */}
        <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <button className="btn ghost" style={{ fontSize: 14.5, padding: "14px 8px" }} onClick={openEdit}>
            ✏️ 作息时间
          </button>
          <button
            className="btn ghost"
            style={{ fontSize: 14.5, padding: "14px 8px" }}
            onClick={() => window.dispatchEvent(new Event("sf:open-plan-config"))}
          >
            🌙 深夜计划{planCount > 0 ? ` · ${planCount}` : ""}
          </button>
          <button className="btn ghost" style={{ fontSize: 14.5, padding: "14px 8px" }} onClick={() => openPage("record")}>
            📊 睡眠记录
          </button>
          <button className="btn ghost" style={{ fontSize: 14.5, padding: "14px 8px" }} onClick={() => openPage("shop")}>
            🎁 奖品兑换
          </button>
        </div>
      </section>

      {/* 底部说明（三行，紧邻主卡不超过一个按钮高度） */}
      <div style={{ marginTop: 18, textAlign: "center", fontSize: 12, lineHeight: 2.3, color: "var(--ink-faint)" }}>
        <div>🌙 深夜计划：可预设定夜间任务，休息前启动，次日可查看交付结果</div>
        <div>⚡ 快速演示：点击「模拟手机」或右下方 debug 控制按钮</div>
        <div>
          ✨ 后续接入 AI：作息建议、温馨话术与助眠内容将个性化生成{" "}
          <span className="tag ai" style={{ fontSize: 10 }}>AI · 规划中</span>
        </div>
      </div>

      {/* 作息编辑弹窗 */}
      {showEdit && (
        <div className="modal-mask" onClick={() => setShowEdit(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>✏️ 调整作息时间</h2>
            <div style={{ marginTop: 12 }}>
              <label style={{ fontSize: 12.5, color: "var(--ink-dim)" }}>目标入睡时间</label>
              <input type="time" value={bed} onChange={(e) => setBed(e.target.value)} style={{ ...tStyle, marginTop: 6 }} />
            </div>
            <div style={{ marginTop: 10 }}>
              <label style={{ fontSize: 12.5, color: "var(--ink-dim)" }}>起床时间</label>
              <input type="time" value={wake} onChange={(e) => setWake(e.target.value)} style={{ ...tStyle, marginTop: 6 }} />
            </div>
            <div className="ai-note" style={{ marginTop: 12 }}>
              🤖 <b>AI 作息分析（规划中）：</b>后续结合历史作息自动推荐最佳入睡时间。
            </div>
            <div className="btn-row" style={{ marginTop: 14 }}>
              <button className="btn ghost" onClick={() => setShowEdit(false)}>取消</button>
              <button className="btn" onClick={() => void saveSchedule()}>保存</button>
            </div>
          </div>
        </div>
      )}

      {/* 深夜计划配置弹窗宿主（不占可见空间） */}
      <DeepNightConfig notify={notify} />

      {/* 首次启动配置向导 */}
      {showSetup && <SetupWizard view={view} run={run} notify={notify} onDone={() => setDismissSetup(true)} />}
    </div>
  );
}
