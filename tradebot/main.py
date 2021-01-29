"""
main script for the trade bot app
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self,self)
        
    def error(self, reqId, errorCode, errorString):
        print(f"Error with Request ID {reqId} with Error Code {errorCode}. {errorString}")

    def contractDetails(self, reqId, contractDetails):
        print(f"Request ID: {reqId}, Contract: {contractDetails}")

# connect the app through the wrapper to the client
app = TradingApp()
app.connect("127.0.0.1", 7497, clientId=1)

# request contract details
contract = Contract()
contract.symbol = 'AAPL' 
contract.secType = 'STK'
contract.currency = 'USD'
contract.exchange = 'SMART'

app.reqContractDetails(1000, contract)

# run the app
app.run()
