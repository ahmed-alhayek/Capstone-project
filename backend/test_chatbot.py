# mental_health_companion/backend/test_chatbot.py

from chatbot import MentalHealthChatbot

# Create the chatbot
bot = MentalHealthChatbot()

# Simulate a conversation
print("Testing chatbot...\n")

# Message 1
result1 = bot.chat("I've been feeling really sad and anxious lately, I can't sleep.")
print("User: I've been feeling really sad and anxious lately, I can't sleep.")
print(f"Claude: {result1['response']}")
print(f"Score: {result1['mental_health_score']}/100\n")

# Message 2
result2 = bot.chat("I don't know what to do, everything feels overwhelming.")
print("User: I don't know what to do, everything feels overwhelming.")
print(f"Claude: {result2['response']}")
print(f"Score: {result2['mental_health_score']}/100\n")

# End session
summary = bot.end_session()
print("── Session Summary ──")
print(f"Total messages: {summary['total_messages']}")
print(f"Average score: {summary['average_score']}/100")
print(f"Dominant emotion: {summary['dominant_emotion']}")