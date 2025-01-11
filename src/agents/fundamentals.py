from langchain_core.messages import HumanMessage

from agents.state import AgentState, show_agent_reasoning

import json

##### Fundamental Agent #####
def fundamentals_agent(state: AgentState):
    """Analyzes fundamental data and generates trading signals."""
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    metrics = data["financial_metrics"][0]

    # Utility functions to handle data conversions
    def safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def calculate_net_margin(revenue, net_income):
        revenue = safe_float(revenue)
        net_income = safe_float(net_income)
        if revenue and net_income:  # Ensure both values are valid
            return net_income / revenue
        return None


    def calculate_operating_margin(operating_income, revenue):
        operating_income = safe_float(operating_income)
        revenue = safe_float(revenue)
        if revenue and operating_income:  # Ensure both values are valid
            return operating_income / revenue
        return None

    # Initialize signals list for different fundamental aspects
    signals = []
    reasoning = {}
    
    # 1. Profitability Analysis
    profitability_score = 0
    
    # Check or calculate return on equity
    roe = safe_float(metrics.get("return_on_equity") or metrics.get("ReturnOnEquityTTM"))
    if roe and roe > 0.15:  # Strong ROE above 15%
        profitability_score += 1

    # Check or calculate net margin
    net_margin = safe_float(metrics.get("net_margin")) or calculate_net_margin(
        metrics.get("RevenueTTM"), metrics.get("net_income")
    )
    if net_margin and net_margin > 0.20:  # Healthy profit margins
        profitability_score += 1

    # Check or calculate operating margin
    operating_margin = safe_float(metrics.get("operating_margin")) or calculate_operating_margin(
        metrics.get("operating_income"), metrics.get("RevenueTTM")
    )
    if operating_margin and operating_margin > 0.15:  # Strong operating efficiency
        profitability_score += 1
        
    signals.append('bullish' if profitability_score >= 2 else 'bearish' if profitability_score == 0 else 'neutral')
    reasoning["profitability_signal"] = {
        "signal": signals[0],
        "details": (
            f"ROE: {f'{roe:.2%}' if roe is not None else 'N/A'}, "
            f"Net Margin: {f'{net_margin:.2%}' if net_margin is not None else 'N/A'}, "
            f"Op Margin: {f'{operating_margin:.2%}' if operating_margin is not None else 'N/A'}"
        )
    }

    
    # 2. Growth Analysis
    growth_score = 0
    revenue_growth = safe_float(metrics.get("revenue_growth") or metrics.get("QuarterlyRevenueGrowthYOY"))
    earnings_growth = safe_float(metrics.get("earnings_growth") or metrics.get("QuarterlyEarningsGrowthYOY"))
    book_value_growth = safe_float(metrics.get("book_value_growth"))  # Assuming this is directly fetched
    
    if revenue_growth and revenue_growth > 0.10:  # 10% revenue growth
        growth_score += 1
    if earnings_growth and earnings_growth > 0.10:  # 10% earnings growth
        growth_score += 1
    if book_value_growth and book_value_growth > 0.10:  # 10% book value growth
        growth_score += 1
        
    signals.append('bullish' if growth_score >= 2 else 'bearish' if growth_score == 0 else 'neutral')
    reasoning["growth_signal"] = {
        "signal": signals[1],
        "details": (
            f"Revenue Growth: {f'{revenue_growth:.2%}' if revenue_growth is not None else 'N/A'}, "
            f"Earnings Growth: {f'{earnings_growth:.2%}' if earnings_growth is not None else 'N/A'}"
        )
    }

    
    # 3. Financial Health
    health_score = 0
    current_ratio = safe_float(metrics.get("current_ratio") or metrics.get("CurrentRatio"))
    debt_to_equity = safe_float(metrics.get("debt_to_equity") or metrics.get("DebtToEquityRatio"))
    fcf_per_share = safe_float(metrics.get("free_cash_flow_per_share"))
    eps = safe_float(metrics.get("earnings_per_share"))

    if current_ratio and current_ratio > 1.5:  # Strong liquidity
        health_score += 1
    if debt_to_equity and debt_to_equity < 0.5:  # Conservative debt levels
        health_score += 1
    if fcf_per_share and eps and fcf_per_share > eps * 0.8:  # Strong FCF conversion
        health_score += 1
        
    signals.append('bullish' if health_score >= 2 else 'bearish' if health_score == 0 else 'neutral')
    reasoning["financial_health_signal"] = {
        "signal": signals[2],
        "details": (
            f"Current Ratio: {f'{current_ratio:.2f}' if current_ratio is not None else 'N/A'}, "
            f"D/E: {f'{debt_to_equity:.2f}' if debt_to_equity is not None else 'N/A'}"
        )
    }

    
    # 4. Price to X ratios
    pe_ratio = safe_float(metrics.get("price_to_earnings_ratio") or metrics.get("PERatio"))
    pb_ratio = safe_float(metrics.get("price_to_book_ratio") or metrics.get("PriceToBookRatio"))
    ps_ratio = safe_float(metrics.get("price_to_sales_ratio") or metrics.get("PriceToSalesRatioTTM"))
    
    price_ratio_score = 0
    if pe_ratio and pe_ratio < 25:  # Reasonable P/E ratio
        price_ratio_score += 1
    if pb_ratio and pb_ratio < 3:  # Reasonable P/B ratio
        price_ratio_score += 1
    if ps_ratio and ps_ratio < 5:  # Reasonable P/S ratio
        price_ratio_score += 1
        
    signals.append('bullish' if price_ratio_score >= 2 else 'bearish' if price_ratio_score == 0 else 'neutral')
    reasoning["price_ratios_signal"] = {
        "signal": signals[3],
        "details": (
            f"P/E: {f'{pe_ratio:.2f}' if pe_ratio is not None else 'N/A'}, "
            f"P/B: {f'{pb_ratio:.2f}' if pb_ratio is not None else 'N/A'}, "
            f"P/S: {f'{ps_ratio:.2f}' if ps_ratio is not None else 'N/A'}"
        )
    }

    
    # Determine overall signal
    bullish_signals = signals.count('bullish')
    bearish_signals = signals.count('bearish')
    
    if bullish_signals > bearish_signals:
        overall_signal = 'bullish'
    elif bearish_signals > bullish_signals:
        overall_signal = 'bearish'
    else:
        overall_signal = 'neutral'
    
    # Calculate confidence level
    total_signals = len(signals)
    confidence = max(bullish_signals, bearish_signals) / total_signals
    
    message_content = {
        "signal": overall_signal,
        "confidence": f"{round(confidence * 100)}%",
        "reasoning": reasoning
    }
    
    # Create the fundamental analysis message
    message = HumanMessage(
        content=json.dumps(message_content),
        name="fundamentals_agent",
    )
    
    # Print the reasoning if the flag is set
    if show_reasoning:
        show_agent_reasoning(message_content, "Fundamental Analysis Agent")
    
    return {
        "messages": [message],
        "data": data,
    }
