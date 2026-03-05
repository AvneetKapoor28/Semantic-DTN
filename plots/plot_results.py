import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

# Load results
epidemic = pd.read_csv("plots/epidemic_results.csv")
spray = pd.read_csv("plots/spray_results.csv")
semantic = pd.read_csv("plots/semantic_results.csv")
spatio = pd.read_csv("plots/spatio_semantic_results.csv")

# Traffic order
traffic_order = ["Low", "Medium", "High"]

# Sort for clean plotting
for df in [epidemic, spray, semantic, spatio]:
    df["Traffic"] = pd.Categorical(df["Traffic"], traffic_order)

# -------- Delivery Ratio Plot --------

plt.figure(figsize=(8,5))

plt.plot(epidemic["Traffic"], epidemic["DeliveryRatio"], marker='o', label="Epidemic")
plt.plot(spray["Traffic"], spray["DeliveryRatio"], marker='o', label="Spray & Wait")
plt.plot(semantic["Traffic"], semantic["DeliveryRatio"], marker='o', label="Semantic")
plt.plot(spatio["Traffic"], spatio["DeliveryRatio"], marker='o', label="Spatio-Semantic")

plt.title("Delivery Ratio vs Traffic Load")
plt.xlabel("Traffic Level")
plt.ylabel("Delivery Ratio")
plt.legend()
plt.tight_layout()
plt.savefig("plots/delivery_ratio.png")
plt.show()

# -------- Critical Delay Plot --------

plt.figure(figsize=(8,5))

plt.plot(epidemic["Traffic"], epidemic["AvgCriticalDelay"], marker='o', label="Epidemic")
plt.plot(spray["Traffic"], spray["AvgCriticalDelay"], marker='o', label="Spray & Wait")
plt.plot(semantic["Traffic"], semantic["AvgCriticalDelay"], marker='o', label="Semantic")
plt.plot(spatio["Traffic"], spatio["AvgCriticalDelay"], marker='o', label="Spatio-Semantic")

plt.title("Critical Delay vs Traffic Load")
plt.xlabel("Traffic Level")
plt.ylabel("Critical Delay (seconds)")
plt.legend()
plt.tight_layout()
plt.savefig("plots/critical_delay.png")
plt.show()

# -------- Overhead Plot --------

plt.figure(figsize=(8,5))

plt.plot(epidemic["Traffic"], epidemic["OverheadRatio"], marker='o', label="Epidemic")
plt.plot(spray["Traffic"], spray["OverheadRatio"], marker='o', label="Spray & Wait")
plt.plot(semantic["Traffic"], semantic["OverheadRatio"], marker='o', label="Semantic")
plt.plot(spatio["Traffic"], spatio["OverheadRatio"], marker='o', label="Spatio-Semantic")

plt.title("Overhead Ratio vs Traffic Load")
plt.xlabel("Traffic Level")
plt.ylabel("Overhead Ratio")
plt.legend()
plt.tight_layout()
plt.savefig("plots/overhead_ratio.png")
plt.show()