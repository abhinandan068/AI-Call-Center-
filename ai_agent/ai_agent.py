import requests
import os
from jinja2 import Template
from ai_agent.utils import get_intent
from backend.memory import get_history, save_history
from backend.copilot import copilot_engine

# Path to the newly created jinja template
PROMPT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'call_center_prompt.jinja'))

# 🔥 AI CALL FUNCTION
def get_ai_reply(message, sentiment, history, intent):
    try:
        # Load and render the dynamic Jinja prompt
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            template = Template(f.read())
        
        prompt = template.render(
            intent=intent,
            sentiment=sentiment,
            history=history,
            message=message
        )

        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "num_predict": 30
            },
            timeout=10
        )

        reply = res.json().get("response", "").strip()

        # 🔥 prevent repetition
        if history and reply.lower() == history[-1]:
            reply = "Let's try a different step. Please check your network mode or move to a better signal area."

        return reply.strip('"') if reply else "Sorry, I couldn't respond."

    except Exception as e:
        print("AI Error:", e)
        return "Sorry, AI service is unavailable."


def generate_response(user_id, message):
    if not message or not message.strip():
        return {
            "response": "Please describe your issue.",
            "sentiment": "Neutral",
            "history": [],
            "suggestions": []
        }

    # save user history first natively
    save_history(user_id, message, role="User")
    history = get_history(user_id)

    if any(word in message.lower() for word in [
        "agent", "human", "representative", "call center", "support person"
    ]):
        response = "I understand. Connecting you to a human agent now."
        save_history(user_id, response, role="AI")
        return {
            "response": response,
            "sentiment": "Neutral",
            "history": get_history(user_id),
            "suggestions": ["Escalate to human agent"]
        }

    # detect using unified engines
    intent = get_intent(message)
    sentiment, suggestions = copilot_engine(user_id, message, history)

    msg_lower = message.lower()

    # 🔥 closing detection
    if any(word in msg_lower for word in ["thank", "thanks", "resolved", "bye", "exit", "quit", "disconnect", "hang up"]):
        response = "Glad I could help, ending the call now. Goodbye!"
        save_history(user_id, response, role="AI")
        return {
            "response": response,
            "sentiment": "Neutral",
            "history": get_history(user_id),
            "suggestions": ["End call"]
        }

    # 🔥 follow-up handling
    if "how" in msg_lower:
        response = "Let me guide you. First check signal strength, then try switching network mode."
    else:
        # 🔥 smart escalation
        if len(history) >= 3 and len(set(history)) == 1:
            response = "Sorry, this issue is repeated, escalating to higher support."
        else:
            response = get_ai_reply(message, sentiment, history, intent)

    # 🔥 fix double apology
    if sentiment == "Negative":
        if not response.lower().startswith("sorry"):
            response = "Sorry, " + response
        else:
            response = response.replace("Sorry, I'm sorry", "Sorry")
            response = response.replace("Sorry, sorry", "Sorry")

    # save AI generated payload locally so the agent remembers what it said
    save_history(user_id, response, role="AI")

    return {
        "response": response,
        "sentiment": sentiment,
        "history": get_history(user_id), # pass the fully finalized dual-sided array
        "suggestions": suggestions
    }