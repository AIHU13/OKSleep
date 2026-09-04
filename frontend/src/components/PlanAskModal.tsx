interface Props {
  busy: boolean;
  /** 已配置任务数（用于文案提示）。 */
  taskCount: number | null;
  onYes: () => void;
  onNo: () => void;
  onClose: () => void;
}

/**
 * 点「好了，去休息」后的第一步询问：是否启动深夜计划（是 / 否）。
 * 选择后进入助眠模式选择（音乐 / 故事 / 安静）。
 */
export default function PlanAskModal({ busy, taskCount, onYes, onNo, onClose }: Props) {
  return (
    <div className="modal-mask" onClick={busy ? undefined : onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 44 }}>🌙</div>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginTop: 10 }}>是否启动深夜计划？</h2>
          <p className="sub" style={{ marginTop: 10, lineHeight: 1.8 }}>
            睡前把想委托的任务交给 Agent 连夜处理（预定早餐、周报撰写、PPT 制作等），
            你安心入睡，明早验收成果。
          </p>
          <p className="muted" style={{ marginTop: 6 }}>
            {taskCount != null && taskCount > 0
              ? `已为你配置 ${taskCount} 个任务待启动`
              : "未配置任务时，将自动按默认任务集启动（早餐 + 周报 + PPT）"}
          </p>
        </div>

        <div className="ai-note" style={{ marginTop: 16 }}>
          ✨ <b>Agent 能力（规划中）：</b>深夜工作 / 服务 Agent 将在你入睡期间
          自主规划与执行；次日早晨可在奖励页查看任务完成情况。
        </div>

        <div className="btn-row" style={{ marginTop: 20 }}>
          <button className="btn ghost" disabled={busy} onClick={onNo}>
            否，直接休息
          </button>
          <button className="btn gold" disabled={busy} onClick={onYes}>
            {busy ? "● 启动中…" : "是，启动深夜计划"}
          </button>
        </div>
        <p style={{ textAlign: "center", marginTop: 12 }}>
          <button
            className="muted"
            style={{ background: "none", border: "none", color: "var(--ink-faint)", fontSize: 12 }}
            disabled={busy}
            onClick={onClose}
          >
            ‹ 返回（暂不休息）
          </button>
        </p>
      </div>
    </div>
  );
}
