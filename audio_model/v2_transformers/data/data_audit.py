"""
Data audit: validates the unified loader.

Run from anywhere; resolves audio_model/ relative to this file.
Prints class distribution per split, dataset breakdown, and checks
that no actor appears in more than one split.
"""

from collections import Counter
from pathlib import Path
import sys

# Allow running this file directly from anywhere
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from unified_loader import (  # noqa: E402
    load_all,
    split_samples,
    EMOTIONS,
    VAL_ACTORS,
    TEST_ACTORS,
)

# v2_transformers/data/data_audit.py  ->  audio_model/
AUDIO_ROOT = HERE.parent.parent


def fmt_dist(samples, title):
    print(f"\n=== {title}  (n={len(samples)}) ===")
    if not samples:
        print("  (empty)")
        return
    c = Counter(s.label_name for s in samples)
    max_count = max(c.values())
    for lbl_id in sorted(EMOTIONS.keys()):
        name = EMOTIONS[lbl_id]
        n = c.get(name, 0)
        bar = "#" * int(n / max_count * 30) if max_count else ""
        print(f"  {name:<11} {n:>5}  {bar}")
    by_ds = Counter(s.dataset for s in samples)
    print(f"  by dataset: {dict(by_ds)}")


def main():
    print(f"Looking for datasets under: {AUDIO_ROOT}")
    print(f"  RAVDESS exists? {(AUDIO_ROOT/'RAVDESS').exists()}")
    print(f"  TESS    exists? {(AUDIO_ROOT/'TESS').exists()}")
    print(f"  SAVEE   exists? {(AUDIO_ROOT/'SAVEE').exists()}")

    samples = load_all(AUDIO_ROOT)
    print(f"\nTotal samples loaded: {len(samples)}")
    if len(samples) == 0:
        print("ERROR: no samples loaded. Check folder structure.")
        return

    fmt_dist(samples, "ALL")

    train, val, test = split_samples(samples)
    fmt_dist(train, "TRAIN")
    fmt_dist(val, "VAL")
    fmt_dist(test, "TEST")

    # Actor leakage check
    train_actors = sorted({s.actor_id for s in train})
    val_actors = sorted({s.actor_id for s in val})
    test_actors = sorted({s.actor_id for s in test})

    print("\n=== Actor leakage check ===")
    print(f"  Train actors: {train_actors}")
    print(f"  Val actors:   {val_actors}")
    print(f"  Test actors:  {test_actors}")
    print(f"  (configured VAL_ACTORS={sorted(VAL_ACTORS)}, "
          f"TEST_ACTORS={sorted(TEST_ACTORS)})")

    leak_tv = set(train_actors) & set(val_actors)
    leak_tt = set(train_actors) & set(test_actors)
    leak_vt = set(val_actors) & set(test_actors)
    if leak_tv or leak_tt or leak_vt:
        print(f"  !!! LEAKAGE DETECTED: "
              f"train&val={leak_tv} train&test={leak_tt} val&test={leak_vt}")
        sys.exit(1)
    else:
        print("  OK - no actor leakage between splits")

    # Sanity: every dataset has samples in train at minimum
    train_ds = {s.dataset for s in train}
    for ds in ("ravdess", "tess", "savee"):
        if ds not in train_ds:
            print(f"  !!! WARNING: '{ds}' missing from training set")


if __name__ == "__main__":
    main()