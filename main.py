import ccxt
from df_maker import create_df
from dotenv import load_dotenv
import os
import time
import sys

while True:

    try:

        load_dotenv()

        API_KEY = os.getenv('API_KEY')
        SECRET_KEY = os.getenv('SECRET_KEY')

        exchange = ccxt.binanceusdm(
            {
                "enableRateLimit": True,
                "apiKey": API_KEY,
                "secret": SECRET_KEY,
            }
        )

        symbol = "BTCUSDT"
        time_frame = "15m"
        limit = 500

        available_tiers = exchange.fetch_leverage_tiers(symbols=[symbol])
        coin = symbol[:-4]
        max_lev = int(available_tiers[f'{coin}/USDT:USDT'][0]['maxLeverage'])

        exchange.set_leverage(leverage=max_lev, symbol=symbol)

        df = create_df(exchange=exchange, symbol=symbol,
                       time_frame=time_frame, limit=limit)

        long_signal = df['long'].iloc[-2]
        short_signal = df['short'].iloc[-2]

        if long_signal:
            entry_price = df['Open'].iloc[-1]
            sl = entry_price - round((df['ATR'].iloc[-2] * 4), 1)
            distance = entry_price - sl
            balance = exchange.fetch_balance()['USDT']['free']
            position_size = round((balance * 0.01) / distance, 3)
            tp = entry_price + round((df['ATR'].iloc[-2] * 7), 1)
            callbackRate = 0.1

            position = exchange.create_market_buy_order(
                symbol=symbol, amount=position_size)

            tp_order = exchange.create_order(symbol=symbol, type="TRAILING_STOP_MARKET", side="sell", amount=position_size, price=tp, params={
                "reduceOnly": True,
                "type": "TRAILING_STOP_MARKET",
                "activationPrice": tp,
                "callbackRate": callbackRate,
            })

            sl_order = exchange.create_limit_sell_order(symbol=symbol, amount=position_size, price=sl, params={
                "stopLossPrice": sl,
                "reduceOnly": True
            })

        elif short_signal:
            entry_price = df['open'].iloc[-1]
            sl = round((df['ATR'].iloc[-2] * 4), 1) + entry_price
            distance = sl - entry_price
            balance = exchange.fetch_balance()['USDT']['free']
            position_size = round((balance * 0.01) / distance, 3)
            tp = entry_price - round((df['ATR'].iloc[-2] * 7), 1)

            position = exchange.create_market_sell_order(symbol=symbol, amount=position_size)

            tp_order = exchange.create_order(symbol=symbol, type="TRAILING_STOP_MARKET", side="buy", amount=position_size, price=tp, params={
                "reduceOnly": True,
                "type": "TRAILING_STOP_MARKET",
                "activationPrice": tp,
                "callbackRate": callbackRate,
            })

            sl_order = exchange.create_limit_buy_order(symbol=symbol, amount=position_size, price=sl, params={
                "stopLossPrice": sl,
                "reduceOnly": True
            })

    except ccxt.RequestTimeout as e:
        print(type(e).__name__, str(e))
        time.sleep(60)
    except ccxt.DDoSProtection as e:
        # recoverable error, you might want to sleep a bit here and retry later
        print(type(e).__name__, str(e))
        time.sleep(300)
    except ccxt.ExchangeNotAvailable as e:
        # recoverable error, do nothing and retry later
        print(type(e).__name__, str(e))
        time.sleep(60)
    except ccxt.NetworkError as e:
        # do nothing and retry later...
        print(type(e).__name__, str(e))
        time.sleep(60)
    except Exception as e:
        # panic and halt the execution in case of any other error
        print(type(e).__name__, str(e))
        sys.exit()
