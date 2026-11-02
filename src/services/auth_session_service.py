import json
import flet as ft

AUTH_STORAGE_KEY = "auth"


def _ensure_page_data(page: ft.Page):
    if getattr(page, "data", None) is None:
        page.data = {}


def _set_storage(page: ft.Page, key: str, value: dict):
    """
    Guarda en el mecanismo disponible según la versión de Flet.
    """
    # 1) client_storage
    if hasattr(page, "client_storage") and getattr(page, "client_storage", None) is not None:
        try:
            page.client_storage.set(key, json.dumps(value))
            return
        except Exception:
            pass

    # 2) session
    if hasattr(page, "session") and getattr(page, "session", None) is not None:
        try:
            page.session.set(key, value)
            return
        except Exception:
            pass

    # 3) solo memoria
    _ensure_page_data(page)
    page.data[key] = value


def _get_storage(page: ft.Page, key: str):
    """
    Lee del mecanismo disponible según la versión de Flet.
    """
    # 1) client_storage
    if hasattr(page, "client_storage") and getattr(page, "client_storage", None) is not None:
        try:
            value = page.client_storage.get(key)
            if value is not None:
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except Exception:
                        return value
                return value
        except Exception:
            pass

    # 2) session
    if hasattr(page, "session") and getattr(page, "session", None) is not None:
        try:
            value = page.session.get(key)
            if value is not None:
                return value
        except Exception:
            pass

    # 3) memoria
    _ensure_page_data(page)
    return page.data.get(key)


def _remove_storage(page: ft.Page, key: str):
    """
    Elimina del mecanismo disponible según la versión de Flet.
    """
    if hasattr(page, "client_storage") and getattr(page, "client_storage", None) is not None:
        try:
            page.client_storage.remove(key)
        except Exception:
            pass

    if hasattr(page, "session") and getattr(page, "session", None) is not None:
        try:
            page.session.remove(key)
        except Exception:
            try:
                page.session.set(key, None)
            except Exception:
                pass

    _ensure_page_data(page)
    page.data.pop(key, None)


def is_authenticated(page: ft.Page) -> bool:
    auth_data = get_auth_data(page)
    return bool(auth_data and auth_data.get("firebase_id_token"))


def get_auth_data(page: ft.Page) -> dict:
    _ensure_page_data(page)

    auth_data = page.data.get(AUTH_STORAGE_KEY)
    if auth_data:
        return auth_data

    stored = _get_storage(page, AUTH_STORAGE_KEY)
    if isinstance(stored, dict):
        page.data[AUTH_STORAGE_KEY] = stored
        return stored

    return {}


def save_auth_data(page: ft.Page, auth_data: dict):
    _ensure_page_data(page)

    if not isinstance(auth_data, dict):
        raise ValueError("auth_data debe ser un diccionario.")

    page.data[AUTH_STORAGE_KEY] = auth_data
    _set_storage(page, AUTH_STORAGE_KEY, auth_data)


def restore_auth_data(page: ft.Page):
    _ensure_page_data(page)

    try:
        saved_auth = _get_storage(page, AUTH_STORAGE_KEY)
        if isinstance(saved_auth, dict):
            page.data[AUTH_STORAGE_KEY] = saved_auth
    except Exception:
        pass


def clear_auth_data(page: ft.Page):
    _ensure_page_data(page)
    page.data.pop(AUTH_STORAGE_KEY, None)
    _remove_storage(page, AUTH_STORAGE_KEY)
