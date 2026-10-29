"""Reviewed deterministic toy ML experiment executed only inside the sandbox image.

It intentionally uses only the Python standard library. The API never accepts
alternate source code for this template.
"""

from __future__ import annotations

import json
import math
import base64
import os
import random


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(min(value, 35.0), -35.0)))


def build_dataset(seed: int, size: int = 260) -> tuple[list[tuple[float, float]], list[int]]:
    generator = random.Random(seed)
    features: list[tuple[float, float]] = []
    labels: list[int] = []
    for _ in range(size):
        first = generator.gauss(0.0, 1.0)
        second = generator.gauss(0.0, 1.0)
        noisy_logit = 1.1 * first - 0.8 * second + generator.gauss(0.0, 0.75)
        features.append((first, second))
        labels.append(1 if noisy_logit >= 0 else 0)
    return features, labels


def train_logistic_regression(
    features: list[tuple[float, float]], labels: list[int], iterations: int, learning_rate: float = 0.12
) -> tuple[float, float, float]:
    weight_one = weight_two = bias = 0.0
    size = len(features)
    for _ in range(iterations):
        gradient_one = gradient_two = gradient_bias = 0.0
        for (first, second), label in zip(features, labels, strict=True):
            error = sigmoid(weight_one * first + weight_two * second + bias) - label
            gradient_one += error * first
            gradient_two += error * second
            gradient_bias += error
        weight_one -= learning_rate * gradient_one / size
        weight_two -= learning_rate * gradient_two / size
        bias -= learning_rate * gradient_bias / size
    return weight_one, weight_two, bias


def accuracy(
    weights: tuple[float, float, float], features: list[tuple[float, float]], labels: list[int]
) -> float:
    weight_one, weight_two, bias = weights
    correct = 0
    for (first, second), label in zip(features, labels, strict=True):
        prediction = int(sigmoid(weight_one * first + weight_two * second + bias) >= 0.5)
        correct += prediction == label
    return correct / len(labels)


def evaluate_trial(seed: int, baseline_iterations: int, treatment_iterations: int) -> tuple[float, float]:
    features, labels = build_dataset(seed)
    train_features, test_features = features[:180], features[180:]
    train_labels, test_labels = labels[:180], labels[180:]
    baseline = train_logistic_regression(train_features, train_labels, baseline_iterations)
    treatment = train_logistic_regression(train_features, train_labels, treatment_iterations)
    return accuracy(baseline, test_features, test_labels), accuracy(treatment, test_features, test_labels)


def main() -> None:
    encoded_configuration = os.environ["RESEARCH_EXPERIMENT_CONFIG_B64"]
    configuration = json.loads(base64.b64decode(encoded_configuration).decode("utf-8"))
    baseline_iterations = int(configuration["baseline_iterations"])
    treatment_iterations = int(configuration["treatment_iterations"])
    trial_count = int(configuration["trial_count"])
    random_seed = int(configuration["random_seed"])
    if not (0 < baseline_iterations < treatment_iterations <= 2_000 and 3 <= trial_count <= 100):
        raise ValueError("The reviewed template received an invalid configuration.")

    baseline_scores: list[float] = []
    treatment_scores: list[float] = []
    for trial_index in range(trial_count):
        baseline, treatment = evaluate_trial(random_seed + trial_index, baseline_iterations, treatment_iterations)
        baseline_scores.append(baseline)
        treatment_scores.append(treatment)

    output = {
        "template_id": "toy_logistic_regression_v1",
        "template_revision": "2026-08-21",
        "baseline_scores": baseline_scores,
        "treatment_scores": treatment_scores,
        "dataset": {"name": "deterministic_synthetic_binary_v1", "version": "1.0"},
        "algorithm": "handwritten_batch_logistic_regression",
    }
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
