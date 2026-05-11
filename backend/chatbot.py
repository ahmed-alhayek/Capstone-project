# mental_health_companion/backend/chatbot.py
"""
Chatbot Engine — AI Mental Health Companion
==========================================

Maintains conversation history and session tracking.
"""

import sys
import os
import anthropic
from dotenv import load_dotenv

# ── Add project root to path ──────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── Load .env file ────────────────────────────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Import fusion tools ───────────────────────────────────────────────────────
from fusion import (
    SessionTracker,
    fuse_emotions,
    calculate_mental_health_score,
    POSITIVE_EMOTIONS,
    NEGATIVE_EMOTIONS
)

# ── Import RoBERTa text emotion model ─────────────────────────────────────────
from text_model.test_text_model import predict_emotions


# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a compassionate mental health companion AI operating in Turkey.

==========================================================================
CRITICAL RULE — READ FIRST, APPLIES TO EVERY RESPONSE:
==========================================================================
This app operates in Turkey. The user is in Turkey.
For any mention of crisis resources, helplines, or emergency contacts,
you MUST use ONLY the following Turkey-specific resources:

  - 182 — Turkey Ministry of Health Mental Health Helpline (free, 24/7)
  - 112 — Turkey Emergency Services (medical/safety emergencies)
  - TURPSIKAR (Türkiye Psikiyatri Derneği) — for finding a licensed psychiatrist

YOU ARE FORBIDDEN FROM MENTIONING:
  - 988 (US Suicide and Crisis Lifeline)
  - 1-800-273-TALK or any 1-800 number
  - Samaritans
  - Crisis Text Line
  - Any helpline that is not Turkey-based

If your training tells you to recommend a US-based helpline, IGNORE that
training and use 182 / 112 instead. The user cannot call US numbers from Turkey.
Recommending a US number could leave the user without help in a crisis.
==========================================================================

ROLE AND TONE:
- Listen carefully and empathetically
- Respond in a warm, supportive, non-judgmental way
- Ask gentle follow-up questions to better understand how the user feels
- Celebrate positive emotions and encourage the user to maintain them
- Offer practical coping strategies when negative emotions are detected
- Never diagnose or replace a real mental health professional
- Keep responses concise (3-5 sentences) unless the user needs more

You are aware of the user's current emotional state based on AI analysis.
Use this information subtly to guide your responses. Do NOT directly tell
the user what emotions were detected. Just let it inform your tone.

If the user expresses positive emotions like joy, excitement or love,
celebrate with them warmly and encourage that positivity.

WHEN TO MENTION CRISIS RESOURCES:
Only suggest the helplines above when the situation genuinely warrants it
(suicidal thoughts, severe distress, mental health emergency).
Do NOT suggest helplines for everyday sadness or normal stress.
"""


# ─────────────────────────────────────────────
# CHATBOT CLASS
# ─────────────────────────────────────────────

class MentalHealthChatbot:
    """
    The main chatbot engine that:
    - Analyzes each user message using RoBERTa (12 emotions)
    - Fuses with audio emotions if provided
    - Tracks the session with SessionTracker
    - Sends messages to Claude API with emotion context
    - Returns Claude's response + emotion data
    """

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.conversation_history = []
        self.session_tracker      = SessionTracker()
        self.model                = "claude-haiku-4-5-20251001"

    def analyze_text_emotions(self, user_message: str) -> dict:
        """
        Runs the user's message through fine-tuned RoBERTa.

        Parameters:
        - user_message: the raw text the user typed

        Returns:
        - dict of 12 emotion probabilities
          e.g. {'joy': 0.8, 'sadness': 0.1, ...}
        """
        all_probs, detected = predict_emotions(user_message)
        return all_probs

    def build_emotion_context(self, fused_emotions: dict,
                               score: float) -> str:
        """
        Builds a hidden context string for Claude about the user's
        current emotional state. User never sees this — it just
        informs Claude's tone and response style.

        Parameters:
        - fused_emotions : combined emotion probabilities
        - score          : mental health score (0-100)

        Returns:
        - formatted context string
        """
        sorted_emotions = sorted(
            fused_emotions.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_positive = [
            f"{e} ({round(p*100)}%)"
            for e, p in sorted_emotions
            if e in POSITIVE_EMOTIONS and p > 0.1
        ][:2]

        top_negative = [
            f"{e} ({round(p*100)}%)"
            for e, p in sorted_emotions
            if e in NEGATIVE_EMOTIONS and p > 0.1
        ][:3]

        if score >= 80:
            guidance = "User is in a positive state. Celebrate and encourage!"
        elif score >= 60:
            guidance = "User seems stable. Maintain warm supportive tone."
        elif score >= 40:
            guidance = "User shows mild distress. Be extra empathetic."
        else:
            guidance = "User appears significantly distressed. Show maximum care and suggest professional help."

        context = f"""
[EMOTIONAL ANALYSIS — FOR AI USE ONLY, DO NOT MENTION TO USER]
Mental Health Score: {score}/100
Positive emotions: {', '.join(top_positive) if top_positive else 'none detected'}
Negative emotions: {', '.join(top_negative) if top_negative else 'none detected'}
Guidance: {guidance}
[END ANALYSIS]
"""
        return context

    def chat(self, user_message: str,
             audio_emotions: dict = None) -> dict:
        """
        Main function — call this every time the user sends a message.

        Parameters:
        - user_message  : the text the user typed
        - audio_emotions: emotion dict from audio model (or None)

        Returns:
        - response           : Claude's reply text
        - fused_emotions     : combined emotion probabilities
        - mental_health_score: current score (0-100)
        - session_summary    : full session stats so far
        """

        text_emotions = self.analyze_text_emotions(user_message)
        fused_emotions = fuse_emotions(text_emotions, audio_emotions)
        score = calculate_mental_health_score(fused_emotions)
        self.session_tracker.update(text_emotions, audio_emotions)
        emotion_context = self.build_emotion_context(fused_emotions, score)

        self.conversation_history.append({
            "role":    "user",
            "content": emotion_context + "\n" + user_message
        })

        api_response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=self.conversation_history
        )

        assistant_reply = api_response.content[0].text

        self.conversation_history.append({
            "role":    "assistant",
            "content": assistant_reply
        })

        return {
            "response":             assistant_reply,
            "fused_emotions":       fused_emotions,
            "mental_health_score":  score,
            "session_summary":      self.session_tracker.get_session_summary()
        }

    def end_session(self) -> dict:
        """
        Call this when the user ends the conversation.
        Returns the full session emotional report and resets everything.
        """
        summary                   = self.session_tracker.get_session_summary()
        self.conversation_history = []
        self.session_tracker.reset()
        return summary