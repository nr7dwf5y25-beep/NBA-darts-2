# 🏀 Hoop Darts — NBA 501 Challenge

A single-file, zero-build web game that fuses **501 Darts** with **NBA trivia**.

Start at **501**. Each turn, throw an NBA player's name — their career stat in the
active category is subtracted from your score. Land on **exactly 0** for a
**Perfect Checkout**, or anywhere from **0 down to −10** to win. Drop below −10
and you **BUST**: your score resets and you burn one of your 3 lives.

## Play it

Just open `index.html` in any modern browser — no build step, no server required
(React 18, Tailwind CSS, Babel, and the sql.js SQLite engine load from CDNs;
the database and icons are embedded).

Or serve it locally:

```bash
python3 -m http.server 8000
# → http://localhost:8000
```

## The database

The dataset lives in **`data/hoopdarts.sql`** — a standard SQLite-dialect
database (~1,150 players spanning every era, ~1,300 stat rows across 10
categories) with a normalized schema:

```
categories(key, name)
players(id, name, search_name)
player_stats(player_id, category, value)
```

At startup the game executes this SQL inside a real in-browser SQLite engine
([sql.js](https://github.com/sql-js/sql.js), SQLite compiled to WebAssembly)
and issues **live SQL queries** for autocomplete and per-throw stat retrieval.
If WASM can't load, a built-in parser reconstructs the same dataset in memory
from the identical SQL text — the game works either way.

`index.html` ships with an embedded copy of the .sql file. After editing the
database, re-embed it with:

```bash
node tools/inject-data.mjs
```

## Darts-legal scoring

Every throw must be a **possible 3-dart visit**:

- Anything **over 180** scores **0** — Westbrook's 203 triple-doubles and
  Wilt's 968 double-doubles are worthless throws.
- The in-range **bogey numbers** (163, 166, 169, 172, 173, 175, 176, 178, 179)
  — totals no combination of three darts can produce — also score 0.
- A player with no tracked value in the category burns the throw for 0.
- Strict bust below −10, three lives, each player throwable once per game.

## Features

- **Three game modes** — Solo 501, 1 v 1 Duel (alternating throws), and a
  **Daily Challenge** with a date-seeded category and localStorage persistence
  (your board is saved after every throw, so refreshing won't undo a bust).
- **Ten stat categories** — Triple-Doubles, 50-Point Games, Playoff Games
  Played, Technical Fouls, Highest Single-Season 3PM, 40-Point Games, Career
  Playoff 3PM, Career Double-Doubles, 30-Point Playoff Games, and Career Games
  Missed — plus a random-category option. Every category is verified to be
  mathematically winnable under darts-legal scoring.
- **SQL-backed autocomplete** over the 1,150+ player database, so spelling
  never costs you a turn — but a lazy throw might.
- **Animated hoop visualizer**, broadcast-style scoreboard, throw history with
  per-throw feedback, and win/loss modals with match stats, confetti, and an
  emoji-grid **Share Results** button.
- Fully **mobile-responsive**, dark-mode basketball aesthetic.

> Stat values in the database are close approximations, tuned for gameplay.
