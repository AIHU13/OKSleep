"""助眠失败记录与积分扣除测试（手机场景模拟）。"""
import pytest

from app.services import reward_service, session_service


def test_miss_deducts_and_clamps(conn):
    # 预置积分 12
    conn.execute(
        "UPDATE user_profile SET total_coins = 12 WHERE id = 1"
    )
    conn.commit()

    r1 = reward_service.miss(conn, "shorts")
    assert r1["coins_deducted"] == 5 and r1["coins_left"] == 7

    r2 = reward_service.miss(conn, "working")
    assert r2["coins_deducted"] == 5 and r2["coins_left"] == 2

    # 积分不足时扣至 0，不为负
    r3 = reward_service.miss(conn, "shorts")
    assert r3["coins_deducted"] == 2 and r3["coins_left"] == 0

    profile = session_service.get_profile(conn)
    assert profile.total_coins == 0

    # 失败记录进入历史（kind=miss，带负积分标记）
    hist = session_service.history(conn)
    miss_items = [h for h in hist if h["kind"] == "miss"]
    assert len(miss_items) == 3
    assert miss_items[0]["coins"] == -2
    assert "助眠失败" in miss_items[0]["result"]
