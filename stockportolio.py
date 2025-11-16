import csv

import pandas as pd
import os

def normalize_ticker(ticker):
    sym = ticker.strip().upper()

    if sym.endswith(".NS") or sym.endswith(".BO"):
        return sym

    return sym + ".NS"



FILE_PATH = "portfolio.csv"

def initialize_portfolio_csv():
    if not os.path.exists(FILE_PATH):

        headers = [
            "ticker", "buy_price", "qty", "buy_amount",
            "sell_price", "sell_amount",
            "current_price", "pnl_live", "pnl_live_percent",
            "pnl_final", "pnl_final_percent",
            "status"
        ]

        with open (FILE_PATH, 'w', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    else:
        print("portfolio.csv already exists.")



def add_trade() :
    # 1. Ask user for ticker, buy_price, qty

    ticker = input("Enter stock symbol: ")
    buy_price = float(input("Enter buy price: "))
    qty = int(input("Enter quantity: "))
    user_ticker = normalize_ticker (ticker)
    buy_amount = buy_price * qty
    new_row = {
        "ticker": user_ticker,
        "buy_price": buy_price,
        "qty": qty,
        "buy_amount": buy_amount,
        "sell_price": None,
        "sell_amount": None,
        "current_price": None,
        "pnl_live": None,
        "pnl_live_percent" : None,
        "pnl_final" : None,
        "pnl_final_percent": None,
        "status" : "OPEN"
    }
    # Load existing CSV
    df = pd.read_csv("portfolio.csv")

    # Append the new row
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Save back to CSV
    df.to_csv("portfolio.csv", index=False)

    print("\n✅ Trade added successfully!")

if __name__ == "__main__":
    initialize_portfolio_csv()
    add_trade()




