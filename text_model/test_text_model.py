"""
STEP 3 (Final) — Text Emotion Detection using RoBERTa + Claude API
AI Mental Health Companion | Capstone Project
===================================================================
Uses SamLowe/roberta-base-go_emotions pretrained model.
Maps 28 GoEmotions → 12 mental health relevant categories.

📁 File location: mental_health_companion/text_model/test_text_model.py
📋 Requires: .env file with ANTHROPIC_API_KEY
"""

import os
import torch
import anthropic
from transformers import pipeline
from dotenv import load_dotenv

# ── LOAD API KEY ──────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
api_key = os.getenv("ANTHROPIC_API_KEY")

# Allow import for predict_emotions without requiring API key
claude_client = None
if api_key:
    claude_client = anthropic.Anthropic(api_key=api_key)

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
ROBERTA_MODEL = 'SamLowe/roberta-base-go_emotions'
THRESHOLD     = 0.10  # minimum probability to consider an emotion detected

# ── OUR 12 EMOTION CATEGORIES ─────────────────────────────────────────────────
EMOTION_COLS = [
    'joy', 'excitement', 'love',                    # positive
    'sadness', 'nervousness', 'fear', 'anger',      # negative
    'disappointment', 'remorse', 'embarrassment',   # negative
    'disgust', 'neutral'                            # negative + neutral
]

POSITIVE_EMOTIONS = {'joy', 'excitement', 'love'}
NEGATIVE_EMOTIONS = {
    'sadness', 'nervousness', 'fear', 'anger',
    'disappointment', 'remorse', 'embarrassment', 'disgust'
}

# ── MAP RoBERTa 28 emotions → our 12 categories ───────────────────────────────
ROBERTA_TO_OURS = {
    # Positive → joy
    'joy':           'joy',
    'amusement':     'joy',
    'admiration':    'joy',
    'approval':      'joy',
    'relief':        'joy',

    # Positive → excitement
    'excitement':    'excitement',
    'optimism':      'excitement',
    'pride':         'excitement',

    # Positive → love
    'love':          'love',
    'caring':        'love',
    'desire':        'love',
    'gratitude':     'love',

    # Negative
    'sadness':       'sadness',
    'grief':         'sadness',
    'nervousness':   'nervousness',
    'confusion':     'nervousness',
    'fear':          'fear',
    'anger':         'anger',
    'annoyance':     'anger',
    'disapproval':   'anger',
    'disappointment':'disappointment',
    'remorse':       'remorse',
    'embarrassment': 'embarrassment',
    'disgust':       'disgust',

    # Neutral
    'neutral':       'neutral',
    'realization':   'neutral',
    'curiosity':     'neutral',
    'surprise':      'neutral',
}

EMOTION_EMOJI = {
    'joy'           : '😊',
    'excitement'    : '🤩',
    'love'          : '❤️',
    'sadness'       : '😢',
    'nervousness'   : '😰',
    'fear'          : '😨',
    'anger'         : '😠',
    'disappointment': '😞',
    'remorse'       : '😔',
    'embarrassment' : '😳',
    'disgust'       : '🤢',
    'neutral'       : '😐',
}

# ── LOAD RoBERTa MODEL ────────────────────────────────────────────────────────
print("Loading RoBERTa emotion model...")
device    = 0 if torch.cuda.is_available() else -1
classifier = pipeline(
    'text-classification',
    model=ROBERTA_MODEL,
    top_k=None,
    device=device
)
print(f"-> RoBERTa emotion model loaded!")
print(f"-> Claude API connected!\n")


# ── EMOTION PREDICTION ────────────────────────────────────────────────────────
def predict_emotions(text: str):
    """
    Predicts emotions from text using RoBERTa.
    Maps 28 GoEmotions → our 12 mental health categories.

    Returns:
    - all_probs : dict of all 12 emotion probabilities
    - detected  : dict of emotions above threshold
    """
    # Get RoBERTa predictions (28 emotions)
    raw_results = classifier(text)[0]

    # Initialize our 12 emotion probabilities to 0
    all_probs = {emotion: 0.0 for emotion in EMOTION_COLS}

    # Map RoBERTa emotions → our categories
    # If multiple RoBERTa emotions map to same category, take the max
    for result in raw_results:
        roberta_label = result['label']
        our_label     = ROBERTA_TO_OURS.get(roberta_label)
        if our_label:
            all_probs[our_label] = max(
                all_probs[our_label],
                round(float(result['score']), 3)
            )

    # Detected emotions are those above threshold
    detected = {e: p for e, p in all_probs.items() if p >= THRESHOLD}

    return all_probs, detected


