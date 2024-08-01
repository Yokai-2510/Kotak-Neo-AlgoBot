# trading_bot.py

import threading
from datetime import datetime, timedelta
import time
from config import strategy_dict
from module_evaluate import start_strategy
from module_data import fetch_indicator, fetch_spot_yf, run_websocket
from module_utilities import read_spot_price, parse_time, log_message, clear_log, read_log , display_info
from credentials import consumer_key, consumer_secret, mobile, mpin, login_password
from neo_api_client import NeoAPI
import os

# Load strategy dictionary values
index = strategy_dict['index']
indicator = fetch_indicator(index)
log_message(indicator)
last_close = fetch_spot_yf(index)
current_zone = None
last_processed_price = None
client = None

client = NeoAPI(consumer_key=consumer_key, consumer_secret=consumer_secret, environment='prod')
client.login(mobilenumber=mobile, password=login_password)
client.session_2fa(OTP=mpin)

websocket_thread = threading.Thread(target=run_websocket, args=(client,))
websocket_thread.start()
time.sleep(4)


def main():
    global current_zone, last_processed_price  # Make sure to use global variables
    
    market_open_str = strategy_dict.get('market_open', "9:15")
    market_close_str = strategy_dict.get('market_close', "15:29")
    
    market_open = parse_time(market_open_str)
    market_close = parse_time(market_close_str)
    
    while True:
        time.sleep(1)
        spot_price = read_spot_price()

        current_time = datetime.now().time()

        if current_time > market_close:
            print("Market closed")
            break

        if current_time < market_open:
            print("Waiting for market to open")
            continue

        current_zone, last_processed_price = start_strategy(client, spot_price, indicator, current_zone, last_processed_price, strategy_dict)
        
        display_info(spot_price, current_zone)

if __name__ == "__main__":
    clear_log() 
    main()
