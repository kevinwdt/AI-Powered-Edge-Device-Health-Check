# from ai_Model import AIModel

# # 1. Create AI model instance (loads model.pkl automatically)
# ai = AIModel(model_path="model.pkl")
# ai.start()

# # 2. Fake incoming MQTT / device metrics
# test_metrics = {
#     "voltagebank1": 46.5,
#     "currentbank1": 20.2,
#     "remainingcapacitybank1": 40.0,
#     "stateofhealthbank1": 68.0,
#     "temperature_max": 88.5,
#     "cpuusage": 0.56,
#     "signal_strength": 2
# }

# # 3. Predict
# status, reason = ai.predict_status(test_metrics)

# print("Predicted status:", status)
# print("Reason:", reason)

# # test_ai_model.py V2
# from ai_Model import AIModel

# if __name__ == "__main__":
#     ai = AIModel(model_path="model.pkl")
#     ai.start()  # loads model.pkl

#     # Example test sample (you can change these numbers)
#     sample = {
#         "totalmemory": 1873.92,
#         "storagetotal": 4249.6,
#         "used_memory": 1200.0,    # high-ish
#         "used_storage": 3900.0,   # high-ish
#         "cpuusage": 72.0,
#         "temperature": 68.0
#     }

#     status, reason = ai.predict_status(sample)
#     print("Predicted:", status, "| Reason:", reason)


# test_ai_model.py
from ai_Model import AIModel

FEATURE_KEYS = ["used_memory", "used_storage", "cpuusage", "temperature"]

if __name__ == "__main__":
    ai = AIModel(model_path="model.pkl")
    ai.start()

    # Example: normal
    status, reason = ai.predict_status({
        "used_memory": 1100,
        "used_storage": 3600,
        "cpuusage": 35,
        "temperature": 36
    })
    print("Case1:", status, "|", reason)

    # Example: critical hot
    status, reason = ai.predict_status({
        "used_memory": 900,
        "used_storage": 3400,
        "cpuusage": 55,
        "temperature": 92
    })
    print("Case2:", status, "|", reason)

    # Example: extreme low temp
    status, reason = ai.predict_status({
        "used_memory": 950,
        "used_storage": 3200,
        "cpuusage": 20,
        "temperature": -8
    })
    print("Case3:", status, "|", reason)
