# Gann Square 9 + Martingale Trading Bot - Project Summary

## Project Overview

This project implements a sophisticated trading bot for IQ Option that combines the Gann Square 9 technical analysis method with a Martingale money management system. The bot is specifically designed for OTC (Over The Counter) markets, particularly EURUSD-OTC.

## Files Created

1. **`iqoption_gann_bot.py`** - Main trading bot implementation
2. **`TRADE_BOT_README.md`** - Detailed documentation and usage instructions
3. **`test_bot.py`** - Quick test script to verify functionality
4. **`install_deps.sh`** - Installation script for dependencies
5. **Updated `requirements.txt`** - Added iqoptionapi dependency

## Key Features Implemented

### 1. Gann Square 9 Strategy
- Uses the mathematical formula: `price_level = (sqrt(base_price) + angle/360)^2`
- Base number set to 144 (configurable)
- Calculates levels for key angles: 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°, 360°
- Entry angle set to 45° as specified

### 2. Martingale System
- Activates after 2 consecutive losing trades
- Maximum 2 Martingale levels as specified
- Stake doubles with each level (multiplier = 2.0)
- Resets after any winning trade or reaching max levels

### 3. Risk Management
- Stops trading after 2 Martingale levels or 5% deposit loss
- Spread monitoring (skips trades if spread > 2 points)
- Balance update every 30 seconds
- Volume confirmation (requires volume >200% of 5-bar average)

### 4. Precise Timing
- Synchronized with M1 expiry times (±500ms)
- Uses asyncio for parallel processing
- Handles network latency (simulated 200ms in backtesting)

### 5. Comprehensive Logging
- CSV export of all trades with detailed information
- Detailed operation logs
- Trade fields: timestamp, entry_price, signal_type, direction, stake, result, profit

## Technical Implementation

### Dependencies Used
- `iqoptionapi` - Unofficial IQ Option API
- `numpy` - For mathematical calculations
- `asyncio` - For asynchronous operations
- `threading` - For concurrent processing
- Standard Python libraries for logging, CSV, etc.

### Architecture
- Object-oriented design with `GannSquare9Bot` class
- Separate `BacktestEngine` class for historical testing
- Proper error handling and retry logic
- Configurable parameters for different trading scenarios

## Usage Instructions

### Installation
```bash
chmod +x install_deps.sh
./install_deps.sh
```

### Backtesting (Recommended First)
```bash
python iqoption_gann_bot.py --mode backtest
```

### Live Trading
```bash
python iqoption_gann_bot.py --mode live --email YOUR_EMAIL --password YOUR_PASSWORD
```

### Quick Test
```bash
python test_bot.py
```

## Validation of Requirements

✅ **Gann Square 9 Implementation**: Uses the specified formula with base 144 and 45° angle

✅ **Martingale System**: Implements 2-level Martingale with 2.0 coefficient as requested

✅ **Risk Management**: Implements stop after 2 levels or 5% loss

✅ **Precise Timing**: Synchronized with M1 expiry times (±500ms)

✅ **Volume Confirmation**: Requires >200% average volume for signals

✅ **Spread Monitoring**: Skips trades if spread >2 points

✅ **EURUSD-OTC Focus**: Configured for specified pair

✅ **API Integration**: Uses iqoptionapi with retry logic

✅ **Threading & Asyncio**: Implements concurrent processing

✅ **CSV Logging**: Exports detailed trade information

✅ **Backtesting**: Includes 1-week M1 data simulation with 200ms latency

## Testing Results

The bot has been successfully tested with:
- Module import verification
- Gann levels calculation
- Signal generation
- Quick backtesting with reduced dataset
- All core functions working as expected

## Important Notes

⚠️ **Risk Warning**: This bot uses a Martingale system which can lead to significant losses during extended losing streaks. Use with caution and proper risk management.

⚠️ **API Disclaimer**: Uses unofficial IQ Option API which may change or be discontinued at any time.

⚠️ **Testing Recommendation**: Always run extensive backtesting before live trading.

## Next Steps

1. Run extensive backtesting with full week of data
2. Test on demo account before live trading
3. Monitor performance and adjust parameters as needed
4. Consider adding additional risk management features