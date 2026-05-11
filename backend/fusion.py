# mental_health_companion/backend/fusion.py
"""
Fusion Layer — Combines Text + Audio Emotions
AI Mental Health Companion | Capstone Project
=============================================

Fuses text emotions + audio emotions into unified score.
"""

from datetime import datetime


# ─────────────────────────────────────────────
# EMOTION LABEL MAPPINGS
# ─────────────────────────────────────────────

# 12 emotions from RoBERTa text model
TEXT_EMOTIONS = [
    'joy', 'excitement', 'love',                    # positive
    'sadness', 'nervousness', 'fear', 'anger',      # negative
    'disappointment', 'remorse', 'embarrassment',   # negative
    'disgust', 'neutral'                            # negative + neutral
]

# 8 emotions from RAVDESS audio model
AUDIO_EMOTIONS = [
    'neutral', 'calm', 'happy', 'sad',
    'angry', 'fearful', 'disgust', 'surprised'
]

# Map AUDIO emotions → TEXT emotions
AUDIO_TO_TEXT_MAP = {
    'neutral':   'neutral',
    'calm':      'neutral',
    'happy':     'joy',         
    'sad':       'sadness',
    'angry':     'anger',
    'fearful':   'fear',
    'disgust':   'disgust',
    'surprised': 'excitement'   # surprise maps to excitement
}

# Emotion weights for mental health score
# Positive emotions → negative weights (improve score)
# Negative emotions → positive weights (lower score)
# Emotion weights for mental health score
# Positive emotions → negative weights (improve score)
# Negative emotions → positive weights (lower score)
EMOTION_WEIGHTS = {
    # Positive — improve score
    'joy'           : -1.00,
    'love'          : -0.85,
    'excitement'    : -0.70,
    # Negative — lower score (weighted by mental health severity)
    'sadness'       :  0.85,   # highest — depression indicator
    'fear'          :  0.75,
    'anger'         :  0.75,
    'nervousness'   :  0.65,   # anxiety
    'disappointment':  0.60,
    'disgust'       :  0.55,
    'remorse'       :  0.50,   # guilt — self-reflective, lower severity
    'embarrassment' :  0.40,   # usually passing, lowest severity
    # Neutral — no effect (was a bug: neutral was boosting score)
    'neutral'       :  0.00,
}

# Separate positive and negative for analysis
POSITIVE_EMOTIONS = {'joy', 'excitement', 'love'}
NEGATIVE_EMOTIONS = {
    'sadness', 'nervousness', 'fear', 'anger',
    'disappointment', 'remorse', 'embarrassment', 'disgust'
}


# ─────────────────────────────────────────────
# FUSION FUNCTION
# ─────────────────────────────────────────────

def fuse_emotions(text_emotions: dict, audio_emotions: dict = None,
                  text_weight: float = 0.7, audio_weight: float = 0.3) -> dict:
    """
    Combines text emotion probabilities and audio emotion probabilities
    into one unified emotion dictionary.

    
    
    """

    # Start with all emotions at zero
    fused = {emotion: 0.0 for emotion in TEXT_EMOTIONS}

    # ── Step 1: Add weighted text emotions ───────────────────────────────────
    for emotion, prob in text_emotions.items():
        if emotion in fused:
            fused[emotion] += prob * text_weight

    # ── Step 2: Add weighted audio emotions  ────────────────────
    if audio_emotions:
        for audio_label, prob in audio_emotions.items():
            text_label = AUDIO_TO_TEXT_MAP.get(audio_label)
            if text_label and text_label in fused:
                fused[text_label] += prob * audio_weight

    # ── Step 3: Clamp all values between 0.0 and 1.0 ────────────────────────
    for emotion in fused:
        fused[emotion] = min(fused[emotion], 1.0)

    return fused


# ─────────────────────────────────────────────
# MENTAL HEALTH SCORE CALCULATOR
# ─────────────────────────────────────────────

