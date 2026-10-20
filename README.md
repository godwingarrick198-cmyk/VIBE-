# VIBE — AI Trading Agent

AI-assisted BUY/SELL signals and optional automated execution through Deriv. Telegram is the control panel; Gemini analyses candle features; Twelve Data supplies candles; Render hosts the service.

## Safety

- Demo-first. Automatic execution is off at startup; live trading requires explicit configuration and Telegram confirmation.
- Only qualifying BUY/SELL signals are sent; weak setups are skipped rather than forcing a trade.
- Default contract expiry is 5 minutes. BUY maps to CALL and SELL to PUT.
- Confidence is an uncalibrated model score, not a probability or guarantee.
- Martingale levels are informational only; automatic recovery trades are not enabled.
- Never commit API keys, Deriv tokens, or Telegram bot tokens.

## Project

The full project package is prepared separately as `VIBE-AI-TRADING-AGENT.zip`. It includes the Python app, Deriv/Twelve Data/Gemini integrations, Telegram controls, Render configuration, backtesting script, and tests.

## Deployment

Keep `AUTO_TRADE=false` and `ENABLE_LIVE_TRADING=false` until demo credentials, supported symbols, contracts, result monitoring, risk limits, and stop controls have been verified. Trading can lose money; no signal or backtest guarantees profit.