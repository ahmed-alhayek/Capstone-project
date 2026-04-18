# mental_health_companion/backend/chatbot.py
"""
Chatbot Engine — AI Mental Health Companion
==========================================
Updated to use RoBERTa text model with 12 emotions.
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

SYSTEM_PROMPT = """You are a compassionate and professional AI mental health companion.
Your role is to:
- Listen carefully and empathetically to the user
- Respond in a warm, supportive, non-judgmental way
- Ask gentle follow-up questions to better understand how the user feels
- Celebrate positive emotions and encourage the user to maintain them
- Offer practical coping strategies when negative emotions are detected
- Never diagnose or replace a real mental health professional
- Always encourage professional help when the situation seems serious
- Keep responses concise (3-5 sentences) unless the user needs more

You are aware of the user's current emotional state based on AI analysis.
Use this information subtly to guide your responses — do NOT directly tell
the user what emotions were detected. Just let it inform your tone and advice.

Important: If the user expresses positive emotions like joy, excitement or love,
celebrate with them warmly and encourage that positivity.
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
        Runs the user's message through RoBERTa text model.

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
        # Sort all emotions by probability
        sorted_emotions = sorted(
            fused_emotions.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Get top positive and negative emotions
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

        # Build guidance based on score
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

        # ── Step 1: Analyze text emotions with RoBERTa ────────────────────
        text_emotions = self.analyze_text_emotions(user_message)

        # ── Step 2: Fuse text + audio emotions ───────────────────────────
        fused_emotions = fuse_emotions(text_emotions, audio_emotions)

        # ── Step 3: Calculate mental health score ─────────────────────────
        score = calculate_mental_health_score(fused_emotions)

        # ── Step 4: Update session tracker ───────────────────────────────
        self.session_tracker.update(text_emotions, audio_emotions)

        # ── Step 5: Build hidden emotion context for Claude ───────────────
        emotion_context = self.build_emotion_context(fused_emotions, score)

        # ── Step 6: Add user message + emotion context to history ─────────
        self.conversation_history.append({
            "role":    "user",
            "content": emotion_context + "\n" + user_message
        })

        # ── Step 7: Send full conversation to Claude API ──────────────────
        api_response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=self.conversation_history
        )

        # ── Step 8: Extract Claude's reply ───────────────────────────────
        assistant_reply = api_response.content[0].text

        # ── Step 9: Save Claude's reply to history ────────────────────────
        self.conversation_history.append({
            "role":    "assistant",
            "content": assistant_reply
        })

        # ── Step 10: Return everything the frontend will need ─────────────
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