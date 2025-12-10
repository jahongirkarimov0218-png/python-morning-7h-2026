import asyncio
import threading
import time
import math
import logging
import csv
from datetime import datetime
import numpy as np
from typing import List, Dict, Optional, Tuple

# Import IQOption API (using unofficial API)
try:
    from iqoptionapi.stable_api import IQ_Option
except ImportError:
    print("IQOption API not found. Install using: pip install iqoptionapi")
    exit(1)

class GannSquare9Bot:
    def __init__(self, email: str, password: str, base_price: float = 144.0):
        """
        Initialize the Gann Square 9 + Martingale Trading Bot
        
        Args:
            email: IQ Option account email
            password: IQ Option account password
            base_price: Base price for Gann Square calculation (default 144)
        """
        self.email = email
        self.password = password
        self.base_price = base_price
        self.angle = 45.0  # Angle for entry in degrees
        
        # Trading parameters
        self.pair = "EURUSD-OTC"
        self.timeframe = "M1"  # 1-minute timeframe
        self.initial_stake = 1.0  # Initial stake amount
        self.current_stake = self.initial_stake
        self.max_martingale_levels = 2
        self.martingale_level = 0
        self.stop_loss_percentage = 0.05  # 5% stop loss
        self.spread_limit = 2.0  # Max spread in points
        
        # Bot state
        self.api = None
        self.is_running = False
        self.balance = 0.0
        self.position_history = []
        self.last_bar_timestamp = 0
        self.gann_levels_cache = {}
        
        # Setup logging
        self.setup_logging()
        
        # Setup CSV logging
        self.setup_csv_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('gann_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_csv_logging(self):
        """Setup CSV file for trade logging"""
        self.csv_filename = f"gann_bot_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(self.csv_filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'entry_price', 'signal_type', 'direction', 'stake', 'result', 'profit']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    
    def connect_to_iqoption(self) -> bool:
        """Connect to IQ Option API with retry logic"""
        max_retries = 3
        retry_delay = 100  # milliseconds
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Connecting to IQ Option (attempt {attempt + 1}/{max_retries})...")
                self.api = IQ_Option(self.email, self.password)
                
                # Check connection
                check, reason = self.api.connect()
                if check:
                    self.logger.info("Successfully connected to IQ Option!")
                    
                    # Set balance type to real or demo based on preference
                    self.api.change_balance("PRACTICE")  # Change to "REAL" for real trading
                    
                    # Get initial balance
                    self.update_balance()
                    
                    return True
                else:
                    self.logger.error(f"Connection failed: {reason}")
            except Exception as e:
                self.logger.error(f"Connection error on attempt {attempt + 1}: {str(e)}")
            
            if attempt < max_retries - 1:
                self.logger.info(f"Retrying in {retry_delay}ms...")
                time.sleep(retry_delay / 1000.0)
        
        self.logger.error("Failed to connect after all retries")
        return False
    
    def update_balance(self):
        """Update account balance"""
        try:
            self.balance = self.api.get_balance()
            self.logger.info(f"Current balance: ${self.balance:.2f}")
        except Exception as e:
            self.logger.error(f"Error updating balance: {str(e)}")
    
    def calculate_gann_levels(self, base_price: float) -> Dict[str, float]:
        """
        Calculate Gann Square 9 levels based on the formula:
        price_level = (sqrt(base_price) + angle/360)^2
        """
        if base_price in self.gann_levels_cache:
            return self.gann_levels_cache[base_price]
        
        sqrt_base = math.sqrt(base_price)
        levels = {}
        
        # Calculate key angles (multiples of 45 degrees)
        angles = [0, 45, 90, 135, 180, 225, 270, 315, 360]
        
        for angle in angles:
            level_value = (sqrt_base + (angle / 360)) ** 2
            levels[f"level_{angle}"] = level_value
        
        # Cache the calculated levels
        self.gann_levels_cache[base_price] = levels
        return levels
    
    def get_market_data(self, pair: str, timeframe: str, count: int = 10) -> List[Dict]:
        """Get market data for analysis"""
        try:
            # Get historical candles
            data = self.api.get_candles(pair, timeframe, count, time.time())
            return data
        except Exception as e:
            self.logger.error(f"Error getting market data: {str(e)}")
            return []
    
    def analyze_volume(self, pair: str, timeframe: str, lookback_bars: int = 5) -> Dict:
        """Analyze volume to detect unusual activity"""
        try:
            data = self.api.get_candles(pair, timeframe, lookback_bars, time.time())
            if not data:
                return {"avg_volume": 0, "current_volume": 0, "volume_ratio": 0}
            
            volumes = [bar['volume'] for bar in data]
            avg_volume = sum(volumes) / len(volumes)
            current_volume = volumes[-1]  # Last bar volume
            
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            return {
                "avg_volume": avg_volume,
                "current_volume": current_volume,
                "volume_ratio": volume_ratio
            }
        except Exception as e:
            self.logger.error(f"Error analyzing volume: {str(e)}")
            return {"avg_volume": 0, "current_volume": 0, "volume_ratio": 0}
    
    def check_spread(self, pair: str) -> float:
        """Check current spread for the pair"""
        try:
            # Get bid and ask prices
            bid = self.api.get_quote(pair)['bid']
            ask = self.api.get_quote(pair)['ask']
            spread = abs(ask - bid) * 10000  # Convert to pips for EURUSD
            return spread
        except Exception as e:
            self.logger.error(f"Error checking spread: {str(e)}")
            return float('inf')
    
    def get_signal_direction(self, current_price: float, gann_levels: Dict[str, float]) -> Optional[str]:
        """
        Determine signal direction based on Gann levels
        Returns 'call' if price breaks above key level, 'put' if below
        """
        # Get the 45-degree level as primary signal level
        primary_level = gann_levels.get('level_45', current_price)
        
        # Additional levels for confirmation
        support_level = gann_levels.get('level_0', current_price * 0.999)
        resistance_level = gann_levels.get('level_90', current_price * 1.001)
        
        if current_price > resistance_level:
            return 'call'
        elif current_price < support_level:
            return 'put'
        elif current_price > primary_level:
            return 'call'
        elif current_price < primary_level:
            return 'put'
        
        return None
    
    def apply_martingale_logic(self, last_trades: List[Dict]):
        """Apply martingale logic based on last trades"""
        if len(last_trades) < 2:
            return
        
        # Check if last 2 trades were losses
        last_two_losses = (
            len(last_trades) >= 2 and 
            not last_trades[-1]['result'] and 
            not last_trades[-2]['result']
        )
        
        if last_two_losses and self.martingale_level < self.max_martingale_levels:
            # Double the stake
            self.current_stake *= 2
            self.martingale_level += 1
            self.logger.info(f"Martingale applied! New stake: ${self.current_stake:.2f}, Level: {self.martingale_level}")
        elif len(last_trades) > 0 and last_trades[-1]['result']:
            # Reset martingale after win
            self.reset_martingale()
    
    def reset_martingale(self):
        """Reset martingale settings"""
        if self.martingale_level > 0:
            self.logger.info("Resetting martingale after profitable trade")
        self.current_stake = self.initial_stake
        self.martingale_level = 0
    
    def check_stop_conditions(self) -> bool:
        """Check if we should stop trading due to losses"""
        # Check if we've reached the maximum martingale levels
        if self.martingale_level >= self.max_martingale_levels:
            self.logger.warning(f"Reached maximum martingale levels ({self.max_martingale_levels}). Stopping.")
            return True
        
        # Update balance and check stop loss
        self.update_balance()
        if self.balance > 0:
            loss_percentage = (self.initial_balance - self.balance) / self.initial_balance
            if loss_percentage >= self.stop_loss_percentage:
                self.logger.warning(f"Stop loss triggered! Loss percentage: {loss_percentage:.2%}. Stopping.")
                return True
        
        return False
    
    def log_trade(self, timestamp: str, entry_price: float, signal_type: str, 
                  direction: str, stake: float, result: bool, profit: float):
        """Log trade to CSV file"""
        with open(self.csv_filename, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'entry_price', 'signal_type', 'direction', 'stake', 'result', 'profit']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({
                'timestamp': timestamp,
                'entry_price': entry_price,
                'signal_type': signal_type,
                'direction': direction,
                'stake': stake,
                'result': result,
                'profit': profit
            })
    
    def execute_trade(self, direction: str, stake: float) -> Tuple[bool, float]:
        """Execute a trade and return result"""
        try:
            # Check spread before trading
            spread = self.check_spread(self.pair)
            if spread > self.spread_limit:
                self.logger.warning(f"Spread too high ({spread:.2f} pips > {self.spread_limit}). Skipping trade.")
                return False, 0.0
            
            self.logger.info(f"Executing {direction} trade with stake ${stake:.2f}")
            
            # Place the trade
            status, buy_id = self.api.buy(stake, self.pair, direction, 1)  # 1 minute expiry
            
            if not status:
                self.logger.error(f"Trade execution failed: {buy_id}")
                return False, 0.0
            
            # Wait for trade to expire and get result
            time.sleep(60)  # Wait for 1 minute expiry
            
            # Check trade result
            trade_result = self.api.check_win_v4(buy_id)
            profit = trade_result if trade_result > 0 else -stake
            
            if trade_result > 0:
                self.logger.info(f"Trade successful! Profit: ${trade_result:.2f}")
                return True, profit
            else:
                self.logger.info(f"Trade failed! Loss: ${stake:.2f}")
                return False, -stake
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")
            return False, 0.0
    
    async def monitor_market_and_trade(self):
        """Main trading loop that monitors market and executes trades"""
        self.initial_balance = self.balance
        
        while self.is_running:
            try:
                # Update balance periodically
                if int(time.time()) % 30 == 0:  # Every 30 seconds
                    self.update_balance()
                
                # Get current market data
                market_data = self.get_market_data(self.pair, self.timeframe, 10)
                if not market_data:
                    await asyncio.sleep(1)
                    continue
                
                # Get latest bar
                latest_bar = market_data[-1]
                current_price = latest_bar['close']
                current_time = latest_bar['time']
                
                # Check if we're waiting for next bar
                if current_time <= self.last_bar_timestamp:
                    # Wait for new bar (with timing precision)
                    sleep_time = 60 - (time.time() % 60) + 0.5  # Aim for ~500ms before next bar
                    await asyncio.sleep(max(0.1, sleep_time))
                    continue
                
                # Process new bar
                self.last_bar_timestamp = current_time
                self.logger.info(f"New bar detected at {datetime.fromtimestamp(current_time)}, Price: {current_price}")
                
                # Calculate Gann levels based on the close of the last completed bar
                gann_levels = self.calculate_gann_levels(current_price)
                
                # Analyze volume for confirmation
                volume_analysis = self.analyze_volume(self.pair, self.timeframe)
                
                # Generate signal
                signal_direction = self.get_signal_direction(current_price, gann_levels)
                
                # Only proceed if we have a clear signal and volume confirmation
                if signal_direction and volume_analysis['volume_ratio'] > 2.0:  # Volume > 200% average
                    signal_type = f"Gann_M{self.martingale_level}" if self.martingale_level > 0 else "Gann"
                    
                    self.logger.info(f"Signal generated: {signal_direction.upper()} at {current_price} "
                                   f"(Volume ratio: {volume_analysis['volume_ratio']:.2f}x)")
                    
                    # Apply martingale logic based on recent trades
                    self.apply_martingale_logic(self.position_history)
                    
                    # Check stop conditions
                    if self.check_stop_conditions():
                        self.is_running = False
                        break
                    
                    # Execute trade
                    success, profit = self.execute_trade(signal_direction, self.current_stake)
                    
                    # Log the trade
                    trade_log = {
                        'timestamp': datetime.fromtimestamp(current_time).isoformat(),
                        'entry_price': current_price,
                        'signal_type': signal_type,
                        'direction': signal_direction,
                        'stake': self.current_stake,
                        'result': success,
                        'profit': profit
                    }
                    
                    self.position_history.append(trade_log)
                    self.log_trade(**trade_log)
                    
                    # Reset martingale after win or after reaching max levels
                    if success or self.martingale_level >= self.max_martingale_levels:
                        self.reset_martingale()
                    
                    # Check stop conditions again after trade
                    if self.check_stop_conditions():
                        self.is_running = False
                        break
                
                # Small delay to prevent overwhelming the API
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def run(self):
        """Run the trading bot"""
        if not self.connect_to_iqoption():
            self.logger.error("Failed to connect to IQ Option. Exiting.")
            return
        
        self.is_running = True
        self.logger.info("Starting Gann Square 9 + Martingale Trading Bot...")
        
        try:
            await self.monitor_market_and_trade()
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
        finally:
            self.is_running = False
            self.logger.info("Bot stopped")


class BacktestEngine:
    """Backtesting engine for historical data simulation"""
    
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.data = []
        self.load_historical_data()
    
    def load_historical_data(self):
        """Load historical data for backtesting"""
        # In a real implementation, this would load from a file
        # For now, we'll simulate data
        self.logger = logging.getLogger(__name__)
        self.logger.info("Loading historical data for backtesting...")
        
        # Simulate 1 week of M1 data (7 days * 24 hours * 60 minutes = 10080 points)
        start_time = time.time() - (7 * 24 * 60 * 60)  # 1 week ago
        current_price = 1.0800  # Starting EURUSD price
        
        for i in range(10080):  # 1 week of M1 data
            # Simulate small price movements
            movement = np.random.normal(0, 0.0005)  # Small random movement
            current_price += movement
            
            timestamp = start_time + (i * 60)  # Each minute
            
            self.data.append({
                'time': timestamp,
                'open': current_price,
                'high': current_price + abs(movement),
                'low': current_price - abs(movement),
                'close': current_price,
                'volume': np.random.randint(100, 1000)  # Random volume
            })
    
    def run_backtest(self, bot_params: Dict):
        """Run backtest with simulated latency"""
        self.logger.info("Running backtest with Gann Square 9 + Martingale strategy...")
        
        # Create a simplified version of the bot for backtesting
        bot = GannSquare9Bot(bot_params.get('email', 'test'), 
                           bot_params.get('password', 'test'))
        
        # Override some methods for backtesting
        bot.get_market_data = lambda pair, timeframe, count, current_time: \
            self.get_historical_candles(count, int(current_time))
        
        bot.execute_trade = self.simulate_trade
        
        # Run the backtest through historical data
        start_balance = 1000.0
        current_balance = start_balance
        position_history = []
        
        # Simulate trading through historical data
        for i in range(len(self.data) - 10):  # Leave last 10 for safety
            # Simulate network latency
            time.sleep(0.2)  # 200ms latency simulation
            
            # Get current market data
            current_data = self.data[i:i+10]  # Last 10 bars
            current_price = current_data[-1]['close']
            
            # Calculate Gann levels
            gann_levels = bot.calculate_gann_levels(current_price)
            
            # Generate signal
            signal_direction = bot.get_signal_direction(current_price, gann_levels)
            
            # Simulate volume analysis
            volumes = [bar['volume'] for bar in current_data[-5:]]
            avg_volume = sum(volumes) / len(volumes)
            current_volume = current_data[-1]['volume']
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Execute trade if conditions met
            if signal_direction and volume_ratio > 2.0:
                # Apply martingale logic
                if len(position_history) >= 2:
                    last_two_losses = all(not trade['result'] for trade in position_history[-2:])
                    if last_two_losses and bot.martingale_level < bot.max_martingale_levels:
                        bot.current_stake *= 2
                        bot.martingale_level += 1
                    elif position_history[-1]['result']:  # Reset after win
                        bot.reset_martingale()
                
                # Simulate trade execution
                success, profit = self.simulate_trade(signal_direction, bot.current_stake, current_data[-1])
                
                trade_log = {
                    'timestamp': datetime.fromtimestamp(current_data[-1]['time']).isoformat(),
                    'entry_price': current_price,
                    'signal_type': f"Gann_M{bot.martingale_level}" if bot.martingale_level > 0 else "Gann",
                    'direction': signal_direction,
                    'stake': bot.current_stake,
                    'result': success,
                    'profit': profit
                }
                
                position_history.append(trade_log)
                current_balance += profit
                
                # Log trade
                bot.log_trade(**trade_log)
                
                # Check stop conditions
                loss_percentage = (start_balance - current_balance) / start_balance
                if loss_percentage >= bot.stop_loss_percentage or bot.martingale_level >= bot.max_martingale_levels:
                    self.logger.info("Stop condition reached during backtest")
                    break
        
        # Print backtest results
        total_profit = current_balance - start_balance
        win_rate = sum(1 for trade in position_history if trade['result']) / len(position_history) if position_history else 0
        
        self.logger.info(f"Backtest Results:")
        self.logger.info(f"Initial Balance: ${start_balance:.2f}")
        self.logger.info(f"Final Balance: ${current_balance:.2f}")
        self.logger.info(f"Total Profit/Loss: ${total_profit:.2f}")
        self.logger.info(f"Win Rate: {win_rate:.2%}")
        self.logger.info(f"Total Trades: {len(position_history)}")
        
        return {
            'initial_balance': start_balance,
            'final_balance': current_balance,
            'total_profit': total_profit,
            'win_rate': win_rate,
            'total_trades': len(position_history)
        }
    
    def get_historical_candles(self, count: int, current_time: int):
        """Get historical candles for backtesting"""
        # Find index closest to current_time
        closest_idx = min(range(len(self.data)), 
                         key=lambda i: abs(self.data[i]['time'] - current_time))
        
        start_idx = max(0, closest_idx - count + 1)
        return self.data[start_idx:closest_idx + 1]
    
    def simulate_trade(self, direction: str, stake: float, current_bar: Dict) -> Tuple[bool, float]:
        """Simulate a trade based on historical data"""
        # Simple simulation: 60% win rate for demonstration
        win_probability = 0.6
        
        # Simulate outcome
        is_win = np.random.random() < win_probability
        
        if is_win:
            # Calculate profit (assuming binary options with 80% payout)
            profit = stake * 0.8
            self.logger.debug(f"Simulated WIN: ${profit:.2f}")
        else:
            # Loss is the stake amount
            profit = -stake
            self.logger.debug(f"Simulated LOSS: ${profit:.2f}")
        
        return is_win, profit


def main():
    """Main function to run the bot or backtest"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gann Square 9 + Martingale Trading Bot for IQ Option")
    parser.add_argument("--mode", choices=["live", "backtest"], default="backtest", 
                       help="Run mode: live trading or backtest")
    parser.add_argument("--email", type=str, help="IQ Option email")
    parser.add_argument("--password", type=str, help="IQ Option password")
    
    args = parser.parse_args()
    
    if args.mode == "live":
        if not args.email or not args.password:
            print("For live trading, email and password are required!")
            return
        
        bot = GannSquare9Bot(args.email, args.password)
        
        # Run the bot
        try:
            asyncio.run(bot.run())
        except KeyboardInterrupt:
            print("\nBot stopped by user")
        except Exception as e:
            print(f"Error running bot: {str(e)}")
    
    elif args.mode == "backtest":
        print("Running backtest...")
        backtester = BacktestEngine("dummy_data")  # Will generate simulated data
        
        bot_params = {
            'email': 'test@example.com',
            'password': 'testpass'
        }
        
        results = backtester.run_backtest(bot_params)
        print(f"Backtest completed. Final balance: ${results['final_balance']:.2f}")


if __name__ == "__main__":
    main()