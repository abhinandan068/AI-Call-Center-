def detect_sentiment(message):
    msg = message.lower()

    if any(word in msg for word in [
        "slow", "not", "issue", "problem", "angry", "disconnect", "delay", "bad"
    ]):
        return "negative"

    return "neutral"


def get_intent(message):
    msg = message.lower()

    if any(word in msg for word in [
        "call", "voice", "hearing", "voice break", "call drop"
    ]):
        return "call_issue"

    if any(word in msg for word in [
        "internet", "network", "signal", "data"
    ]):
        return "network"

    if any(word in msg for word in [
        "bill", "refund", "recharge", "payment"
    ]):
        return "billing"

    return "general"


def generate_suggestions(intent, sentiment):
    suggestions = []

    if intent == "call_issue":
        suggestions.append("Check SIM network coverage")
        suggestions.append("Switch network mode (4G/5G)")

    if sentiment == "negative":
        suggestions.append("Apologize to the customer")

    if intent == "network":
        suggestions.append("Guide router restart")
        suggestions.append("Check signal strength")

    if intent == "billing":
        suggestions.append("Ask for transaction ID")

    if not suggestions:
        suggestions.append("Provide polite assistance")

    return suggestions