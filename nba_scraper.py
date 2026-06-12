#!/usr/bin/env python3
"""nba_scraper.py — fetch NBA 2025-26 per-game statistics into SQLite.

Fetches the per-game statistics table from basketball-reference.com,
cleans the repeated header rows, and stores the result in a SQLite
database (``nba_stats.db``, table ``player_stats``).

The script is deliberately polite to the source site: it sends a
realistic User-Agent and sleeps 4 seconds before and after the request,
keeping usage far below the site's rate limit of 20 requests/minute.

Usage:
    python3 nba_scraper.py
"""

import io
import sqlite3
import sys
import time

import pandas as pd
import requests

URL = "https://www.basketball-reference.com/leagues/NBA_2026_per_game.html"
DB_PATH = "nba_stats.db"
TABLE_NAME = "player_stats"

# A realistic desktop-browser User-Agent so the request is not instantly
# rejected as a bare bot.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_page(url: str) -> str:
    """Fetch the stats page, rate-limited and with graceful error handling."""
    # MANDATORY rate-limit guard: sleep before the request so repeated runs
    # of this script can never exceed 20 requests/minute.
    print("Sleeping 4s before request (rate-limit guard)...")
    time.sleep(4)

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        sys.exit(f"Connection error — could not reach {url}: {exc}")
    except requests.exceptions.Timeout as exc:
        sys.exit(f"Request timed out for {url}: {exc}")
    except requests.exceptions.HTTPError as exc:
        sys.exit(f"HTTP error from {url}: {exc}")
    except requests.exceptions.RequestException as exc:
        sys.exit(f"Request failed for {url}: {exc}")

    # MANDATORY rate-limit guard: sleep after the request as well, so any
    # caller that loops over this function stays under the limit too.
    print("Sleeping 4s after request (rate-limit guard)...")
    time.sleep(4)

    # The page is UTF-8 but the response omits a charset, which makes
    # requests fall back to ISO-8859-1 and mangle accented names (Dončić).
    response.encoding = "utf-8"
    return response.text


def parse_table(html: str) -> pd.DataFrame:
    """Extract the main per-game statistics table from the page HTML."""
    tables = pd.read_html(io.StringIO(html))
    # The per-game table is the one with the 'Rk' (rank) column; on this
    # page it is also the first table.
    for df in tables:
        if "Rk" in df.columns:
            return df
    raise ValueError("Could not find the per-game statistics table ('Rk' column)")


def clean_table(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the in-body repeated header rows (where Rk literally says 'Rk')."""
    df = df[df["Rk"].astype(str) != "Rk"].copy()
    df.reset_index(drop=True, inplace=True)
    return df


def save_to_sqlite(df: pd.DataFrame, db_path: str, table: str) -> None:
    """Write the dataframe to SQLite, replacing any previous snapshot."""
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table, conn, if_exists="replace", index=False)
    finally:
        conn.close()


def main() -> None:
    print(f"Fetching {URL}")
    html = fetch_page(URL)

    df = parse_table(html)
    print(f"Parsed table: {len(df)} raw rows, {len(df.columns)} columns")

    df = clean_table(df)
    print(f"After cleaning repeated headers: {len(df)} player rows")

    save_to_sqlite(df, DB_PATH, TABLE_NAME)
    print(f"Saved to {DB_PATH} (table '{TABLE_NAME}', if_exists='replace')")


if __name__ == "__main__":
    main()
