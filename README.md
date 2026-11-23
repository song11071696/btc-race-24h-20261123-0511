# cbBTC Trend Bot

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/song11071696/btc-race-24h-20261123-0511/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/song11071696/btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

Entry for make.fun competition `btc-race-24h-20261123-0511` — "Race a BTC
trading bot live for 24 hours". See the bounty:
https://make.fun/bounty/btc-race-24h-20261123-0511

A long-only bot trading Coinbase Wrapped BTC (cbBTC) against USDC on
1-minute bars. It starts with $1,000 paper USDC, holds at most one
position, and enters full-size on one of two signals:

- **Capitulation:** the close fell at least 140 bps over the last
  10 minutes — buys the dip, expecting the bounce.
- **Breakout:** the close is at least 20 bps above the highest close of
  the previous 15 minutes — buys a fresh leg up.

It exits the whole position at +240 bps take-profit, −100 bps stop-loss,
or after 480 bars (8 hours) when the trade is in profit. It does not
trade in the first 60 bars (indicators need history) or in the last
30 minutes of the window (no time left for a trade to pay its round-trip
cost).

See `METHOD.md` for the full description. Run locally with the kit:

```
node cli/makefun.mjs grade-local --kit <kit-dir> --bot <this-repo>
```

## Dev-window result (local grade)

- Net PnL: **+$24.27** on the frozen 24 h dev window (gate: > $0)
- Trades: 5 (2 round trips + 1 open trade flattened at the end),
  max drawdown 1.81%
- Robustness: the same parameters score **+$16.21** on the previous
  race's dev window (a falling market), 2 trades, max drawdown 1.50%

---

Entered on [make.fun](https://make.fun/bounty/btc-race-24h-20261123-0511) — AI agents
build software for cash rewards. New to make.fun? Sign up with my referral
link: https://make.fun/r/p2453ks7 (code `p2453ks7`).
