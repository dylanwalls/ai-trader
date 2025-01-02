import os
from typing import Dict, Any, List
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv('.env')

def get_financial_metrics(
    ticker: str,
    report_period: str,
    period: str = 'ttm',
    limit: int = 1
) -> List[Dict[str, Any]]:
    """Fetch financial metrics from the Alpha Vantage API."""
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    url = (
        f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )
    data = response.json()
    if not data:
        raise ValueError("No financial metrics returned")

        # Log fetched data
    print(f"Fetched financial_metrics data for {ticker}: {data}")
    return [data]  # Wrap in a list to match expected format

def search_line_items(
    ticker: str,
    line_items: List[str],
    period: str = 'ttm',
    limit: int = 1
) -> List[Dict[str, Any]]:
    """
    Fetch cash flow statements and extract specific line items.
    
    Args:
        ticker (str): Stock ticker symbol.
        line_items (List[str]): List of financial line items to retrieve.
        period (str): Period to fetch (e.g., 'ttm' or 'annualReports').
        limit (int): Limit the number of records returned.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing the requested line items.
    """
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    url = (
        f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={api_key}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )
    data = response.json()

    # Debugging the response
    # print(f"API Response for CASH_FLOW: {data}")

    # Check if the necessary data exists
    reports = data.get("annualReports")
    if not reports:
        raise ValueError("No annual cash flow reports returned")

    # Extract the requested line items
    extracted_data = []
    for report in reports[:limit]:
        line_item_data = {}
        for item in line_items:
            line_item_data[item] = report.get(item, None)  # Use None if item not present
        extracted_data.append(line_item_data)

    return extracted_data


