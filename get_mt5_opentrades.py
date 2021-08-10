import MetaTrader5 as mt5
import time
from datetime import datetime
import telegram
import pytz
import schedule
import login

# DEFINE GLOBAL CONSTANTS
message_html = ""


def connect():
    if not mt5.initialize(
        login=login.login_id,
        server=login.server,
        password=login.login_pw,
        portable=True,
    ):
        print("User not authorized.")
        quit()


def get_new_positions():

    positions = mt5.positions_get()

    if positions == None:
        print("No positions, error code={}".format(mt5.last_error()))
    elif len(positions) > 0:

        global message_html
        posMsg = ""

        for position in positions:
            lst = list(position)
            """ print(position) """
            get_symbol = lst[16]
            get_lotsize = lst[9]
            get_oprice = datetime.fromtimestamp(lst[1]).strftime("%Y-%m-%d %I:%M:%S")
            get_price_open = lst[10]
            get_SL = lst[11]
            get_TP = lst[12]
            get_curr_price = lst[13]
            get_profit = lst[15]
            get_type = lst[5]
            typeStr = {0: "BUY", 1: "SELL"}

            posMsg += "{} {} {} {} {} {} {} {} {}\n".format(
                get_symbol,
                typeStr[get_type],
                get_lotsize,
                get_oprice,
                get_price_open,
                get_SL,
                get_TP,
                get_curr_price,
                get_profit,
            )

        message_html += (
            "\n\n===ACTIVE ORDERS===\nSYM TYPE LOT O/PRICE ENTRY SL TP CUR_PRICE PROFIT\n\n"
            + posMsg
            + ("\n\nTotal Positions: %s" % str(len(positions)))
        )

    mt5.shutdown()


def telegram_bot():
    ## Initializing telegram bot ##
    """bot = telegram.Bot(token=login.bot_token)
    bot.send_message(
        chat_id="@%s" % login.bot_id,
        text=message_html,
        parse_mode=telegram.ParseMode.HTML,
    )"""
    print(message_html)


def exec_trade():
    connect()
    get_new_positions()
    telegram_bot()


def schedule_trade():
    schedule.every(10).seconds.do(exec_trade)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    schedule_trade()
