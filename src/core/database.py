import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path="speed_dic.db"):
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS review_stats (
                    word_id INTEGER PRIMARY KEY,
                    ease_factor REAL DEFAULT 2.5,
                    interval INTEGER DEFAULT 0,
                    repetition INTEGER DEFAULT 0,
                    next_review_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status INTEGER DEFAULT 0, -- 0: 学习中, 1: 已掌握
                    FOREIGN KEY(word_id) REFERENCES words(id)
                )
            ''')
            
            # 系统设置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            conn.commit()

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
