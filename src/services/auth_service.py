import hashlib
from typing import Optional
from storage.db import Database

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def ensure_demo_user(db: Database) -> None:
    # Demo local: admin / admin123
    row = db.fetchone("SELECT id FROM users WHERE username = ?", ("admin",))
    if row:
        return
    db.execute(
        "INSERT INTO users(username, password_hash) VALUES (?, ?)",
        ("admin", _hash_password("admin123")),
    )

def validate_credentials(db: Database, username: str, password: str) -> bool:
    u = (username or "").strip()
    p = password or ""
    if not u or not p:
        return False
    row = db.fetchone("SELECT password_hash FROM users WHERE username = ?", (u,))
    if not row:
        return False
    return row["password_hash"] == _hash_password(p)

def save_session(db: Database, username: Optional[str], is_active: bool) -> None:
    db.execute(
        "UPDATE session SET username = ?, is_active = ?, updated_at=CURRENT_TIMESTAMP WHERE id=1",
        (username if is_active else None, 1 if is_active else 0),
    )

def load_session(db: Database) -> Optional[str]:
    row = db.fetchone("SELECT username, is_active FROM session WHERE id=1")
    if row and row["is_active"] == 1 and row["username"]:
        return str(row["username"])
    return None

def clear_session(db: Database) -> None:
    save_session(db, None, False)
