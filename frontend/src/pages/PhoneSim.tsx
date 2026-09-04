import { useCallback, useEffect, useRef, useState } from "react";
import {
  activatePlan,
  chooseScenario,
  fetchPlanCatalog,
  fetchPlanDraft,
  loadAppState,
  recordMiss,
  savePlanDraft,
  startSession,
} from "../api/endpoints";
import SleepPrepModal, { type SleepContentChoice } from "../components/SleepPrepModal";
import type { AppState, PlanTaskType } from "../types";

interface Props {
  onExit: () => void;
  /** 交接成功：后端已把会话推进到 SLEEP_MODE 的视图。 */
  onHandoff: (view: AppState) => void;
  notify: (msg: string, kind?: "ok" | "err") => void;
}

type Stage = "perm" | "watch" | "r1" | "snooze" | "health" | "deep" | "prep";

const SNOOZE_DEMO_SEC = 5; // 演示加速：1 秒 ≈ 模拟 1.x 分钟
const BACK_DEMO_SEC = 5;

/**
 * 手机端场景模拟层（抖音拟真，tiktok.mp4 循环播放）：
 * ① 到达睡前 30 分钟 → 视频暂停 + 小窗提醒；
 * ② 「再刷一会儿」→ 5s（模拟 6 分钟）后自动切健康视频 sleep.mp4（返回 / 好了，去休息）；
 * ③ 点休息 → 深夜计划：是 / 否 / 修改计划（修改并确认后继续进入助眠模式）→ 选助眠模式。
 * （健康页返回后顶部显示"模拟明日日程"横幅 + 倒计时，之后进入深夜计划说明页。）
 */
