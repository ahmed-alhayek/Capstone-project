"""
STEP 1 (Final) — Text Dataset Preprocessing

"""

import pandas as pd
import re
import ast
from sklearn.model_selection import train_test_split

# ── GoEmotions 28 emotion labels (by index) ───────────────────────────────────
GO_EMOTIONS_LABELS = [
    'admiration', 'amusement', 'anger', 'annoyance', 'approval',
    'caring', 'confusion', 'curiosity', 'desire', 'disappointment',
    'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear',
    'gratitude', 'grief', 'joy', 'love', 'nervousness',
    'optimism', 'pride', 'realization', 'relief', 'remorse',
    'sadness', 'surprise', 'neutral'
]

# ── Map GoEmotions → our 11 emotions ─────────────────────────────────────────
EMOTION_MAP = {
    # All positive emotions → joy
    'admiration':    'joy',
    'amusement':     'joy',
    'approval':      'joy',
    'joy':           'joy',
    'excitement':    'joy',
    'optimism':      'joy',
    'pride':         'joy',
    'caring':        'joy',
    'love':          'joy',
    'desire':        'joy',
    'gratitude':     'joy',
    'relief':        'joy',

    # Negative emotions
    'sadness':        'sadness',
    'grief':          'sadness',       # merge grief → sadness
    'nervousness':    'nervousness',
    'confusion':      'nervousness',   # merge confusion → nervousness
    'fear':           'fear',
    'anger':          'anger',
    'annoyance':      'anger',         # merge annoyance → anger
    'disapproval':    'anger',         # merge disapproval → anger
    'disappointment': 'disappointment',
    'remorse':        'remorse',
    'embarrassment':  'embarrassment',
    'disgust':        'disgust',

    # Neutral
    'neutral':        'neutral',
    'realization':    'neutral',
    'curiosity':      'neutral',
    'surprise':       'neutral',
}

# ── Final 11 emotion columns ──────────────────────────────────────────────────
EMOTION_COLS = [
    'joy',                                          # positive
    'sadness', 'nervousness', 'fear', 'anger',      # negative
    'disappointment', 'remorse', 'embarrassment',   # negative
    'disgust', 'neutral'                            # negative + neutral
]

print(f"Target emotions ({len(EMOTION_COLS)}): {EMOTION_COLS}")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
print("\nLoading GoEmotions full dataset...")
df = pd.read_csv('go_emotions_full.csv')
print(f"Loaded: {df.shape[0]:,} rows")

# ── PARSE LABELS ──────────────────────────────────────────────────────────────
def parse_labels(label_str):
    """Converts '[8, 20]' string → list of ints [8, 20]"""
    try:
        return ast.literal_eval(label_str)
    except:
        return []

df['label_list'] = df['labels'].apply(parse_labels)

# ── BUILD EMOTION COLUMNS ─────────────────────────────────────────────────────
print("Building emotion columns...")
for col in EMOTION_COLS:
    df[col] = 0

for idx, row in df.iterrows():
    for label_id in row['label_list']:
        if label_id < len(GO_EMOTIONS_LABELS):
            go_emotion  = GO_EMOTIONS_LABELS[label_id]
            our_emotion = EMOTION_MAP.get(go_emotion)
            if our_emotion and our_emotion in EMOTION_COLS:
                df.at[idx, our_emotion] = 1

# ── REMOVE ROWS WITH NO LABEL ─────────────────────────────────────────────────
mask = df[EMOTION_COLS].sum(axis=1) > 0
df   = df[mask].reset_index(drop=True)
print(f"After removing unlabeled rows: {df.shape[0]:,} rows")

# ── CLEAN TEXT ────────────────────────────────────────────────────────────────
def clean_text(text):
    text = str(text)
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s\'\"!?.,]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['text'] = df['text'].apply(clean_text)

# ── REMOVE VERY SHORT TEXTS ───────────────────────────────────────────────────
df = df[df['text'].str.len() >= 3].reset_index(drop=True)
print(f"After removing short texts: {df.shape[0]:,} rows")

# ── KEEP ONLY NEEDED COLUMNS ──────────────────────────────────────────────────
df = df[['text'] + EMOTION_COLS]

# ── TRAIN / VALIDATION / TEST SPLIT ──────────────────────────────────────────
df['dominant_emotion'] = df[EMOTION_COLS].idxmax(axis=1)

train_df, temp_df = train_test_split(
    df, test_size=0.2, random_state=42,
    stratify=df['dominant_emotion']
)
val_df, test_df = train_test_split(
    temp_df, test_size=0.5, random_state=42,
    stratify=temp_df['dominant_emotion']
)

print(f"\nSplit sizes:")
print(f"  Train      : {len(train_df):,}")
print(f"  Validation : {len(val_df):,}")
print(f"  Test       : {len(test_df):,}")

# ── SAVE SPLITS ───────────────────────────────────────────────────────────────
train_df.to_csv('train.csv', index=False)
val_df.to_csv('val.csv',     index=False)
test_df.to_csv('test.csv',   index=False)
print("\n Saved: train.csv | val.csv | test.csv")

# ── EMOTION DISTRIBUTION ──────────────────────────────────────────────────────
print("\nEmotion distribution in training set:")
counts = train_df[EMOTION_COLS].sum().sort_values(ascending=False)
for emotion, count in counts.items():
    bar = "█" * int(count / 100)
    print(f"  {emotion:<15} {bar} {count:,}")