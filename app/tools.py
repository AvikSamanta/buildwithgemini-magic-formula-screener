import json
from google.cloud import firestore
from google.adk.tools import ToolContext

# Hardcode the project ID as a string as required by Agent Platform
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-02-8acb2ff2c23a"



def _get_firestore_client():
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def get_top_magic_formula_stocks(limit: int = 10) -> str:
    """Fetches stock data from Firestore and ranks Nifty 100 companies using Joel Greenblatt's Magic Formula.

    Magic Formula ranks companies based on:
    1. Earnings Yield = EBIT / Enterprise Value (Highest to Lowest)
    2. Return on Capital (ROC) = EBIT / (Net Working Capital + Net Fixed Assets) (Highest to Lowest)
    Combined Rank = Earnings Yield Rank + ROC Rank (Lowest is best).

    Args:
        limit: Number of top ranked stocks to return (default 10).

    Returns:
        A JSON string containing the top Magic Formula ranked stocks.
    """
    db = _get_firestore_client()
    docs = db.collection("stocks").stream()

    stocks = []
    for doc in docs:
        data = doc.to_dict()
        stocks.append(data)

    if not stocks:
        return "No stock data found in Firestore."

    # Rank by Earnings Yield (descending)
    stocks_ey_sorted = sorted(stocks, key=lambda x: x.get("earnings_yield", 0), reverse=True)
    for rank, stock in enumerate(stocks_ey_sorted, 1):
        stock["ey_rank"] = rank

    # Rank by Return on Capital (descending)
    stocks_roc_sorted = sorted(stocks, key=lambda x: x.get("roc", 0), reverse=True)
    for rank, stock in enumerate(stocks_roc_sorted, 1):
        stock["roc_rank"] = rank

    # Calculate combined Magic Rank
    for stock in stocks:
        stock["combined_rank"] = stock["ey_rank"] + stock["roc_rank"]

    # Sort by combined rank (ascending: rank 1 + rank 1 = rank 2 is best)
    final_sorted = sorted(stocks, key=lambda x: (x["combined_rank"], -x["roc"]))[:limit]

    results = []
    for final_rank, s in enumerate(final_sorted, 1):
        results.append({
            "magic_rank": final_rank,
            "ticker": s.get("ticker"),
            "company_name": s.get("company_name"),
            "sector": s.get("sector"),
            "earnings_yield_pct": f"{s.get('earnings_yield', 0) * 100:.2f}%",
            "roc_pct": f"{s.get('roc', 0) * 100:.2f}%",
            "enterprise_value_cr": f"₹{s.get('enterprise_value_cr', 0):,.2f} Cr",
            "combined_score": s.get("combined_rank"),
        })

    return json.dumps(results, indent=2)


def get_stock_financials(ticker: str) -> str:
    """Fetches financial data and Magic Formula metrics for a specific company by ticker symbol.

    Args:
        ticker: The stock ticker symbol (e.g. 'TCS', 'INFY', 'RELIANCE', 'ITC').

    Returns:
        JSON string containing the company's financials or an error message.
    """
    db = _get_firestore_client()
    doc_ref = db.collection("stocks").document(ticker.upper())
    doc = doc_ref.get()

    if not doc.exists:
        return f"Stock ticker '{ticker.upper()}' not found in Firestore database."

    data = doc.to_dict()
    data.pop("updated_at", None)
    return json.dumps(data, indent=2)


