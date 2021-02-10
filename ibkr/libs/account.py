import time
import numpy as np


def getOpenOrders(app):
    app.reqOpenOrders()
    time.sleep(1)
    order_df = app.order_df
    order_df = order_df.drop_duplicates()
    return order_df


def getCurrentPositions(app):
    app.reqPositions()
    time.sleep(1)
    pos_df = app.pos_df
    pos_df = pos_df[pos_df.Position != 0].drop_duplicates()
    return pos_df


def getCurrentPositionsList(app):
    """return unique list of current symbols in position"""
    app.reqPositions()
    time.sleep(1)
    pos_df = app.pos_df
    pos_df = pos_df[pos_df.Position != 0].drop_duplicates()
    tickers_curr = np.unique(pos_df.Symbol.to_numpy())
    return tickers_curr


def getAccountSummary(app):
    app.reqAccountSummary(1, "All", "$LEDGER:ALL")
    time.sleep(1)
    acc_summ_df = app.acc_summary
    acc_summ_df = acc_summ_df.drop_duplicates()
    return acc_summ_df


def getAccountBalance(app):
    """return current account balance"""
    app.reqAccountSummary(1, "All", "$LEDGER:ALL")
    time.sleep(1)
    acc_summ_df = app.acc_summary
    acc_summ_df = acc_summ_df.drop_duplicates()
    current_balance = acc_summ_df[
        (acc_summ_df.Currency == "EUR") & (acc_summ_df.Tag == "CashBalance")
    ]["Value"].values[0]
    return float(current_balance)


def getPnlSummary(app):
    app.reqPnL(2, "DU3213143", "")
    time.sleep(1)
    pnl_summ_df = app.pnl_summary
    pnl_summ_df = pnl_summ_df.drop_duplicates()
    return pnl_summ_df


def calculateOpenTradeSlots(portfolio_size, num_of_curr_pos):
    """return amount of open trade slots"""
    open_slots = int(portfolio_size) - int(num_of_curr_pos)
    return open_slots


def allocateTradeBudget(curr_balance, open_slots, max_per_trade=2000):
    """"return available budget per open trade slot"""
    trade_budget = min(float(curr_balance) / float(open_slots), float(max_per_trade))
    return trade_budget
