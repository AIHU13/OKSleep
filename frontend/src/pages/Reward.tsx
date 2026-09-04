import { useEffect, useState } from "react";
import { fetchPlanReport } from "../api/endpoints";
import type { PlanArtifact, PlanReportResp, RewardData } from "../types";

interface Props {
  data: RewardData;
  onDone: () => Promise<void>;
  onShop?: () => void;
}

const FLOATS = ["✨", "🌟", "🪙", "💤"];

/** 页面 5：Reward —— 次日奖励 + 深夜计划交付（单页整合、无需下滑分层）。 */
export default function Reward({ data, onDone, onShop }: Props) {
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<PlanReportResp | null>(null);
  const [detail, setDetail] = useState<PlanArtifact | null>(null);

  useEffect(() => {
    fetchPlanReport(data.session_id)
      .then((r) => setReport(r))
      .catch(() => setReport(null));
  }, [data.session_id]);

  const tasks = report?.has_plan ? (report.items ?? []) : [];

  return (
    <div className="page" style={{ position: "relative" }}>
      {/* 飘浮点缀 */}
      <div aria-hidden style={{ position: "absolute", inset: 0, pointerEvents: "none", animation: "fadeUp .8s ease both" }}>
        {FLOATS.map((c, i) => (
          <span
            key={i}
            style={{
              position: "absolute",
              fontSize: 14 + i * 4,
              opacity: 0.5,
              left: `${10 + i * 26}%`,
              top: `${6 + ((i * 23) % 30)}%`,
              animation: `floatY ${2.4 + i * 0.6}s ease-in-out ${i * 0.2}s infinite alternate`,
            }}
          >
            {c}
          </span>
        ))}
      </div>

      {/* 单页整合卡：奖励 + 深夜计划交付看板 */}
      <section className="card" style={{ padding: "18px 16px", textAlign: "center" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
          <span style={{ fontSize: 28 }}>🎉</span>
          <h1 className="h1" style={{ fontSize: 22 }}>
            昨晚完成睡前计划
          </h1>
        </div>
        <p className="muted" style={{ fontSize: 12, marginTop: 4 }}>
          新的一天 · Sleep Coins 已到账
        </p>

        {/* 奖励数字 */}
        <div style={{ margin: "10px auto 0" }}>
          <span style={{ fontSize: 38, fontWeight: 850, color: "var(--gold)" }}>+{data.coins} 🪙</span>
        </div>
        <p style={{ fontSize: 12.5, opacity: 0.9, marginTop: 4 }}>{data.message}</p>

        {/* 三格统计（压缩） */}
        <div style={{ marginTop: 12, display: "flex", justifyContent: "center", gap: 8 }}>
          {[
            { v: `${data.streak_days} 天`, l: "连续打卡 🔥" },
            { v: `${data.total_coins}`, l: "累计积分 🪙" },
            { v: "✓", l: "昨晚完成" },
          ].map((s) => (
            <div
              key={s.l}
              style={{
                flex: 1,
                maxWidth: 110,
                background: "rgba(255,255,255,.05)",
                border: "1px solid rgba(255,255,255,.08)",
                borderRadius: 12,
                padding: "8px 6px",
              }}
            >
              <div style={{ fontSize: 17, fontWeight: 800, color: "var(--gold)" }}>{s.v}</div>
              <div className="muted" style={{ fontSize: 10.5, marginTop: 2 }}>{s.l}</div>
            </div>
          ))}
        </div>

        {/* 深夜计划交付（同卡整合，紧凑展示） */}
        {tasks.length > 0 && (
          <>
            <div
              style={{
                marginTop: 14,
                height: 1,
                background: "linear-gradient(90deg,transparent,rgba(185,168,255,.5),transparent)",
              }}
            />
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, marginTop: 10 }}>
              <b style={{ fontSize: 13.5 }}>🌙 深夜计划 · Agent 交付</b>
              <span className="tag ai" style={{ fontSize: 10 }}>
                工作/服务 Agent
              </span>
            </div>
            <div style={{ marginTop: 8, display: "grid", gap: 6 }}>
              {tasks.map((it) => (
                <div
                  key={it.task_id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "7px 10px",
                    borderRadius: 10,
                    background: "rgba(255,255,255,.045)",
                    border: "1px solid rgba(255,255,255,.07)",
                  }}
                >
                  <span style={{ fontSize: 18 }}>{it.icon}</span>
                  <div style={{ flex: 1, minWidth: 0, textAlign: "left" }}>
                    <span style={{ fontSize: 12.5, fontWeight: 650 }}>{it.title}</span>
                    <span
                      className="muted"
                      style={{
                        display: "block",
                        fontSize: 10.5,
                        marginTop: 1,
                        color:
                          it.status === "done"
                            ? "var(--success)"
                            : it.status === "delivering"
                              ? "var(--gold)"
                              : undefined,
                      }}
                    >
                      {it.label}
                    </span>
                  </div>
                  {it.artifact ? (
                    <button className="btn ghost sm" style={{ fontSize: 11, padding: "4px 10px" }} onClick={() => setDetail(it.artifact!)}>
                      查看
                    </button>
                  ) : (
                    <span className="tag" style={{ fontSize: 10 }}>
                      处理中
                    </span>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* 操作 */}
        <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: onShop ? "1fr 1fr" : "1fr", gap: 8 }}>
          <button className="btn sm" disabled={busy} onClick={async () => { setBusy(true); try { await onDone(); } finally { setBusy(false); } }}>
            {busy ? "返回中…" : "🌙 好的，今晚继续"}
          </button>
          {onShop && (
            <button className="btn ghost sm" disabled={busy} onClick={() => onShop()}>
              🎁 积分兑换
            </button>
          )}
        </div>
        <p className="muted" style={{ fontSize: 10.5, marginTop: 8 }}>
          连续打卡与历史积分将用于后续更个性化的助眠策略
        </p>
      </section>

      {/* 交付物查看弹窗 */}
      {detail && (
        <div className="modal-mask" onClick={() => setDetail(null)}>
          <div className="modal-box" style={{ maxWidth: 520 }} onClick={(e) => e.stopPropagation()} role="dialog" aria-modal>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
              <h2 style={{ fontSize: 17, fontWeight: 700 }}>{detail.title}</h2>
              <button className="btn ghost sm" onClick={() => setDetail(null)}>✕</button>
            </div>
            <pre
              style={{
                marginTop: 14,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "inherit",
                fontSize: 13,
                lineHeight: 1.8,
                color: "var(--ink)",
                background: "rgba(255,255,255,.04)",
                border: "1px solid rgba(255,255,255,.08)",
                borderRadius: 14,
                padding: "12px 14px",
                maxHeight: "58vh",
                overflow: "auto",
              }}
            >
              {detail.body}
            </pre>
            <p className="muted" style={{ fontSize: 11, marginTop: 10 }}>
              ✨ 模拟交付内容（Mock）；接入真实 Agent 后可查看 / 下载真实产物
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
