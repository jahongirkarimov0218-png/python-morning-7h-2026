#!/usr/bin/env python3
"""
Simple script to run the Gann Square 9 + Martingale Trading Bot
"""

import sys
import os

# Add the workspace directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to run the bot"""
    print("Gann Square 9 + Martingale Trading Bot")
    print("=" * 40)
    
    # Import the main module
    try:
        from iqoption_gann_bot import main as bot_main
        print("✅ Successfully imported bot module")
        
        # Run the bot
        print("\n🚀 Starting the bot...")
        bot_main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the iqoption_gann_bot.py file exists in the current directory.")
        return 1
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())