import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
from predict_v2 import predict_emotion, EMOTIONS

data = np.load(r"C:\Users\Ahmad Alhayek\audio_cache_v2\test.npz")
X_test, y_true = data["waveforms"], data["labels"]

print(f"Predicting on {len(X_test)} test samples...")

y_pred = []
for i, waveform in enumerate(X_test):
    result = predict_emotion(waveform)
    if i == 0:
        print("First result looks like:", result)

    if "dominant" in result:
        pred = EMOTIONS.index(result["dominant"])
    elif "emotion" in result:
        pred = EMOTIONS.index(result["emotion"])
    elif "predicted_class" in result:
        pred = int(result["predicted_class"])
    elif "probabilities" in result:
        pred = int(np.argmax(result["probabilities"]))
    else:
        # last resort: find any emotion-name value
        pred = next(EMOTIONS.index(v) for v in result.values()
                    if isinstance(v, str) and v in EMOTIONS)
    y_pred.append(pred)

    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(X_test)}")

y_pred = np.array(y_pred)

print("\n=== Classification Report ===")
print(classification_report(y_true, y_pred, target_names=EMOTIONS, digits=3))

cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=EMOTIONS, yticklabels=EMOTIONS, cbar=False)
plt.title("HuBERT audio emotion, test confusion matrix")
plt.xlabel("Predicted"); plt.ylabel("True")
plt.tight_layout()
plt.savefig("confusion_matrix_hubert.png", dpi=200)
print("\nSaved confusion_matrix_hubert.png")