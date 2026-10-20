# VIBE — AI Trading Agent

VIBE is a Python service for Gemini-assisted BUY/SELL signal analysis across six configured forex pairs, Twelve Data candles, Telegram controls, optional Deriv contract execution, Render hosting, and an illustrative historical EMA baseline.

## Current safety defaults

- Signal-only by default: `AUTO_TRADE=false`.
- Live trading locked by default: `ENABLE_LIVE_TRADING=false`.
- Contract expiry defaults to five minutes; analysis runs hourly.
- Telegram commands are restricted to the numeric `TELEGRAM_OWNER_ID`.
- Weak signals are skipped; no WAIT signal is sent.
- Confidence is an uncalibrated model score, not a probability.
- Martingale levels are display-only; no automatic recovery staking is implemented.
- Trading can lose money. Backtests are not proof of future performance.

## Deploy on Render

1. Create a Telegram bot with BotFather and obtain its token.
2. Create API credentials with Gemini 3.6 Flash (model ID: `gemini-3.6-flash`), Twelve Data, and Deriv. Start with a Deriv demo token.
3. Connect this repository to Render as a Web Service. The included `render.yaml` sets the start command.
4. Add the environment variables below in Render's Environment page. Never commit real tokens.
5. Deploy and check `/health`. Send `/start` to the bot from the Telegram account whose numeric ID is configured.
6. Confirm signals and Deriv demo symbols/contracts before enabling demo execution. Live execution requires a separate environment unlock and explicit Telegram confirmation.

## Required environment variables

`TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_ID`, `TELEGRAM_CHAT_ID`, `GEMINI_API_KEY`, `TWELVE_DATA_API_KEY`, `DERIV_APP_ID`, and `DERIV_DEMO_TOKEN` for demo balance/orders.

Optional controls are documented in `.env.example`. Use `AUTO_TRADE=false` until the full workflow is verified. To permit demo orders, set `AUTO_TRADE=true` and redeploy, then use `/resume`. Live mode additionally requires `ENABLE_LIVE_TRADING=true`, a real Deriv token, `/live`, and `/confirm_live YES`.

## Telegram commands

- `/start`, `/status`, `/signals`, `/trades`, `/pnl`
- `/demo`, `/live`, `/confirm_live YES`, `/stop`, `/resume`
- `/balance`, `/target 20`, `/maxloss 5`, `/stake 1`

`/stop` stops new orders; it does not close already-open contracts. Session state is in memory and resets on service restart.

## Tests and historical baseline

Run `pip install -r requirements.txt`, then `python -m compileall -q app backtest.py` and `pytest -q`.

For a six-month historical candle baseline, set `TWELVE_DATA_API_KEY` and run `python backtest.py --symbol EUR/USD --months 6`. The live signal cycle currently analyzes the latest 120 five-minute candles per configured asset; it does not feed six months of history into Gemini automatically. This simple EMA baseline is illustrative, assumes a fixed payout multiplier, and is not a simulation of the Gemini strategy or a guarantee of returns. Historical requests can be limited by Twelve Data plan quotas and symbol support.
