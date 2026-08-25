import sqlite3
from urllib.request import Request

from fastapi.templating import Jinja2Templates


def get_db():
    conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

templates = Jinja2Templates(directory="templates")

def grid_col_width(request: Request, columns: int, gap: float = 8, padding: float = 8) -> float:
    if not hasattr(request.state, "screen_width"):
        dims = request.headers.get("x-hyperview-dimensions", "390w 844h")
        request.state.screen_width = float(dims.split("w")[0])
    return (request.state.screen_width - (padding * 2) - (gap * (columns - 1))) / columns

templates.env.globals["grid_col_width"] = grid_col_width