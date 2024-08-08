# module_order.py


"""
Glossary -->

- This Module Contains functions related to Order Placement 

- order_info contains all the flags and details of the order and is also used for communication within the execute order function
    It is initialized for every new order

Flow of Execution -->

- Entry Function / Entry point - execute order function 

    -> Function >> select_ikey
        - The appropriate instrument key is selected according to the user config 

    -> Function >> initialize_order_info
        - The order_info dictioanary is intitialzed 
        - Buy Sell for entry / exit is decided etc 

    -> Function >> place_order 
        - ENTRY ORDER - The actual order is placed        

        - Function >> update_order_details
            - The order details are updated into the order info dictionary 

    -> evaluate_exit
        - This will constantly check for the exit conditions indefinitely and return true if exit conditions are met
        
        -> Function >> place_order 
            - EXIT ORDER is placed this time
            
            - Function >> update_order_details
                - The order details are updated into the order info dictionary 
"""


import math
import pandas as pd
import time
from datetime import datetime
from module_utilities import create_report, read_option_chain, read_spot_price , calculate_mtm , log_message
from config import strategy_dict


client = None    
option_type = None
zone_index = None


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


def select_ikey(strategy_dict, order_info,  option_type):

    nifty_options_df = read_option_chain()
    spot_price = read_spot_price()

    def ikey_atm(nifty_options_df, spot_price, order_info,option_type):
        if option_type == 'CE':
            atm_strike = math.ceil(spot_price / 100) * 100
        elif option_type == 'PE':
            atm_strike = math.floor(spot_price / 100) * 100
        
        filtered_df = nifty_options_df[(nifty_options_df['option_type'] == option_type) & 
                                       (nifty_options_df['strike_price'] == atm_strike)]
        
        if not filtered_df.empty:
            instrument_key = filtered_df.iloc[0]['instrument_key']
            order_info['order_strike'] = atm_strike
            order_info['order_ikey'] = instrument_key
            return instrument_key
        else:
            return None

    def ikey_itm(nifty_options_df, spot_price, order_info,option_type):
        if option_type == 'CE':
            itm_strike = math.floor((spot_price - 1) / 100) * 100
        elif option_type == 'PE':
            itm_strike = math.ceil((spot_price + 1) / 100) * 100
        
        filtered_df = nifty_options_df[(nifty_options_df['option_type'] == option_type) & 
                                       (nifty_options_df['strike_price'] == itm_strike)]
        
        if not filtered_df.empty:
            instrument_key = filtered_df.iloc[0]['instrument_key']
            order_info['order_strike'] = itm_strike
            order_info['order_ikey'] = instrument_key
            return instrument_key
        else:
            return None

    def ikey_ltp(nifty_options_df, strategy_dict, order_info, option_type):
        preferred_ltp = float(strategy_dict['ikey_criteria_value'])
        filtered_options = nifty_options_df[nifty_options_df['option_type'] == option_type].copy()
        
        if filtered_options.empty:
            log_message(f"No options found for type {option_type}")
            return None
        
        filtered_options['ltp_diff'] = abs(filtered_options['ltp'] - preferred_ltp)
        nearest_option = filtered_options.loc[filtered_options['ltp_diff'].idxmin()]
        
        order_info['order_strike'] = nearest_option['strike_price']
        order_info['order_ikey'] = nearest_option['instrument_key']
        return nearest_option['instrument_key']
    
    def ikey_strike(nifty_options_df, strategy_dict, order_info, option_type):
        preferred_strike = float(strategy_dict['ikey_criteria_value'])
        filtered_options = nifty_options_df[nifty_options_df['option_type'] == option_type].copy()
        
        if filtered_options.empty:
            log_message(f"No options found for type {option_type}")
            return None
        
        filtered_options['strike_diff'] = abs(filtered_options['strike_price'] - preferred_strike)
        nearest_option = filtered_options.loc[filtered_options['strike_diff'].idxmin()]
        
        order_info['order_strike'] = nearest_option['strike_price']
        order_info['order_ikey'] = nearest_option['instrument_key']
        return nearest_option['instrument_key']

    if strategy_dict['ikey_criteria'] == 'ATM':
        return ikey_atm(nifty_options_df, spot_price, order_info,option_type)
    elif strategy_dict['ikey_criteria'] == 'ITM':
        return ikey_itm(nifty_options_df, spot_price, order_info,option_type)
    elif strategy_dict['ikey_criteria'] == 'LTP':
        return ikey_ltp(nifty_options_df, strategy_dict, order_info,option_type)
    elif strategy_dict['ikey_criteria'] == 'STRIKE':
        return ikey_strike(nifty_options_df, strategy_dict, order_info , option_type)
    else:
        log_message(f"Invalid ikey_criteria: {strategy_dict['ikey_criteria']}")
        return None



