import threading
import time, datetime, pytz
from collections import defaultdict
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
#from ibapi.order_state import OrderState
from ibapi.execution import ExecutionFilter
from ibapi.common import *

# IBAPI Wrapper and Client class
class TradeApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        # Store recent trades
        self.recent_trades = []
        
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

    def execDetails(self, reqId, contract, execution):
        """Handle execution details received from IBAPI."""
        super().execDetails(reqId, contract, execution) #initialise to reset recent_trades to be empty
        trade_data = {
            "id": execution.execId,
            "orderId": execution.orderId,
            "symbol": contract.symbol,
            "price": execution.price,
            "avgPrice": execution.avgPrice, #if 2 or more trades to fill one order, avePrice is correct only on the last trade of this orderID
            "quantity": execution.shares,
            "cumQuantity": execution.cumQty,
            "direction": execution.side,
            "timestamp": execution.time
        }
        # Store this trade
        self.recent_trades.append(trade_data)
        #print(f"Trade executed: {trade_data}")
    
    def get_recent_trades(self):
        """Return the 20 most recent trades stored in memory."""
        print("Requesting recent trades...")
        return self.recent_trades[-20:]
    def request_recent_trades(self):
        """Send a request to Interactive Brokers to get recent trades."""
        # Set up the execution filter to limit request to last 10 days
        filter = ExecutionFilter()
        today = datetime.datetime.now(pytz.utc)
        ten_days_ago = today - datetime.timedelta(days=10)
        filter.time = ten_days_ago.strftime("%Y%m%d-%H:%M:%S")

        # Request historical executions from IB
        self.reqExecutions(1002, filter)

    def get_consolidated_trades(self):
        """Return a list of consolidated trades based on orderId."""
        # Group trades by orderId
        grouped_trades = defaultdict(list)
        for trade in self.recent_trades:
            grouped_trades[trade['orderId']].append(trade)

        # Create a consolidated list
        consolidated_trades = []
        for order_id, trades in grouped_trades.items():
            if len(trades) == 1:
                # If orderId appears only once, copy the trade over
                trade = trades[0]
                consolidated_trade = {
                    "orderId": trade["orderId"],
                    "symbol": trade["symbol"],
                    "avgPrice": trade["avgPrice"],
                    "cumQuantity": trade["cumQuantity"],
                    "direction": trade["direction"],
                    "timestamp": trade["timestamp"]
                }
                consolidated_trades.append(consolidated_trade)
            else:
                # If orderId appears more than once, find the trade with max cumQuantity
                max_trade = max(trades, key=lambda x: x['cumQuantity'])
                consolidated_trade = {
                    "orderId": max_trade["orderId"],
                    "symbol": max_trade["symbol"],
                    "avgPrice": max_trade["avgPrice"],
                    "cumQuantity": max_trade["cumQuantity"],
                    "direction": max_trade["direction"],
                    "timestamp": max_trade["timestamp"]
                }
                consolidated_trades.append(consolidated_trade)

        return consolidated_trades

# Function to start the IBAPI connection
def start_ibapi_connection():
    app = TradeApp()
    app.connect("127.0.0.1", 7496, clientId=22)

    # Start the connection in a new thread to prevent blocking
    con_thread = threading.Thread(target=app.run, daemon=True)
    con_thread.start()

    # Allow some time for the connection to establish
    time.sleep(1)

    return app

# Future and Stock Contract Setup
def usFuture(localSymbol, sectype="FUT", currency="USD", exchange="CME"):
    contract = Contract()
    contract.localSymbol = localSymbol
    contract.secType = sectype
    contract.currency = currency
    contract.exchange = exchange
    return contract

def usStk(symbol, sectype="STK", currency="USD", exchange="SMART"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sectype
    contract.currency = currency
    contract.exchange = exchange
    return contract

# Create a market order
def mktOrder(direction, quantity):
    order = Order()
    order.action = direction
    order.orderType = "MKT"
    order.totalQuantity = quantity
    return order