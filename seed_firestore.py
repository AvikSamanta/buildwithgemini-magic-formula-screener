import os
from google.cloud import firestore

# Hardcode the project ID as a string to avoid project number issues in Agent Platform
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-02-8acb2ff2c23a"

def seed_database():
    print(f"Connecting to Firestore for project: {FIRESTORE_PROJECT_ID}...")
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)

    stocks_data = [
        {
            "ticker": "TCS",
            "company_name": "Tata Consultancy Services Ltd",
            "sector": "IT Services",
            "market_cap_cr": 1450000.0,
            "total_debt_cr": 8000.0,
            "cash_cr": 12000.0,
            "net_working_capital_cr": 45000.0,
            "net_fixed_assets_cr": 18000.0,
            "ebit_cr": 62000.0,
        },
        {
            "ticker": "INFY",
            "company_name": "Infosys Ltd",
            "sector": "IT Services",
            "market_cap_cr": 780000.0,
            "total_debt_cr": 4000.0,
            "cash_cr": 15000.0,
            "net_working_capital_cr": 28000.0,
            "net_fixed_assets_cr": 16000.0,
            "ebit_cr": 34000.0,
        },
        {
            "ticker": "ITC",
            "company_name": "ITC Ltd",
            "sector": "Consumer Goods",
            "market_cap_cr": 610000.0,
            "total_debt_cr": 300.0,
            "cash_cr": 10000.0,
            "net_working_capital_cr": 18000.0,
            "net_fixed_assets_cr": 22000.0,
            "ebit_cr": 27000.0,
        },
        {
            "ticker": "RELIANCE",
            "company_name": "Reliance Industries Ltd",
            "sector": "Energy & Conglomerate",
            "market_cap_cr": 2010000.0,
            "total_debt_cr": 310000.0,
            "cash_cr": 180000.0,
            "net_working_capital_cr": 85000.0,
            "net_fixed_assets_cr": 720000.0,
            "ebit_cr": 110000.0,
        },
        {
            "ticker": "HDFCBANK",
            "company_name": "HDFC Bank Ltd",
            "sector": "Banking",
            "market_cap_cr": 1280000.0,
            "total_debt_cr": 0.0,
            "cash_cr": 150000.0,
            "net_working_capital_cr": 120000.0,
            "net_fixed_assets_cr": 15000.0,
            "ebit_cr": 85000.0,
        },
        {
            "ticker": "BHARTIARTL",
            "company_name": "Bharti Airtel Ltd",
            "sector": "Telecommunications",
            "market_cap_cr": 920000.0,
            "total_debt_cr": 210000.0,
            "cash_cr": 25000.0,
            "net_working_capital_cr": 15000.0,
            "net_fixed_assets_cr": 180000.0,
            "ebit_cr": 48000.0,
        },
        {
            "ticker": "COALINDIA",
            "company_name": "Coal India Ltd",
            "sector": "Mining & Energy",
            "market_cap_cr": 300000.0,
            "total_debt_cr": 5000.0,
            "cash_cr": 55000.0,
            "net_working_capital_cr": 40000.0,
            "net_fixed_assets_cr": 45000.0,
            "ebit_cr": 42000.0,
        },
        {
            "ticker": "BAJAJ-AUTO",
            "company_name": "Bajaj Auto Ltd",
            "sector": "Automobile",
            "market_cap_cr": 270000.0,
            "total_debt_cr": 100.0,
            "cash_cr": 22000.0,
            "net_working_capital_cr": 12000.0,
            "net_fixed_assets_cr": 5000.0,
            "ebit_cr": 9500.0,
        },
    ]

    collection_ref = db.collection("stocks")
    for stock in stocks_data:
        # Calculate derived Magic Formula metrics
        ev = stock["market_cap_cr"] + stock["total_debt_cr"] - stock["cash_cr"]
        earnings_yield = stock["ebit_cr"] / ev if ev > 0 else 0.0
        capital_employed = stock["net_working_capital_cr"] + stock["net_fixed_assets_cr"]
        roc = stock["ebit_cr"] / capital_employed if capital_employed > 0 else 0.0

        doc_data = {
            **stock,
            "enterprise_value_cr": round(ev, 2),
            "earnings_yield": round(earnings_yield, 4),
            "roc": round(roc, 4),
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        doc_ref = collection_ref.document(stock["ticker"])
        doc_ref.set(doc_data)
        print(f"Seeded stock: {stock['ticker']} ({stock['company_name']}) - EV: {ev:.2f} Cr, EY: {earnings_yield:.2%}, ROC: {roc:.2%}")

    print("\n✅ Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
