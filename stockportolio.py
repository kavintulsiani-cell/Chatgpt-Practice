import csv

import pandas as pd
import os
import datetime as dt
from yahoo_live_price import get_live_price

def normalize_ticker(ticker):
    sym = ticker.strip().upper()

    if sym.endswith(".NS") or sym.endswith(".BO"):
        return sym

    return sym + ".NS"



FILE_PATH = "portfolio.csv"
def initialize_files():
    # Portfolio: open positions only
    if not os.path.exists("portfolio.csv"):
        portfolio_cols = [
            "ticker",
            "buy_price",
            "qty",
            "buy_amount",
            "current_price",
            "pnl_live",
            "pnl_live_percent",
            "date_buy",
            "status"
        ]
        pd.DataFrame(columns=portfolio_cols).to_csv("portfolio.csv", index=False)
        print("Created portfolio.csv")

    # Closed trades: every sell (full or partial)
    if not os.path.exists("closed_trades.csv"):
        closed_cols = [
            "ticker",
            "buy_price",
            "qty_sold",
            "buy_amount_sold",
            "sell_price",
            "sell_amount",
            "pnl_final",
            "pnl_final_percent",
            "date_buy",
            "date_sell",
            "holding_days"
        ]
        pd.DataFrame(columns=closed_cols).to_csv("closed_trades.csv", index=False)
        print("Created closed_trades.csv")

