from datetime import datetime
from backend.db_manager import get_next_session_id

# simple in-memory storage
user_memory = {}
user_sessions = {}

def get_history(user_id):
    return user_memory.get(user_id, [])

def get_session_id(user_id):
    return user_sessions.get(user_id)

def clear_session(user_id):
    if user_id in user_memory:
        del user_memory[user_id]
    if user_id in user_sessions:
        del user_sessions[user_id]

def save_history(user_id, message, role="User"):
    if user_id not in user_memory:
        user_memory[user_id] = []
        user_sessions[user_id] = get_next_session_id()

    # Format the tag natively into the array string
    msg = f"{role}: {message.strip()}"
    
    # keep last 10 messages for dual-sided context
    user_memory[user_id].append(msg)
    user_memory[user_id] = user_memory[user_id][-10:]

# ==============================
# 🧪 TEST BLOCK (LOCAL TESTING)
# ==============================
if __name__ == "__main__":
    print("Testing memory tagging...")
    save_history("101", "My internet is not working")
    print(f"User 101 History after Msg 1: {get_history('101')}")
    print(f"Session ID: {get_session_id('101')}")
