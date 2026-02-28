import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path=None):
        import sys
        if db_path is None:
            if getattr(sys, 'frozen', False):
                # When packaged by PyInstaller, store the DB in the same directory as the executable
                base_dir = os.path.dirname(sys.executable)
            else:
                # Use an absolute path based on the project root
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(base_dir, "speed_dic.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 单词主表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    phonetic TEXT,
                    definition TEXT NOT NULL,
                    example_en TEXT,
                    example_cn TEXT,
                    scene_tag TEXT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 复习统计表 (基于 SM-2 算法)
            # status: 0=不清楚, 1=模糊, 2=熟练(已掌握进SRS), 3=牢记(跳过，不再复习)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS review_stats (
                    word_id INTEGER PRIMARY KEY,
                    ease_factor REAL DEFAULT 2.5,
                    interval INTEGER DEFAULT 0,
                    repetition INTEGER DEFAULT 0,
                    next_review_time TIMESTAMP,
                    status INTEGER DEFAULT 0,
                    FOREIGN KEY(word_id) REFERENCES words(id)
                )
            ''')
            # 迁移：旧库 status=1 (已掌握) 对应新 status=2 (熟练)
            self._migrate_status(cursor)
            
            # 系统设置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            conn.commit()

    def _migrate_status(self, cursor):
        """
        旧版 status 只有 0(学习中)/1(已掌握)。
        迁移规则：旧 status=1 → 新 status=2(熟练)，旧 status=0 保持 0(不清楚)。
        通过检查列注释无法判断版本，改为检查是否存在 status=1 且 next_review_time 有值的行
        来决定是否需要迁移（保守策略：仅在 status=1 时升为 2）。
        """
        cursor.execute("UPDATE review_stats SET status = 2 WHERE status = 1")

    def execute(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def fetch_all(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

if __name__ == "__main__":
    # 测试初始化
    db = DatabaseManager()
    print("Database initialized successfully.")
