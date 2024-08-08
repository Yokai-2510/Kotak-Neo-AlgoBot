
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

**NOTE** : If the zone is starting from Zone 3, an order for Zone 3 will not be placed. Once a zone change is detected , only then ,  a new order will be placed for the new zone.

## Exit Conditions

- **Exit Time**
- **Global Profit**
- **Global Loss**
- **Strategy Profit**
- **Strategy Loss**
- **Zone Change**
