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

        df = create_df(exchange=exchange, symbol=symbol,
                       time_frame=time_frame, limit=limit)
        
        print(df)
        time.sleep(1)

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
