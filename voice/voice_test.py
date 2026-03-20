import time
from .stt import listen
from .tts import speak
from ai_agent.ai_agent import generate_response
from backend.db_manager import add_or_update_session
from backend.memory import get_session_id, clear_session

def run_voice_test():
    print("=========================================")
    print("🎙️ AI Call Center - Voice Test Started 🎙️")
    print("=========================================")
    
    # Secure CRM linkage via Phone Number
    valid_number = input("📞 Enter Caller Phone Number (e.g. +91XXXXXXXXXX): ")
    phone_number = valid_number.strip() if valid_number.strip() else "unknown"
    
    # Treat the phone number natively as the unique caller ID thread
    user_id = phone_number
    
    while True:
        print("\n[Please speak now...]")
        user_input = listen()
        
        if not user_input:
            print("[No speech detected. Please try again.]")
            continue
            
        if "exit" in user_input.lower() or "quit" in user_input.lower():
            speak("Goodbye! Have a great day.")
            print("Exiting...")
            break
            
        # Get AI Response
        print("🧠 Processing with AI Engine...")
        result = generate_response(user_id, user_input)
        
        reply = result.get("response", "Sorry, I am facing technical difficulties.")
        sentiment = result.get("sentiment", "Neutral")
        
        print(f"📊 Detected Sentiment: {sentiment}")
        print(f"💡 Suggestions: {result.get('suggestions', [])}")
        
        # Determine status and record natively into Database
        status = "resolved" if "Glad I could help" in reply else "unsolved"
        session_id = get_session_id(user_id)
        
        if session_id:
            add_or_update_session(
                session_id=session_id,
                phone_number=user_id,
                issue="Voice Interaction",
                summary=f"Voice call concerning {sentiment} issues. AI output: {reply}",
                mood=sentiment.lower(),
                status=status
            )
            print(f"✅ Session actively logged to DB: {session_id}")
            
            if status == "resolved":
                clear_session(user_id)
        
        # Speak response
        speak(reply)
        time.sleep(1)

if __name__ == "__main__":
    run_voice_test()