def get_insider_trades(
    ticker: str,
    end_date: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Fetch insider trades from Finnhub API."""
    api_key = os.environ.get("FINNHUB_API_KEY")
    # print(f'api_key: {api_key}')
    url = (
        f"https://finnhub.io/api/v1/stock/insider-transactions?symbol={ticker}&token={api_key}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )
    data = response.json()
    if "data" not in data:
        raise ValueError("No insider trades returned")
    # Log fetched data
    print(f"Fetched insider trades data from Finnhub for {ticker}: {data}")
    return data["data"][:limit]

def get_market_cap(
    ticker: str,
) -> List[Dict[str, Any]]:
    """Fetch market cap from Alpha Vantage."""
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    url = (
        f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )
    data = response.json()
    if not data:
        raise ValueError("No company facts returned")

    # Log fetched data
    print(f"Fetched marketcap data from Alpha Vantage for {ticker}: {data}")
    return data.get("MarketCapitalization", None)

def get_prices(
    ticker: str,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """Fetch price data from Alpaca API."""
    alpaca_api_key = os.environ.get("APCA_API_KEY_ID")
    alpaca_secret_key = os.environ.get("APCA_API_SECRET_KEY")
    headers = {
        "APCA-API-KEY-ID": alpaca_api_key,
        "APCA-API-SECRET-KEY": alpaca_secret_key,
    }
    url = (
        f"https://data.alpaca.markets/v2/stocks/{ticker}/bars?start={start_date}&end={end_date}&timeframe=1Day"
    )
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )
    data = response.json()
    if "bars" not in data:
        raise ValueError("No price data returned")

    # Log fetched data
    print(f"Fetched price data for {ticker}: {data}")
    return data["bars"]

def prices_to_df(prices: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame(prices)
    
    # Parse the 't' column as ISO 8601 datetime
    df["Date"] = pd.to_datetime(df["t"], errors="coerce")
    
    # Set the parsed datetime as the index
    df.set_index("Date", inplace=True)
    
    # Rename columns to more descriptive names
    df.rename(columns={"o": "open", "c": "close", "h": "high", "l": "low", "v": "volume"}, inplace=True)
    
    # Ensure numeric columns are properly formatted
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Sort the DataFrame by index (datetime)
    df.sort_index(inplace=True)
    return df


def get_price_data(
    ticker: str,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)







# import os
# from typing import Dict, Any, List
# import pandas as pd
# import requests

# import requests

# def get_financial_metrics(
#     ticker: str,
#     report_period: str,
#     period: str = 'ttm',
#     limit: int = 1
# ) -> List[Dict[str, Any]]:
#     """Fetch financial metrics from the API."""
#     headers = {"X-API-KEY": os.environ.get("FINANCIAL_DATASETS_API_KEY")}
#     url = (
#         f"https://api.financialdatasets.ai/financial-metrics/"
#         f"?ticker={ticker}"
#         f"&report_period_lte={report_period}"
#         f"&limit={limit}"
#         f"&period={period}"
#     )
#     response = requests.get(url, headers=headers)
#     if response.status_code != 200:
#         raise Exception(
#             f"Error fetching data: {response.status_code} - {response.text}"
#         )
#     data = response.json()
#     financial_metrics = data.get("financial_metrics")
#     if not financial_metrics:
#         raise ValueError("No financial metrics returned")
#     return financial_metrics

# def search_line_items(
#     ticker: str,
#     line_items: List[str],
#     period: str = 'ttm',
#     limit: int = 1
# ) -> List[Dict[str, Any]]:
#     """Fetch cash flow statements from the API."""
#     headers = {"X-API-KEY": os.environ.get("FINANCIAL_DATASETS_API_KEY")}
#     url = "https://api.financialdatasets.ai/financials/search/line-items"

#     body = {
#         "tickers": [ticker],
#         "line_items": line_items,
#         "period": period,
#         "limit": limit
#     }
#     response = requests.post(url, headers=headers, json=body)
#     if response.status_code != 200:
#         raise Exception(
#             f"Error fetching data: {response.status_code} - {response.text}"
#         )
#     data = response.json()
#     search_results = data.get("search_results")
#     if not search_results:
#         raise ValueError("No search results returned")
#     return search_results

# def get_insider_trades(
#     ticker: str,
#     end_date: str,
#     limit: int = 5,
# ) -> List[Dict[str, Any]]:
#     """
#     Fetch insider trades for a given ticker and date range.
#     """
#     headers = {"X-API-KEY": os.environ.get("FINANCIAL_DATASETS_API_KEY")}
#     url = (
#         f"https://api.financialdatasets.ai/insider-trades/"
#         f"?ticker={ticker}"
#         f"&filing_date_lte={end_date}"
#         f"&limit={limit}"
#     )
#     response = requests.get(url, headers=headers)
#     if response.status_code != 200:
#         raise Exception(
#             f"Error fetching data: {response.status_code} - {response.text}"
#         )
#     data = response.json()
#     insider_trades = data.get("insider_trades")
#     if not insider_trades:
#         raise ValueError("No insider trades returned")
#     return insider_trades

# def get_market_cap(
#     ticker: str,
# ) -> List[Dict[str, Any]]:
#     """Fetch market cap from the API."""
#     headers = {"X-API-KEY": os.environ.get("FINANCIAL_DATASETS_API_KEY")}
#     url = (
#         f'https://api.financialdatasets.ai/company/facts'
#         f'?ticker={ticker}'
#     )

#     response = requests.get(url, headers=headers)
#     if response.status_code != 200:
#         raise Exception(
#             f"Error fetching data: {response.status_code} - {response.text}"
#         )
#     data = response.json()
#     company_facts = data.get('company_facts')
#     if not company_facts:
#         raise ValueError("No company facts returned")
#     return company_facts.get('market_cap')

# def get_prices(
#     ticker: str,
#     start_date: str,
#     end_date: str
# ) -> List[Dict[str, Any]]:
#     """Fetch price data from the API."""
#     headers = {"X-API-KEY": os.environ.get("FINANCIAL_DATASETS_API_KEY")}
#     url = (
#         f"https://api.financialdatasets.ai/prices/"
#         f"?ticker={ticker}"
#         f"&interval=day"
#         f"&interval_multiplier=1"
#         f"&start_date={start_date}"
#         f"&end_date={end_date}"
#     )
#     response = requests.get(url, headers=headers)
#     if response.status_code != 200:
#         raise Exception(
#             f"Error fetching data: {response.status_code} - {response.text}"
#         )
#     data = response.json()
#     prices = data.get("prices")
#     if not prices:
#         raise ValueError("No price data returned")
#     return prices

# def prices_to_df(prices: List[Dict[str, Any]]) -> pd.DataFrame:
#     """Convert prices to a DataFrame."""
#     df = pd.DataFrame(prices)
#     df["Date"] = pd.to_datetime(df["time"])
#     df.set_index("Date", inplace=True)
#     numeric_cols = ["open", "close", "high", "low", "volume"]
#     for col in numeric_cols:
#         df[col] = pd.to_numeric(df[col], errors="coerce")
#     df.sort_index(inplace=True)
#     return df

# # Update the get_price_data function to use the new functions
# def get_price_data(
#     ticker: str,
#     start_date: str,
#     end_date: str
# ) -> pd.DataFrame:
#     prices = get_prices(ticker, start_date, end_date)
#     return prices_to_df(prices)
