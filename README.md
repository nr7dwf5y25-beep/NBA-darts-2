# 🏀 Hoop Darts — NBA 501 Challenge

A single-file, zero-build web game that fuses **501 Darts** with **NBA trivia**.

Start at **501**. Each turn, throw an NBA player's name — their career stat in the
active category is subtracted from your score. Land on **exactly 0** for a
**Perfect Checkout**, or anywhere from **0 down to −10** to win. Drop below −10
and you **BUST**: your score resets and you burn one of your 3 lives.

## Play it

Just open `index.html` in any modern browser — no build step, no server required
(React 18, Tailwind CSS, and Babel load from CDNs; icons are embedded inline).

Or serve it locally:

```bash
python3 -m http.server 8000
# → http://localhost:8000
```

## Features

- **Three game modes** — Solo 501, 1 v 1 Duel (alternating throws), and a
  **Daily Challenge** with a date-seeded category and localStorage persistence
  (your board is saved after every throw, so refreshing won't undo a bust).
- **Eleven stat categories** — Triple-Doubles, 50-Point Games, 200+ 3PT Seasons,
  Playoff Games Played, Technical Fouls, Highest Single-Season 3PM, 40-Point
  Games, Career Playoff 3PM, Career Double-Doubles, 30-Point Playoff Games, and
  Career Games Missed (availability tracking for selected stars) — plus a
  random-category option.
- **Darts rules** — single-throw cap of 180, strict bust below −10, each player
  usable only once per game, 0-stat "bricks" burn the throw.
- **Autocomplete search** over a 1,000+ player embedded database spanning every
  era — a curated core of ~235 stars carries detailed stats across all 11
  categories; everyone else counts as 0 ("no tracked value"), so spelling never
  costs you a turn but a lazy throw might.
- **Animated hoop visualizer** — a neon progress ring and a basketball that arcs
  toward the rim as your score counts down.
- **TV-broadcast scoreboard** with lives, throw history, and per-throw feedback.
- **Win/loss modals** with match stats (turns, best throw, busts, checkout
  accuracy), confetti, and a one-tap emoji-grid **Share Results** button.
- Fully **mobile-responsive**, dark-mode basketball aesthetic.

> Stat values in the database are close approximations, tuned for gameplay.
