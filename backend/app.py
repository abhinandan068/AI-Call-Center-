from flask import Flask, request, jsonify, Response
from ai_agent.ai_agent import generate_response
from backend.db_manager import add_or_update_session
from backend.memory import get_session_id, clear_session, get_history
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client

app = Flask(__name__)

# Temporary memory cache for live Twilio Dashboard syncing
LIVE_SUGGESTIONS = {}

BASE_URL = "https://cyclonical-cameron-hearable.ngrok-free.dev"


import os

# ========================================================
# 🌐 WEB DASHBOARD INTERFACE
# ========================================================

@app.route('/')
def index():
    file_path = os.path.join(os.path.dirname(__file__), 'frontend', 'index.html')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "UI Error: backend/frontend/index.html file missing.", 404

@app.route('/style.css')
def style():
    file_path = os.path.join(os.path.dirname(__file__), 'frontend', 'style.css')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='text/css')
    return "", 404

@app.route('/app.js')
def script():
    file_path = os.path.join(os.path.dirname(__file__), 'frontend', 'app.js')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='application/javascript')
    return "", 404

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

    print(f"🤖 AI RESPONSE: {ai_reply}")
    print(f"📊 Detected Sentiment: {ai_result.get('sentiment', 'Neutral')}")

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
    direction = request.values.get('Direction', 'inbound')
    if 'outbound' in direction:
        caller_phone = request.values.get('To', '').strip()
    else:
        caller_phone = request.values.get('From', '').strip()

    print("📞 Initializing call with:", caller_phone)

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
    direction = request.values.get('Direction', 'inbound')
    if 'outbound' in direction:
        caller_phone = request.values.get('To', '').strip()
    else:
        caller_phone = request.values.get('From', '').strip()
        
    speech_result = request.values.get('SpeechResult', '')

    print("👤 Caller:", caller_phone)
    print("🗣 User:", speech_result)

    response = VoiceResponse()

    # ✅ FIX: Always define history
    history = get_history(caller_phone) if caller_phone else []

    # 🔥 ESCALATION FIX (VERY IMPORTANT)
    if any(word in speech_result.lower() for word in [
        "agent", "human", "representative", "call center"
    ]):
        response.say("I understand. Connecting you to a human agent now.")
        response.pause(length=2)
        response.say("All agents are currently busy. Please try again later.")
        response.hangup()
        return Response(str(response), mimetype='text/xml')

    # 🔥 DISCONNECT (EXIT / QUIT) FIX
    if any(word in speech_result.lower() for word in [
        "exit", "quit", "disconnect", "hang up", "stop calling", "goodbye", "bye"
    ]):
        response.say("Ending the call. Goodbye!")
        response.hangup()
        
        # Explicitly tag SQL and trigger final Summary before wiping memory
        session_id = get_session_id(caller_phone)
        if session_id:
            final_summary = generate_summary(history, "Neutral")
            add_or_update_session(session_id=session_id, phone_number=caller_phone, issue="Live Call", summary=final_summary, mood="neutral", status="resolved")
            
        clear_session(caller_phone)
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

        # Sync suggestions natively to memory cache for Web Dashboard!
        LIVE_SUGGESTIONS[caller_phone] = ai_result.get("suggestions", [])

        ai_reply = ai_result.get("response", "Sorry, something went wrong.")

        # 🔥 SHORT RESPONSE CONTROL
        sentences = ai_reply.split(".")
        ai_reply = ".".join(sentences[:2])
        ai_reply = " ".join(ai_reply.split()[:25])

        summary = generate_summary(
            ai_result.get("history", []),
            ai_result.get("sentiment", "Neutral")
        )

        print("🤖 AI:", ai_reply)
        print(f"📊 Detected Sentiment: {ai_result.get('sentiment', 'Neutral')}")

        session_id = get_session_id(caller_phone)

        status = "resolved" if any(w in ai_reply.lower() for w in ["glad", "resolved", "goodbye", "ending the call"]) else "unsolved"

        if session_id:
            add_or_update_session(
                session_id=session_id,
                phone_number=caller_phone,
                issue="Live Call",
                summary=summary,
                mood=ai_result.get("sentiment", "Neutral").lower(),
                status=status
            )

            print("✅ DB SYNC:", session_id)

            if status == "resolved":
                clear_session(caller_phone)

    except Exception as e:
        print("🔥 ERROR:", e)
        ai_reply = "Sorry, something went wrong."

    # 🔁 FLOW
    if any(word in ai_reply.lower() for word in ["resolved", "glad", "goodbye", "ending the call"]):
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
# 🛑 TWILIO STATUS HANDLER
# ========================================================

