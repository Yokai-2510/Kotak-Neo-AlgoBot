# Trading-Bot---Kotak-Neo
A Price Action / Range based algo trading bot using Kotak Neo API 

## Strategy Dict 
Users can configure the strategy dict inside the config file 

## Zone Definitions

| **Zone**   | **Condition**                              | **Option Type** |
| ---------- | ------------------------------------------ | --------------- |
| **Zone 5** | Spot price > **High**                      | CE              |
| **Zone 4** | **High** < Spot price < **Max Close**      | PE              |
| **Zone 3** | **Max Close** > Spot price > **Min Close** | CE + PE         |
| **Zone 2** | **Min Close** > Spot price > **Low**       | CE              |
| **Zone 1** | Spot price < **Low**                       | PE              |

## Entry Conditions

- **Market Hours** : Current Time should be between Market Hours.
- **Zone Change Detection:** A new order will be placed only when a zone change is detected.
- **New Order Delay:**  A delay specified by the user in the strategy dict will be implemented for a new zone.
  
**NOTE** : If the zone is starting from Zone 3, an order for Zone 3 will not be placed. Once a zone change is detected , only then ,  a new order will be placed for the new zone.

## Exit Conditions

- **Exit Time** : Exit time specified by the user, default value is market close .
- **Global Profit** : Global level Profit
- **Global Loss** : Global level Loss
- **Strategy Profit** : Strategy level profit
- **Strategy Loss** : Strategy level loss
- **Zone Change** : If zone change detected from the time when the order was placed 
