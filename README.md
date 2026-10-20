# VIBE — AI Trading Agent

VIBE is a Python service for Gemini-assisted BUY/SELL signal analysis across six configured forex pairs, Twelve Data candles, Telegram controls, optional Deriv contract execution, Render hosting, and an illustrative historical EMA baseline.

## Current safety defaults

- Trading execution is enabled as a capability: choose DEMO or LIVE from Telegram.
- Default mode is DEMO; LIVE requires a configured real Deriv token and `/live` followed by `/confirm_live YES`.
- Use `/stop` to stop new orders at any time.
- Contract expiry defaults to five minutes; analysis runs every five minutes, with a maximum of 50 trades per 24-hour session.
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

Optional controls are documented in `.env.example`. The repository defaults `AUTO_TRADE=true` and `ENABLE_LIVE_TRADING=true`, while `DEFAULT_MODE=demo` keeps startup in demo mode. If these variables already exist in Render as `false`, change each to `true` once and redeploy; after that, choose `/demo` or `/live` in Telegram without changing Render. Demo execution starts with `/demo` then `/resume`. Live requires a real Deriv token, `/live`, and `/confirm_live YES`.

## Telegram commands

- `/start`, `/status`, `/signals`, `/trades`, `/pnl`
- `/demo`, `/live`, `/confirm_live YES`, `/stop`, `/resume`
- `/balance`, `/target 20` or `/target off`, `/maxloss 5` or `/maxloss off`, `/stake 1`

`/stop` stops new orders; it does not close already-open contracts. The 24-hour session allows at most 50 trades. Profit and loss limits can be enabled or disabled in Telegram using `/target 20` or `/target off`, and `/maxloss 5` or `/maxloss off`. Session state is in memory and resets on service restart.

## Tests and historical baseline

Run `pip install -r requirements.txt`, then `python -m compileall -q app backtest.py` and `pytest -q`.

The live analyzer uses six months of hourly historical data plus current five-minute candles. For a separate illustrative historical candle baseline, set `TWELVE_DATA_API_KEY` and run `python backtest.py --symbol EUR/USD --months 6`. The live signal cycle now combines the latest 120 five-minute candles with a compact summary of six months of hourly historical data for each asset. Historical summaries are cached for 24 hours and refreshed daily. The service requires the provider to return at least about 170 days of hourly history; if that is unavailable, it skips that asset instead of pretending the history was analyzed. This simple EMA baseline is illustrative, assumes a fixed payout multiplier, and is not a simulation of the Gemini strategy or a guarantee of returns. Historical requests can be limited by Twelve Data plan quotas and symbol support.
