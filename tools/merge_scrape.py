#!/usr/bin/env python3
"""Merge the scraped 2025-26 season snapshot into the game database.

Reads ``nba_stats.db`` (produced by ``nba_scraper.py``) and folds it into
``data/hoopdarts.sql`` as three live categories:

    gp26   — 2025-26 Games Played
    ppg26  — 2025-26 Points Per Game (rounded)
    tpm26  — 2025-26 Total 3-Pointers Made (3P per game x G, rounded)

Players already in the game are matched by normalized name; anyone new in
the scrape (rookies, two-way players) is added to the player pool. Scraped
values are stored as-is — under darts-legal scoring, real stats that land
over 180 or on a bogey number simply score 0 in-game.

Run from the repository root, then re-embed the SQL into the page:

    python3 nba_scraper.py
    python3 tools/merge_scrape.py
    node tools/inject-data.mjs
"""

import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRAPE_DB = ROOT / "nba_stats.db"
GAME_SQL = ROOT / "data" / "hoopdarts.sql"

LIVE_CATEGORIES = {
    "gp26": "2025-26 Games Played",
    "ppg26": "2025-26 Points Per Game",
    "tpm26": "2025-26 Total 3-Pointers Made",
}


def norm(s: str) -> str:
    """Match the game's search normalization (see index.html)."""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def esc(s: str) -> str:
    return s.replace("'", "''")


def chunk(items, n):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def load_game_db() -> sqlite3.Connection:
    if not GAME_SQL.exists():
        sys.exit(f"Game database not found: {GAME_SQL}")
    conn = sqlite3.connect(":memory:")
    conn.executescript(GAME_SQL.read_text())
    return conn


def load_season_rows() -> list[dict]:
    """One row per player: the multi-team total row wins for traded players."""
    if not SCRAPE_DB.exists():
        sys.exit(f"Scrape not found: {SCRAPE_DB} — run nba_scraper.py first")
    conn = sqlite3.connect(SCRAPE_DB)
    rows = conn.execute(
        'SELECT Player, Team, G, PTS, "3P" FROM player_stats'
    ).fetchall()
    conn.close()

    best: dict[str, tuple] = {}
    for player, team, g, pts, tp in rows:
        g = int(float(g or 0))
        # Multi-team rows ("2TM"/"3TM") carry the full-season totals and
        # always have the highest G, so keeping max-G picks them naturally.
        if player not in best or g > best[player][0]:
            best[player] = (g, float(pts or 0), float(tp or 0))

    season = []
    for player, (g, pts, tp) in best.items():
        season.append({
            "name": player,
            "sn": norm(player),
            "gp26": g,
            "ppg26": round(pts),
            "tpm26": round(tp * g),
        })
    return season


def merge(conn: sqlite3.Connection, season: list[dict]) -> tuple[int, int]:
    cur = conn.cursor()
    for key, name in LIVE_CATEGORIES.items():
        cur.execute("INSERT OR REPLACE INTO categories VALUES (?, ?)", (key, name))
    # Re-running the pipeline replaces the previous season snapshot
    cur.execute(
        "DELETE FROM player_stats WHERE category IN (%s)"
        % ",".join("?" * len(LIVE_CATEGORIES)),
        list(LIVE_CATEGORIES),
    )

    existing = {sn: pid for pid, sn in cur.execute("SELECT id, search_name FROM players")}
    next_id = cur.execute("SELECT MAX(id) FROM players").fetchone()[0] + 1

    matched = added = 0
    for row in season:
        if not row["sn"]:
            continue
        pid = existing.get(row["sn"])
        if pid is None:
            cur.execute(
                "INSERT INTO players VALUES (?, ?, ?)",
                (next_id, row["name"], row["sn"]),
            )
            existing[row["sn"]] = pid = next_id
            next_id += 1
            added += 1
        else:
            matched += 1
        for key in LIVE_CATEGORIES:
            if row[key] > 0:
                cur.execute("INSERT INTO player_stats VALUES (?, ?, ?)", (pid, key, row[key]))
    conn.commit()
    return matched, added


def dump_sql(conn: sqlite3.Connection) -> str:
    """Regenerate hoopdarts.sql in the game's marker format."""
    cur = conn.cursor()
    cats = cur.execute("SELECT key, name FROM categories ORDER BY rowid").fetchall()
    players = cur.execute("SELECT id, name, search_name FROM players ORDER BY id").fetchall()
    stats = cur.execute(
        "SELECT player_id, category, value FROM player_stats ORDER BY player_id, category"
    ).fetchall()

    lines = [
        "-- ---------------------------------------------------------------",
        "-- Hoop Darts player database (SQLite dialect)",
        "-- Canonical dataset for the game. index.html embeds a copy of this",
        "-- file and loads it into sql.js (SQLite/WASM) at startup; run",
        "-- `node tools/inject-data.mjs` after editing to re-embed it.",
        "-- Career categories are close approximations tuned for gameplay;",
        "-- the 2025-26 categories (gp26/ppg26/tpm26) are scraped from",
        "-- basketball-reference.com via nba_scraper.py + tools/merge_scrape.py.",
        "-- ---------------------------------------------------------------",
        "CREATE TABLE categories (",
        "  key  TEXT PRIMARY KEY,",
        "  name TEXT NOT NULL",
        ");",
        "CREATE TABLE players (",
        "  id          INTEGER PRIMARY KEY,",
        "  name        TEXT NOT NULL UNIQUE,",
        "  search_name TEXT NOT NULL UNIQUE",
        ");",
        "CREATE TABLE player_stats (",
        "  player_id INTEGER NOT NULL REFERENCES players(id),",
        "  category  TEXT    NOT NULL REFERENCES categories(key),",
        "  value     INTEGER NOT NULL,",
        "  PRIMARY KEY (player_id, category)",
        ");",
        "CREATE INDEX idx_players_search ON players(search_name);",
        "CREATE INDEX idx_stats_player   ON player_stats(player_id);",
        "",
        "INSERT INTO categories VALUES",
        ",\n".join(f"  ('{k}','{esc(n)}')" for k, n in cats) + ";",
        "",
        "-- @players",
    ]
    for group in chunk([f"({i},'{esc(n)}','{esc(sn)}')" for i, n, sn in players], 50):
        lines.append("INSERT INTO players VALUES")
        lines.append(",".join(group) + ";")
    lines += ["", "-- @stats"]
    for group in chunk([f"({p},'{c}',{v})" for p, c, v in stats], 100):
        lines.append("INSERT INTO player_stats VALUES")
        lines.append(",".join(group) + ";")
    lines.append("")
    sql = "\n".join(lines)
    if "</script" in sql:
        sys.exit("SQL must not contain a script terminator")
    return sql


def main() -> None:
    season = load_season_rows()
    print(f"Season snapshot: {len(season)} distinct players")

    conn = load_game_db()
    matched, added = merge(conn, season)
    print(f"Matched to existing players: {matched} | new players added: {added}")

    GAME_SQL.write_text(dump_sql(conn))
    total = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    stats = conn.execute("SELECT COUNT(*) FROM player_stats").fetchone()[0]
    cats = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    print(f"Wrote {GAME_SQL}: {total} players, {cats} categories, {stats} stat rows")


if __name__ == "__main__":
    main()
