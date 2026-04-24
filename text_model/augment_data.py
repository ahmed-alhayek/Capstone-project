"""
Data Augmentation Script
AI Mental Health Companion | Capstone Project
=============================================
Generates synthetic sentences for all rare emotions using:
1. Claude API — generates diverse new sentences
2. Synonym replacement — multiplies existing sentences

Target: 5,000 samples per emotion

📁 File location: mental_health_companion/text_model/augment_data.py
"""

import os
import pandas as pd
import numpy as np
import anthropic
import nltk
import random
from dotenv import load_dotenv

nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
from nltk.corpus import wordnet

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
TARGET_SAMPLES = 5000

EMOTION_COLS = [
    'joy', 'sadness', 'nervousness', 'fear', 'anger',
    'disappointment', 'remorse', 'embarrassment', 'disgust', 'neutral'
]

# Emotions that need augmentation with their descriptions
RARE_EMOTIONS = {
    'nervousness': {
        'description': 'feeling anxious, worried, stressed, uneasy or nervous',
        'examples': [
            "I can't stop worrying about tomorrow",
            "My heart is racing and I feel so anxious",
            "I'm stressed out about everything lately"
        ]
    },
    'sadness': {
        'description': 'feeling sad, unhappy, depressed, melancholy or down',
        'examples': [
            "I feel so empty and lost inside",
            "Everything feels heavy and meaningless",
            "I just want to cry but I don't know why"
        ]
    },
    'disappointment': {
        'description': 'feeling disappointed, let down, discouraged or disillusioned',
        'examples': [
            "I expected so much more from this situation",
            "I feel let down by people I trusted",
            "Things didn't turn out the way I hoped"
        ]
    },
    'disgust': {
        'description': 'feeling disgusted, revolted, repulsed or appalled',
        'examples': [
            "That behavior is completely unacceptable",
            "I'm repulsed by what I witnessed",
            "This makes me sick to my stomach"
        ]
    },
    'fear': {
        'description': 'feeling scared, afraid, terrified or fearful',
        'examples': [
            "I'm terrified of what might happen next",
            "I can't sleep because I'm so scared",
            "The thought of it fills me with dread"
        ]
    },
    'remorse': {
        'description': 'feeling remorseful, guilty, regretful or sorry',
        'examples': [
            "I deeply regret what I did to them",
            "I can't forgive myself for my actions",
            "I wish I could take back what I said"
        ]
    },
    'embarrassment': {
        'description': 'feeling embarrassed, ashamed, humiliated or mortified',
        'examples': [
            "I wanted to disappear after what happened",
            "I can't believe I made such a fool of myself",
            "My face turned red with shame"
        ]
    }
}


# ── SYNONYM REPLACEMENT ───────────────────────────────────────────────────────

def get_synonyms(word):
    """Gets synonyms for a word using WordNet."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace('_', ' ')
            if synonym != word and len(synonym) > 2:
                synonyms.add(synonym)
    return list(synonyms)


def synonym_replacement(sentence, n_replacements=2):
    """
    Replaces n random words in a sentence with their synonyms.
    Creates a new natural-sounding sentence.
    """
    words  = sentence.split()
    result = words.copy()

    # Find words that have synonyms
    replaceable = []
    for i, word in enumerate(words):
        clean_word = word.lower().strip('.,!?')
        syns = get_synonyms(clean_word)
        if syns:
            replaceable.append((i, syns))

    # Randomly replace up to n words
    random.shuffle(replaceable)
    for i, (idx, syns) in enumerate(replaceable[:n_replacements]):
        result[idx] = random.choice(syns)

    new_sentence = ' '.join(result)
    return new_sentence if new_sentence != sentence else None


def augment_with_synonyms(sentences, target_count, current_count):
    """
    Generates new sentences using synonym replacement until
    we reach the target count.
    """
    augmented = []
    needed    = target_count - current_count

    while len(augmented) < needed:
        sentence = random.choice(sentences)
        new_sentence = synonym_replacement(sentence)
        if new_sentence and new_sentence not in augmented:
            augmented.append(new_sentence)

    return augmented[:needed]


# ── CLAUDE API GENERATION ─────────────────────────────────────────────────────

def generate_sentences_with_claude(emotion, description, examples, count=100):
    """
    Uses Claude API to generate diverse new sentences for a given emotion.
    Generates in batches of 50 to avoid token limits.
    """
    print(f"  🤖 Generating {count} sentences for '{emotion}' using Claude...")
    all_sentences = []
    batches       = count // 50

    for batch in range(batches):
        prompt = f"""Generate exactly 50 diverse, natural sentences expressing {description}.

