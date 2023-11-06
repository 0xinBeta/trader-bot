import asyncio
import ccxt.async_support as ccxt
from df_maker import create_df_async
from dotenv import load_dotenv
import os
import logging
import sys

# Load environment variables
load_dotenv()
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
TIME_FRAME = "15m"
LIMIT = 500
BALANCE_PERCENTAGE = 0.01
LEVERAGE_MULTIPLIER_LONG = 4
LEVERAGE_MULTIPLIER_SHORT = 7
CALLBACK_RATE = 0.1


async def set_max_leverage(exchange, symbol, coin):
    """
    Fetch the maximum leverage and set it for the given symbol.
    """
    available_tiers = await exchange.fetch_leverage_tiers(symbols=[symbol])
    max_lev = int(available_tiers[f'{coin}/USDT:USDT'][0]['maxLeverage'])
    await exchange.set_leverage(leverage=max_lev, symbol=symbol)


def calculate_order_details(entry_price, atr, symbol, balance, direction):
    """
    Calculate the position size, stop loss, and take profit based on entry price, ATR, and balance.
    """
    round_decimal_price = 1 if symbol == "BTCUSDT" else 2
    round_decimal_pos = 3 if symbol == "BTCUSDT" else 2

    sl_multiplier = LEVERAGE_MULTIPLIER_LONG if direction == 'long' else -LEVERAGE_MULTIPLIER_SHORT
    tp_multiplier = LEVERAGE_MULTIPLIER_SHORT if direction == 'long' else -LEVERAGE_MULTIPLIER_LONG

    sl = entry_price - round((atr * sl_multiplier), round_decimal_price)
    tp = entry_price + round((atr * tp_multiplier), round_decimal_price)
    distance = abs(entry_price - sl)
    position_size = round((balance * BALANCE_PERCENTAGE) / distance, round_decimal_pos)

    return position_size, sl, tp


async def place_orders(exchange, symbol, position_size, sl, tp, direction):
    """
    Place the market and limit orders based on the given direction.
    """
    side = 'buy' if direction == 'long' else 'sell'
    opposite_side = 'sell' if direction == 'long' else 'buy'

    # Create market order
    await exchange.create_market_order(symbol=symbol, type="market", side=side, amount=position_size)

    # Create take profit order
    await exchange.create_order(symbol=symbol, type="TRAILING_STOP_MARKET", side=opposite_side, amount=position_size,
                                price=tp, params={"reduceOnly": True, "activationPrice": tp, "callbackRate": CALLBACK_RATE})

    # Create stop loss order
    order_type = 'limit' + opposite_side
    await getattr(exchange, f'create_{order_type}_order')(symbol=symbol, amount=position_size, price=sl,
                                                          params={"stopPrice": sl, "reduceOnly": True})


async def trade_logic(exchange, symbol):
    """
    The core trading logic for a symbol.
    """
    await set_max_leverage(exchange, symbol, coin=symbol[:-4])

    while True:
        try:
            df = await create_df_async(exchange=exchange, symbol=symbol, time_frame=TIME_FRAME, limit=LIMIT)

            long_signal = df['long'].iloc[-2]
            short_signal = df['short'].iloc[-2]

            open_position = await exchange.fetch_positions(symbols=[symbol])
            open_pos_condition = int(open_position[0]['contracts'])

            if open_pos_condition == 0:
                if long_signal or short_signal:
                    entry_price = df['Open'].iloc[-1]
                    atr = df['ATR'].iloc[-2]
                    balance = await exchange.fetch_balance()['USDT']['free']
                    direction = 'long' if long_signal else 'short'

                    position_size, sl, tp = calculate_order_details(entry_price, atr, symbol, balance, direction)
                    await place_orders(exchange, symbol, position_size, sl, tp, direction)

            await asyncio.sleep(1)

        except ccxt.NetworkError as e:
            logging.error(f'NetworkError: {str(e)}')
            await asyncio.sleep(60)
        except Exception as e:
            logging.error(f'An unexpected error occurred: {str(e)}')
            sys.exit()


async def main():
    """
    Main function to start trading on specified symbols.
    """
    exchange = ccxt.binanceusdm({
        "enableRateLimit": True,
        "apiKey": API_KEY,
        "secret": SECRET_KEY,
    })

    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "LINKUSDT"]
    tasks = [trade_logic(exchange, symbol) for symbol in symbols]
    await asyncio.gather(*tasks)

    await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())