def save_stock_financials(
    ticker: str,
    company_name: str,
    sector: str,
    market_cap_cr: float,
    total_debt_cr: float,
    cash_cr: float,
    ebit_cr: float,
    net_working_capital_cr: float,
    net_fixed_assets_cr: float,
) -> str:
    """Saves or updates a company's financial metrics in Firestore and calculates Magic Formula metrics.

    Args:
        ticker: Stock ticker symbol (e.g., 'TCS').
        company_name: Full company name.
        sector: Industry sector.
        market_cap_cr: Market Capitalization in INR Crores.
        total_debt_cr: Total Debt in INR Crores.
        cash_cr: Cash & Cash Equivalents in INR Crores.
        ebit_cr: Earnings Before Interest and Taxes in INR Crores.
        net_working_capital_cr: Net Working Capital in INR Crores.
        net_fixed_assets_cr: Net Fixed Assets in INR Crores.

    Returns:
        Confirmation message with calculated EV, Earnings Yield, and ROC.
    """
    db = _get_firestore_client()
    ev = market_cap_cr + total_debt_cr - cash_cr
    earnings_yield = ebit_cr / ev if ev > 0 else 0.0
    capital_employed = net_working_capital_cr + net_fixed_assets_cr
    roc = ebit_cr / capital_employed if capital_employed > 0 else 0.0

    doc_data = {
        "ticker": ticker.upper(),
        "company_name": company_name,
        "sector": sector,
        "market_cap_cr": float(market_cap_cr),
        "total_debt_cr": float(total_debt_cr),
        "cash_cr": float(cash_cr),
        "ebit_cr": float(ebit_cr),
        "net_working_capital_cr": float(net_working_capital_cr),
 net_fixed_assets_cr: float(net_fixed_assets_cr),
        "enterprise_value_cr": round(ev, 2),
        "earnings_yield": round(earnings_yield, 4),
        "roc": round(roc, 4),
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    db.collection("stocks").document(ticker.upper()).set(doc_data)
    return (
        f"Successfully updated {ticker.upper()} ({company_name}) in Firestore!\n"
        f"Enterprise Value: ₹{ev:,.2f} Cr | Earnings Yield: {earnings_yield:.2%} | ROC: {roc:.2%}"
    )


def export_screener_to_csv(limit: int = 10) -> str:
    """Exports the top Magic Formula ranked stocks to a CSV file and uploads it to Google Cloud Storage.

    Args:
        limit: The number of top ranked stocks to export to CSV (default 10).

    Returns:
        A message containing the public Google Cloud Storage download link for the CSV file.
    """
    import csv
    import tempfile
    from google.cloud import storage

    bucket_name = "magic-formula-screener-qwiklabs-gcp-02-8acb2ff2c23a"
    db = _get_firestore_client()
    docs = db.collection("stocks").stream()

    stocks = []
    for doc in docs:
        stocks.append(doc.to_dict())

    if not stocks:
        return "No stock records found in Firestore to export."

    # Compute Magic Formula Ranks
    stocks_ey = sorted(stocks, key=lambda x: x.get("earnings_yield", 0), reverse=True)
    for rank, s in enumerate(stocks_ey, 1):
        s["ey_rank"] = rank

    stocks_roc = sorted(stocks, key=lambda x: x.get("roc", 0), reverse=True)
    for rank, s in enumerate(stocks_roc, 1):
        s["roc_rank"] = rank

    for s in stocks:
        s["combined_rank"] = s["ey_rank"] + s["roc_rank"]

    ranked_stocks = sorted(stocks, key=lambda x: (x["combined_rank"], -x.get("roc", 0)))[:limit]

    fieldnames = [
        "Magic Rank",
        "Ticker",
        "Company Name",
        "Sector",
        "Earnings Yield (%)",
        "ROC (%)",
        "Combined Score",
        "Enterprise Value (Cr)",
        "Market Cap (Cr)",
        "Total Debt (Cr)",
        "Cash (Cr)",
        "EBIT (Cr)",
        "Net Working Capital (Cr)",
        "Net Fixed Assets (Cr)",
    ]

    filename = f"magic_formula_top_{limit}.csv"
    filepath = f"/tmp/{filename}"

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, s in enumerate(ranked_stocks, 1):
            writer.writerow({
                "Magic Rank": idx,
                "Ticker": s.get("ticker", ""),
                "Company Name": s.get("company_name", ""),
                "Sector": s.get("sector", ""),
                "Earnings Yield (%)": f"{s.get('earnings_yield', 0) * 100:.2f}%",
                "ROC (%)": f"{s.get('roc', 0) * 100:.2f}%",
                "Combined Score": s.get("combined_rank", ""),
                "Enterprise Value (Cr)": s.get("enterprise_value_cr", 0),
                "Market Cap (Cr)": s.get("market_cap_cr", 0),
                "Total Debt (Cr)": s.get("total_debt_cr", 0),
                "Cash (Cr)": s.get("cash_cr", 0),
                "EBIT (Cr)": s.get("ebit_cr", 0),
                "Net Working Capital (Cr)": s.get("net_working_capital_cr", 0),
                "Net Fixed Assets (Cr)": s.get("net_fixed_assets_cr", 0),
            })

    # Upload to Cloud Storage bucket
    storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob_path = f"exports/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(filepath, content_type="text/csv")

    public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_path}"
    return (
        f"Successfully exported top {len(ranked_stocks)} Magic Formula stocks to CSV!\n\n"
        f"📥 Public Download URL: {public_url}"
    )


