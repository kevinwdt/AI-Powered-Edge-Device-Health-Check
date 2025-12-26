from ai_Model import AIModel

# 1. Create AI model instance (loads model.pkl automatically)
ai = AIModel(model_path="model.pkl")
ai.start()

# 2. Fake incoming MQTT / device metrics
test_metrics = {
    "voltagebank1": 46.5,
    "currentbank1": 20.2,
    "remainingcapacitybank1": 40.0,
    "stateofhealthbank1": 68.0,
    "temperature_max": 88.5,
    "cpuusage": 0.56,
    "signal_strength": 2
}

# 3. Predict
status, reason = ai.predict_status(test_metrics)

print("Predicted status:", status)
print("Reason:", reason)
