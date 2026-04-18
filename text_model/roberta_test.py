# mental_health_companion/text_model/roberta_test.py

from transformers import pipeline

classifier = pipeline(
    'text-classification',
    model='SamLowe/roberta-base-go_emotions',
    top_k=5
)

tests = [
    'I am so happy about my graduation!',
    'I feel so lonely and empty inside',
    'I am furious at how they treated me',
    'I am terrified of what might happen',
    'I deeply regret what I did to them',
    'I am really anxious about my exam',
    'That behavior is completely disgusting',
    'I made a fool of myself in front of everyone',
    'I expected so much more, I feel let down',
    'Today I went to the store and bought groceries'
]

for text in tests:
    print(f'\nText: {text}')
    results = classifier(text)
    for r in results[0]:
        print(f'  {r["label"]:<20} {r["score"]:.3f}')