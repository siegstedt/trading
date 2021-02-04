import time


def getOpenOrders(app):
    app.reqOpenOrders()
    time.sleep(1)
    order_df = app.order_df
    return order_df


def getCurrentPositions(app):
    app.reqPositions()
    time.sleep(1)
    pos_df = app.pos_df
    return pos_df


def getAccountSummary(app):
    app.reqAccountSummary(1, "All", "$LEDGER:ALL")
    time.sleep(1)
    acc_summ_df = app.acc_summary
    return acc_summ_df


def getPnlSummary(app):
    app.reqPnL(2, "DU3213143", "")
    time.sleep(1)
    pnl_summ_df = app.pnl_summary
    return pnl_summ_df