# ── MENTAL HEALTH SCORE ───────────────────────────────────────────────────────
def calculate_mental_health_score(all_probs: dict) -> float:
    """
    Calculates a Mental Health Score from 0 to 100.

    Positive emotions → improve score (negative weights)
    Negative emotions → lower score  (positive weights)
    Higher score = better mental health.
    """
    weights = {
        # Positive emotions — improve score
        'joy'           : -0.15,
        'excitement'    : -0.10,
        'love'          : -0.12,
        # Negative emotions — lower score
        'sadness'       :  0.15,
        'nervousness'   :  0.12,
        'fear'          :  0.12,
        'anger'         :  0.10,
        'disappointment':  0.10,
        'remorse'       :  0.08,
        'embarrassment' :  0.08,
        'disgust'       :  0.10,
        # Neutral — slight improvement
        'neutral'       : -0.05,
    }

    distress_score = sum(
        all_probs.get(e, 0) * w
        for e, w in weights.items()
    )
    distress_score = max(-1.0, min(1.0, distress_score))
    score          = round((1 - distress_score) * 50, 1)
    return max(0, min(100, score))


# ── CLAUDE API RECOMMENDATION ─────────────────────────────────────────────────
def get_ai_recommendation(text: str, detected_emotions: dict,
                           mental_health_score: float) -> str:
    """
    Sends detected emotions to Claude API for personalized recommendations.
    Handles both positive and negative emotions appropriately.
    """
    if detected_emotions:
        pos = {e: p for e, p in detected_emotions.items()
               if e in POSITIVE_EMOTIONS}
        neg = {e: p for e, p in detected_emotions.items()
               if e in NEGATIVE_EMOTIONS}

        parts = []
        if pos:
            pos_str = ", ".join(
                f"{e} ({p:.0%})"
                for e, p in sorted(pos.items(), key=lambda x: -x[1])
            )
            parts.append(f"Positive: {pos_str}")
        if neg:
            neg_str = ", ".join(
                f"{e} ({p:.0%})"
                for e, p in sorted(neg.items(), key=lambda x: -x[1])
            )
            parts.append(f"Negative: {neg_str}")

        emotion_summary = " | ".join(parts) if parts else "neutral"
    else:
        emotion_summary = "no strong emotions detected (neutral)"

    prompt = f"""You are a compassionate mental health companion AI assistant.

A user wrote the following message:
"{text}"

Our emotion detection model analyzed this text and found:
- Detected emotions: {emotion_summary}
- Mental Health Score: {mental_health_score}/100 (100 = very healthy, 0 = high distress)

Based on this analysis, provide a short, warm, and empathetic response (3-4 sentences max).
- If positive emotions detected: celebrate with them and encourage continuation
- If negative emotions detected: be supportive and suggest one practical coping activity
- If mixed emotions: acknowledge complexity and offer balanced support
- Be warm, human, and non-clinical
- Do NOT diagnose or label any mental health condition"""

    message = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


# ── ONLY RUNS WHEN THIS FILE IS EXECUTED DIRECTLY ────────────────────────────
if __name__ == "__main__":

    test_sentences = [
        "I am so happy and excited about my graduation!",
        "I feel so lonely and empty inside, nothing makes me happy.",
        "I am really anxious and stressed about my exam tomorrow.",
        "I am furious at how they treated me, it is not fair.",
        "I deeply regret what I did, I cannot forgive myself.",
        "I am terrified of what might happen next.",
        "Today I went to the store, nothing special happened.",
        "I made a fool of myself in front of everyone.",
        "That behavior is completely disgusting and unacceptable.",
        "I expected so much more, I feel completely let down.",
    ]

    print("=" * 65)
    print("       AI MENTAL HEALTH COMPANION — TEXT ANALYSIS")
    print("=" * 65)

    for sentence in test_sentences:
        all_probs, detected = predict_emotions(sentence)
        score               = calculate_mental_health_score(all_probs)
        recommendation      = get_ai_recommendation(sentence, detected, score)

        print(f"\n📝 Text: \"{sentence}\"")
        print(f"\n🎯 Detected Emotions:", end=" ")
        if detected:
            for emotion, prob in sorted(detected.items(), key=lambda x: -x[1]):
                emoji = EMOTION_EMOJI.get(emotion, '')
                print(f"{emoji} {emotion} ({prob:.0%})", end="  ")
        else:
            print("😐 None detected above threshold")

        print(f"\n💯 Mental Health Score : {score}/100")
        print(f"\n💡 AI Recommendation   :\n   {recommendation}")
        print("\n" + "-" * 65)

    # ── INTERACTIVE MODE ──────────────────────────────────────────────────────
    print("\n\n" + "=" * 65)
    print("       INTERACTIVE MODE — Type your own text!")
    print("       (type 'quit' to exit)")
    print("=" * 65)

    while True:
        user_input = input("\n📝 Enter text: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Take care! 👋")
            break
        if not user_input:
            continue

        print("\n⏳ Analyzing...")
        all_probs, detected = predict_emotions(user_input)
        score               = calculate_mental_health_score(all_probs)
        recommendation      = get_ai_recommendation(user_input, detected, score)

        print("\n🎯 Detected Emotions:")
        if detected:
            for emotion, prob in sorted(detected.items(), key=lambda x: -x[1]):
                emoji = EMOTION_EMOJI.get(emotion, '')
                bar   = "█" * int(prob * 20)
                print(f"   {emoji} {emotion:<15} {bar} {prob:.0%}")
        else:
            print("   😐 No strong emotions detected")

        print(f"\n💯 Mental Health Score : {score}/100")
        print(f"\n💡 AI Recommendation   :\n   {recommendation}")