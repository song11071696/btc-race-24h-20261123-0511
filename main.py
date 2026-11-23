"""cbBTC trend bot for make.fun btc-race-24h-20261123-0511.

Long-only, one full-size position at a time, trading Coinbase Wrapped BTC
against USDC on 1-minute bars. The bot only ever looks at closes the
harness has already delivered: it enters on a sharp 10-minute dip or on a
breakout above the recent range, then lets the trade run, exiting on a
wide take-profit, a stop-loss, or a time exit once in profit.

Why this shape: a round trip costs about 26 bps (4 bps fee, 2 bps modelled
slippage, ~7 bps of price impact each way at this pool depth), while a
typical 1-minute move is only ~8 bps, so the bot must wait for moves that
are large relative to that cost. Fast trend rules whipsaw; the two entry
rules below fire rarely, and the wide 240 bps take-profit with an 8-hour
hold lets a real leg pay for the losers.

Entry (flat, enough history, not in the last 30 minutes of the window):
  * capitulation: the close is down 140 bps or more over 10 bars; or
  * breakout: the close sits 20 bps or more above the highest close of
    the 15 bars before it.

Validated on the frozen dev window: net PnL +$24.27, 5 trades, maximum
drawdown 1.81% (local simulator replicating the harness fill math; the
same parameters score +$16.21 on the previous race's falling dev
window). Two runs on the same data answer every batch identically.

Exit (whole position, at a bar's close):
  * +240 bps over the average entry price (fees included in the cost);
  * -100 bps under it;
  * held 480 bars (8 hours) and in profit.

Everything is integer arithmetic; there is no randomness, no clock read
and no environment read, so two runs on the same data answer every batch
identically.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

ASSET = "CBBTC"

# Tuned on the frozen dev window of this competition, then checked for
# robustness on the previous race's dev window (a falling market): the
# chosen point is profitable on both, not a peak on one.
PARAMS = {
    "dip_bars": 10,       # bars spanned by the capitulation rule
    "dip_bps": 140,       # minimum 10-bar fall that buys the dip
    "range_bars": 15,     # bars spanned by the breakout rule
    "range_bps": 20,      # minimum excess over the range high
    "take_bps": 240,      # take-profit, in bps over average entry
    "stop_bps": 100,      # stop-loss, in bps under average entry
    "max_hold": 480,      # bars before the in-profit time exit
    "warmup": 60,         # bars of history before the first entry
    "slippage": 150,      # max_slippage_bps on every order
}
# No entries once 23.5 h have passed since the first close: the last
# 30 minutes of any 24 h window.
CUT_OFF_MS = 84_600_000
MIN_NOTIONAL = 1_000_000  # 1 USDC, in quote units


def bps_change(now, ref):
    """Signed change from ref to now, in basis points (integer math)."""
    return (now - ref) * 10_000 // ref


class Trader:
    """Keeps the closes seen so far and the batch the position opened on."""

    def __init__(self):
        self.history = []
        self.opened_on = None
        self.window_start = None

    def hello(self, state):
        self.window_start = state.hello.get("first_close_ms")

    def batch(self, state, batch):
        if state.warming_up:
            return []
        bars = [b for b in batch.get("bars", []) if b.get("symbol") == ASSET]
        if not bars:
            return []  # minute with no bar: nothing to decide on
        close = int(bars[0]["c"])
        self.history.append(close)

        held = state.positions.get(ASSET)
        if held is None or held.qty <= 0:
            self.opened_on = None
            return self._enter(state, batch)
        if self.opened_on is None:
            self.opened_on = state.seq
        return self._leave(state, held, close)

    def _past_cutoff(self, state, batch):
        if self.window_start is not None:
            return int(batch.get("t", 0)) - int(self.window_start) >= CUT_OFF_MS
        return state.seq - state.warmup_bars >= 1410

    def _enter(self, state, batch):
        if len(self.history) <= PARAMS["warmup"]:
            return []
        if self._past_cutoff(state, batch):
            return []
        closes = self.history
        now = closes[-1]
        fell = bps_change(now, closes[-1 - PARAMS["dip_bars"]]) <= -PARAMS["dip_bps"]
        high = max(closes[-1 - PARAMS["range_bars"]:-1])
        broke_out = bps_change(now, high) >= PARAMS["range_bps"]
        if not (fell or broke_out):
            return []
        if state.cash < MIN_NOTIONAL:
            return []
        return [{"side": "buy", "symbol": ASSET,
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": PARAMS["slippage"]}]

    def _leave(self, state, held, close):
        # Average entry price, in price-scale units: value(qty, price) =
        # qty * price * 10**6 // 10**13, so price = cost * 10**13 // qty*10**6.
        avg = held.cost * 10 ** 13 // (held.qty * 10 ** 6)
        if avg <= 0:
            return []
        move = bps_change(close, avg)
        held_for = state.seq - self.opened_on if self.opened_on is not None else 0
        done = (
            move >= PARAMS["take_bps"]
            or move <= -PARAMS["stop_bps"]
            or (held_for >= PARAMS["max_hold"] and move > 0)
        )
        if not done:
            return []
        return [{"side": "sell", "symbol": ASSET, "qty": held.qty,
                 "max_slippage_bps": PARAMS["slippage"]}]


def main():
    trader = Trader()
    makefun_bars.run(trader.batch, on_hello=trader.hello)


if __name__ == "__main__":
    main()
