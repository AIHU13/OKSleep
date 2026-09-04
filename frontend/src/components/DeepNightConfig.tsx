import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { fetchPlanCatalog, fetchPlanDraft, savePlanDraft } from "../api/endpoints";
import type { PlanCatalog, PlanDraftTask, PlanParamMeta, PlanTaskType } from "../types";

interface Props {
  notify: (msg: string, kind?: "ok" | "err") => void;
}

interface Row {
  uid: number;
  category: string;
  task_type: string;
  title: string;
  params: Record<string, string>;
}

let UID = 100;

/**
 * 深夜计划配置（以表格/卡片形式录入任务）。本组件不占页面空间：
 * 由 Home / 手机模拟层通过 `sf:open-plan-config` 事件触发弹窗。
 */
export default function DeepNightConfig({ notify }: Props) {
  const [rows, setRows] = useState<Row[]>([]);
  const [open, setOpen] = useState(false);
  const [catalog, setCatalog] = useState<PlanCatalog | null>(null);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(() => {
    fetchPlanDraft()
      .then((d) => {
        setRows(
          d.tasks.map((t) => ({
            uid: UID++,
            category: t.category,
            task_type: t.task_type,
            title: t.title,
            params: { ...t.params },
          }))
        );
      })
      .catch((e) => notify(e instanceof Error ? e.message : "加载失败", "err"));
  }, [notify]);

  useEffect(() => {
    reload();
  }, [reload]);

  // 打开配置弹窗（Home 深夜计划按钮 / 外部触发）
  useEffect(() => {
    const handler = () => openModal();
    window.addEventListener("sf:open-plan-config", handler);
    return () => window.removeEventListener("sf:open-plan-config", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function openModal() {
    fetchPlanCatalog()
      .then((c) => setCatalog(c))
      .catch((e) => notify(e instanceof Error ? e.message : "加载失败", "err"));
    setOpen(true);
  }

  function typeOf(key: string): PlanTaskType | undefined {
    return catalog?.task_types.find((t) => t.key === key);
  }

  function addTask(type: PlanTaskType) {
    if (rows.some((r) => r.task_type === type.key)) {
      notify(`《${type.name}》已在计划中`, "err");
      return;
    }
    const params: Record<string, string> = {};
    for (const meta of type.params) params[meta.key] = meta.default || "";
    setRows((prev) => [...prev, { uid: UID++, category: type.category, task_type: type.key, title: type.name, params }]);
  }

  function patchParam(uid: number, key: string, value: string) {
    setRows((prev) => prev.map((r) => (r.uid === uid ? { ...r, params: { ...r.params, [key]: value } } : r)));
  }

  function removeRow(uid: number) {
    setRows((prev) => prev.filter((r) => r.uid !== uid));
  }

  async function save() {
    setBusy(true);
    try {
      const tasks = rows.map((r) => ({ category: r.category, task_type: r.task_type, title: r.title, params: r.params }));
      const resp = await savePlanDraft(tasks);
      setRows(
        resp.tasks.map((t: PlanDraftTask) => ({
          uid: UID++,
          category: t.category,
          task_type: t.task_type,
          title: t.title,
          params: { ...t.params },
        }))
      );
      notify(resp.tasks.length > 0 ? `深夜计划已保存：${resp.tasks.length} 个任务待启动 🌙` : "已清空深夜计划草稿", "ok");
    } catch (e) {
      notify(e instanceof Error ? e.message : "保存失败", "err");
    } finally {
      setBusy(false);
    }
  }

  async function fillExample() {
    if (!catalog) return;
    setBusy(true);
    try {
      await savePlanDraft(
        catalog.default_tasks.map((d) => ({ category: d.category, task_type: d.task_type, title: d.title, params: d.params }))
      );
      notify("已填入示例任务并保存（早餐 + 周报 + PPT）", "ok");
      reload();
    } catch (e) {
      notify(e instanceof Error ? e.message : "保存失败", "err");
    } finally {
      setBusy(false);
    }
  }

  function fieldInput(meta: PlanParamMeta, row: Row) {
    const base: CSSProperties = {
      width: "100%",
      padding: "8px 10px",
      marginTop: 4,
      borderRadius: 10,
      border: "1px solid rgba(255,255,255,.13)",
      background: "rgba(255,255,255,.05)",
      color: "var(--ink)",
      fontSize: 13,
      fontFamily: "inherit",
      outline: "none",
    };
    if (meta.type === "time") {
      return <input type="time" value={row.params[meta.key] ?? ""} onChange={(e) => patchParam(row.uid, meta.key, e.target.value)} style={base} />;
    }
    if (meta.type === "spec") {
      return (
        <select value={row.params[meta.key] ?? ""} onChange={(e) => patchParam(row.uid, meta.key, e.target.value)} style={base}>
          {catalog?.spec_docs.map((d) => (
            <option key={d.key} value={d.key}>{d.name}</option>
          ))}
        </select>
      );
    }
    return <input type="text" value={row.params[meta.key] ?? ""} placeholder={meta.label} onChange={(e) => patchParam(row.uid, meta.key, e.target.value)} style={base} />;
  }

  if (!open) return null;

  const dailyTypes = catalog?.task_types.filter((t) => t.category === "daily") ?? [];
  const workTypes = catalog?.task_types.filter((t) => t.category === "work") ?? [];

  return (
    <div className="modal-mask" onClick={() => setOpen(false)}>
      <div className="modal-box" style={{ maxWidth: 640 }} onClick={(e) => e.stopPropagation()} role="dialog" aria-modal>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ fontSize: 19, fontWeight: 700 }}>🌙 深夜计划 · 任务表格</h2>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn ghost sm" onClick={() => void fillExample()} disabled={busy}>📋 一键示例</button>
            <button className="btn ghost sm" onClick={() => setOpen(false)}>✕</button>
          </div>
        </div>
        <p className="sub" style={{ margin: "6px 0 12px" }}>
          填入今晚想委托的任务，保存为草稿；休息前选择「启动」即可交给 Agent。
        </p>

        {/* 添加入口 */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <div>
            <div className="muted" style={{ marginBottom: 6 }}>日常任务</div>
            <div style={{ display: "grid", gap: 6 }}>
              {dailyTypes.map((t) => (
                <button key={t.key} className="choice-card" onClick={() => addTask(t)} style={{ padding: "8px 12px" }}>
                  <span style={{ fontSize: 18 }}>{t.icon}</span>
                  <div style={{ flex: 1, textAlign: "left" }}><b style={{ fontSize: 13 }}>+ {t.name}</b></div>
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="muted" style={{ marginBottom: 6 }}>工作任务</div>
            <div style={{ display: "grid", gap: 6 }}>
              {workTypes.map((t) => (
                <button key={t.key} className="choice-card" onClick={() => addTask(t)} style={{ padding: "8px 12px" }}>
                  <span style={{ fontSize: 18 }}>{t.icon}</span>
                  <div style={{ flex: 1, textAlign: "left" }}><b style={{ fontSize: 13 }}>+ {t.name}</b></div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 任务清单 */}
        <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
          {rows.length === 0 && (
            <p className="muted" style={{ textAlign: "center", padding: 12 }}>还没有任务 —— 点击上方「+」添加，或使用「一键示例」</p>
          )}
          {rows.map((row) => {
            const t = typeOf(row.task_type);
            if (!t) return null;
            return (
              <div key={row.uid} style={{ border: "1px solid rgba(255,255,255,.1)", borderRadius: 14, padding: "10px 12px", background: "rgba(255,255,255,.03)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <b style={{ fontSize: 13.5 }}>
                    {t.icon} {row.title}
                    <span className="muted" style={{ fontSize: 11, marginLeft: 8 }}>{row.category === "daily" ? "日常" : "工作"}</span>
                  </b>
                  <button className="btn ghost sm" onClick={() => removeRow(row.uid)} style={{ padding: "4px 10px" }}>删除</button>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 8, marginTop: 8 }}>
                  {t.params.map((meta) => (
                    <label key={meta.key} style={{ display: "block" }}>
                      <span className="muted" style={{ fontSize: 10.5 }}>{meta.label}</span>
                      {fieldInput(meta, row)}
                    </label>
                  ))}
                </div>
                {t.params.some((p) => p.type === "spec") && (
                  <div className="muted" style={{ fontSize: 11, marginTop: 7 }}>
                    📄 {catalog?.spec_docs.find((d) => d.key === row.params.spec_doc)?.summary ?? ""}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="ai-note" style={{ marginTop: 12 }}>
          ✨ <b>AI / Agent 能力（规划中）：</b>任务将交由深夜工作 Agent 按工作区与规范文档
          自主规划执行（数据汇总 / 报告 / PPT），服务类（早餐配送等）由服务 Agent 完成；本版本以 Mock 演示全流程。
        </div>

        <div className="btn-row" style={{ marginTop: 14 }}>
          <button className="btn ghost" disabled={busy} onClick={() => setOpen(false)}>关闭</button>
          <button className="btn" disabled={busy} onClick={() => void save()}>
            {busy ? "● 保存中…" : `保存深夜计划草稿（${rows.length}）`}
          </button>
        </div>
      </div>
    </div>
  );
}
