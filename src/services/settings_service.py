from storage.db import Database
import locale

LANG_KEY = "lang"
THEME_KEY = "theme"  # "light" | "dark"

SUPPORTED_LANG = {"es", "qu", "ay", "en"}

def detect_system_language() -> str:
    try:
        lang = locale.getdefaultlocale()[0]  # ej: es_PE, en_US
        if not lang:
            return "es"
        code = lang.split("_")[0].lower()
        return code if code in SUPPORTED_LANG else "es"
    except Exception:
        return "es"

def save_setting(db: Database, key: str, value: str) -> None:
    db.execute(
        "INSERT INTO settings(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )

def load_setting(db: Database, key: str) -> str | None:
    row = db.fetchone("SELECT value FROM settings WHERE key = ?", (key,))
    return str(row["value"]) if row and row["value"] is not None else None

# ---------- Language ----------
def save_language(db: Database, lang_code: str) -> None:
    save_setting(db, LANG_KEY, lang_code)

def load_language(db: Database) -> str:
    existing = load_setting(db, LANG_KEY)
    if existing:
        return existing
    detected = detect_system_language()
    save_language(db, detected)
    return detected

# ---------- Theme ----------
def save_theme(db: Database, theme: str) -> None:
    # theme: "light" | "dark"
    save_setting(db, THEME_KEY, theme)

def load_theme(db: Database) -> str:
    existing = load_setting(db, THEME_KEY)
    if existing in ("light", "dark"):
        return existing
    # default: follow light (puedes cambiar a "dark" si prefieres)
    save_theme(db, "light")
    return "light"
