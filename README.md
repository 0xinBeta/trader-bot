# Advanced Crypto Trading Bot

Welcome to the repository of an Advanced Crypto Trading Bot designed to interface with Binance Futures. This Python-based algorithmic trading bot is tailored for high-frequency trading with robust strategies, including the use of technical indicators for automated trade execution.

## Features

- Multi-symbol support: `BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `XRPUSDT`, `LINKUSDT`.
- Dynamic leverage fetching and setting for each symbol.
- Automated order placement with stop loss and take profit parameters.
- Real-time calculation of order details based on ATR and account balance.
- Built-in error handling for resilience and stability.
- Efficient asynchronous data handling with `asyncio`.

## Technical Indicators

- EMA9, EMA21, EMA50
- SMMA200
- ADX
- ATR
- RSI

## Strategy

The bot's strategy involves entering long or short positions based on EMA crossovers, relative positions of EMAs to the SMMA200, RSI values, and the ADX trend strength. A position is taken with a calculated size based on the current balance and a predefined balance percentage risk. Stop loss and take profit orders are set with a trailing stop market order to secure profits.

## Setup

### Prerequisites

Ensure you have Python 3.8+ installed on your system.

### Installation

1. Clone the repository to your local machine.
2. Navigate to the cloned directory.
3. Install the required dependencies:
   ```shell
   pip install -r requirements.txt
   ```

## Configuration

1. Rename .env.example to .env.
2. Fill in your Binance API and Secret keys in .env.

## Error Handling

The bot is designed to handle various network and API related errors gracefully by logging the error details and applying a cool-down period where appropriate.

## Logging

Logging is set to INFO level by default, providing a concise output of the bot's operations. Adjust the logging level in main.py as needed for debugging purposes.

## Disclaimer

This bot is for educational purposes only. Trading cryptocurrencies is risky. Please use this bot on a test net with a demo account before considering going live.

## Contribution

Contributions are welcome! If you have a suggestion or improvement, please fork the repository and submit a pull request.

## License

Distributed under the MIT License. See LICENSE for more information.

## Contact

https://www.linkedin.com/in/aref-zarandi-9327bb128/

## Project Link: https://github.com/0xinBeta/trader-bot