def add_trade():
    df = pd.read_csv("portfolio.csv")

    raw_ticker = input("Enter stock symbol (e.g. SBIN): ")
    ticker = normalize_ticker(raw_ticker)

    buy_price = float(input("Enter BUY price: "))
    qty = int(input("Enter quantity: "))

    buy_amount = round(buy_price * qty, 2)
    date_buy = dt.date.today().isoformat() # YYYY-MM-DD

    new_row = {
        "ticker": ticker,
        "buy_price": buy_price,
        "qty": qty,
        "buy_amount": buy_amount,
        "current_price": None,
        "pnl_live": None,
        "pnl_live_percent": None,
        "date_buy": date_buy,
        "status": "OPEN",
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv("portfolio.csv", index=False)

    print(f"\n✅ Added trade: {ticker}, {qty} @ {buy_price} (₹{buy_amount})\n")




def update_portfolio_live():
    df = pd.read_csv("portfolio.csv")

    for index, row in df.iterrows():

        # Skip closed trades
        if row["status"] == "CLOSED":
            continue

        ticker = row["ticker"]
        buy_price = float(row["buy_price"])
        qty = int(row["qty"])
        sell_price = row["sell_price"] if pd.notna(row["sell_price"]) else None

        # --- Fetch live price ---
        live_price = get_live_price(ticker)
        df.loc[index, "current_price"] = live_price

        # --- LIVE P&L calculations ---
        if live_price is not None:
            pnl_live = (live_price - buy_price) * qty
            pnl_live_percent = (pnl_live / (buy_price * qty)) * 100
        else:
            pnl_live = None
            pnl_live_percent = None

        df.loc[index, "pnl_live"] = pnl_live
        df.loc[index, "pnl_live_percent"] = pnl_live_percent

        # --- FINAL P&L (only if sell_price exists) ---
        if sell_price is not None:
            sell_price = float(sell_price)
            pnl_final = (sell_price - buy_price) * qty
            pnl_final_percent = (pnl_final / (buy_price * qty)) * 100
        else:
            pnl_final = None
            pnl_final_percent = None

        df.loc[index, "pnl_final"] = pnl_final
        df.loc[index, "pnl_final_percent"] = pnl_final_percent

    # Save updates back to CSV
    df.to_csv("portfolio.csv", index=False)
    print("\nPortfolio updated with live prices and P&L.\n")


def sell_stock():
    # Load open portfolio
    df = pd.read_csv("portfolio.csv")

    if df.empty:
        print("⚠️ Portfolio is empty. Nothing to sell.")
        return

    raw_ticker = input("Enter the stock symbol to sell: ").upper().strip()
    ticker = normalize_ticker(raw_ticker)

    # Filter open rows for this ticker
    mask = (df["ticker"] == ticker) & (df["status"] == "OPEN")
    if not mask.any():
        print("❌ No OPEN position found for this ticker.")
        return

    # For now we assume 1 open row per ticker
    idx = df.index[mask][0]
    row = df.loc[idx]

    total_qty = int(row["qty"])
    buy_price = float(row["buy_price"])
    date_buy_str = row["date_buy"]

    print(f"\nCurrent OPEN position in {ticker}: {total_qty} shares @ ₹{buy_price}")
    qty_to_sell = int(input("How many shares do you want to SELL? "))

    if qty_to_sell <= 0:
        print("❌ Quantity to sell must be > 0.")
        return
    if qty_to_sell > total_qty:
        print(f"❌ You only have {total_qty} shares. Cannot sell {qty_to_sell}.")
        return

    sell_price = float(input("Enter the SELL price: "))

    # --- Calculate sold leg P&L ---
    buy_amount_sold = round(buy_price * qty_to_sell, 2)
    sell_amount = round(sell_price * qty_to_sell, 2)
    pnl_final = round(sell_amount - buy_amount_sold, 2)
    pnl_final_percent = round((pnl_final / buy_amount_sold) * 100, 2) if buy_amount_sold > 0 else None

    # Dates / holding period
    date_sell = dt.date.today()
    try:
        date_buy = dt.date.fromisoformat(date_buy_str)
        holding_days = (date_sell - date_buy).days
    except Exception:
        holding_days = None

    # --- Append to closed_trades.csv ---
    closed_df = pd.read_csv("closed_trades.csv")

    closed_row = {
        "ticker": ticker,
        "buy_price": buy_price,
        "qty_sold": qty_to_sell,
        "buy_amount_sold": buy_amount_sold,
        "sell_price": sell_price,
        "sell_amount": sell_amount,
        "pnl_final": pnl_final,
        "pnl_final_percent": pnl_final_percent,
        "date_buy": date_buy_str,
        "date_sell": date_sell.isoformat(),
        "holding_days": holding_days
    }

    closed_df = pd.concat([closed_df, pd.DataFrame([closed_row])], ignore_index=True)
    closed_df.to_csv("closed_trades.csv", index=False)

    # --- Update or remove from portfolio.csv ---
    qty_left = total_qty - qty_to_sell

    if qty_left == 0:
        # Full exit: remove row
        df = df.drop(index=idx)
        print(f"\n✅ FULL EXIT: Sold all {total_qty} shares of {ticker}.")
    else:
        # Partial exit: reduce qty and buy_amount
        new_buy_amount = round(buy_price * qty_left, 2)
        df.loc[idx, "qty"] = qty_left
        df.loc[idx, "buy_amount"] = new_buy_amount
        # keep current_price and live P&L to be refreshed next time
        print(f"\n✅ PARTIAL EXIT: Sold {qty_to_sell}, {qty_left} remaining in {ticker}.")

    df.to_csv("portfolio.csv", index=False)

    print(f"\n📌 Closed leg summary:")
    print(f" Sold {qty_to_sell} @ ₹{sell_price}")
    print(f" P&L: ₹{pnl_final} ({pnl_final_percent}%)")
    if holding_days is not None:
        print(f" Holding period: {holding_days} days\n")

def show_portfolio_summary(refresh_prices=True):
    """
    Prints a summary of:
    - Open positions (cost, value, P&L)
    - Closed trades (realised P&L)
    - Overall totals
    """

    # ---------- Load data ----------
    if not os.path.exists("portfolio.csv"):
        print("⚠️ portfolio.csv not found.")
        return
    if not os.path.exists("closed_trades.csv"):
        print("⚠️ closed_trades.csv not found.")
        return

    df_open = pd.read_csv("portfolio.csv")
    df_closed = pd.read_csv("closed_trades.csv")

    # ---------- Handle open positions ----------
    if df_open.empty:
        total_cost_open = 0.0
        current_value_open = 0.0
        pnl_open = 0.0
        pnl_open_pct = 0.0
    else:
        # Make sure numeric columns are numeric
        for col in ["buy_amount", "qty", "current_price"]:
            if col in df_open.columns:
                df_open[col] = pd.to_numeric(df_open[col], errors="coerce")

        # Optionally refresh live prices
        if refresh_prices:
            for i, row in df_open.iterrows():
                ticker = row["ticker"]
                qty = row["qty"]
                if pd.isna(qty) or qty == 0:
                    continue
                live = get_live_price(ticker)
                if live is not None:
                    df_open.at[i, "current_price"] = live

        # Compute current value per row
        df_open["position_value"] = df_open["qty"] * df_open["current_price"]

        total_cost_open = df_open["buy_amount"].fillna(0).sum()
        current_value_open = df_open["position_value"].fillna(0).sum()
        pnl_open = current_value_open - total_cost_open
        pnl_open_pct = (pnl_open / total_cost_open * 100) if total_cost_open > 0 else 0.0

        # Save updated live prices back if we refreshed
        if refresh_prices:
            df_open.to_csv("portfolio.csv", index=False)

    # ---------- Handle closed trades ----------
    if df_closed.empty:
        total_cost_closed = 0.0
        total_realised_pnl = 0.0
        realised_pct = 0.0
    else:
        for col in ["buy_amount_sold", "pnl_final"]:
            if col in df_closed.columns:
                df_closed[col] = pd.to_numeric(df_closed[col], errors="coerce")

        total_cost_closed = df_closed["buy_amount_sold"].fillna(0).sum()
        total_realised_pnl = df_closed["pnl_final"].fillna(0).sum()
        realised_pct = (total_realised_pnl / total_cost_closed * 100) if total_cost_closed > 0 else 0.0

    # ---------- Overall picture ----------
    total_invested = total_cost_open + total_cost_closed
    total_pnl = pnl_open + total_realised_pnl
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

    # ---------- Print nicely ----------
    print("\n================ PORTFOLIO SUMMARY ================\n")

    print("📂 OPEN POSITIONS")
    print(f" Invested (Open) : ₹{total_cost_open:,.2f}")
    print(f" Current Value (Open) : ₹{current_value_open:,.2f}")
    print(f" Open P&L : ₹{pnl_open:,.2f} ({pnl_open_pct:.2f}%)\n")

    print("💰 CLOSED TRADES")
    print(f" Cost (Closed) : ₹{total_cost_closed:,.2f}")
    print(f" Realised P&L : ₹{total_realised_pnl:,.2f} ({realised_pct:.2f}%)\n")

    print("📊 OVERALL (OPEN + CLOSED)")
    print(f" Total Invested : ₹{total_invested:,.2f}")
    print(f" Total P&L : ₹{total_pnl:,.2f} ({total_pnl_pct:.2f}%)")
    print("\n===================================================\n")




if __name__ == "__main__":
    #initialize_files()
    #add_trade()
    show_portfolio_summary(refresh_prices=True)
    #sell_stock()
    #norm = normalize_ticker()
    #get_live_price(norm)
    #add_trade()#
    #update_portfolio_live()
    #sell_stock()



