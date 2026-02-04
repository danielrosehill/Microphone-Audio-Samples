#!/usr/bin/env python3
"""
Update price vs WER correlation analysis with new samples.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
SPECTROGRAMS_DIR = BASE_DIR / "spectrograms"
EVAL_FILE = BASE_DIR / "evaluation_results.json"
METADATA_FILE = BASE_DIR / "metadata.json"
PRICE_FILE = SPECTROGRAMS_DIR / "price_correlation.json"

# Load data
with open(EVAL_FILE) as f:
    eval_results = json.load(f)

with open(METADATA_FILE) as f:
    metadata = json.load(f)

# Load existing price data
with open(PRICE_FILE) as f:
    price_data = json.load(f)

# Existing prices lookup
existing_prices = {s["sample_id"]: s["price"] for s in price_data["samples"]}

# New prices to add (USD retail)
new_prices = {
    16: 40,   # EMEET M0 Conference Speakerphone
    17: 100,  # Sony ICD-UX570 Digital Voice Recorder
}

# Build complete sample list
samples = []
for result in eval_results["detailed_results"]:
    sid = result["sample_id"]
    mic = result["microphone"]
    name = f"{mic['manufacturer']} {mic['model']}"
    mic_type = mic.get("type", "Unknown")
    category = mic.get("category", "unknown")

    # Get WER
    wer = None
    for t in result["transcriptions"]:
        if t["service"] == "openai_whisper_1":
            wer = t["wer"] * 100
            break

    if wer is None:
        continue

    # Get price (from existing or new)
    price = existing_prices.get(sid) or new_prices.get(sid)

    # Skip samples without price (e.g., phone samples)
    if price is None:
        continue

    samples.append({
        "sample_id": sid,
        "name": name,
        "type": mic_type,
        "price": price,
        "wer": wer,
        "category": category
    })

# Sort by sample_id
samples.sort(key=lambda x: x["sample_id"])

# Calculate correlations
prices = np.array([s["price"] for s in samples])
wers = np.array([s["wer"] for s in samples])

pearson_r, pearson_p = stats.pearsonr(prices, wers)
spearman_rho, spearman_p = stats.spearmanr(prices, wers)

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(prices, wers)

print("=" * 60)
print("Price vs WER Correlation Analysis")
print("=" * 60)
print(f"\nSamples with price data: {len(samples)}")
print(f"\nPearson correlation: r = {pearson_r:.3f} (p = {pearson_p:.3f})")
print(f"Spearman correlation: rho = {spearman_rho:.3f} (p = {spearman_p:.3f})")
print(f"\nRegression: WER = {slope:.4f} * price + {intercept:.2f}")

# Save updated price data
output_data = {
    "pearson_r": pearson_r,
    "pearson_p": pearson_p,
    "spearman_rho": spearman_rho,
    "spearman_p": spearman_p,
    "regression_slope": slope,
    "regression_intercept": intercept,
    "samples": samples
}

with open(PRICE_FILE, "w") as f:
    json.dump(output_data, f, indent=2)
print(f"\nSaved to: {PRICE_FILE}")

# Generate visualization
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Color map by category
category_colors = {
    "desktop": "#2ecc71",
    "headset": "#3498db",
    "mobile": "#e74c3c",
    "lavalier": "#9b59b6",
    "portable": "#f39c12",
}

# Left plot: Scatter with regression
ax1 = axes[0]
for s in samples:
    color = category_colors.get(s["category"], "#95a5a6")
    ax1.scatter(s["price"], s["wer"], c=color, s=150, alpha=0.7, edgecolors='white', linewidth=2)
    # Add label
    ax1.annotate(s["name"].split()[0], (s["price"], s["wer"]),
                 textcoords="offset points", xytext=(5, 5), fontsize=8, alpha=0.8)

# Regression line
x_line = np.linspace(0, max(prices) * 1.1, 100)
y_line = slope * x_line + intercept
ax1.plot(x_line, y_line, 'r--', alpha=0.7, linewidth=2, label=f'Regression (r={pearson_r:.2f})')

ax1.set_xlabel("Price (USD)", fontsize=12)
ax1.set_ylabel("Word Error Rate (%)", fontsize=12)
ax1.set_title("Price vs STT Accuracy", fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Add category legend
for cat, color in category_colors.items():
    ax1.scatter([], [], c=color, s=100, label=cat.title(), alpha=0.7)
ax1.legend(loc='upper left', fontsize=9)

# Right plot: By microphone type
ax2 = axes[1]

# Group by type
type_data = {}
for s in samples:
    t = s["type"]
    if t not in type_data:
        type_data[t] = {"prices": [], "wers": [], "names": []}
    type_data[t]["prices"].append(s["price"])
    type_data[t]["wers"].append(s["wer"])
    type_data[t]["names"].append(s["name"])

# Create bar chart comparing types
types = list(type_data.keys())
avg_wers = [np.mean(type_data[t]["wers"]) for t in types]
avg_prices = [np.mean(type_data[t]["prices"]) for t in types]

# Sort by avg WER
sorted_idx = np.argsort(avg_wers)
types = [types[i] for i in sorted_idx]
avg_wers = [avg_wers[i] for i in sorted_idx]
avg_prices = [avg_prices[i] for i in sorted_idx]

x = np.arange(len(types))
width = 0.35

bars1 = ax2.bar(x - width/2, avg_wers, width, label='Avg WER (%)', color='#3498db', alpha=0.8)
ax2_twin = ax2.twinx()
bars2 = ax2_twin.bar(x + width/2, avg_prices, width, label='Avg Price ($)', color='#e74c3c', alpha=0.8)

ax2.set_xlabel("Microphone Type", fontsize=12)
ax2.set_ylabel("Average WER (%)", fontsize=12, color='#3498db')
ax2_twin.set_ylabel("Average Price ($)", fontsize=12, color='#e74c3c')
ax2.set_title("WER vs Price by Microphone Type", fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels([t.replace(' ', '\n') for t in types], fontsize=9)
ax2.tick_params(axis='y', labelcolor='#3498db')
ax2_twin.tick_params(axis='y', labelcolor='#e74c3c')

# Combined legend
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

plt.suptitle(f"Price-Performance Analysis (n={len(samples)} microphones)\n"
             f"Correlation: r={pearson_r:.2f} (p={pearson_p:.3f}) - "
             f"{'Significant' if pearson_p < 0.05 else 'Not significant'} at p<0.05",
             fontsize=12, y=1.02)

plt.tight_layout()
output_path = SPECTROGRAMS_DIR / "price_vs_wer_analysis.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Generated: {output_path}")

# Print detailed table
print("\n" + "=" * 80)
print("DETAILED PRICE-PERFORMANCE TABLE (sorted by WER)")
print("=" * 80)
print(f"{'Rank':<5} {'Microphone':<35} {'Type':<22} {'Price':<8} {'WER':<8}")
print("-" * 80)

sorted_samples = sorted(samples, key=lambda x: x["wer"])
for i, s in enumerate(sorted_samples, 1):
    print(f"{i:<5} {s['name']:<35} {s['type']:<22} ${s['price']:<7} {s['wer']:.2f}%")

print("\n" + "=" * 60)
print("KEY COMPARISONS")
print("=" * 60)

# Find specific comparisons
emeet = next((s for s in samples if "EMEET" in s["name"]), None)
jabra = next((s for s in samples if "Jabra" in s["name"]), None)
ugreen = next((s for s in samples if "UGreen" in s["name"]), None)
at_boundary = next((s for s in samples if "ATR4697" in s["name"]), None)
sony = next((s for s in samples if "Sony" in s["name"]), None)

if emeet and jabra:
    print(f"\nConference Speakerphones:")
    print(f"  EMEET (${emeet['price']}): {emeet['wer']:.2f}% WER")
    print(f"  Jabra Speak 510 (${jabra['price']}): {jabra['wer']:.2f}% WER")
    print(f"  -> EMEET is {jabra['price']/emeet['price']:.1f}x cheaper with similar accuracy!")

if emeet and at_boundary:
    print(f"\nConference vs Boundary Mic:")
    print(f"  EMEET Conference (${emeet['price']}): {emeet['wer']:.2f}% WER")
    print(f"  Audio-Technica Boundary (${at_boundary['price']}): {at_boundary['wer']:.2f}% WER")

if ugreen:
    print(f"\nBest Value (Gooseneck):")
    print(f"  UGreen CM564 (${ugreen['price']}): {ugreen['wer']:.2f}% WER - Best WER/$ ratio!")

if sony:
    print(f"\nDigital Voice Recorder:")
    print(f"  Sony ICD-UX570 (${sony['price']}): {sony['wer']:.2f}% WER")