def initialize_order_info(order_info, zone_index, option_type, instrument_key):
    
    df = read_option_chain()
    
    order_info.update({
        'index': strategy_dict['index'],
        'order_status': 'Defining entry conditions, proceeding to Entry Order',
        'zone_index': zone_index,
        'mtm': None,
        'order_ikey': instrument_key,
        'order_strike': df.loc[df['instrument_key'] == instrument_key, 'strike_price'].values[0],
        'option_type': option_type,
        'real_quantity': None,
        'current_ltp': None,

        'entry_transaction_type': 'B' if zone_index in [1, 5] else 'S',
        'entry_order_id': None,
        'entry_success': False,
        'entry_ltp': None,
        'entry_time': None,
        'entry_spot': None,

        'exit_transaction_type': 'S' if zone_index in [1, 5] else 'B',
        'exit_order_id': None,
        'exit_success': False,
        'exit_criteria': None,
        'exit_ltp': None,
        'exit_time': None,
        'exit_spot': None,
    })



def update_order_details(client ,order_response, order_flag, strategy_dict, order_info):

    try:
        now = datetime.now()
        spot_price = read_spot_price()
        options_df = read_option_chain()
        instrument_key = order_info.get('order_ikey')
        current_ltp = options_df.loc[options_df['instrument_key'] == instrument_key, 'ltp'].values[0]
        order_placed = order_response.get('stat') == 'Ok' and 'nOrdNo' in order_response
        
        if order_placed:
            order_id = order_response['nOrdNo']
            order_details = client.order_history(order_id=str(order_id))
            order_complete = order_details['data'].get('stat') == 'Ok'
            
            # # Check if the order is rejected
            # order_completion = next((order['ordSt'] for order in order_details['data']['data']), None)
            # rejection_reason = next((order.get('rejRsn', '') for order in order_details['data']['data'] if order['ordSt'] == 'rejected'), None)
            
            # if order_completion == 'rejected':
            #     log_message(" Rejection Reason : ", rejection_reason)
            #     return False

            if order_complete:
                if order_flag == 'ENTRY':
                    order_info.update({
                        'entry_success': True,
                        'entry_order_id': order_id,
                        'entry_time': now,
                        'entry_ltp': current_ltp,
                        'entry_spot': spot_price,
                        'order_status': 'Entry Order Placed Successfully'
                    })
                elif order_flag == 'EXIT':
                    order_info.update({
                        'exit_success': True,
                        'exit_order_id': order_id,
                        'exit_time': now,
                        'exit_ltp': current_ltp,
                        'exit_spot': spot_price,
                        'order_status': 'Exit Order Placed Successfully'
                    })
                return True

        if order_flag == 'ENTRY':
            order_info['entry_success'] = False
        elif order_flag == 'EXIT':
            order_info['exit_success'] = False

        order_info['order_status'] = 'Order Placement or Execution Failed'
        return False


    except Exception as e:
        if order_flag == 'ENTRY':
            order_info['entry_success'] = False
        elif order_flag == 'EXIT':
            order_info['exit_success'] = False
        
        log_message(f"{order_flag} Order Execution Failed: If Position Open , Square Off Manually {e}")
        order_info['order_status'] = f"{order_flag} Order Execution Failed , If Position Open , Square OFf Manually"
        return False



def place_order(client, order_info, instrument_key, strategy_dict, order_flag):

    try:
        transaction = order_info.get('entry_transaction_type') if order_flag == 'ENTRY' else order_info.get('exit_transaction_type')
        quantity = str(int(strategy_dict.get('quantity', 0)) * 15) if strategy_dict.get('index') == 'BANKNIFTY' else str(int(strategy_dict.get('quantity', 0)) * 25)
        limit_price = str(strategy_dict.get('limit_price', 0)) if strategy_dict.get('order_type') == 'LIMIT' else '0'
        order_type = 'L' if strategy_dict.get('order_type') == 'LIMIT' else 'MKT'
        amo_flag = 'YES' if strategy_dict.get('AMO') == 'TRUE' else 'NO'
        order_info['real_quantity'] = quantity

        order_response = client.place_order(
            price = limit_price,
            order_type = order_type,
            quantity = quantity,
            trading_symbol = instrument_key,
            transaction_type = transaction,
            exchange_segment = "nse_fo",
            product = "NRML",
            validity = "DAY",
            amo = amo_flag,
            disclosed_quantity = "0",
            pf = "N",
            trigger_price = "0",
            market_protection = "0",
            tag = ''
        )

        #log_message("Order response:", order_response)
        return update_order_details(client ,order_response, order_flag, strategy_dict, order_info)
    
    except Exception as e:
        log_message(f"Exception when placing order: {e}")
        if order_flag == 'ENTRY':
            order_info['entry_success'] = False
        elif order_flag == 'EXIT':
            order_info['exit_success'] = False
        return False



