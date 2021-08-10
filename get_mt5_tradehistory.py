import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import telegram
import login

if not mt5.initialize(
    login=login.login_id,
    server=login.server,
    password=login.login_pw,
    portable=True,
):
    print("User not authorized.")
    quit()

## Configurations to export trade histroy into csv file
# Set location
loc = ""

# Set excel name to be generated
fname = "fx_tradehistory_mt5"

## Main
# global_message for sending via telegram
message_html = ""

# number of columns to be displayed
pd.set_option("display.max_columns", 500)

# max table width to display
pd.set_option("display.width", 1500)

# Set the timeframe to retrieve our trades history
from_date = datetime(2021, 1, 1)
to_date = datetime.now()

# Get Account Info Main
def getAccountInfo():
    global message_html

    account_info = mt5.account_info()
    if account_info != None:
        # Display trading account data 'as is'
        """print(account_info)"""

        # Get the info we require from account_info
        account_info_dict = mt5.account_info()._asdict()

        get_account = account_info_dict["login"]
        get_name = account_info_dict["name"]
        get_currency = account_info_dict["currency"]
        get_leverage = account_info_dict["leverage"]
        get_balance = account_info_dict["balance"]
        get_credit = account_info_dict["credit"]
        get_profit = account_info_dict["profit"]
        get_equity = account_info_dict["equity"]
        get_margin = account_info_dict["margin"]
        get_margin_free = account_info_dict["margin_free"]

        message_html += "===TRADING SUMMARY===\nAccount: %s\nName: %s\nCurrency: %s\nLeverage: 1:%s\nBalance: %s\nCredit: %s\nProfit: %s\nEquity: %s\nMargin: %s\nMargin Free: %s" % (
            get_account,
            get_name,
            get_currency,
            get_leverage,
            get_balance,
            get_credit,
            get_profit,
            get_equity,
            get_margin,
            get_margin_free,
        )
    else:
        print(
            "failed to authorize, error code =",
            mt5.last_error(),
        )


# Get History Orders Main
def getHistoryOrders():
    global message_html

    # Retrieve the list of deals in tuple and frame with pandas
    deals = mt5.history_deals_get(from_date, to_date)

    if deals == None:
        print("No deals, error code={}".format(mt5.last_error()))
    elif len(deals) > 0:

        # pandas.DataFrame to display in table-view
        df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        df["time"] = pd.to_datetime(df["time"], unit="s")
        # We sort if by position_id followed by entry so as to get completed trades (deal-in/deal-out)

        df = df.sort_values(by=["position_id", "entry"])
        """ print(df) """

        # We do df.duplicated to remove away 1 row of the similar trade position to get the position_id
        # df_no_duplicates is used as a temporary dataframe
        df_no_duplicates = df.loc[df.index[df.duplicated(subset=["position_id"])]]

        # posList contains all the trade positions that have completed a deal -> (deal-in/deal-out)
        posList = []
        totalDeposits = df.loc[df["type"] == 2].iloc[0]["profit"]
        totalProfits = 0
        tradesWon = 0
        tradesLost = 0
        winRate = 0
        sendMsg = ""
        typeStr = {0: "BUY", 1: "SELL"}

        # Iterate through the rows in dataframe to retrieve only the specific column values of 'position_id'
        for index, row in df_no_duplicates.iterrows():
            posList.append(row["position_id"])

        # Once we got all the required position_ids, we search them on the main dataframe
        for pos_id in posList:
            pos = df.loc[df["position_id"] == pos_id]
            """ print(pos) """
            (
                symbol,
                type,
                size,
                open_time,
                open_price,
                close_time,
                close_price,
                swap,
                profit,
            ) = (
                pos["symbol"].iloc[0],
                pos["type"].iloc[0],
                pos["volume"].iloc[0],
                pos["time"].iloc[0],
                pos["price"].iloc[0],
                pos["time"].iloc[1],
                pos["price"].iloc[1],
                pos["swap"].iloc[1],
                pos["profit"].iloc[1],
            )

            totalProfits += profit + swap
            if profit > 0:
                tradesWon += 1
            else:
                tradesLost += 1

            sendMsg += "{} {} {} {} {} {} {} {} {}\n".format(
                symbol,
                typeStr[type],
                size,
                open_time,
                open_price,
                close_time,
                close_price,
                swap,
                profit,
            )

        ## Miscellaneous
        winRate = (tradesWon / tradesWon + tradesLost) * 10

        message_html += (
            "\n\n===ORDER HISTORY===\nSYM TYPE LOT O/PRICE ENTRY C/PRICE EXIT SWAP PROFIT\n\n"
            + sendMsg
            + (
                "\nDEPOSIT: {:.2f}\nCLOSED P/L: {:.2f}\nW/R: {:.0f}%".format(
                    totalDeposits, totalProfits, winRate
                )
            )
        )

        # Generate mt5 trades history into excel sheet
        """ df.to_excel(loc + fname + ".xlsx") """


# Telegram Bot Main
def telegram_bot():
    ## Initializing telegram bot ##
    """bot = telegram.Bot(token=login.bot_token)
    bot.send_message(
        chat_id="@%s" % login.bot_id,
        text=message_html,
        parse_mode=telegram.ParseMode.HTML,
    )"""
    print(message_html)


getAccountInfo()
getHistoryOrders()
telegram_bot()

mt5.shutdown()