export default function PhoneSim({ onExit, onHandoff, notify }: Props) {
  const [stage, setStage] = useState<Stage>("perm");
  const [prepDeep, setPrepDeep] = useState(true);
  const [planAsk, setPlanAsk] = useState(false);
  const [editPlan, setEditPlan] = useState(false);
  const [like, setLike] = useState(12800);
  const [liked, setLiked] = useState(false);
  const [vol, setVol] = useState(true);
  const [snoozeLeft, setSnoozeLeft] = useState(SNOOZE_DEMO_SEC);
  const [backLeft, setBackLeft] = useState<number | null>(null);
  const [handoffBusy, setHandoffBusy] = useState(false);
  const [shortsOk, setShortsOk] = useState(true);
  const [sleepOk, setSleepOk] = useState(true);
  const [grad, setGrad] = useState(0);

  const watchPaused = stage === "r1" || stage === "deep" || planAsk;

  /* ---------- 自动检测：虚拟时间进入睡前窗口 → 第一次提醒 ---------- */
  useEffect(() => {
    if (stage !== "watch" || backLeft !== null) return;
    const t = window.setInterval(async () => {
      try {
        const d = await loadAppState();
        if (d.home.is_in_window && d.session === null) firstRemind();
      } catch {
        /* 忽略 */
      }
    }, 5000);
    return () => window.clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage, backLeft]);

  const firstRemind = useCallback(() => setStage("r1"), []);

  /** 再刷一会儿：演示 5s（模拟 6 分钟）后自动切健康视频 */
  const snooze = useCallback(() => {
    setStage("snooze");
    setSnoozeLeft(SNOOZE_DEMO_SEC);
  }, []);

  useEffect(() => {
    if (stage !== "snooze") return;
    if (snoozeLeft <= 0) {
      setStage("health");
      return;
    }
    const t = window.setTimeout(() => setSnoozeLeft((v) => v - 1), 1000);
    return () => window.clearTimeout(t);
  }, [stage, snoozeLeft]);

  /** 健康视频返回：回到 tiktok，顶部横幅 + 倒计时后进入深夜计划说明 */
  const backToWatch = useCallback(() => {
    setStage("watch");
    setBackLeft(BACK_DEMO_SEC);
  }, []);

  useEffect(() => {
    if (stage !== "watch" || backLeft === null) return;
    if (backLeft <= 0) {
      setBackLeft(null);
      setStage("deep");
      return;
    }
    const t = window.setTimeout(() => setBackLeft((v) => (v === null ? null : v - 1)), 1000);
    return () => window.clearTimeout(t);
  }, [stage, backLeft]);

  /** 深夜计划说明页点「返回（不启动）」→ 助眠失败 + 积分扣除 */
  const refuseAtDeep = useCallback(async () => {
    setStage("watch");
    setBackLeft(null);
    try {
      const r = await recordMiss("shorts");
      notify(`${r.message}（已在睡眠记录中标记为助眠失败）`, "err");
    } catch (e) {
      notify(e instanceof Error ? e.message : "记录失败", "err");
    }
  }, [notify]);

  /** 进入助眠模式交接 */
  const doHandoff = async (deepPlan: boolean, ct: SleepContentChoice) => {
    if (handoffBusy) return;
    setHandoffBusy(true);
    try {
      let d = await loadAppState();
      if (!d.session) d = await startSession();
      const sid = d.session!.session_id;
      if (deepPlan) await activatePlan(sid);
      const final = await chooseScenario("ready", ct);
      onHandoff(final);
      notify(deepPlan ? "已启动深夜计划并进入助眠模式 🌙" : "已进入助眠模式 🌙", "ok");
    } catch (e) {
      notify(e instanceof Error ? e.message : "进入助眠失败", "err");
      setHandoffBusy(false);
    }
  };

  const openPrep = (deep: boolean) => {
    setPlanAsk(false);
    setEditPlan(false);
    setPrepDeep(deep);
    setStage("prep");
  };

  const showPlanAsk = () => {
    if (stage === "r1" || stage === "health" || stage === "watch") setPlanAsk(true);
  };

  /* ---------- 渲染 ---------- */
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 200, background: "#000", display: "flex", justifyContent: "center" }}>
      <div style={{ position: "relative", width: "min(100vw, 430px)", height: "100dvh", background: "#05070f", overflow: "hidden" }}>
        {stage === "perm" && <PermOverlay onAllow={() => setStage("watch")} notify={notify} />}

        {stage !== "perm" && stage !== "prep" && (
          <ShortsPane
            mode={stage === "health" ? "health" : "watch"}
            shortsOk={shortsOk}
            sleepOk={sleepOk}
            setShortsOk={setShortsOk}
            setSleepOk={setSleepOk}
            vol={vol}
            setVol={setVol}
            grad={grad}
            setGrad={setGrad}
            like={like}
            liked={liked}
            onLike={() => {
              setLike((v) => (liked ? v - 1 : v + 1));
              setLiked((v) => !v);
            }}
            paused={watchPaused}
            onBackFromHealth={backToWatch}
            onSleepFromHealth={showPlanAsk}
          />
        )}

        {/* 状态栏 */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            zIndex: 60,
            display: "flex",
            justifyContent: "space-between",
            padding: "10px 16px 4px",
            color: "#fff",
            fontSize: 11.5,
          }}
        >
          <span>{nowTime()}</span>
          <span>📶 OKSleep 守护中 · 🔋 87%</span>
        </div>

        {/* 顶部返回 */}
        <button
          onClick={onExit}
          style={{
            position: "absolute",
            top: 38,
            left: 10,
            zIndex: 65,
            background: "rgba(0,0,0,.45)",
            border: "none",
            color: "#fff",
            fontSize: 12.5,
            borderRadius: 999,
            padding: "6px 12px",
            cursor: "pointer",
          }}
        >
          ‹ OKSleep 主界面
        </button>

        {/* 演示推进 */}
        <div style={{ position: "absolute", top: 38, right: 10, zIndex: 65 }}>
          <button className="btn ghost sm" style={{ fontSize: 11, padding: "5px 10px" }} onClick={demoNext}>
            ⏰ 模拟时间推进
          </button>
        </div>

        {/* ---------- ① 暂停 + 小窗提醒 ---------- */}
        {stage === "r1" && (
          <div style={{ position: "absolute", inset: 0, zIndex: 70, background: "rgba(4,8,20,.55)", display: "grid", placeItems: "end center", padding: 18 }}>
            <div
              style={{
                width: "100%",
                background: "linear-gradient(165deg,#16204a,#0d1430)",
                border: "1px solid rgba(142,168,255,.4)",
                borderRadius: 18,
                padding: "16px 16px 12px",
                boxShadow: "0 -10px 40px rgba(0,0,0,.5)",
                animation: "fadeUp .35s ease both",
              }}
            >
              <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                <span style={{ fontSize: 28 }}>🌙</span>
                <div>
                  <b style={{ fontSize: 15 }}>OKSleep 提醒：该睡啦</b>
                  <p style={{ fontSize: 12.5, opacity: .9, marginTop: 5, lineHeight: 1.7 }}>
                    已到你的睡前 30 分钟窗口（目标 23:30 入睡）。视频已暂停，
                    短视频只会让你越刷越清醒哦。
                  </p>
                </div>
              </div>
              <div className="btn-row" style={{ marginTop: 12 }}>
                <button className="btn ghost sm" onClick={snooze}>
                  📱 再刷一会儿
                </button>
                <button className="btn gold sm" onClick={showPlanAsk}>
                  😴 去休息
                </button>
              </div>
            </div>
          </div>
        )}

        {/* snooze：5s 演示（模拟 6 分钟）后自动切健康视频 */}
        {stage === "snooze" && (
          <div
            style={{
              position: "absolute",
              top: 80,
              left: "50%",
              transform: "translateX(-50%)",
              zIndex: 66,
              background: "rgba(0,0,0,.68)",
              color: "#ffd98a",
              fontSize: 12,
              borderRadius: 999,
              padding: "6px 14px",
              whiteSpace: "nowrap",
            }}
          >
            ⏱ 再刷一会儿 · 模拟 6 分钟后自动切换健康助眠内容（{snoozeLeft}s 演示）
          </div>
        )}

        {/* 健康页返回后的横幅：模拟明日日程提醒 + 倒计时 */}
        {stage === "watch" && backLeft !== null && (
          <div
            style={{
              position: "absolute",
              top: 80,
              left: "50%",
              transform: "translateX(-50%)",
              zIndex: 66,
              width: "calc(100% - 36px)",
              background: "rgba(20,28,62,.92)",
              border: "1px solid rgba(142,168,255,.45)",
              color: "#fff",
              fontSize: 12,
              borderRadius: 14,
              padding: "8px 12px",
              textAlign: "center",
            }}
          >
            ⏰ 模拟明日日程提醒：07:30 起床 · 09:00 周会
            <br />
            <span style={{ color: "#ffd98a" }}>
              若继续忽略，{backLeft}s 后将进入深夜计划说明（{BACK_DEMO_SEC}s 演示 ≈ 6 分钟）
            </span>
          </div>
        )}

        {/* ---------- 第三次：深夜计划启动说明 ---------- */}
        {stage === "deep" && (
          <div style={{ position: "absolute", inset: 0, zIndex: 75, background: "rgba(6,10,28,.96)", display: "grid", placeItems: "center", padding: 20 }}>
            <div style={{ width: "100%", textAlign: "center", animation: "fadeUp .4s ease both" }}>
              <div style={{ fontSize: 48 }}>🌙</div>
              <h2 style={{ fontSize: 20, fontWeight: 800, marginTop: 10 }}>深夜计划 · 启动说明</h2>
              <p style={{ fontSize: 13, opacity: .92, marginTop: 10, lineHeight: 2 }}>
                已经深夜了，剩下的交给 Agent：
                <br />🥐 明早早餐配送 · 📝 周报撰写 · 🖥️ PPT 制作
                <br />你安心入睡，明早验收成果
              </p>
              <div className="btn-row" style={{ marginTop: 16 }}>
                <button className="btn gold" onClick={() => openPrep(true)}>🚀 是，启动并休息</button>
                <button className="btn ghost" onClick={() => openPrep(false)}>😴 否，直接休息</button>
              </div>
              <div className="btn-row" style={{ marginTop: 10 }}>
                <button className="btn ghost" onClick={() => void refuseAtDeep()}>‹ 返回（记录助眠失败 -5 🪙）</button>
                <button className="btn ghost" onClick={openEditPlan}>✏️ 修改计划</button>
              </div>
            </div>
          </div>
        )}

        {/* 深夜计划选择：是 / 否 / 修改计划 */}
        {planAsk && (
          <div className="modal-mask" style={{ zIndex: 90 }} onClick={() => setPlanAsk(false)}>
            <div className="modal-box" style={{ maxWidth: 380 }} onClick={(e) => e.stopPropagation()}>
              <h2 style={{ fontSize: 19, fontWeight: 800, textAlign: "center" }}>🌙 是否启动深夜计划？</h2>
              <p className="sub" style={{ marginTop: 10, fontSize: 13, lineHeight: 1.9 }}>
                把预定早餐、周报撰写、PPT 制作交给深夜 Agent，你安心入睡、明早验收成果；
                也可以先修改今晚的计划内容。
              </p>
              <div className="btn-row" style={{ marginTop: 16 }}>
                <button className="btn ghost" onClick={() => openPrep(false)} disabled={handoffBusy}>否，直接休息</button>
                <button className="btn gold" onClick={() => openPrep(true)} disabled={handoffBusy}>是，启动深夜计划</button>
              </div>
              <div style={{ marginTop: 10 }}>
                <button className="btn ghost block" onClick={openEditPlan} disabled={handoffBusy}>✏️ 修改计划</button>
              </div>
              <p style={{ textAlign: "center", marginTop: 10 }}>
                <button
                  className="muted"
                  style={{ background: "none", border: "none", color: "var(--ink-faint)", fontSize: 12 }}
                  onClick={() => { setPlanAsk(false); setStage("watch"); }}
                >
                  ‹ 暂不休息，继续看一会儿
                </button>
              </p>
            </div>
          </div>
        )}

        {/* 深夜计划修改（在手机层内完成，确认后继续助眠模式） */}
        {editPlan && <PlanEditSheet notify={notify} onCancel={() => { setEditPlan(false); setPlanAsk(true); }} onSaved={() => openPrep(true)} />}

        {/* 助眠模式选择 */}
        {stage === "prep" && (
          <SleepPrepModal
            title="选择助眠模式"
            subtitle="需要一点声音陪你入睡吗？（不会再自动播放）"
            busy={handoffBusy}
            onConfirm={(ct) => void doHandoff(prepDeep, ct)}
            onCancel={() => { setPlanAsk(true); setStage("watch"); }}
          />
        )}
      </div>
    </div>
  );

  async function openEditPlan() {
    setPlanAsk(false);
    setEditPlan(true);
  }

  function demoNext() {
    switch (stage) {
      case "watch":
        firstRemind();
        break;
      case "r1":
        snooze();
        break;
      case "snooze":
        setStage("health");
        break;
      case "health":
        setStage("deep");
        break;
      default:
        break;
    }
  }
}

