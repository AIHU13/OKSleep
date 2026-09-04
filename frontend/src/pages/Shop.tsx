import { useCallback, useEffect, useState } from "react";
import {
  fetchFoodOrders,
  fetchOrders,
  fetchShopItems,
  loadAppState,
  placeFoodOrder,
  redeemShopItem,
} from "../api/endpoints";
import type { AppState, FoodOrderItem, ShopOrder, ShopProduct } from "../types";

interface Props {
  view: AppState;
  run: (fn: () => Promise<AppState>) => Promise<boolean>;
  onBack: () => void;
  notify: (msg: string, kind?: "ok" | "err") => void;
}

/** 页面 7：积分兑换区（Mock 商品，后续填充真实内容）。 */
export default function Shop({ view, run, onBack, notify }: Props) {
  const [items, setItems] = useState<ShopProduct[] | null>(null);
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [food, setFood] = useState<FoodOrderItem[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);
  const coins = view.profile.total_coins;

  const loadOrders = useCallback(() => {
    fetchOrders()
      .then((r) => setOrders(r.items))
      .catch(() => setOrders([]));
  }, []);

  const loadFood = useCallback(() => {
    fetchFoodOrders()
      .then((r) => setFood(r.items))
      .catch(() => setFood([]));
  }, []);

  useEffect(() => {
    fetchShopItems()
      .then((r) => setItems(r.items))
      .catch((e) => notify(e instanceof Error ? e.message : "加载失败", "err"));
    loadOrders();
    loadFood();
  }, [notify, loadOrders, loadFood]);

  // 外卖配送中时轮询接单动态
  const foodActive = food.some((f) => !f.delivered);
  useEffect(() => {
    if (!foodActive) return;
    const timer = window.setInterval(loadFood, 4000);
    return () => window.clearInterval(timer);
  }, [foodActive, loadFood]);

  async function redeem(item: ShopProduct) {
    if (busyId !== null) return;
    let note: string | undefined;
    if (item.custom) {
      const answer = window.prompt("写下一件想送自己的礼物（将作为你的专属激励目标）：", "一次周末旅行");
      if (answer === null) return; // 用户取消
      note = answer;
    }
    setBusyId(item.id);
    let ok = false;
    let msg = "";
    try {
      ok = await run(async () => {
        const res = await redeemShopItem(item.id, note ?? undefined);
        msg = res.message;
        return await loadAppState(); // 刷新积分
      });
    } finally {
      setBusyId(null);
    }
    if (ok) {
      notify(msg || "兑换成功", "ok");
      loadOrders();
      // 暖心早餐：询问是否自动下单外卖（服务 Agent 演示后续真实能力）
      if (item.kind === "breakfast" || item.id === 7) {
        const auto = window.confirm("兑换成功！是否自动下单外卖，明早配送到家？");
        if (auto) {
          try {
            await placeFoodOrder("redeem_breakfast");
            notify("已自动下单外卖 🛵 请留意接单动态", "ok");
            loadFood();
          } catch (e) {
            notify(e instanceof Error ? e.message : "下单失败", "err");
          }
        }
      }
    }
  }

  return (
    <div className="page">
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button className="btn ghost sm" onClick={onBack}>
          ‹ 返回
        </button>
        <h1 className="h1" style={{ fontSize: 22 }}>
          🎁 积分兑换
        </h1>
      </div>

      {/* 余额 */}
      <section className="card" style={{ marginTop: 16, textAlign: "center" }}>
        <div className="muted">我的 Sleep Coins</div>
        <div style={{ fontSize: 44, fontWeight: 850, color: "var(--gold)", marginTop: 4 }}>
          {coins}
        </div>
        <div className="muted" style={{ marginTop: 2 }}>
          每完成一晚规律作息 +10 · 连续打卡 {view.profile.streak_days} 天
        </div>
        <div className="ai-note" style={{ marginTop: 14, textAlign: "left" }}>
          ✨ <b>AI 礼品建议（规划中）：</b>接入 LLM 后，将结合你的睡眠积分与作息表现，
          智能推荐最适合你的激励礼品与兑换时机。
        </div>
      </section>

      {/* 商品 */}
      <section style={{ marginTop: 18 }}>
        <div className="h2" style={{ fontSize: 16 }}>
          🛍️ 兑换好物（示例商品）
        </div>
        <p className="muted" style={{ marginTop: 4 }}>
          以下为模拟展示，用于演示「攒积分 → 兑换激励」闭环；后续可替换真实商品
        </p>

        {items === null ? (
          <p className="muted" style={{ marginTop: 16, textAlign: "center" }}>
            加载中…
          </p>
        ) : (
          <div
            style={{
              marginTop: 12,
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: 12,
            }}
          >
            {items.map((item) => {
              const afford = coins >= item.price_coins;
              return (
                <div
                  key={item.id}
                  className="card"
                  style={{
                    padding: "18px 16px",
                    display: "flex",
                    flexDirection: "column",
                    margin: 0,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 30 }}>{item.icon}</span>
                    <span
                      className="tag"
                      style={{
                        background: "rgba(185,168,255,.14)",
                        color: "#d4c7ff",
                        borderColor: "rgba(185,168,255,.4)",
                      }}
                    >
                      {item.tag}
                    </span>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: 15, marginTop: 10 }}>{item.name}</div>
                  <div className="muted" style={{ fontSize: 11, marginTop: 2 }}>
                    {item.brand}
                  </div>
                  <div className="sub" style={{ fontSize: 12.5, marginTop: 8, flex: 1 }}>
                    {item.desc}
                  </div>
                  <div style={{ marginTop: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <b style={{ color: afford ? "var(--gold)" : "var(--danger)", fontSize: 16 }}>
                      {item.price_coins} 🪙
                    </b>
                    <span className="muted" style={{ fontSize: 11 }}>
                      库存 {item.stock}
                    </span>
                  </div>
                  <button
                    className={`btn sm ${afford ? "gold" : "ghost"}`}
                    style={{ marginTop: 10, width: "100%" }}
                    disabled={!afford || busyId !== null}
                    onClick={() => redeem(item)}
                  >
                    {busyId === item.id
                      ? "● 兑换中…"
                      : afford
                        ? "兑换"
                        : `还差 ${item.price_coins - coins} 🪙`}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* 兑换记录 */}
      <section className="card" style={{ marginTop: 18 }}>
        <div className="h2" style={{ fontSize: 16 }}>
          📦 兑换记录
        </div>
        {orders.length === 0 ? (
          <p className="muted" style={{ marginTop: 12, textAlign: "center" }}>
            暂无兑换记录
          </p>
        ) : (
          <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
            {orders.map((o) => (
              <div
                key={o.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 12px",
                  borderRadius: 12,
                  background: "rgba(255,255,255,.04)",
                }}
              >
                <span style={{ fontSize: 20 }}>{o.item_icon ?? "🎁"}</span>
                <span style={{ flex: 1, fontSize: 14 }}>{o.item_name}</span>
                <span style={{ color: "var(--gold)", fontSize: 13, fontWeight: 700 }}>
                  -{o.coins_spent} 🪙
                </span>
                <span className="tag">{o.status === "delivering" ? "派送中" : o.status}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 暖心早餐 · 外卖接单动态 */}
      <section className="card" style={{ marginTop: 18 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <div className="h2" style={{ fontSize: 16 }}>
            🛵 暖心早餐 · 外卖动态
          </div>
          <span className="tag ai">服务 Agent · Mock</span>
        </div>
        <p className="muted" style={{ marginTop: 4 }}>
          兑换「暖心早餐」后可自动下单；此处实时展示下单与接单情况（可用 ⚙️ 快进时间观察配送）
        </p>
        {food.length === 0 ? (
          <p className="muted" style={{ marginTop: 12, textAlign: "center" }}>
            还没有外卖订单 —— 兑换一杯暖心早餐试试（10 🪙）
          </p>
        ) : (
          <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
            {food.map((f) => (
              <div
                key={f.id}
                style={{
                  padding: "12px 14px",
                  borderRadius: 14,
                  background: "rgba(255,217,138,.06)",
                  border: "1px solid rgba(255,217,138,.2)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                  <b style={{ fontSize: 14 }}>
                    🥐 {f.item_name}
                  </b>
                  <span
                    className="tag"
                    style={{
                      color: f.delivered ? "var(--success)" : "var(--gold)",
                      borderColor: f.delivered ? "rgba(125,227,164,.4)" : "rgba(255,217,138,.4)",
                    }}
                  >
                    {f.delivered ? "✅ 已送达" : f.stage_label}
                  </span>
                </div>
                {f.note && <div className="muted" style={{ fontSize: 11.5, marginTop: 4 }}>备注：{f.note}</div>}
                <p style={{ marginTop: 7, fontSize: 13, color: "#ffe6b3" }}>🛵 {f.message}</p>
                <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
                  {["placed", "accepted", "pickup", "delivering", "delivered"].map((key, i) => (
                    <div key={key} style={{ flex: 1, textAlign: "center" }}>
                      <div
                        style={{
                          width: 12,
                          height: 12,
                          margin: "0 auto",
                          borderRadius: "50%",
                          background:
                            i <= f.stage_index
                              ? i === f.stage_index && !f.delivered
                                ? "var(--gold)"
                                : "var(--success)"
                              : "rgba(255,255,255,.12)",
                          boxShadow:
                            i === f.stage_index && !f.delivered
                              ? "0 0 0 5px rgba(255,217,138,.18)"
                              : "none",
                          transition: "all .3s ease",
                        }}
                      />
                      <div className="muted" style={{ fontSize: 9.5, marginTop: 4, whiteSpace: "nowrap" }}>
                        {["已下单", "商家接单", "骑手取餐", "配送中", "已送达"][i]}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
