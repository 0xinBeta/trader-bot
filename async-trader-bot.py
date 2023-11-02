import asyncio
import ccxt.async_support as ccxt
from df_maker import create_df_async  # this will also need to be converted to async
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

async def trade_logic(exchange, symbol):
    time_frame = "15m"
    limit = 500

    # You will need to adapt this call to async as well
    available_tiers = await exchange.fetch_leverage_tiers(symbols=[symbol])
    coin = symbol[:-4]
    max_lev = int(available_tiers[f'{coin}/USDT:USDT'][0]['maxLeverage'])
    await exchange.set_leverage(leverage=max_lev, symbol=symbol)

    while True:
        try:
            df = await create_df_async(exchange=exchange, symbol=symbol,
                                       time_frame=time_frame, limit=limit)

            long_signal = df['long'].iloc[-2]
            short_signal = df['short'].iloc[-2]

            open_position = await exchange.fetch_positions(symbols=[symbol])
            open_pos_condition = int(open_position[0]['contracts'])
            
            if open_pos_condition == 0:
                if long_signal:

                    round_decimal_price = 1 if symbol == "BTCUSDT" else 2
                    round_decimal_pos = 3 if symbol == "BTCUSDT" else 2

                    entry_price = df['Open'].iloc[-1]
                    sl = entry_price - round((df['ATR'].iloc[-2] * 4), round_decimal_price)
                    distance = entry_price - sl
                    balance = await exchange.fetch_balance()['USDT']['free']
                    position_size = round((balance * 0.01) / distance, round_decimal_pos)
                    tp = entry_price + round((df['ATR'].iloc[-2] * 7), round_decimal_price)
                    callbackRate = 0.1

                    position = await exchange.create_market_buy_order(
                        symbol=symbol, amount=position_size)

                    tp_order = await exchange.create_order(symbol=symbol, type="TRAILING_STOP_MARKET", side="sell", amount=position_size, price=tp, params={
                        "reduceOnly": True,
                        "type": "TRAILING_STOP_MARKET",
                        "activationPrice": tp,
                        "callbackRate": callbackRate,
                    })

                    sl_order = await exchange.create_limit_sell_order(symbol=symbol, amount=position_size, price=sl, params={
                        "stopLossPrice": sl,
                        "reduceOnly": True
                    })

                elif short_signal:
                    round_decimal_price = 1 if symbol == "BTCUSDT" else 2
                    round_decimal_pos = 3 if symbol == "BTCUSDT" else 2

                    entry_price = df['Open'].iloc[-1]
                    sl = round((df['ATR'].iloc[-2] * 4), round_decimal_price) + entry_price
                    distance = sl - entry_price
                    balance = await exchange.fetch_balance()['USDT']['free']
                    position_size = round((balance * 0.01) / distance, round_decimal_pos)
                    tp = entry_price - round((df['ATR'].iloc[-2] * 7), round_decimal_price)

                    position = await exchange.create_market_sell_order(
                        symbol=symbol, amount=position_size)

                    tp_order = await exchange.create_order(symbol=symbol, type="TRAILING_STOP_MARKET", side="buy", amount=position_size, price=tp, params={
                        "reduceOnly": True,
                        "type": "TRAILING_STOP_MARKET",
                        "activationPrice": tp,
                        "callbackRate": callbackRate,
                    })

                    sl_order = await exchange.create_limit_buy_order(symbol=symbol, amount=position_size, price=sl, params={
                        "stopLossPrice": sl,
                        "reduceOnly": True
                    })

            await asyncio.sleep(1)  # Non-blocking sleep

        except ccxt.BaseError as e:
            print(type(e).__name__, str(e))
            await asyncio.sleep(60)  # Non-blocking sleep
        except ccxt.DDoSProtection as e:
            # recoverable error, you might want to sleep a bit here and retry later
            print(type(e).__name__, str(e))
            await asyncio.sleep(300)
        except ccxt.ExchangeNotAvailable as e:
            # recoverable error, do nothing and retry later
            print(type(e).__name__, str(e))
            await asyncio.sleep(60)
        except ccxt.NetworkError as e:
            # do nothing and retry later...
            print(type(e).__name__, str(e))
            await asyncio.sleep(60)
        except Exception as e:
            print(type(e).__name__, str(e))
            return  # Exit the loop and therefore end the task

async def main():
    exchange = ccxt.binanceusdm({
        "enableRateLimit": True,
        "apiKey": API_KEY,
        "secret": SECRET_KEY,
    })

    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # List of symbols to trade
    tasks = [trade_logic(exchange, symbol) for symbol in symbols]
    await asyncio.gather(*tasks)

    await exchange.close()  # Remember to close the connection

if __name__ == "__main__":
    asyncio.run(main())
