
from __future__ import annotations
import random
import numpy as np

from ai_Model import AIModel

RNG = np.random.default_rng(42)

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def maybe_nan(x, p=0.08):
    # simulate nulls/missing
    return np.nan if RNG.random() < p else x

def generate_synthetic_training_data(n_samples: int = 3000) -> list[dict]:
    """
    Generates labeled training data based on your real metric patterns:
    - totalmemory ~ 1873.92
    - storagetotal ~ 4249.6
    - remainingmemory typically ~ 500-950
    - remainingstorage typically ~ 250-850
    - cpuusage typically 20-60 with spikes
    - temperature typically 25-60 with extremes
    Includes:
    - cold extremes
    - hot spikes
    - sensor glitches
    - missing values
    - correlated behavior
    """
    rows = []

    TOTAL_MEM = 1873.92
    TOTAL_STORAGE = 4249.6

    for i in range(n_samples):
        # --- base (normal) behavior ---
        remainingmemory = float(clamp(RNG.normal(750, 140), 200, 1200))
        remainingstorage = float(clamp(RNG.normal(600, 120), 50, 1100))

        used_memory = TOTAL_MEM - remainingmemory
        used_storage = TOTAL_STORAGE - remainingstorage

        cpuusage = float(clamp(RNG.normal(40, 12), 0, 100))
        temperature = float(clamp(RNG.normal(42, 8), -5, 95))

        # --- correlated effects (high CPU raises temp + memory a bit) ---
        if cpuusage > 70:
            temperature = clamp(temperature + RNG.normal(8, 3), -10, 110)
            used_memory = clamp(used_memory + RNG.normal(80, 30), 0, TOTAL_MEM)

        # --- EVENT: storage growth over time (some devices drift upward) ---
        if RNG.random() < 0.15:
            used_storage = clamp(used_storage + RNG.normal(250, 120), 0, TOTAL_STORAGE)

        # --- EVENT: memory leak (slow rise) ---
        if RNG.random() < 0.12:
            used_memory = clamp(used_memory + RNG.normal(220, 90), 0, TOTAL_MEM)

        # --- EVENT: extremely LOW temperature (cold site / environment) ---
        if RNG.random() < 0.05:
            temperature = float(clamp(RNG.normal(2, 4), -15, 12))

        # --- EVENT: extremely HIGH temperature (overheat) ---
        if RNG.random() < 0.06:
            temperature = float(clamp(RNG.normal(86, 6), 70, 110))
            cpuusage = float(clamp(cpuusage + RNG.normal(20, 10), 0, 100))

        # --- EVENT: sudden spike (transient anomaly) ---
        if RNG.random() < 0.08:
            cpuusage = float(clamp(cpuusage + RNG.normal(35, 15), 0, 100))
            temperature = float(clamp(temperature + RNG.normal(12, 5), -15, 110))

        # --- EVENT: sensor glitch / impossible values ---
        # (helps you test robustness + data cleaning)
        if RNG.random() < 0.02:
            temperature = float(RNG.choice([-999, 999, -50, 150]))
        if RNG.random() < 0.02:
            cpuusage = float(RNG.choice([-10, 150, 999]))

        # --- EVENT: missing values / NULLs ---
        used_memory = maybe_nan(used_memory, p=0.07)
        used_storage = maybe_nan(used_storage, p=0.07)
        cpuusage = maybe_nan(cpuusage, p=0.05)
        temperature = maybe_nan(temperature, p=0.06)

        # --- labeling rules (realistic + includes low temp and glitches) ---
        label = "Healthy"

        # Sensor out-of-range => Critical (or you can make a separate "Invalid" class later)
        if (isinstance(temperature, float) and not np.isnan(temperature) and (temperature < -10 or temperature > 120)) \
           or (isinstance(cpuusage, float) and not np.isnan(cpuusage) and (cpuusage < 0 or cpuusage > 100)):
            label = "Critical"

        # If missing too many key metrics, treat as Warning (data quality issue)
        missing_count = sum([
            1 if (isinstance(used_memory, float) and np.isnan(used_memory)) else 0,
            1 if (isinstance(used_storage, float) and np.isnan(used_storage)) else 0,
            1 if (isinstance(cpuusage, float) and np.isnan(cpuusage)) else 0,
            1 if (isinstance(temperature, float) and np.isnan(temperature)) else 0,
        ])
        if missing_count >= 2:
            label = "Warning"

        # Normal thresholds (only apply if not NaN)
        if label != "Critical":
            t = temperature if (not (isinstance(temperature, float) and np.isnan(temperature))) else None
            c = cpuusage if (not (isinstance(cpuusage, float) and np.isnan(cpuusage))) else None
            um = used_memory if (not (isinstance(used_memory, float) and np.isnan(used_memory))) else None
            us = used_storage if (not (isinstance(used_storage, float) and np.isnan(used_storage))) else None

            # Critical
            if (t is not None and (t > 80 or t < 5)) \
               or (c is not None and c > 90) \
               or (um is not None and um > 1600) \
               or (us is not None and us > 3900):
                label = "Critical"
            # Warning
            elif (t is not None and (65 <= t <= 80 or 5 <= t < 10)) \
                 or (c is not None and 60 <= c <= 90) \
                 or (um is not None and 1350 <= um <= 1600) \
                 or (us is not None and 3400 <= us <= 3900):
                label = "Warning"
            else:
                label = "Healthy"

        rows.append({
            "used_memory": used_memory,
            "used_storage": used_storage,
            "cpuusage": cpuusage,
            "temperature": temperature,
            "label": label
        })

    return rows


if __name__ == "__main__":
    # 1) Generate realistic dataset
    rows = generate_synthetic_training_data(n_samples=4000)

    # 2) Train model
    FEATURE_KEYS = ["used_memory", "used_storage", "cpuusage", "temperature"]
    LABEL_KEY = "label"

    ai = AIModel(model_path="model.pkl")
    metrics = ai.train_from_rows(
        rows,
        feature_keys=FEATURE_KEYS,
        label_key=LABEL_KEY,
        test_size=0.3,
        n_estimators=400,
        max_depth=None
    )

    print("\n✅ Training complete!")
    print("Accuracy:", metrics["accuracy"])
    print("Feature importance:", metrics["feature_importance"])
    print(metrics["classification_report"])

    # 3) Quick sanity-test predictions
    tests = [
        {"used_memory": 900, "used_storage": 3400, "cpuusage": 45, "temperature": 40},
        {"used_memory": 1700, "used_storage": 3500, "cpuusage": 55, "temperature": 50},
        {"used_memory": 1400, "used_storage": 4100, "cpuusage": 88, "temperature": 83},
        {"used_memory": 800, "used_storage": 3200, "cpuusage": 20, "temperature": 2},
        {"used_memory": 900, "used_storage": 3300, "cpuusage": 999, "temperature": 45},   # glitch
        {"used_memory": np.nan, "used_storage": np.nan, "cpuusage": 55, "temperature": 40}, # missing
    ]

    ai.start()  # loads model.pkl if saved
    for t in tests:
        status, reason = ai.predict_status(t)
        print(f"Test: {t} -> {status} | {reason}")
