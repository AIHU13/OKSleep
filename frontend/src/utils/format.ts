/** 通用小工具。 */

/** "YYYY-MM-DD HH:MM:SS" -> 显示用 {time:"23:06", week:"周四", date:"9月3日"} */
export function formatClock(iso?: string | null): {
  time: string;
  week: string;
  date: string;
} | null {
  if (!iso) return null;
  const d = new Date(iso.replace(" ", "T"));
  if (Number.isNaN(d.getTime())) return null;
  const weeks = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return {
    time: `${hh}:${mm}`,
    week: weeks[d.getDay()],
    date: `${d.getMonth() + 1}月${d.getDate()}日`,
  };
}

/** 秒 -> "MM:SS" / "HH:MM:SS" */
export function formatSec(total: number | null | undefined): string {
  if (total == null) return "--:--";
  const s = Math.max(0, Math.floor(total));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(sec).padStart(2, "0");
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

/** 睡眠剩余进度 0-1 */
export function sleepProgress(remainingSec: number | null | undefined, total = 3600): number {
  if (remainingSec == null) return 0;
  const p = 1 - Math.max(0, remainingSec) / total;
  return Math.min(1, Math.max(0, p));
}
