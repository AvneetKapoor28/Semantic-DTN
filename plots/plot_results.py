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
# ---------- COMMON STYLE ----------
LINE_WIDTH_MAIN = 3.2   # for Spatio-Semantic
LINE_WIDTH = 2.2        # for others
MARKER_SIZE = 7
FONT_SIZE = 12

def setup_plot():
    plt.figure(figsize=(9,6))
    plt.xticks(fontsize=FONT_SIZE)
    plt.yticks(fontsize=FONT_SIZE)
    plt.grid(True, linestyle='--', alpha=0.4)

# -------- Delivery Ratio Plot --------
setup_plot()

plt.plot(epidemic["Traffic"], epidemic["DeliveryRatio"],
         marker='o', linewidth=LINE_WIDTH, markersize=MARKER_SIZE,
         label="Epidemic")

plt.plot(spray["Traffic"], spray["DeliveryRatio"],
         marker='o', linewidth=LINE_WIDTH, markersize=MARKER_SIZE,
         label="Spray & Wait")

plt.plot(semantic["Traffic"], semantic["DeliveryRatio"],
         marker='o', linewidth=LINE_WIDTH, markersize=MARKER_SIZE,
         label="Semantic")

# Highlight your method
plt.plot(spatio["Traffic"], spatio["DeliveryRatio"],
         marker='o', linewidth=LINE_WIDTH_MAIN, markersize=MARKER_SIZE+1,
         label="Spatio-Semantic")

plt.title("Delivery Ratio vs Traffic", fontsize=FONT_SIZE+2)
plt.xlabel("Traffic Level", fontsize=FONT_SIZE)
plt.ylabel("Delivery Ratio", fontsize=FONT_SIZE)
plt.legend(fontsize=FONT_SIZE)
plt.tight_layout()
plt.savefig("plots/delivery_ratio.png", dpi=300)
plt.show()


# -------- Critical Delay Plot --------
setup_plot()

plt.plot(epidemic["Traffic"], epidemic["AvgCriticalDelay"],
         marker='o', linewidth=LINE_WIDTH, markersize=MARKER_SIZE,
         label="Epidemic")

plt.plot(spray["Traffic"], spray["AvgCriticalDelay"],
         marker='o', linewidth=LINE_WIDTH, markersize=MARKER_SIZE,
         label="Spray & Wait")

plt.plot(semantic["Traffic"], semantic["AvgCriticalDelay"],
         marker='o', linewidth=LINE_WIDTH, markersize=MARKER_SIZE,
         label="Semantic")

plt.plot(spatio["Traffic"], spatio["AvgCriticalDelay"],
         marker='o', linewidth=LINE_WIDTH_MAIN, markersize=MARKER_SIZE+1,
         label="Spatio-Semantic")

plt.title("Critical Delay vs Traffic", fontsize=FONT_SIZE+2)
plt.xlabel("Traffic Level", fontsize=FONT_SIZE)
plt.ylabel("Delay (seconds)", fontsize=FONT_SIZE)
plt.legend(fontsize=FONT_SIZE)
plt.tight_layout()
plt.savefig("plots/critical_delay.png", dpi=300)
plt.show()


# -------- Overhead Plot --------
setup_plot()

plt.plot(epidemic["Traffic"], epidemic["OverheadRatio"],
         marker='o', linewidth=LINE_WIDTH, markersize=MARKER_SIZE,
         label="Epidemic")

plt.plot(spray["Traffic"], spray["OverheadRatio"],
         marker='o', linewidth=LINE_WIDTH, markersize=MARKER_SIZE,
         label="Spray & Wait")

plt.plot(semantic["Traffic"], semantic["OverheadRatio"],
         marker='o', linewidth=LINE_WIDTH, markersize=MARKER_SIZE,
         label="Semantic")

plt.plot(spatio["Traffic"], spatio["OverheadRatio"],
         marker='o', linewidth=LINE_WIDTH_MAIN, markersize=MARKER_SIZE+1,
         label="Spatio-Semantic")

plt.title("Overhead Ratio vs Traffic", fontsize=FONT_SIZE+2)
plt.xlabel("Traffic Level", fontsize=FONT_SIZE)
plt.ylabel("Overhead Ratio", fontsize=FONT_SIZE)
plt.legend(fontsize=FONT_SIZE)
plt.tight_layout()
plt.savefig("plots/overhead_ratio.png", dpi=300)
plt.show()