def evaluate_exit(order_info , strategy_dict, indicator , status_dict):

    if order_info.get('entry_success') is False:
        order_info['exit_success'] = 'Entry Order Failed, hence no exit order placed'
        return False
    
    entry_ltp = float(order_info['entry_ltp'])
    global_profit = entry_ltp + float(strategy_dict.get('global_profit', 0))
    strategy_profit = entry_ltp + float(strategy_dict.get('strategy_profit', 0))
    global_loss = entry_ltp - float(strategy_dict.get('global_loss', 0))
    strategy_loss = entry_ltp - float(strategy_dict.get('strategy_loss', 0))
    exit_time_str = strategy_dict.get('exit_time', '3:28')
    exit_time = datetime.strptime(exit_time_str, '%H:%M').time()
    exit_time_today = datetime.combine(datetime.now().date(), exit_time)
    zone_index = order_info['zone_index'] 
    order_info['order_status'] = 'Checking Exit Conditions...'
    instrument_key = order_info['order_ikey']
    
    while True:

        time.sleep(1)
    
        options_df = read_option_chain()
        spot_price = read_spot_price()
        current_ltp = options_df.loc[options_df['instrument_key'] == instrument_key, 'ltp'].values[0]
        status_dict['current_ltp'] = current_ltp
        current_zone = detect_zone(spot_price, indicator)

        order_info['current_ltp'] = current_ltp

        if current_ltp >= global_profit:
            order_info['exit_criteria'] = 'global_profit'
            return True

        if current_ltp >= strategy_profit:
            order_info['exit_criteria'] = 'strategy_profit'
            return True
        
        if current_ltp <= global_loss:
            order_info['exit_criteria'] = 'global_loss'
            return True
        
        if current_ltp <= strategy_loss:
            order_info['exit_criteria'] = 'strategy_loss'
            return True
        
        if datetime.now() > exit_time_today:
            order_info['exit_criteria'] = 'exit time'
            return True
        
        if zone_index != current_zone :
            order_info['exit_criteria'] = 'Zone Changed'
            return True 



def execute_order(zone_index,option_type,indicator,strategy_dict,client,status_dict):
    
    # Initialize flags and Fetch Instrument Key
    #------------------------------------------------------------------------------------------------------
    status_dict['order_active'] = True
    order_info = {}
    instrument_key = select_ikey(strategy_dict,order_info, option_type)

    if instrument_key is None:
        create_report(order_info, zone_index)
        log_message(f"No suitable instrument found for option_type: {option_type}")
        status_dict['order_active'] = False
        return
    else :
        log_message("instrument key : " , instrument_key)
    initialize_order_info(order_info, zone_index, option_type, instrument_key)
    #------------------------------------------------------------------------------------------------------


    # Place Entry Order
    #------------------------------------------------------------------------------------------------------
    if  place_order(client, order_info, instrument_key, strategy_dict, 'ENTRY') is  False :
        order_info['order_status'] = ['Entry Order Failed . Order Cancelled']
        log_message(f"Order for zone : {zone_index} , option type : {option_type} failed")
        create_report (order_info,zone_index)
        status_dict['order_active'] = False
        return
    else :
        log_message(f" Entry Order for zone : {zone_index} , option type : {option_type} Placed successfully")
    #------------------------------------------------------------------------------------------------------


    # Place Exit Order and Check Exit Conditions
    #------------------------------------------------------------------------------------------------------
    try :
        if evaluate_exit(order_info,strategy_dict,indicator , status_dict) == True: 
            order_info['order_status'] = 'Exit conditions Met , Proceeding to exit order'
            if  place_order(client, order_info, instrument_key, strategy_dict, 'EXIT') is True :
                order_info['order_status'] = 'Exit order placed, Order Complete ! Report saved'
                log_message(f" Exit Order for zone : {zone_index} , option type : {option_type} Placed successfully")
                calculate_mtm(order_info)
                create_report(order_info, zone_index)
                status_dict['order_active'] = False
                return   
            else:
                order_info['order_status'] = 'Exit Order could not take place , if order is pending, square off manually'
                create_report(order_info, zone_index)
                status_dict['order_active'] = False
                log_message(f" Exit Order for zone : {zone_index} , option type : {option_type}  failed ! Square off if order pending")
                return      
    except :
        order_info['order_status'] =  "unknown_error within exit evaluation , order cancelled"
        create_report(order_info, zone_index)
        status_dict['order_active'] = False
        log_message(f" Exit Order for zone : {zone_index} , option type : {option_type}  failed ! Square off if order pending")
        return
    #------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    execute_order()
