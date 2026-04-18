# mental_health_companion/backend/test_fusion.py

from fusion import fuse_emotions, calculate_mental_health_score, SessionTracker

# Simulate what the TEXT model might output
text_output = {
    'sadness': 0.8,
    'grief': 0.6,
    'nervousness': 0.3,
    'fear': 0.2,
    'neutral': 0.1,
    'anger': 0.0,
    'disappointment': 0.0,
    'remorse': 0.0,
    'embarrassment': 0.0,
    'disgust': 0.0
}

# Simulate what the AUDIO model might output
audio_output = {
    'sad': 0.7,
    'fearful': 0.2,
    'neutral': 0.1
}

# Test fusion
fused = fuse_emotions(text_output, audio_output)
print("Fused Emotions:", fused)

# Test score
score = calculate_mental_health_score(fused)
print(f"Mental Health Score: {score}/100")

# Test session tracker
tracker = SessionTracker()
tracker.update(text_output, audio_output)
tracker.update({'neutral': 0.9, 'sadness': 0.1}, None)  # a calmer message
summary = tracker.get_session_summary()
print("\nSession Summary:", summary)