Requirements:
- Each sentence must clearly express {emotion}
- Vary the sentence structure, length and vocabulary
- Use first person perspective (I, me, my)
- Make them sound like real people talking
- Do NOT number them
- Each sentence on a new line
- Do NOT repeat similar sentences
- Mix short and long sentences
- Use different contexts (work, relationships, school, life)

Examples of the style:
{chr(10).join(examples)}

Generate 50 NEW sentences (different from examples above):"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response into individual sentences
        text      = response.content[0].text
        sentences = [
            s.strip()
            for s in text.strip().split('\n')
            if s.strip() and len(s.strip()) > 10
        ]
        all_sentences.extend(sentences)
        print(f"    Batch {batch+1}/{batches} done — {len(sentences)} sentences generated")

    return all_sentences[:count]


# ── MAIN AUGMENTATION PIPELINE ────────────────────────────────────────────────

def augment_dataset():
    """
    Main function that augments the training dataset for all rare emotions.
    """
    print("=" * 60)
    print("DATA AUGMENTATION PIPELINE")
    print("=" * 60)

    # Load existing training data
    print("\nLoading train.csv...")
    train_df = pd.read_csv('train.csv')
    print(f"Original training samples: {len(train_df):,}")

    # Show current distribution
    print("\nCurrent emotion distribution:")
    for emotion in EMOTION_COLS:
        count = train_df[emotion].sum()
        print(f"  {emotion:<15} {count:,}")

    all_new_rows = []

    # Process each rare emotion
    for emotion, config in RARE_EMOTIONS.items():
        print(f"\n{'='*60}")
        print(f"Processing: {emotion.upper()}")
        print(f"{'='*60}")

        current_count = int(train_df[emotion].sum())
        needed        = TARGET_SAMPLES - current_count

        print(f"  Current: {current_count:,} | Target: {TARGET_SAMPLES:,} | Need: {needed:,}")

        if needed <= 0:
            print(f"  ✅ Already at target!")
            continue

        # Step 1: Generate sentences with Claude
        claude_count  = min(needed, 200)
        claude_sentences = generate_sentences_with_claude(
            emotion,
            config['description'],
            config['examples'],
            count=claude_count
        )
        print(f"  ✅ Claude generated: {len(claude_sentences)} sentences")

        # Step 2: Synonym replacement to fill remaining gap
        all_source    = claude_sentences + config['examples']
        synonym_count = needed - len(claude_sentences)

        if synonym_count > 0:
            print(f"  🔄 Generating {synonym_count} more via synonym replacement...")
            synonym_sentences = augment_with_synonyms(
                all_source,
                target_count=needed,
                current_count=len(claude_sentences)
            )
            all_sentences = claude_sentences + synonym_sentences
        else:
            all_sentences = claude_sentences[:needed]

        print(f"  ✅ Total new sentences for {emotion}: {len(all_sentences)}")

        # Step 3: Create new rows for training data
        for sentence in all_sentences:
            if not sentence or len(sentence) < 5:
                continue

            new_row          = {col: 0 for col in EMOTION_COLS}
            new_row['text']  = sentence
            new_row[emotion] = 1
            all_new_rows.append(new_row)

    # Add all new rows to training data
    if all_new_rows:
        new_df   = pd.DataFrame(all_new_rows)
        train_df = pd.concat([train_df, new_df], ignore_index=True)

        # Shuffle the dataset
        train_df = train_df.sample(frac=1, random_state=42).reset_index(drop=True)

        # Save augmented training data
        train_df.to_csv('train.csv', index=False)
        print(f"\n{'='*60}")
        print(f"✅ AUGMENTATION COMPLETE")
        print(f"{'='*60}")
        print(f"Original samples : {len(train_df) - len(all_new_rows):,}")
        print(f"New samples added: {len(all_new_rows):,}")
        print(f"Total samples    : {len(train_df):,}")

        print("\nNew emotion distribution:")
        for emotion in EMOTION_COLS:
            count = train_df[emotion].sum()
            bar   = "█" * int(count / 200)
            print(f"  {emotion:<15} {bar} {count:,}")
    else:
        print("\n✅ All emotions already at target!")


if __name__ == "__main__":
    augment_dataset()