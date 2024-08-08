
strategy_dict = {

    # User Configuration
    "index" : "NIFTY" , # BANKNIFTY or NIFTY
    'zone_change_delay': 10,  # Delay in seconds between zone changes before order placement
    "market_open" : "00:15" , # Time at which the Market Opens
    "market_close" : "15:29" , # Time at which the Market closes .

    # Entry 
    "quantity" : '2', # Enter the Quantity ( in lots)
    "order_type" : "MKT" , # L for LIMIT and MKT for MARKET
    "limit_price" : "0" , # if order type is limit , then put the limit value
    "ikey_criteria" : "LTP" , # Possible Values : STRIKE , ATM , ITM , LTP
    "ikey_criteria_value" : "13" , # only applicable for STRIKE and LTP otherwise 0
    "AMO" : "False" , # YES  or NO (after market order)
    
    # Exit
    "global_loss" : "20" , # Global stop loss - will supersede strategy stop loss
    "global_profit" : "20" , # Global profit - will supersede strategy profit 
    "strategy_loss" : "10" , # stop loss at strategy level
    "strategy_profit" : "10" , # profit/target at strategy level
    "exit_time" : "15:29"  # Open Positions will brute force exit at this time (supersedes risk conditions)
    
}