def calculate_mental_health_score(fused_emotions: dict) -> float:
    """
    Converts fused emotion probabilities into a single Mental Health Score.

    Score range: 0 to 100
    - 100 = perfectly healthy / calm / positive
    -   0 = extreme distress across all emotions

    
    """
    distress_score = 0.0

    for emotion, prob in fused_emotions.items():
        weight = EMOTION_WEIGHTS.get(emotion, 0.0)
        distress_score += prob * weight

    # Clamp between -1 and 1
    distress_score = max(-1.0, min(1.0, distress_score))

    # Convert to 0-100 scale
    mental_health_score = (1 - distress_score) * 50

    return round(mental_health_score, 2)


# ─────────────────────────────────────────────
# SESSION TRACKER CLASS
# ─────────────────────────────────────────────

class SessionTracker:
    """
    Tracks ALL emotion readings across an entire conversation session.

    Each time the user sends a message (text or voice), we store:
    - The timestamp
    - The fused emotions for that message
    - The mental health score for that message

    At the end, we can generate a full session summary.
    """

    def __init__(self):
        self.history       = []
        self.current_score = 100.0
        self.session_start = datetime.now()

    def update(self, text_emotions: dict,
               audio_emotions: dict = None) -> dict:
        """
        Call this every time the user sends a message.

        Parameters:
        - text_emotions : emotion probabilities from RoBERTa text model
        - audio_emotions: emotion probabilities from audio model (or None)

        Returns a snapshot dict with fused emotions + score.
        """
        fused              = fuse_emotions(text_emotions, audio_emotions)
        score              = calculate_mental_health_score(fused)
        self.current_score = score

        snapshot = {
            'timestamp':           datetime.now().isoformat(),
            'fused_emotions':      fused,
            'mental_health_score': score,
            'had_audio':           audio_emotions is not None
        }
        self.history.append(snapshot)

        return snapshot

    def get_session_summary(self) -> dict:
        """
        Generates a full emotional report at the end of a session.

        Returns:
        - total messages analyzed
        - average mental health score
        - highest score (best moment)
        - lowest score (most distressed moment)
        - average probability for each emotion
        - dominant emotion
        - dominant positive emotion
        - dominant negative emotion
        """
        if not self.history:
            return {'message': 'No data recorded in this session.'}

        scores = [snap['mental_health_score'] for snap in self.history]

        # Average emotion probabilities across all messages
        emotion_totals = {emotion: 0.0 for emotion in TEXT_EMOTIONS}
        for snap in self.history:
            for emotion, prob in snap['fused_emotions'].items():
                emotion_totals[emotion] += prob

        n            = len(self.history)
        avg_emotions = {
            emotion: round(total / n, 4)
            for emotion, total in emotion_totals.items()
        }

        # Find dominant emotion overall
        dominant_emotion = max(avg_emotions, key=avg_emotions.get)

        # Find dominant positive emotion
        pos_emotions     = {e: p for e, p in avg_emotions.items()
                           if e in POSITIVE_EMOTIONS}
        dominant_positive = max(pos_emotions, key=pos_emotions.get) \
                           if pos_emotions else None

        # Find dominant negative emotion
        neg_emotions     = {e: p for e, p in avg_emotions.items()
                           if e in NEGATIVE_EMOTIONS}
        dominant_negative = max(neg_emotions, key=neg_emotions.get) \
                           if neg_emotions else None

        return {
            'total_messages':          n,
            'session_duration_seconds': (
                datetime.now() - self.session_start
            ).seconds,
            'average_score':           round(sum(scores) / n, 2),
            'highest_score':           round(max(scores), 2),
            'lowest_score':            round(min(scores), 2),
            'final_score':             round(scores[-1], 2),
            'average_emotions':        avg_emotions,
            'dominant_emotion':        dominant_emotion,
            'dominant_positive':       dominant_positive,
            'dominant_negative':       dominant_negative,
            'score_history':           scores
        }

    def reset(self):
        """Clears the session — call this when starting a new conversation."""
        self.history       = []
        self.current_score = 100.0
        self.session_start = datetime.now()