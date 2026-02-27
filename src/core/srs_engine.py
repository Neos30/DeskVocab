from datetime import datetime, timedelta
import math

class SRSEngine:
    """
    基于 SM-2 算法的间隔重复引擎
    """
    @staticmethod
    def calculate_next_review(ease_factor, interval, repetition, quality):
        """
        quality: 0-5 (0: 不清楚, 3: 模糊, 5: 已掌握)
        """
        if quality >= 3:
            if repetition == 0:
                interval = 1
            elif repetition == 1:
                interval = 6
            else:
                interval = math.ceil(interval * ease_factor)
            repetition += 1
        else:
            repetition = 0
            interval = 1

        # 更新简易度因子 (Ease Factor)
        ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if ease_factor < 1.3:
            ease_factor = 1.3

        next_review_time = datetime.now() + timedelta(days=interval)
        return ease_factor, interval, repetition, next_review_time

class SRSCoordinator:
    def __init__(self, db_manager):
        self.db = db_manager

    def update_word_review(self, word_id, quality):
        # 获取当前状态
        res = self.db.fetch_all("SELECT ease_factor, interval, repetition FROM review_stats WHERE word_id = ?", (word_id,))
        if not res:
            # 初始数据
            ef, iv, rep, next_time = SRSEngine.calculate_next_review(2.5, 0, 0, quality)
            self.db.execute(
                "INSERT INTO review_stats (word_id, ease_factor, interval, repetition, next_review_time, status) VALUES (?, ?, ?, ?, ?, ?)",
                (word_id, ef, iv, rep, next_time.strftime('%Y-%m-%d %H:%M:%S'), 1 if quality == 5 else 0)
            )
        else:
            ef, iv, rep = res[0]
            new_ef, new_iv, new_rep, next_time = SRSEngine.calculate_next_review(ef, iv, rep, quality)
            self.db.execute(
                "UPDATE review_stats SET ease_factor=?, interval=?, repetition=?, next_review_time=?, status=? WHERE word_id=?",
                (new_ef, new_iv, new_rep, next_time.strftime('%Y-%m-%d %H:%M:%S'), 1 if quality == 5 else 0, word_id)
            )

    def get_todays_words(self, limit=10):
        query = """
        SELECT w.* FROM words w
        LEFT JOIN review_stats r ON w.id = r.word_id
        WHERE r.next_review_time <= DATETIME('now', 'localtime') OR r.word_id IS NULL
        ORDER BY r.next_review_time ASC
        LIMIT ?
        """
        return self.db.fetch_all(query, (limit,))
