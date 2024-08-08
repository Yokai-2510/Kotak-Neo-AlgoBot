from datetime import datetime, timedelta
import time
import threading
from module_data import fetch_indicator
from module_utilities import read_spot_price, parse_time, log_message
from module_order import execute_order
from config import strategy_dict

def assign_zone_order(zone: int, client, indicator, strategy_dict , status_dict):
    if zone == 5:
        threading.Thread(target=execute_order, args=(zone, 'CE', indicator, strategy_dict, client , status_dict)).start()
    elif zone == 4:
        threading.Thread(target=execute_order, args=(zone, 'PE', indicator, strategy_dict, client , status_dict)).start()
    elif zone == 3:
        threading.Thread(target=execute_order, args=(zone, "CE", indicator, strategy_dict, client , status_dict)).start()
        threading.Thread(target=execute_order, args=(zone, "PE", indicator, strategy_dict, client , status_dict)).start()
    elif zone == 2:
        threading.Thread(target=execute_order, args=(zone, "CE", indicator, strategy_dict, client , status_dict)).start()
    elif zone == 1:
        threading.Thread(target=execute_order, args=(zone, "PE", indicator, strategy_dict, client , status_dict)).start()


def is_market_hours(strategy_dict):

    current_time = datetime.now().time()
    market_open = parse_time(strategy_dict.get('market_open', "9:15"))
    market_close = parse_time(strategy_dict.get('market_close', "15:29"))
    return market_open <= current_time < market_close


def detect_zone(spot_price, indicator):

    if spot_price > indicator['high']:
        return 5
    elif indicator['high'] >= spot_price > indicator['max_close']:
        return 4
    elif indicator['max_close'] >= spot_price > indicator['min_close']:
        return 3
    elif indicator['min_close'] >= spot_price > indicator['low']:
        return 2
    else:
        return 1


def detect_zone_change(spot_price, indicator, status_dict, strategy_dict):
    new_zone = detect_zone(spot_price, indicator)
    last_zone = status_dict.get('current_zone')

    # Check if the zone has changed
    if new_zone != last_zone:
        status_dict['last_zone'] = last_zone
        status_dict['current_zone'] = new_zone
        status_dict['zone_changed'] = True
        status_dict['zone_change_time'] = datetime.now()

        # Calculate target time based on delay
        zone_change_delay = strategy_dict.get('zone_change_delay', 10)
        status_dict['target_time'] = status_dict['zone_change_time'] + timedelta(seconds=zone_change_delay)

        log_message(f"Zone changed from {last_zone} to {new_zone}. Waiting for delay period.")

    current_time = datetime.now()
    target_time = status_dict.get('target_time', None)

    # Only return True if the delay period has passed
    if status_dict['zone_changed']:
        if current_time >= target_time:
            # Reset the flag after the delay period has passed
            status_dict['zone_changed'] = False
            return True  # Time has passed

    return False



def evaluate_strategy(client, strategy_dict ,status_dict):
    
    index = strategy_dict['index']
    indicator = fetch_indicator(index)
    
    while True:

        spot_price = read_spot_price()
        status_dict['current_spot_price'] = spot_price
        
        if is_market_hours(strategy_dict):
            status_dict['market_status'] = 'open'
            
            if detect_zone_change(spot_price, indicator, status_dict, strategy_dict):
                log_message(f"Assigning new order for zone {status_dict['current_zone']}.")
                assign_zone_order(status_dict['current_zone'], client, indicator, strategy_dict, status_dict)
                status_dict['zone_changed'] = False
        
        else:
            status_dict['market_status'] = 'closed'
                
        time.sleep(1) 


if __name__ == "__main__":
    evaluate_strategy()
    detect_zone()
    detect_zone_change()
    assign_zone_order()
    is_market_hours(strategy_dict)
