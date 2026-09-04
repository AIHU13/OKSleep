import { useState } from "react";
import { demoAdvance, demoEnterWindow, demoNextDay, demoReset } from "../api/endpoints";
import type { AppState } from "../types";

interface Props {
  /** 每次模拟操作后回调最新 AppState，由上层统一提交（自动导航）。 */
  onChanged: (view: AppState) => void;
  notify: (msg: string, kind?: "ok" | "err") => void;
}

const ITEMS: Array<{
  key: string;
  icon: string;
  label: string;
  danger?: boolean;
  fn: () => Promise<AppState>;
}> = [
  { key: "enter", icon: "🌙", label: "进入睡前 30 分钟", fn: () => demoEnterWindow() },
  { key: "adv6", icon: "⏱️", label: "模拟 6 分钟", fn: () => demoAdvance(6) },
  { key: "adv60", icon: "😴", label: "模拟 1 小时（未使用手机）", fn: () => demoAdvance(60) },
  { key: "next", icon: "☀️", label: "模拟第二天", fn: () => demoNextDay() },
  { key: "reset", icon: "🔄", label: "重置 Demo", danger: true, fn: () => demoReset() },
];

/** 隐藏 Demo Control（设计说明 §4）：右下角悬浮齿轮展开。 */
export default function DemoControl({ onChanged, notify }: Props) {
  const [open, setOpen] = useState(false);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  async function run(item: (typeof ITEMS)[number]) {
    if (busyKey) return;
    if (item.key === "reset") {
      const ok = window.confirm("重置 Demo 将清空所有演示数据与虚拟时间，确定吗？");
      if (!ok) return;
    }
    setBusyKey(item.key);
    try {
      const view = await item.fn();
      onChanged(view);
      notify(item.key === "reset" ? "Demo 已重置，回到首页" : `已${item.label}`, "ok");
    } catch (e) {
      notify(e instanceof Error ? e.message : "操作失败", "err");
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <>
      {open && (
        <div
          style={{
            position: "fixed",
            right: 18,
            bottom: 74,
            zIndex: 81,
            width: 264,
            borderRadius: 18,
            background: "rgba(13, 19, 46, 0.95)",
            border: "1px solid rgba(255,255,255,0.13)",
            backdropFilter: "blur(14px)",
            boxShadow: "0 18px 44px rgba(0,0,0,0.5)",
            padding: 14,
            animation: "fadeUp .25s ease both",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 10,
            }}
          >
            <b style={{ fontSize: 13.5 }}>🧪 Demo Control</b>
            <span style={{ fontSize: 11, color: "var(--ink-faint)" }}>演示辅助</span>
          </div>
          <div style={{ display: "grid", gap: 7 }}>
            {ITEMS.map((item) => (
              <button
                key={item.key}
                className="btn ghost sm"
                style={{
                  justifyContent: "flex-start",
                  color: item.danger ? "#ffd0d0" : undefined,
                  borderColor: item.danger ? "rgba(255,157,157,.4)" : undefined,
                  opacity: busyKey && busyKey !== item.key ? 0.4 : 1,
                }}
                disabled={!!busyKey}
                onClick={() => run(item)}
              >
                <span>{item.icon}</span> {item.label}
                {busyKey === item.key && (
                  <span style={{ marginLeft: "auto", color: "var(--ink-faint)" }}>…</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
      <button
        className="demo-fab"
        title="Demo Control"
        aria-label="Demo Control"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "✕" : "⚙️"}
      </button>
    </>
  );
}
