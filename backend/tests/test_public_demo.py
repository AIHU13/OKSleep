"""公开演示模式行为测试（新访客自动重置 / 不打断进行中的会话）。"""
import pytest

from app import clock
from app.services import intervention_service, session_service
from app.services.session_service import maybe_reset_public


def _seed_profile_ok(conn):
    conn.execute("UPDATE user_profile SET total_coins = 10, streak_days = 3 WHERE id = 1")
    conn.commit()


def _seed_finished_trace(conn):
    """残留完成痕迹：历史会话/奖励等（无进行中会话）。"""
    conn.execute(
        "INSERT INTO sleep_sessions (user_id, date, state, started_at, updated_at, created_at) "
        "VALUES (1, '2026-09-03', 'REWARD', '2026-09-03 23:00:00', '2026-09-04 08:00:00', "
        "'2026-09-03 23:00:00')"
    )
    conn.execute(
        "INSERT INTO reward_records (session_id, user_id, date, coins, streak_after, total_after, created_at) "
        "VALUES (1, 1, '2026-09-04', 10, 1, 10, '2026-09-04 08:00:00')"
    )
    conn.commit()


@pytest.mark.parametrize("public", [True, False])
def test_reset_only_in_public_mode(conn, monkeypatch, public):
    monkeypatch.setattr(session_service.settings, "public_demo", public)
    _seed_profile_ok(conn)
    _seed_finished_trace(conn)

    maybe_reset_public(conn)

    profile = session_service.get_profile(conn)
    if public:
        assert profile.total_coins == 0 and profile.streak_days == 0
    else:
        assert profile.total_coins == 10 and profile.streak_days == 3


def test_reset_skipped_when_session_active(conn, monkeypatch):
    monkeypatch.setattr(session_service.settings, "public_demo", True)
    _seed_profile_ok(conn)

    # 建立一个进行中的会话：不应被打断
    clock.set_virtual_now(conn, clock.combine_date_hm(clock.now_dt().date(), "23:00"))
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "shorts")

    maybe_reset_public(conn)

    profile = session_service.get_profile(conn)
    assert profile.total_coins == 10
    assert session_service.active_session(conn) is not None
