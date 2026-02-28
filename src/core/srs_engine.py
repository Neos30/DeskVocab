from datetime import datetime, timedelta
import math


# 用户操作与 SM-2 quality 值的映射
# 跳过操作不走 SRS，使用独立的 skip_word() 路径
QUALITY_MAP = {
    "unclear":  0,   # 不清楚 → 高频复习
    "vague":    3,   # 模糊   → 约 1 天后
    "mastered": 5,   # 已掌握 → 长期低频
}

# status 字段含义
STATUS_UNCLEAR  = 0   # 不清楚
STATUS_VAGUE    = 1   # 模糊
STATUS_MASTERED = 2   # 熟练（已掌握，走 SRS）
STATUS_SKIPPED  = 3   # 牢记（跳过，不再复习）


class SRSEngine:
    """
    基于 SM-2 算法的间隔重复引擎
    """
    @staticmethod
    def calculate_next_review(ease_factor, interval, repetition, quality):
        """
        quality: 使用 QUALITY_MAP 中的值（0/3/5）
        返回: (ease_factor, interval, repetition, next_review_time)
        """
        if quality >= 3:
            if repetition == 0:
                interval = 1
            elif repetition == 1:
                interval = 6
            else:
                interval = math.ceil(interval * ease_factor)
            repetition += 1
            next_review_time = datetime.now() + timedelta(days=interval)
        else:
            # 不清楚：10 分钟后再次复现
            repetition = 0
            interval = 0
            next_review_time = datetime.now() + timedelta(minutes=10)

        ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if ease_factor < 1.3:
            ease_factor = 1.3

        return ease_factor, interval, repetition, next_review_time


class SRSCoordinator:
    def __init__(self, db_manager):
        self.db = db_manager

    def update_word_review(self, word_id, action: str):
        """
        根据用户操作更新 SRS 状态。
        action: "unclear" | "vague" | "mastered"
        跳过操作请使用 skip_word()。
        """
        quality = QUALITY_MAP[action]
        status = {
            "unclear":  STATUS_UNCLEAR,
            "vague":    STATUS_VAGUE,
            "mastered": STATUS_MASTERED,
        }[action]

        res = self.db.fetch_all(
            "SELECT ease_factor, interval, repetition FROM review_stats WHERE word_id = ?",
            (word_id,)
        )
        if not res:
            ef, iv, rep, next_time = SRSEngine.calculate_next_review(2.5, 0, 0, quality)
            self.db.execute(
                "INSERT INTO review_stats (word_id, ease_factor, interval, repetition, next_review_time, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (word_id, ef, iv, rep, next_time.strftime('%Y-%m-%d %H:%M:%S'), status)
            )
        else:
            ef, iv, rep = res[0]
            new_ef, new_iv, new_rep, next_time = SRSEngine.calculate_next_review(ef, iv, rep, quality)
            self.db.execute(
                "UPDATE review_stats SET ease_factor=?, interval=?, repetition=?, next_review_time=?, status=? "
                "WHERE word_id=?",
                (new_ef, new_iv, new_rep, next_time.strftime('%Y-%m-%d %H:%M:%S'), status, word_id)
            )

    def skip_word(self, word_id):
        """
        跳过操作：直接标记为"牢记"，不进入 SRS，不写入 next_review_time。
        """
        res = self.db.fetch_all(
            "SELECT word_id FROM review_stats WHERE word_id = ?", (word_id,)
        )
        if not res:
            self.db.execute(
                "INSERT INTO review_stats (word_id, ease_factor, interval, repetition, next_review_time, status) "
                "VALUES (?, 2.5, 0, 0, NULL, ?)",
                (word_id, STATUS_SKIPPED)
            )
        else:
            self.db.execute(
                "UPDATE review_stats SET status=?, next_review_time=NULL WHERE word_id=?",
                (STATUS_SKIPPED, word_id)
            )

    def get_todays_words(self, limit=10):
        """
        返回今日待复习单词：next_review_time 已到期，且未被标记为牢记（status != 3）。
        新词（无 review_stats 记录）也包含在内。
        """
        query = """
        SELECT w.* FROM words w
        LEFT JOIN review_stats r ON w.id = r.word_id
        WHERE (r.next_review_time <= DATETIME('now', 'localtime') OR r.word_id IS NULL)
          AND (r.status IS NULL OR r.status != ?)
        ORDER BY r.next_review_time ASC
        LIMIT ?
        """
        return self.db.fetch_all(query, (STATUS_SKIPPED, limit))
