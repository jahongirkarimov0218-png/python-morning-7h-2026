# Gann Square 9 + Martingale Trading Bot for IQ Option

## Overview

This is a sophisticated trading bot that implements the Gann Square 9 strategy combined with a Martingale system for IQ Option trading. The bot is designed for OTC (Over The Counter) markets, specifically EURUSD-OTC with tight spreads.

## Features

- **Gann Square 9 Strategy**: Uses the mathematical formula `price_level = (sqrt(base_price) + angle/360)^2` with a base value of 144
- **Martingale System**: Doubles stake after 2 consecutive losses, with maximum 2 levels
- **Volume Analysis**: Requires volume >200% of average for signal confirmation
- **Spread Monitoring**: Skips trades if spread exceeds 2 points
- **Risk Management**: Stops trading after 2 Martingale levels or 5% deposit loss
- **Precise Timing**: Synchronized with M1 expiry times (±500ms)
- **Comprehensive Logging**: CSV export of all trades with detailed information

## Requirements

- Python 3.7+
- IQ Option account (demo or real)
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Make sure you have the iqoptionapi installed:
```bash
pip install iqoptionapi
```

## Configuration

The bot can run in two modes:
- `backtest`: Runs a simulation using historical data
- `live`: Connects to IQ Option API for real trading

## Usage

### Backtesting Mode (Recommended First)
```bash
python iqoption_gann_bot.py --mode backtest
```

### Live Trading Mode
```bash
python iqoption_gann_bot.py --mode live --email your_email@example.com --password your_password
```

**WARNING**: Live trading involves real financial risk. Always test thoroughly in demo mode first.

## Strategy Details

### Gann Square 9 Calculation
- Base number: 144 (configurable)
- Entry angle: 45°
- Formula: `price_level = (sqrt(base_price) + angle/360)^2`
- Key levels calculated for angles: 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°, 360°

### Signal Generation
- Entry signal generated when price breaks above/below Gann levels
- Confirmed by volume >200% of 5-bar average
- Direction: 'call' if price breaks above levels, 'put' if below

### Martingale Logic
- Activates after 2 consecutive losing trades
- Maximum 2 Martingale levels
- Stake doubles with each level (multiplier = 2.0)
- Resets after any winning trade or reaching max levels

### Risk Management
- Maximum loss: 5% of initial balance
- Maximum Martingale levels: 2
- Spread limit: 2 points (skips trade if exceeded)
- Balance update every 30 seconds

## Output Files

The bot generates two output files:

1. **Log file**: `gann_bot.log` - Contains detailed operation logs
2. **Trade log**: `gann_bot_trades_YYYYMMDD_HHMMSS.csv` - CSV with all trade details:
   - timestamp: Time of trade entry
   - entry_price: Price at trade entry
   - signal_type: Either "Gann" or "Gann_M{level}" for Martingale trades
   - direction: 'call' or 'put'
   - stake: Amount risked
   - result: True for win, False for loss
   - profit: Profit/loss amount

## Important Notes

1. **Testing**: Always run backtests before live trading
2. **Risk**: Trading involves substantial risk of loss
3. **API Limitations**: The unofficial IQ Option API may stop working if IQ Option changes their systems
4. **Network Latency**: The bot accounts for 200ms latency in backtesting
5. **Timing**: Trades are synchronized with M1 expiry times for precise entry

## Disclaimer

This bot is provided for educational purposes. Trading involves significant risk and may result in loss of capital. Past performance does not guarantee future results. Use at your own risk.

## Troubleshooting

- If you get API connection errors, check your credentials and internet connection
- If the bot is not generating signals, verify market conditions meet the volume threshold
- For timing issues, ensure your system clock is synchronized

## License

This project is for educational purposes only.