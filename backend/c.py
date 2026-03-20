from flask import Flask, request, jsonify, Response
from ai_agent.ai_agent import generate_response
from backend.db_manager import add_or_update_session
from backend.memory import get_session_id, clear_session, get_history
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import os

# ✅ SAFE: Load from environment variables
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

app = Flask(__name__)

BASE_URL = "https://your-ngrok-url.ngrok-free.app"


# ========================================================
# 💬 CHAT API
# ========================================================

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()

    user_id = data.get("user_id", "default_user")
    message = data.get("message")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    ai_result = generate_response(user_id, message)

    summary = generate_summary(
        ai_result.get("history", []),
        ai_result.get("sentiment", "Neutral")
    )

    session_id = get_session_id(user_id)
    ai_reply = ai_result.get("response", "")

    if session_id:
        status = "resolved" if ai_result.get("sentiment") == "Positive" else "unsolved"
        issue_cat = "Customer Inquiry"

        if "network" in summary.lower():
            issue_cat = "Network"
        elif "refund" in summary.lower():
            issue_cat = "Billing"

        add_or_update_session(
            session_id=session_id,
            phone_number=user_id,
            issue=issue_cat,
            summary=summary,
            mood=ai_result.get("sentiment", "Neutral").lower(),
            status=status
        )

        if status == "resolved":
            clear_session(user_id)

    return jsonify({
        "response": ai_reply,
        "sentiment": ai_result.get("sentiment", "Neutral"),
        "suggestions": ai_result.get("suggestions", []),
        "history": ai_result.get("history", []),
        "summary": summary
    })


# ========================================================
# 📞 TWILIO ENTRY
# ========================================================

@app.route('/twilio/voice', methods=['POST', 'GET'])
def twilio_voice():
    caller_phone = request.values.get('From', '').strip()

    print("📞 Incoming call:", caller_phone)

    response = VoiceResponse()

    gather = Gather(
        input='speech',
        action=f"{BASE_URL}/twilio/respond",
        method='POST',
        speechTimeout="auto",
        bargeIn=True,
        language="en-IN"
    )

    gather.say("Hello. I am your AI assistant. How can I help you?")
    response.append(gather)

    return Response(str(response), mimetype='text/xml')


# ========================================================
# 🎤 PROCESS SPEECH
# ========================================================

@app.route('/twilio/respond', methods=['POST', 'GET'])
def twilio_respond():
    caller_phone = request.values.get('From', '').strip()
    speech_result = request.values.get('SpeechResult', '')

    print("👤 Caller:", caller_phone)
    print("🗣 User:", speech_result)

    response = VoiceResponse()

    history = get_history(caller_phone) if caller_phone else []

    # Escalation
    if any(word in speech_result.lower() for word in [
        "agent", "human", "representative", "call center"
    ]):
        response.say("Connecting you to a human agent.")
        response.hangup()
        return Response(str(response), mimetype='text/xml')

    try:
        if not speech_result:
            gather = Gather(
                input='speech',
                action=f"{BASE_URL}/twilio/respond",
                speechTimeout="auto"
            )
            gather.say("I didn't catch that. Please repeat.")
            response.append(gather)
            return Response(str(response), mimetype='text/xml')

        ai_result = generate_response(caller_phone, speech_result)

        ai_reply = ai_result.get("response", "Sorry, something went wrong.")

        # Shorten response
        sentences = ai_reply.split(".")
        ai_reply = ".".join(sentences[:2])
        ai_reply = " ".join(ai_reply.split()[:25])

        summary = generate_summary(
            ai_result.get("history", []),
            ai_result.get("sentiment", "Neutral")
        )

        print("🤖 AI:", ai_reply)

        session_id = get_session_id(caller_phone)

        status = "resolved" if "glad" in ai_reply.lower() else "unsolved"

        if session_id:
            add_or_update_session(
                session_id=session_id,
                phone_number=caller_phone,
                issue="Live Call",
                summary=summary,
                mood=ai_result.get("sentiment", "Neutral").lower(),
                status=status
            )

            if status == "resolved":
                clear_session(caller_phone)

    except Exception as e:
        print("ERROR:", e)
        ai_reply = "Sorry, something went wrong."

    # Flow control
    if "resolved" in ai_reply.lower():
        response.say(ai_reply)
        response.hangup()
    else:
        gather = Gather(
            input='speech',
            action=f"{BASE_URL}/twilio/respond",
            speechTimeout="auto"
        )
        gather.say(ai_reply)
        response.append(gather)

    return Response(str(response), mimetype='text/xml')


# ========================================================
# 📞 OUTBOUND CALL
# ========================================================

@app.route('/make-call')
def make_call():
    client = Client(account_sid, auth_token)

    call = client.calls.create(
        to=os.getenv("TO_PHONE_NUMBER"),
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=f"{BASE_URL}/twilio/voice"
    )

    return f"Calling... {call.sid}"


# ========================================================
# 🧠 SUMMARY
# ========================================================

def generate_summary(history, sentiment=None):
    if not history:
        return "No interactions"
    return f"[{sentiment}] " + " | ".join(history)


# ========================================================
# 🌐 CORS
# ========================================================

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response


# ========================================================
# 🚀 RUN
# ========================================================

if __name__ == "__main__":
    app.run(port=5001, debug=True)