import math

import numpy as np


FEATURE_NAMES = [
    "visual_score",
    "content_score",
    "template_score",
    "ocr_confidence",
    "ela_anomaly_score",
    "metadata_suspicious",
    "missing_field_count",
    "word_count",
]
LABELS = ["forged", "review", "authentic"]

_TRAINING_ROWS = [
    ([88, 92, 96, 90, 3, 0, 0, 68], "authentic"),
    ([84, 88, 91, 86, 8, 0, 0, 55], "authentic"),
    ([79, 82, 85, 78, 12, 0, 1, 43], "authentic"),
    ([72, 78, 80, 64, 20, 0, 1, 38], "review"),
    ([67, 70, 76, 58, 26, 0, 1, 31], "review"),
    ([76, 62, 64, 55, 18, 0, 2, 28], "review"),
    ([58, 35, 30, 40, 55, 1, 4, 14], "forged"),
    ([42, 8, 0, 18, 88, 1, 5, 4], "forged"),
    ([34, 18, 12, 24, 74, 1, 5, 9], "forged"),
    ([65, 25, 20, 35, 62, 1, 4, 12], "forged"),
]

_classifier = None


def get_certificate_classifier() -> dict:
    global _classifier
    if _classifier is None:
        _classifier = _train_classifier()
    return _classifier


def classify_certificate(features: dict) -> dict:
    model = get_certificate_classifier()
    vector = _feature_vector(features)
    scaled = (vector - model["mean"]) / model["std"]
    logits = scaled @ model["weights"] + model["bias"]
    probabilities = _softmax(logits)
    prediction_index = int(np.argmax(probabilities))
    prediction = LABELS[prediction_index]
    authentic_probability = float(probabilities[LABELS.index("authentic")])

    return {
        "ml_model": "VerifyNGCustomSoftmaxClassifier",
        "ml_prediction": prediction,
        "ml_authenticity_probability": round(authentic_probability, 3),
        "ml_probabilities": {
            LABELS[i]: round(float(probabilities[i]), 3)
            for i in range(len(LABELS))
        },
        "ml_features_used": FEATURE_NAMES,
        "trained_cases": model["training_cases"],
    }


def _train_classifier() -> dict:
    x = np.array([row for row, _label in _TRAINING_ROWS], dtype=float)
    y = np.array([LABELS.index(label) for _row, label in _TRAINING_ROWS], dtype=int)
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std[std == 0] = 1
    x_scaled = (x - mean) / std

    weights = np.zeros((len(FEATURE_NAMES), len(LABELS)), dtype=float)
    bias = np.zeros(len(LABELS), dtype=float)
    learning_rate = 0.18

    for _ in range(900):
        logits = x_scaled @ weights + bias
        probabilities = _softmax_matrix(logits)
        targets = np.eye(len(LABELS))[y]
        error = probabilities - targets
        weights -= learning_rate * ((x_scaled.T @ error) / len(x_scaled))
        bias -= learning_rate * error.mean(axis=0)

    return {
        "trained": True,
        "model_type": "custom_numpy_softmax_regression",
        "feature_names": FEATURE_NAMES,
        "labels": LABELS,
        "training_cases": len(_TRAINING_ROWS),
        "mean": mean,
        "std": std,
        "weights": weights,
        "bias": bias,
    }


def _feature_vector(features: dict) -> np.ndarray:
    return np.array([
        float(features.get(name, 0) or 0)
        for name in FEATURE_NAMES
    ], dtype=float)


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits)
    exps = np.exp(shifted)
    total = exps.sum()
    if math.isclose(float(total), 0.0):
        return np.ones(len(logits)) / len(logits)
    return exps / total


def _softmax_matrix(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exps = np.exp(shifted)
    return exps / exps.sum(axis=1, keepdims=True)
