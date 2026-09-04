import { useCallback, useEffect, useRef, useState } from "react";
import { loadAppState } from "./api/endpoints";
import { ApiError } from "./api/client";
import DemoControl from "./components/DemoControl";
import Sky from "./components/Sky";
import TopBar from "./components/TopBar";
import Home from "./pages/Home";
import Intervention from "./pages/Intervention";
import PhoneSim from "./pages/PhoneSim";
import Record from "./pages/Record";
import Reward from "./pages/Reward";
import Scenario from "./pages/Scenario";
import Shop from "./pages/Shop";
import SleepMode from "./pages/SleepMode";
import type { AppState, Screen } from "./types";

/** 会话状态 -> 页面 */
function screenFromState(state: string): Screen {
  if (state === "BEDTIME_START") return { name: "scenario" };
  if (state.startsWith("STAGE_")) return { name: "intervention" };
  if (state === "SLEEP_MODE" || state === "SLEEP_SUCCESS") return { name: "sleep" };
  return { name: "home" };
}

function msgOf(e: unknown): string {
  return e instanceof ApiError || e instanceof Error ? e.message : "发生未知错误";
}

export default function App() {
  const [view, setView] = useState<AppState | null>(null);
  const [screen, setScreen] = useState<Screen>({ name: "home" });
  const [notice, setNotice] = useState<{ text: string; kind: "ok" | "err" } | null>(null);
  const [syncing, setSyncing] = useState(false);
  const screenRef = useRef<Screen>({ name: "home" });
  screenRef.current = screen;

  const notify = useCallback((text: string, kind: "ok" | "err" = "err") => {
    setNotice({ text, kind });
    window.setTimeout(() => setNotice(null), 3800);
  }, []);

  /** 提交后端视图：更新数据并（非独立页面时）自动导航。
   *  reward/record/shop 为独立功能区，页面内自行控制返回。 */
  const commit = useCallback((d: AppState) => {
    setView(d);
    const current = screenRef.current.name;
    if (
      current !== "reward" &&
      current !== "record" &&
      current !== "shop" &&
      current !== "phone"
    ) {
      setScreen(d.session ? screenFromState(d.session.state) : { name: "home" });
    }
  }, []);

  const silentRefresh = useCallback(async () => {
    try {
      const d = await loadAppState();
      commit(d);
    } catch {
      /* 静默轮询失败不打扰用户 */
    }
  }, [commit]);

  /** 动作执行器：成功提交视图并自动跳转，失败提示。
   *  执行期间显示顶部"正在同步"指示条，避免把等待误认为卡死。 */
  const run = useCallback(
    async (fn: () => Promise<AppState>): Promise<boolean> => {
      setSyncing(true);
      try {
        const d = await fn();
        commit(d);
        return true;
      } catch (e) {
        notify(msgOf(e));
        return false;
      } finally {
        setSyncing(false);
      }
    },
    [commit, notify]
  );

  const backHome = useCallback(async () => {
    try {
      const d = await loadAppState();
      setView(d);
      setScreen({ name: "home" });
    } catch (e) {
      notify(msgOf(e));
    }
  }, [notify]);

  /** 打开功能页：先同步最新数据，再进入对应页面 / 手机模拟层。 */
  const openPage = useCallback(
    async (page: "record" | "shop" | "phone") => {
      try {
        const d = await loadAppState();
        setView(d);
        if (page === "phone") setScreen({ name: "phone" });
        else setScreen(page === "record" ? { name: "record" } : { name: "shop" });
      } catch (e) {
        notify(msgOf(e));
      }
    },
    [notify]
  );

  const exitPhone = useCallback(async () => {
    try {
      const d = await loadAppState();
      setView(d);
      setScreen({ name: "home" });
    } catch (e) {
      notify(msgOf(e));
    }
  }, [notify]);

  /** 手机模拟层交接：直接进入助眠模式页。 */
  const phoneHandoff = useCallback((d: AppState) => {
    setView(d);
    setScreen(d.session ? screenFromState(d.session.state) : { name: "home" });
  }, []);

  const goShop = () => {
    void openPage("shop");
  };

  // 启动：加载 AppState（刷新页面后从后端恢复 Session）
  useEffect(() => {
    let alive = true;
    loadAppState()
      .then((d) => {
        if (!alive) return;
        setView(d);
        setScreen(d.session ? screenFromState(d.session.state) : { name: "home" });
      })
      .catch((e) => notify(`无法连接后端：${msgOf(e)}`));
    return () => {
      alive = false;
    };
  }, [notify]);

  if (!view) {
    return (
      <>
        <Sky />
        <div className="loading-wrap">
          <div className="moon-spin" />
        </div>
        {notice && (
          <div className={`notice ${notice.kind === "ok" ? "ok" : "err"}`}>{notice.text}</div>
        )}
      </>
    );
  }

  return (
    <>
      <Sky />
      {syncing && (
        <>
          <div className="sync-bar" />
          <div className="sync-toast">正在同步 · 即将为你跳转…</div>
        </>
      )}
      {notice && (
        <div className={`notice ${notice.kind === "ok" ? "ok" : "err"}`}>{notice.text}</div>
      )}

      <div className="shell">
        <div className="content">
          <TopBar view={view} />

          {/* 各页面组件；session 为空时展示 Home */}
          {screen.name === "reward" ? (
            <div key="screen-reward" style={{ marginTop: 16 }}>
              <Reward
                data={(screen as Extract<Screen, { name: "reward" }>).data}
                onDone={backHome}
                onShop={goShop}
              />
            </div>
          ) : screen.name === "record" ? (
            <div key="screen-record" style={{ marginTop: 16 }}>
              <Record view={view} onBack={backHome} notify={notify} />
            </div>
          ) : screen.name === "shop" ? (
            <div key="screen-shop" style={{ marginTop: 16 }}>
              <Shop view={view} run={run} onBack={backHome} notify={notify} />
            </div>
          ) : !view.session ? (
            <div key="screen-home" style={{ marginTop: 16 }}>
              <Home view={view} run={run} openPage={openPage} notify={notify} />
            </div>
          ) : (
            /* key 绑定会话状态/阶段：每次推进后整页重放入场动画，明确"已自动跳转/刷新" */
            <div
              key={`screen:${screen.name}:${view.session.session_id}:${view.session.state}:${view.session.stage ?? "-"}`}
              style={{ marginTop: 16 }}
            >
              {screen.name === "scenario" && (
                <Scenario
                  run={run}
                  sessionId={view.session.session_id}
                  notify={notify}
                />
              )}
              {screen.name === "intervention" && (
                <Intervention view={view} run={run} notify={notify} />
              )}
              {screen.name === "sleep" && (
                <SleepMode
                  view={view}
                  run={run}
                  silentRefresh={silentRefresh}
                  onReward={(data) => setScreen({ name: "reward", data })}
                  notify={notify}
                />
              )}
            </div>
          )}
        </div>
      </div>

      <DemoControl onChanged={commit} notify={notify} />

      {/* 手机场景模拟层（全屏） */}
      {screen.name === "phone" && (
        <PhoneSim onExit={exitPhone} onHandoff={phoneHandoff} notify={notify} />
      )}
    </>
  );
}
