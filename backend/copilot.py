# ==============================
# 📦 IMPORTS
# ==============================
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download VADER lexicon (only once)
nltk.download('vader_lexicon', quiet=True)

# Initialize analyzer
sia = SentimentIntensityAnalyzer()


# ==============================
# 🧠 SENTIMENT ENGINE (Positive / Neutral / Negative)
# ==============================
def detect_sentiment(message: str) -> str:
    message_lower = message.lower()

    # 🔥 Rule-based overrides (high accuracy for demo)
    if any(word in message_lower for word in ["slow", "error", "not working", "problem", "refund", "issue", "bad", "terrible", "worst", "stop", "fail", "broken"]):
        return "Negative"

    if any(word in message_lower for word in ["thank", "thanks", "good", "working", "resolved", "awesome", "great", "ok", "okay", "yes", "nice", "perfect"]):
        return "Positive"

    # 🧠 Fallback to VADER
    score = sia.polarity_scores(message)

    if score['compound'] >= 0.05:
        return "Positive"
    elif score['compound'] <= -0.05:
        return "Negative"
    return "Neutral"


# ==============================
# 🔑 KEYWORD-BASED SUGGESTIONS
# ==============================
def keyword_based_suggestions(message: str) -> list:
    message = message.lower()
    suggestions = []

    keyword_map = {
        "slow": ["Ask user to restart router", "Check network speed"],
        "not working": ["Check service outage", "Ask user to reconnect device"],
        "refund": ["Check refund policy", "Verify transaction details"],
        "cancel": ["Assist with cancellation process"],
        "login": ["Ask user to reset password", "Check account credentials"],
        "payment": ["Verify payment status", "Check transaction logs"],
        "error": ["Ask for error details"]
    }

    for key, value in keyword_map.items():
        if key in message:
            suggestions.extend(value)

    return suggestions


# ==============================
# 🤖 BASE SUGGESTIONS (CLEAN)
# ==============================
BASE_SUGGESTIONS = {
    "Negative": [
        "Apologize to the customer",
        "Provide troubleshooting steps",
        "Offer quick resolution"
    ],
    "Neutral": [
        "Ask for more details",
        "Guide step-by-step"
    ],
    "Positive": [
        "Thank the customer",
        "Offer additional help"
    ]
}


# ==============================
# 🤖 SUGGESTION ENGINE
# ==============================
def generate_suggestions(message: str, sentiment: str) -> list:
    suggestions = BASE_SUGGESTIONS.get(sentiment, []).copy()

    # Add keyword-based intelligence
    suggestions.extend(keyword_based_suggestions(message))

    if not suggestions:
        suggestions.append("Assist the customer with general support")

    return suggestions


# ==============================
# 🚀 MAIN COPILOT ENGINE
# ==============================
def copilot_engine(user_id: str, message: str, history: list):
    sentiment = detect_sentiment(message)
    suggestions = generate_suggestions(message, sentiment)

    # 🧠 CONTEXT-AWARE MEMORY LOGIC
    if history:
        last_issue = history[-1].lower()

        if "network" in last_issue and "slow" in message.lower():
            suggestions.append("Prioritize network issue resolution")

        if "refund" in last_issue:
            suggestions.append("Check previous refund status")

    # ✅ Remove duplicates + limit to 5
    suggestions = list(dict.fromkeys(suggestions))[:5]

    return sentiment, suggestions


# ==============================
# 🧪 TEST BLOCK
# ==============================
if __name__ == "__main__":
    test_data = [
        {"user_id": "101", "message": "My internet is very slow", "history": ["Network problem"]},
        {"user_id": "102", "message": "I want a refund", "history": ["Refund issue"]},
        {"user_id": "101", "message": "Thanks, it's working now", "history": ["Network problem"]},
        {"user_id": "103", "message": "I can't login to my account", "history": []},
        {"user_id": "104", "message": "I got an error", "history": []}
    ]

    for data in test_data:
        sentiment, suggestions = copilot_engine(
            data["user_id"],
            data["message"],
            data["history"]
        )

        print("\nUser ID:", data["user_id"])
        print("Message:", data["message"])
        print("History:", data["history"])
        print("Sentiment:", sentiment)
        print("Suggestions:", suggestions)