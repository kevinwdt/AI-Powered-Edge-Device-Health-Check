# Generate graphs from Diagnostic_Data.csv
# Use Graph to analyze treds in memory, CPU, storage, temperature
# Includes four separate plots and one combined plot
# Kevin Wang


# import pandas as pd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ------- LOAD CSV -------
df = pd.read_csv("PLC AI project Capstone/Diagnostic_Data/axin-ep-ph_2026-02-23 00_00_00_messagesdiagnostic.csv", low_memory=False)

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


# Temperature at restart events
# First plot, Used memory drop vs temp
# Second plot, Used storage drop vs temp

def plot_temperature_at_restarts_auto(df, metric_col, title_suffix, k=5):
    diff_col = f"{metric_col}_diff"
    df[diff_col] = df[metric_col].diff()

    # Show the biggest drops so you can see what "real restart" looks like
    biggest_drops = df[diff_col].dropna().sort_values().head(15)
    print(f"\n{title_suffix} - biggest drops (most negative):")
    print(biggest_drops)

    # Auto-threshold: take the k-th biggest drop as the cutoff
    # (k=5 usually matches your “4–5 restarts” expectation)
    threshold = biggest_drops.iloc[k-1]
    print(f"{title_suffix} - using threshold <= {threshold}")

    restarts = df[df[diff_col] <= threshold].copy()
    restarts = restarts.sort_values("timestamp")
    restarts["restart_id"] = range(1, len(restarts) + 1)

    if restarts.empty:
        print(f"{title_suffix}: No restarts found even with auto threshold.")
        return

    plt.figure(figsize=(8, 5))
    plt.scatter(restarts["restart_id"], restarts["temperature"], s=120)

    plt.axhline(df["temperature"].mean(), linestyle="--", label="Average Operating Temperature")
    plt.title(f"Temperature at Restart Events ({title_suffix})")
    plt.xlabel("Restart Event")
    plt.ylabel("Temperature")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.show()

    print(f"{title_suffix}: plotted {len(restarts)} restart events")


# ---- Used Memory ----
plot_temperature_at_restarts_auto(df, "used_memory", "Restart = Used Memory Drop", k=5)

# ---- Used Storage ----
plot_temperature_at_restarts_auto(df, "used_storage", "Restart = Used Storage Drop", k=5)