@app.route('/twilio/status', methods=['POST'])
def twilio_status():
    status = request.values.get('CallStatus')
    direction = request.values.get('Direction', 'inbound')
    
    if 'outbound' in direction:
        caller_phone = request.values.get('To', '').strip()
    else:
        caller_phone = request.values.get('From', '').strip()

    if status in ['completed', 'failed', 'canceled', 'busy', 'no-answer']:
        print(f"☎️ Twilio Hardware Hangup: {caller_phone} (Status: {status})")
        session_id = get_session_id(caller_phone)
        if session_id:
            from backend.memory import get_history
            history = get_history(caller_phone)
            final_summary = generate_summary(history, "Neutral")
            add_or_update_session(
                session_id=session_id, phone_number=caller_phone,
                issue="Live Call", summary=final_summary,
                mood="neutral", status="resolved"
            )
            clear_session(caller_phone)
    
    return "", 200

# ========================================================
# 📞 OUTBOUND CALL
# ========================================================

@app.route('/make-call')
def make_call():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)

    call = client.calls.create(
        to="+91YOURNUMBER",
        from_="+1CUSTOMERCARE",
        url=f"{BASE_URL}/twilio/voice",
        status_callback=f"{BASE_URL}/twilio/status",
        status_callback_event=['completed']
    )

    return f"Calling... {call.sid}"


# ========================================================
# 🧠 SUMMARY
# ========================================================

import requests

def generate_summary(history, sentiment="Neutral"):
    if not history:
        return "No interactions"
        
    if len(history) <= 2:
        return f"[{sentiment}] " + history[0].replace("User:", "Issue:")

    try:
        # Pass the last 10 messages for extremely fast LLM understanding
        convo_text = "\n".join(history[-10:])
        prompt = f"Summarize this customer support chat in exactly 1 or 2 short sentences. Focus strictly on the customer's core issue and if it was resolved.\n\nChat:\n{convo_text}\n\nSummary:"
        
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "num_predict": 40
            },
            timeout=5
        )
        
        summary = res.json().get("response", "").strip()
        return f"[{sentiment}] {summary}" if summary else f"[{sentiment}] " + " | ".join(history[:2]) + "..."
    except Exception as e:
        print("Summary Error:", e)
        return f"[{sentiment}] " + " | ".join(history[:2]) + "..."


# ========================================================
# 🌐 CORS SUPPORT
# ========================================================

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response


# ========================================================
# 📡 LIVE TWILIO DASHBOARD MONITOR
# ========================================================

@app.route('/live-monitor', methods=['GET'])
def live_monitor():
    from backend.db_manager import SESSION_DB
    import sqlite3
    try:
        if not os.path.exists(SESSION_DB):
            return jsonify({"error": "No database"}), 200

        with sqlite3.connect(SESSION_DB) as conn:
            c = conn.cursor()
            c.execute("SELECT session_id, phone_number, issue, summary, mood, status FROM sessions ORDER BY session_id DESC LIMIT 1")
            row = c.fetchone()
            
            if row:
                session_id, phone_number, issue, summary, mood, status = row
                return jsonify({
                    "session_id": session_id,
                    "phone": phone_number,
                    "history": get_history(phone_number) if phone_number else [],
                    "summary": summary,
                    "sentiment": mood,
                    "status": status,
                    "suggestions": LIVE_SUGGESTIONS.get(phone_number, [])
                })
    except Exception as e:
        print("Monitor error:", e)
        
    return jsonify({"error": "no active calls"}), 200

# ========================================================
# 🚀 RUN
# ========================================================

if __name__ == "__main__":
    app.run(port=5001, debug=True)