# trading_bot.py

from config import strategy_dict
from module_evaluate import evaluate_strategy
from module_data import run_websocket
from module_utilities import log_message, clear_log , display_info
from credentials import fetch_client
from module_data import fetch_indicator

import threading
from datetime import datetime
import time

global status_dict
status_dict = {
    'order_active': False,
    'last_zone': None,
    'current_zone': None,
    'zone_changed': False,
    'zone_change_time': None,
    'current_spot_price': None,
    'market_status': None ,
    'current_ltp' : None
}
client = None
index = strategy_dict['index']
indicator = fetch_indicator(index)

# Connect with Kotak API and store it in client object
# ------------------------------------------------------------------------------------------------------
client = fetch_client()
log_message(f"Client / Access Token fetched successfully")
# ------------------------------------------------------------------------------------------------------


# Start the Websocket Thread
# ------------------------------------------------------------------------------------------------------
websocket_thread = threading.Thread(target=run_websocket, args=(client,))
websocket_thread.start()
time.sleep(5)
# ------------------------------------------------------------------------------------------------------


# Start the Evaluation Thread 
# ------------------------------------------------------------------------------------------------------
evaluation_thread = threading.Thread(target=evaluate_strategy, args=(client, strategy_dict,status_dict ,))
evaluation_thread.start()
time.sleep(1)
log_message(f"Websocket / Live Data connected successfully")
# ------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    clear_log() 
    while True :
        display_info(status_dict , indicator)
        time.sleep(2)