/* ================ 深夜计划修改面板（手机内，确认后继续助眠） ================ */

function PlanEditSheet({ notify, onCancel, onSaved }: { notify: (m: string, k?: "ok" | "err") => void; onCancel: () => void; onSaved: () => void }) {
  const [catalog, setCatalog] = useState<PlanTaskType[] | null>(null);
  const [existing, setExisting] = useState<Array<{ task_type: string; params: Record<string, string> }>>([]);
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void Promise.all([fetchPlanCatalog(), fetchPlanDraft()]).then(([cat, draft]) => {
      setCatalog(cat.task_types);
      const existed = draft.tasks.map((t) => ({ task_type: t.task_type, params: { ...t.params } }));
      setExisting(existed);
      setSel(new Set(existed.map((t) => t.task_type)));
    });
  }, []);

  function toggle(key: string) {
    setSel((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function saveAndContinue() {
    if (busy || !catalog) return;
    setBusy(true);
    try {
      const tasks = catalog
        .filter((t) => sel.has(t.key))
        .map((t) => {
          const prev = existing.find((e) => e.task_type === t.key);
          const params: Record<string, string> = {};
          for (const meta of t.params) {
            const before = prev?.params?.[meta.key];
            params[meta.key] =
              before != null && before !== "" ? before : meta.type === "spec" ? "weekly_v2" : meta.default || "";
          }
          return { category: t.category, task_type: t.key, title: t.name, params };
        });
      await savePlanDraft(tasks);
      notify(
        tasks.length > 0 ? `深夜计划已更新（${tasks.length} 个任务），继续助眠 🌙` : "已清空深夜计划，继续助眠 🌙",
        "ok"
      );
      onSaved();
    } catch (e) {
      notify(e instanceof Error ? e.message : "保存失败", "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-mask" style={{ zIndex: 95 }}>
      <div className="modal-box" style={{ maxWidth: 400, maxHeight: "86vh", overflow: "auto" }} role="dialog" aria-modal>
        <h2 style={{ fontSize: 18, fontWeight: 800, textAlign: "center" }}>✏️ 修改深夜计划</h2>
        <p className="muted" style={{ fontSize: 11.5, marginTop: 6, textAlign: "center" }}>
          勾选需要的任务，保存后继续助眠（明早查看交付）
        </p>
        {catalog === null ? (
          <p className="muted" style={{ marginTop: 14, textAlign: "center" }}>加载中…</p>
        ) : (
          <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
            {catalog.map((t) => {
              const checked = sel.has(t.key);
              return (
                <button
                  key={t.key}
                  className={`choice-card${checked ? " sel" : ""}`}
                  onClick={() => toggle(t.key)}
                  style={{ padding: "10px 12px" }}
                >
                  <span style={{ fontSize: 22 }}>{t.icon}</span>
                  <div style={{ flex: 1, textAlign: "left" }}>
                    <b style={{ fontSize: 13.5 }}>{t.name}</b>
                    <div className="muted" style={{ fontSize: 11, marginTop: 1 }}>{t.desc}</div>
                  </div>
                  <span style={{ fontSize: 16, color: checked ? "var(--gold)" : "var(--ink-faint)" }}>
                    {checked ? "✓" : "○"}
                  </span>
                </button>
              );
            })}
          </div>
        )}
        <div className="btn-row" style={{ marginTop: 16 }}>
          <button className="btn ghost" disabled={busy} onClick={onCancel}>‹ 取消</button>
          <button className="btn gold" disabled={busy || !catalog} onClick={() => void saveAndContinue()}>
            {busy ? "● 保存中…" : "保存并继续助眠"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ================= 抖音播放页 ================= */

interface ShortsPaneProps {
  mode: "watch" | "health";
  shortsOk: boolean;
  sleepOk: boolean;
  setShortsOk: (v: boolean) => void;
  setSleepOk: (v: boolean) => void;
  vol: boolean;
  setVol: (v: boolean) => void;
  grad: number;
  setGrad: (v: number) => void;
  like: number;
  liked: boolean;
  onLike: () => void;
  paused: boolean;
  onBackFromHealth?: () => void;
  onSleepFromHealth?: () => void;
}

function ShortsPane(props: ShortsPaneProps) {
  const { mode, paused } = props;
  const isHealth = mode === "health";
  const colors = ["#0b2a4a", "#22304f", "#3d2c4d", "#124c4a"];
  const vidRef = useRef<HTMLVideoElement | null>(null);

  // 暂停/恢复真实播放：提醒出现时必须真正暂停视频
  useEffect(() => {
    const el = vidRef.current;
    if (!el) return;
    if (paused) {
      el.pause();
    } else {
      const p = el.play();
      if (p) void p.catch(() => undefined);
    }
  }, [paused, isHealth]);

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        background: `linear-gradient(180deg, ${colors[props.grad % 4]} 0%, #05070f 88%)`,
        overflow: "hidden",
      }}
    >
      {isHealth ? (
        props.sleepOk ? (
          <video
            ref={vidRef}
            src="/videos/sleep.mp4"
            autoPlay
            loop
            muted
            playsInline
            onError={() => props.setSleepOk(false)}
            style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.92 }}
          />
        ) : (
          <FallbackPane title="晚安助眠 · 星空与呼吸" tags="#健康睡眠 #睡前放松" note="将 sleep.mp4 放入 frontend/public/videos 后自动播放真实视频" />
        )
      ) : props.shortsOk ? (
        <video
          ref={vidRef}
          src="/videos/tiktok.mp4"
          autoPlay
          loop
          muted={!props.vol}
          playsInline
          onError={() => props.setShortsOk(false)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      ) : (
        <FallbackPane title="工作日的最后一条" tags="#加班夜 #睡前刷到" note="将 tiktok.mp4 放入 frontend/public/videos 后自动播放真实视频" />
      )}

      <div
        style={{
          position: "absolute",
          top: 62,
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 55,
          background: "rgba(0,0,0,.5)",
          color: "#fff",
          fontSize: 11.5,
          borderRadius: 999,
          padding: "5px 12px",
          whiteSpace: "nowrap",
        }}
      >
        {isHealth ? "😴 OKSleep · 健康睡眠内容" : "23:00 · OKSleep 睡前监测中"}
      </div>

      {/* 右侧互动栏 */}
      <div style={{ position: "absolute", right: 10, bottom: 120, zIndex: 55, display: "flex", flexDirection: "column", gap: 18, alignItems: "center", color: "#fff" }}>
        <button onClick={props.onLike} style={{ background: "none", border: "none", color: "#fff", textAlign: "center", cursor: "pointer" }}>
          <span style={{ fontSize: 30, color: props.liked ? "#fe2c55" : "#fff", display: "block" }}>♥</span>
          <span style={{ fontSize: 11 }}>{props.like.toLocaleString()}</span>
        </button>
        <div style={{ textAlign: "center" }}>
          <span style={{ fontSize: 26, display: "block" }}>💬</span>
          <span style={{ fontSize: 11 }}>1.2w</span>
        </div>
        <div style={{ textAlign: "center" }}>
          <span style={{ fontSize: 24, display: "block" }}>★</span>
          <span style={{ fontSize: 11 }}>收藏</span>
        </div>
        <div style={{ textAlign: "center" }}>
          <span style={{ fontSize: 24, display: "block" }}>↻</span>
          <span style={{ fontSize: 11 }}>分享</span>
        </div>
      </div>

      {/* 底部文案 */}
      <div style={{ position: "absolute", left: 14, right: 84, bottom: isHealth ? 96 : 36, zIndex: 55, color: "#fff", textShadow: "0 1px 8px rgba(0,0,0,.6)" }}>
        {isHealth ? (
          <>
            <div style={{ fontSize: 17, fontWeight: 800 }}>晚安 · 深睡引导</div>
            <p style={{ fontSize: 12.5, opacity: .9, marginTop: 6, lineHeight: 1.7 }}>
              呼吸放松 · 无算法刺激 · 来自 OKSleep 健康睡眠频道
            </p>
          </>
        ) : (
          <>
            <div style={{ fontSize: 15, fontWeight: 700 }}>@深夜打工人</div>
            <div style={{ fontSize: 13, opacity: .95, marginTop: 4 }}>睡前刷到的第 N 条… 今天也辛苦啦 🌙</div>
            <div style={{ fontSize: 12.5, opacity: .8, marginTop: 4 }}>#加班夜 #助眠 #按时睡觉打卡</div>
          </>
        )}
      </div>

      {!isHealth && (
        <button
          onClick={() => props.setVol(!props.vol)}
          style={{ position: "absolute", top: 60, left: 12, zIndex: 55, background: "rgba(0,0,0,.4)", border: "none", color: "#fff", fontSize: 17, width: 34, height: 34, borderRadius: "50%", cursor: "pointer" }}
        >
          {props.vol ? "🔊" : "🔇"}
        </button>
      )}

      {/* 健康页操作：返回 / 好了，去休息 */}
      {isHealth && props.onBackFromHealth && props.onSleepFromHealth && (
        <div style={{ position: "absolute", left: 14, right: 14, bottom: 26, zIndex: 56, display: "flex", gap: 10 }}>
          <button className="btn ghost" style={{ flex: 1, fontSize: 13 }} onClick={props.onBackFromHealth}>‹ 返回刚才的视频</button>
          <button className="btn gold" style={{ flex: 1, fontSize: 13 }} onClick={props.onSleepFromHealth}>😴 好了，去休息</button>
        </div>
      )}

      {paused && (
        <div style={{ position: "absolute", inset: 0, zIndex: 54, display: "grid", placeItems: "center", background: "rgba(2,6,16,.35)" }}>
          <span style={{ color: "#fff", fontSize: 42, opacity: .9 }}>⏸</span>
        </div>
      )}
    </div>
  );
}

function FallbackPane({ title, tags, note }: { title: string; tags: string; note: string }) {
  return (
    <div style={{ width: "100%", height: "100%", display: "grid", placeItems: "center", background: "radial-gradient(circle at 70% 20%, #27448a, #060a1c 60%)", color: "#fff", textAlign: "center", padding: "0 26px" }}>
      <div>
        <div style={{ fontSize: 40, animation: "breathe 4s ease-in-out infinite" }}>🎬</div>
        <b style={{ fontSize: 17, display: "block", marginTop: 12 }}>{title}</b>
        <p style={{ fontSize: 12.5, opacity: .85, marginTop: 8 }}>{tags}</p>
        <p style={{ fontSize: 11.5, opacity: .6, marginTop: 14, lineHeight: 1.7 }}>{note}</p>
      </div>
    </div>
  );
}

function PermOverlay({ onAllow, notify }: { onAllow: () => void; notify: (m: string, k?: "ok" | "err") => void }) {
  const [checked, setChecked] = useState(false);
  return (
    <div style={{ width: "100%", height: "100%", display: "grid", placeItems: "center", padding: 24, background: "linear-gradient(170deg,#1a2350,#070b1f 80%)" }}>
      <div style={{ width: "100%", maxWidth: 380 }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 46 }}>🌙</div>
          <h2 style={{ fontSize: 21, fontWeight: 800, marginTop: 10 }}>OKSleep 需要以下权限</h2>
          <p className="muted" style={{ marginTop: 6 }}>用于在睡前自动接管播放与按时提醒（演示用，数据均保存在本地）</p>
        </div>
        <div style={{ marginTop: 18, display: "grid", gap: 10 }}>
          {[
            { icon: "🔔", name: "通知提醒", desc: "到达睡前 30 分钟窗口时发送提醒" },
            { icon: "🎛️", name: "媒体播放控制", desc: "可暂停当前视频 / 切换到健康睡眠内容" },
            { icon: "⏳", name: "后台运行监测", desc: "识别你仍在使用的应用（如短视频）" },
          ].map((p) => (
            <div key={p.name} style={{ display: "flex", gap: 12, background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.1)", borderRadius: 14, padding: "12px 14px" }}>
              <span style={{ fontSize: 24 }}>{p.icon}</span>
              <div>
                <b style={{ fontSize: 14 }}>{p.name}</b>
                <div style={{ fontSize: 12, opacity: .75, marginTop: 2 }}>{p.desc}</div>
              </div>
            </div>
          ))}
        </div>
        <button className="btn block" style={{ marginTop: 20 }} disabled={!checked} onClick={() => { onAllow(); notify("已获得演示授权：通知 / 媒体控制 / 后台监测", "ok"); }}>
          允许（模拟授权）
        </button>
        <label style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center", marginTop: 14, fontSize: 12, color: "var(--ink-dim)", cursor: "pointer" }}>
          <input type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)} />
          我已知晓：本页为演示还原，所有数据均在本地
        </label>
        <p className="muted" style={{ textAlign: "center", marginTop: 8, fontSize: 11 }}>真实版本将引导你在系统设置中完成授权</p>
      </div>
    </div>
  );
}

function nowTime() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}
