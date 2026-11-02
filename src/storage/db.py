# src/db.py
import sqlite3
from typing import Optional, Tuple, Any


class Database:
    def __init__(self, path: str):
        self.path = path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self._conn() as conn:
            cur = conn.cursor()

            # ---------------- settings ----------------
            cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """)

            # ---------------- users ----------------
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # ---- Migraciones seguras (ADD COLUMN) ----
            def _add_col(sql: str):
                try:
                    cur.execute(sql)
                except sqlite3.OperationalError:
                    pass

            _add_col("ALTER TABLE users ADD COLUMN email TEXT;")
            _add_col("ALTER TABLE users ADD COLUMN phone TEXT;")
            _add_col("ALTER TABLE users ADD COLUMN full_name TEXT;")
            _add_col("ALTER TABLE users ADD COLUMN farm_location TEXT;")
            _add_col("ALTER TABLE users ADD COLUMN avocado_variety TEXT;")

            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users(email);")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_phone ON users(phone);")

            # ---------------- session ----------------
            cur.execute("""
            CREATE TABLE IF NOT EXISTS session (
                id INTEGER PRIMARY KEY CHECK (id=1),
                username TEXT,
                is_active INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cur.execute("INSERT OR IGNORE INTO session (id, username, is_active) VALUES (1, NULL, 0);")

            # ---------------- scans (historial) ----------------
            cur.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                source TEXT,                -- "camera"
                image_asset TEXT,           -- nombre de asset, ej: history_1.png
                maturity_percent INTEGER,   -- 0-100
                status TEXT                 -- "Listo" | "Espera"
            );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at);")

            conn.commit()

    def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> None:
        with self._conn() as conn:
            conn.execute(sql, params)
            conn.commit()

    def fetchone(self, sql: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        with self._conn() as conn:
            cur = conn.execute(sql, params)
            return cur.fetchone()
