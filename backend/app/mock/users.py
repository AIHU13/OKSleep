"""Mock 用户数据源。默认画像见 db/init_db.py（避免双份种子逻辑）。"""

DEFAULT_PROFILE = {
    "weekday_bedtime": "23:30",
    "weekday_wake": "07:30",
    "weekend_bedtime": "23:30",
    "weekend_wake": "07:30",
    "preferred_content": ["music", "story"],
}
