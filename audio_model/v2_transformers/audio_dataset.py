"""
PyTorch Dataset for cached preprocessed audio (created by cache_audio.py).
Everything is loaded into RAM at __init__, so __getitem__ is just an array slice.
"""

import numpy as np
import torch
from torch.utils.data import Dataset


class CachedAudioEmotionDataset(Dataset):
    def __init__(self, npz_path):
        data = np.load(npz_path)
        self.waveforms = data["waveforms"]   # (N, max_samples) float32
        self.labels = data["labels"]          # (N,) int64
        print(f"  Loaded {len(self)} samples from {npz_path.name}")

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.waveforms[idx], int(self.labels[idx])


def make_collate_fn(feature_extractor):
    def collate(batch):
        audios = [b[0] for b in batch]
        labels = torch.tensor([b[1] for b in batch], dtype=torch.long)
        inputs = feature_extractor(
            audios,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
        )
        return inputs.input_values, labels
    return collate