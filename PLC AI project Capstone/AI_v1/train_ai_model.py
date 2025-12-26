# train_ai_model.py
# Generate data to train Ai model

from ai_Model import AIModel
import random
import numpy as np

# --- Step 1. Generate synthetic MQTT-like dataset ---
def generate_synthetic_training_data(n_samples=500):
    data = []
    for _ in range(n_samples):
        device_key = random.choice(["bms-1", "bms-2", "rectifier-1", "env-1"])

        voltagebank1 = random.uniform(44.0, 52.0)
        currentbank1 = random.uniform(0.0, 30.0)
        remainingcapacitybank1 = random.uniform(10, 100)
        stateofhealthbank1 = random.uniform(60, 100)
        temperature_max = random.uniform(20.0, 95.0)
        cpuusage = random.uniform(0.05, 0.98)
        signal_strength = random.randint(0, 4)

        # Label logic: mimic realistic fault triggers
        if temperature_max > 85.0 or voltagebank1 < 45.0 or cpuusage > 0.95:
            label = "Critical"
        elif temperature_max > 70.0 or stateofhealthbank1 < 75.0 or signal_strength <= 1:
            label = "Warning"
        else:
            label = "Healthy"

        data.append({
            "device_key": device_key,
            "voltagebank1": voltagebank1,
            "currentbank1": currentbank1,
            "remainingcapacitybank1": remainingcapacitybank1,
            "stateofhealthbank1": stateofhealthbank1,
            "temperature_max": temperature_max,
            "cpuusage": cpuusage,
            "signal_strength": signal_strength,
            "label": label
        })
    return data


# --- Step 2. Train the model ---
if __name__ == "__main__":
    rows = generate_synthetic_training_data(500)

    FEATURE_KEYS = [
        "voltagebank1",
        "currentbank1",
        "remainingcapacitybank1",
        "stateofhealthbank1",
        "temperature_max",
        "cpuusage",
        "signal_strength"
    ]
    LABEL_KEY = "label"

    ai = AIModel(model_path="model.pkl")

    metrics = ai.train_from_rows(
        rows,
        feature_keys=FEATURE_KEYS,
        label_key=LABEL_KEY
    )

    print("✅ Training complete!")
    print("Accuracy:", metrics["accuracy"])
    print("Feature importance:", metrics["feature_importance"])
    print(metrics["classification_report"])

    # --- Step 3. Test prediction on new MQTT message ---
    test_metrics = {
        "voltagebank1": 46.5,
        "currentbank1": 20.2,
        "remainingcapacitybank1": 40.0,
        "stateofhealthbank1": 68.0,
        "temperature_max": 88.5,
        "cpuusage": 0.56,
        "signal_strength": 2
    }

    status, reason = ai.predict_status(test_metrics)
    print(f"\nPredicted Health: {status} | Reason: {reason}")
