# Method

## Market and costs

One asset, cbBTC/USDC, 1-minute bars. Orders decided on a bar's close fill
at the next bar's open. Every fill pays 4 bps fee + 2 bps modelled slippage
+ constant-product price impact against that bar's open depth, so a
full-size round trip costs roughly 26 bps. A trade therefore has to catch a
move clearly larger than that; 1-minute noise (about 8 bps standard
deviation on the dev window) is far too small to trade on its own.

## The dev window

The frozen dev window (2026-11-22 05:12 UTC to 2026-11-23 05:11 UTC) rose
about 3.6% from first close to last, with the price ranging roughly
$58,669–$61,655. The bot's edge on it comes from two selective triggers
plus a wide take-profit that lets a real leg run, rather than from
chasing every 1-minute wiggle.

## Rules

- Entry, full size (100% of cash), when either trigger fires and no
  position is open:
  - capitulation: close down ≥ 140 bps over the last 10 closes;
  - breakout: close ≥ 20 bps above the highest close of the previous
    15 closes.
- Exit, whole position, when any of these holds at a bar's close:
  - take-profit +240 bps over the position's average entry price
    (cost basis, fees included);
  - stop-loss −100 bps;
  - time exit: held ≥ 480 bars (8 hours) and in profit.
- No entries before 60 bars of history, and none in the last 30 minutes
  of the window (measured from bar time, so it holds on any 24 h window).
- `max_slippage_bps` 150 on every order: far above any 1-minute move in
  the dev data, so fills are effectively never rejected for slippage,
  while still bounding a freak gap.

## Tuning and robustness

Parameters were grid-searched with a local simulator that replicates the
harness fill math exactly (integer arithmetic, fee/slippage/impact at the
next bar's open, flatten at the last close); the simulator was verified
by reproducing the previous race's local grade (+$10.33, 4 trades, max
drawdown 1.50%) to the cent. The search was scored on this window AND on
the previous race's dev window (a falling market, −2.8%): the chosen
point is profitable on both, which is what matters, because the race
window's direction is unknown.

- Chosen: dip 140 bps, breakout 20 bps, take-profit 240 bps, stop-loss
  100 bps, hold 480 bars → dev +$24.27 (5 trades, max drawdown 1.81%),
  previous window +$16.21 (2 trades, max drawdown 1.50%).
- The point is not a sharp peak: take-profit 240–260 bps gives identical
  results on both windows, and dip 120–160 bps with the same other
  settings gives the same dev result; the neighbouring settings that do
  move the score stay positive on both windows. The most aggressive
  single-window point found (dip 100, breakout 15, take-profit 120)
  scored +$55.87 on this window but −$27.81 on the falling one, so it
  was rejected as a rising-market artefact.
- The dev trades: a dip buy early in the window that ran to the
  +240 bps take-profit, a breakout buy held to the 8-hour time exit,
  and a late breakout buy flattened at the close.

## Determinism

Integer arithmetic only, no randomness, no wall clock, no environment
reads. The bot's state is the closes it has been sent and the batch its
position opened on; two runs on the same data produce byte-identical
replies (verified locally).
