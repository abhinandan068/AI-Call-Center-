from ai_agent.ai_agent import generate_response

user_id = "101"

while True:
    msg = input("User: ")

    if msg.lower() == "exit":
        break

    res = generate_response(user_id, msg)

    print("AI:", res["response"])
    print("Sentiment:", res["sentiment"])
    print("Suggestions:", res["suggestions"])
    print("History:", res["history"])
    print("-" * 40)