# Generate graphs from Diagnostic_Data.csv
# Use Graph to analyze treds in memory, CPU, storage, temperature
# Includes four separate plots and one combined plot
# Kevin Wang


# import pandas as pd
import matplotlib.pyplot as plt

# ------- LOAD CSV -------
df = pd.read_csv("Diagnostic_Data/Diagnostic_Data.csv", low_memory=False)

# ------- CLEAN DATA (remove null rows) -------
df = df.dropna(subset=[
    "totalmemory", "remainingmemory",
    "cpuusage", "temperature",
    "storagetotal", "remainingstorage",
    "unixtime"
])

# ------- COMPUTE NEW COLUMNS -------
df["used_memory"] = df["totalmemory"] - df["remainingmemory"]
df["used_storage"] = df["storagetotal"] - df["remainingstorage"]

# ------- CONVERT TIMESTAMP (NOT UNIX!) -------
df["timestamp"] = pd.to_datetime(df["unixtime"], errors="coerce")

# Remove any bad timestamps
df = df.dropna(subset=["timestamp"])

# ------- SORT BY TIME -------
df = df.sort_values("timestamp")

# ------- PLOT #1: Used Memory -------
plt.figure(figsize=(10,4))
plt.scatter(df["timestamp"], df["used_memory"], s=10)
plt.title("Used Memory vs Time")
plt.xlabel("Time")
plt.ylabel("Used Memory")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# ------- PLOT #2: CPU Usage -------
plt.figure(figsize=(10,4))
plt.scatter(df["timestamp"], df["cpuusage"], s=10)
plt.title("CPU Usage vs Time")
plt.xlabel("Time")
plt.ylabel("CPU Usage")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# ------- PLOT #3: Used Storage -------
plt.figure(figsize=(10,4))
plt.scatter(df["timestamp"], df["used_storage"], s=10)
plt.title("Used Storage vs Time")
plt.xlabel("Time")
plt.ylabel("Used Storage")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# ------- PLOT #4: Temperature -------
plt.figure(figsize=(10,4))
plt.scatter(df["timestamp"], df["temperature"], s=10)
plt.title("Temperature vs Time")
plt.xlabel("Time")
plt.ylabel("Temperature")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# ======================================================
#                   COMBINED FOUR-GRAPH PLOT
# ======================================================

plt.figure(figsize=(12,6))

plt.scatter(df["timestamp"], df["used_memory"], color="red", label="Used Memory")
plt.scatter(df["timestamp"], df["cpuusage"], color="blue", label="CPU Usage")
plt.scatter(df["timestamp"], df["used_storage"], color="green", label="Used Storage")
plt.scatter(df["timestamp"], df["temperature"], color="yellow", label="Temperature")


plt.title("All Metrics vs Time")
plt.xlabel("Time")
plt.ylabel("Metric Values")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()
