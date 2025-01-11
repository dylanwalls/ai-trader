from langchain_core.messages import HumanMessage

from agents.state import AgentState, show_agent_reasoning

import pandas as pd

import numpy as np

import json

##### Sentiment Agent #####
def sentiment_agent(state: AgentState):
    """Analyzes market sentiment and generates trading signals."""
    data = state["data"]
    insider_trades = data.get("insider_trades", [])
    show_reasoning = state["metadata"]["show_reasoning"]

    # Safely extract 'transaction_shares' and handle missing keys
    transaction_shares = pd.Series(
        [t.get('transaction_shares', None) for t in insider_trades]
    ).dropna()

    if transaction_shares.empty:
        # Handle case where no valid 'transaction_shares' data is found
        overall_signal = "neutral"
        confidence = 0.0
        reasoning = "No valid 'transaction_shares' data available for sentiment analysis."
    else:
        # Evaluate signals based on transaction_shares
        bearish_condition = transaction_shares < 0
        signals = np.where(bearish_condition, "bearish", "bullish").tolist()

        # Determine overall signal
        bullish_signals = signals.count("bullish")
        bearish_signals = signals.count("bearish")

        if bullish_signals > bearish_signals:
            overall_signal = "bullish"
        elif bearish_signals > bullish_signals:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"

        # Calculate confidence level based on the proportion of indicators agreeing
        total_signals = len(signals)
        confidence = max(bullish_signals, bearish_signals) / total_signals

        reasoning = f"Bullish signals: {bullish_signals}, Bearish signals: {bearish_signals}"

    message_content = {
        "signal": overall_signal,
        "confidence": f"{round(confidence * 100)}%",
        "reasoning": reasoning,
    }

    # Print the reasoning if the flag is set
    if show_reasoning:
        show_agent_reasoning(message_content, "Sentiment Analysis Agent")

    # Create the sentiment message
    message = HumanMessage(
        content=json.dumps(message_content),
        name="sentiment_agent",
    )

    return {
        "messages": [message],
        "data": data,
    }
