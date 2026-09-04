import { useState, type CSSProperties } from "react";
import {
  completeOnboarding,
  fetchPlanCatalog,
  loadAppState,
  savePlanDraft,
  updateProfile,
} from "../api/endpoints";
import type { AppState } from "../types";

interface Props {
  view: AppState;
  /** 动作执行器（成功后自动提交新视图）。 */
  run: (fn: () => Promise<AppState>) => Promise<boolean>;
  /** 完成后关闭向导。 */
  onDone: () => void;
  notify: (msg: string, kind?: "ok" | "err") => void;
}

const inputStyle: CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,.14)",
  background: "rgba(255,255,255,.06)",
  color: "var(--ink)",
  fontSize: 18,
  fontFamily: "inherit",
  outline: "none",
};

/**
 * 首次启动配置向导：入睡时间 + 深夜计划（可一键示例），完成后进入主界面。
 */
export default function SetupWizard({ view, run, onDone, notify }: Props) {
  const [bed, setBed] = useState(view.profile.weekday_bedtime);
  const [wake, setWake] = useState(view.profile.weekday_wake);
  const [useExample, setUseExample] = useState(true);
  const [busy, setBusy] = useState(false);

  async function finish() {
    if (busy) return;
    setBusy(true);
    const ok = await run(async () => {
      await updateProfile({ weekday_bedtime: bed, weekday_wake: wake });
      if (useExample) {
        const cat = await fetchPlanCatalog();
        await savePlanDraft(
          cat.default_tasks.map((d) => ({
            category: d.category,
            task_type: d.task_type,
            title: d.title,
            params: d.params,
          }))
        );
      }
      await completeOnboarding();
      return loadAppState();
    });
    setBusy(false);
    if (ok) {
      notify(
        useExample
          ? "首次配置完成 ✅ 已写入默认深夜计划（早餐+周报+PPT）"
          : "首次配置完成 ✅",
        "ok"
      );
      onDone();
    }
  }

  return (
    <div className="modal-mask" style={{ zIndex: 130 }}>
      <div className="modal-box" style={{ maxWidth: 440 }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 46 }}>🌙</div>
          <h2 style={{ fontSize: 21, fontWeight: 800, marginTop: 8 }}>欢迎使用 OKSleep</h2>
          <p className="muted" style={{ marginTop: 4 }}>
            首次使用，先完成基础配置（可随时在首页修改）
          </p>
        </div>

        {/* Step 1 作息 */}
        <div style={{ marginTop: 18 }}>
          <div style={{ fontSize: 13.5, fontWeight: 700 }}>① 设置你的作息时间</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 8 }}>
            <label>
              <span className="muted" style={{ fontSize: 11 }}>目标入睡时间</span>
              <input type="time" value={bed} onChange={(e) => setBed(e.target.value)} style={inputStyle} />
            </label>
            <label>
              <span className="muted" style={{ fontSize: 11 }}>起床时间</span>
              <input type="time" value={wake} onChange={(e) => setWake(e.target.value)} style={inputStyle} />
            </label>
          </div>
          <p className="muted" style={{ marginTop: 6, fontSize: 11.5 }}>
            🤖 后续 AI 将基于历史作息自动推荐最佳入睡时间
          </p>
        </div>

        {/* Step 2 深夜计划 */}
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 13.5, fontWeight: 700 }}>② 深夜计划（可选，可稍后配置）</div>
          <label
            style={{
              marginTop: 8,
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
              background: "rgba(255,255,255,.05)",
              border: "1px solid rgba(255,255,255,.1)",
              borderRadius: 14,
              padding: "12px 14px",
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={useExample}
              onChange={(e) => setUseExample(e.target.checked)}
              style={{ marginTop: 3 }}
            />
            <span style={{ fontSize: 13, lineHeight: 1.8 }}>
              使用示例任务：🥐 明早 07:40 预定早餐 · 📝 周报撰写 · 🖥️ PPT 制作
              （深夜工作/服务 Agent 在你入睡后自动完成）
            </span>
          </label>
        </div>

        <div style={{ marginTop: 20 }}>
          <button className="btn block" disabled={busy} onClick={() => void finish()}>
            {busy ? "● 保存中…" : "🚀 保存配置，进入 OKSleep"}
          </button>
        </div>
        <p style={{ textAlign: "center", marginTop: 10 }}>
          <button
            className="muted"
            style={{ background: "none", border: "none", color: "var(--ink-faint)", fontSize: 12 }}
            disabled={busy}
            onClick={() => void finish()}
          >
            跳过（使用默认作息，稍后再配置）
          </button>
        </p>
      </div>
    </div>
  );
}