def get_currency_exchange_rate(base_currency: str = "USD", target_currency: str = "INR") -> str:
    """Fetches real-time currency exchange rates from a free public finance API (ExchangeRate API / open.er-api.com).

    Useful for converting Indian stock metrics (in INR Crores) to USD, EUR, or other global currencies for international investors.
    If an API key is configured in the environment (e.g. RAPIDAPI_KEY or EXCHANGE_RATE_API_KEY), it reads from os.environ.

    Args:
        base_currency: The source currency code (default 'USD').
        target_currency: The destination currency code (default 'INR').

    Returns:
        JSON string containing the real-time conversion rate and timestamp.
    """
    import os
    import urllib.request

    api_key = os.environ.get("EXCHANGE_RATE_API_KEY") or os.environ.get("RAPIDAPI_KEY")
    base = base_currency.upper()
    target = target_currency.upper()

    if api_key:
        # If API key is provided in environment, use authenticated endpoint
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
    else:
        # Free open-access public API endpoint (listed on github.com/public-apis/public-apis)
        url = f"https://open.er-api.com/v6/latest/{base}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MagicFormulaAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("result") == "success":
            rates = data.get("rates", {})
            rate = rates.get(target)
            if rate:
                return json.dumps(
                    {
                        "base_currency": base,
                        "target_currency": target,
                        "exchange_rate": rate,
                        "last_updated": data.get("time_last_update_utc"),
                        "note": f"1 {base} = {rate:.4f} {target}",
                    },
                    indent=2,
                )
            return f"Currency symbol '{target}' not found in exchange rate data."
        return f"Failed to fetch exchange rates: {data.get('error-type', 'Unknown error')}"

    except Exception as e:
        return f"Error fetching exchange rate data: {str(e)}"


def generate_stock_chart_image(
    prompt: str,
    filename: str = "magic_formula_chart.png",
    tool_context: ToolContext = None,
) -> str:
    """Generates an image or chart visualization for a stock or investment topic using the gemini-3.1-flash-lite-image model in the global region.

    Saves the image with tool_context.save_artifact for the Playground Artifacts panel and uploads the in-memory bytes to public Cloud Storage.

    Args:
        prompt: Description of the stock chart, infographic, or financial visual to generate.
        filename: File name for the image (default 'magic_formula_chart.png').
        tool_context: ADK ToolContext injected by the framework.

    Returns:
        Public Google Cloud Storage HTTPS URL of the generated image.
    """
    from google import genai
    from google.genai import types
    from google.cloud import storage

    bucket_name = "magic-formula-screener-qwiklabs-gcp-02-8acb2ff2c23a"
    project_id = "qwiklabs-gcp-02-8acb2ff2c23a"

    if not filename.endswith(".png") and not filename.endswith(".jpg"):
        filename = f"{filename}.png"

    # Generate image using gemini-3.1-flash-lite-image in global location
    client = genai.Client(vertexai=True, project=project_id, location="global")
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    image_bytes = None
    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                break

    if not image_bytes:
        return "Failed to generate image: No image data returned from gemini-3.1-flash-lite-image."

    # 1. Save with tool_context.save_artifact so it shows up in Playground's Artifacts panel
    if tool_context is not None:
        try:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Notice: Could not save artifact to tool_context: {e}")

    # 2. Upload image bytes directly to public Cloud Storage bucket (no local file path returned)
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob_path = f"charts/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(image_bytes, content_type="image/png")

    public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_path}"
    return (
        f"Successfully generated stock chart image!\n\n"
        f"🖼️ Public Image URL: {public_url}"
    )



