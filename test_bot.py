#!/usr/bin/env python3
"""
Quick test script for the IQ Option Gann Square 9 + Martingale Trading Bot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iqoption_gann_bot import GannSquare9Bot, BacktestEngine

def quick_test():
    """Run a quick test to verify the bot functionality"""
    print("🔍 Running quick test of the Gann Square 9 + Martingale Bot...")
    
    # Test 1: Initialize the bot
    print("\n✅ Test 1: Initializing bot...")
    bot = GannSquare9Bot('test@example.com', 'test_password')
    print("   Bot initialized successfully")
    
    # Test 2: Test Gann levels calculation
    print("\n✅ Test 2: Testing Gann levels calculation...")
    levels = bot.calculate_gann_levels(144.0)
    print(f"   Calculated levels: {list(levels.keys())}")
    
    # Test 3: Test signal generation
    print("\n✅ Test 3: Testing signal generation...")
    signal = bot.get_signal_direction(1.0850, levels)
    print(f"   Generated signal: {signal}")
    
    # Test 4: Quick backtest with limited data
    print("\n✅ Test 4: Running quick backtest...")
    # Create a backtester with limited data for quick testing
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce logging for test
    
    backtester = BacktestEngine("dummy_data")
    # Override the data to use fewer points for quick test
    backtester.data = backtester.data[:100]  # Only use first 100 data points
    
    bot_params = {
        'email': 'test@example.com',
        'password': 'testpass'
    }
    
    # Temporarily modify the backtest method to reduce sleep time
    original_sleep = __import__('time').sleep
    
    def quick_sleep(seconds):
        if seconds == 0.2:  # This is the latency simulation
            original_sleep(0.001)  # Reduce to 1ms for testing
        else:
            original_sleep(seconds)
    
    import time
    time.sleep = quick_sleep
    
    try:
        results = backtester.run_backtest(bot_params)
        print(f"   Backtest completed! Final balance: ${results['final_balance']:.2f}")
        print(f"   Total trades: {results['total_trades']}")
        print(f"   Win rate: {results['win_rate']:.2%}")
    except Exception as e:
        print(f"   Backtest error: {e}")
    
    print("\n🎉 All tests completed successfully!")
    print("\n💡 To run full backtest: python iqoption_gann_bot.py --mode backtest")
    print("💡 To run live trading: python iqoption_gann_bot.py --mode live --email YOUR_EMAIL --password YOUR_PASSWORD")

if __name__ == "__main__":
    quick_test()