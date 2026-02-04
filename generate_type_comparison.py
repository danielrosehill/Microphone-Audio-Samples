#!/usr/bin/env python3
"""
Generate microphone type comparison charts.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
SPECTROGRAMS_DIR = BASE_DIR / "spectrograms"
EVAL_FILE = BASE_DIR / "evaluation_results.json"
PRICE_FILE = SPECTROGRAMS_DIR / "price_correlation.json"

# Load data
with open(EVAL_FILE) as f:
    eval_results = json.load(f)

with open(PRICE_FILE) as f:
    price_data = json.load(f)

# Build price lookup
price_lookup = {s["sample_id"]: s["price"] for s in price_data["samples"]}

# Build complete data
samples = []
for result in eval_results["detailed_results"]:
    sid = result["sample_id"]
    mic = result["microphone"]

    wer = None
    for t in result["transcriptions"]:
        if t["service"] == "openai_whisper_1":
            wer = t["wer"] * 100
            break

    if wer is None:
        continue

    samples.append({
        "sample_id": sid,
        "name": f"{mic['manufacturer']} {mic['model']}",
        "type": mic.get("type", "Unknown"),
        "category": mic.get("category", "unknown"),
        "wer": wer,
        "price": price_lookup.get(sid),
        "quality_score": result["audio_quality_score"]
    })

# Sort by WER
samples.sort(key=lambda x: x["wer"])

# Create comprehensive comparison chart
fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Color by type
type_colors = {
    "USB Gooseneck": "#2ecc71",
    "Condenser Gooseneck": "#27ae60",
    "Dynamic USB/XLR": "#3498db",
    "Boundary Microphone": "#9b59b6",
    "USB Speakerphone": "#e74c3c",
    "USB Headset": "#f39c12",
    "Wireless Headset": "#f1c40f",
    "Webcam built-in": "#1abc9c",
    "Lavalier": "#e67e22",
    "Smartphone built-in": "#95a5a6",
    "Digital Voice Recorder": "#34495e",
}

# 1. WER by Microphone (horizontal bar chart)
ax1 = axes[0, 0]
y_pos = np.arange(len(samples))
colors = [type_colors.get(s["type"], "#bdc3c7") for s in samples]

bars = ax1.barh(y_pos, [s["wer"] for s in samples], color=colors, alpha=0.8, edgecolor='white')
ax1.set_yticks(y_pos)
ax1.set_yticklabels([f"{s['name']}" for s in samples], fontsize=9)
ax1.set_xlabel("Word Error Rate (%)", fontsize=11)
ax1.set_title("All Microphones Ranked by WER (Best to Worst)", fontsize=13, fontweight='bold')
ax1.invert_yaxis()

# Add WER values and prices on bars
for i, (bar, s) in enumerate(zip(bars, samples)):
    price_str = f"${s['price']}" if s['price'] else "N/A"
    ax1.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
             f"{s['wer']:.2f}% ({price_str})", va='center', fontsize=8)

ax1.set_xlim(0, max(s["wer"] for s in samples) * 1.3)
ax1.axvline(x=5.0, color='green', linestyle='--', alpha=0.5, label='5% WER threshold')
ax1.legend(loc='lower right')

# 2. Type comparison (grouped)
ax2 = axes[0, 1]

# Group by type
type_stats = {}
for s in samples:
    t = s["type"]
    if t not in type_stats:
        type_stats[t] = {"wers": [], "prices": [], "names": []}
    type_stats[t]["wers"].append(s["wer"])
    if s["price"]:
        type_stats[t]["prices"].append(s["price"])
    type_stats[t]["names"].append(s["name"])

# Calculate averages and sort
type_summary = []
for t, data in type_stats.items():
    type_summary.append({
        "type": t,
        "avg_wer": np.mean(data["wers"]),
        "min_wer": min(data["wers"]),
        "max_wer": max(data["wers"]),
        "avg_price": np.mean(data["prices"]) if data["prices"] else None,
        "count": len(data["wers"])
    })

type_summary.sort(key=lambda x: x["avg_wer"])

y_pos = np.arange(len(type_summary))
colors = [type_colors.get(t["type"], "#bdc3c7") for t in type_summary]

# Bar for average WER
bars = ax2.barh(y_pos, [t["avg_wer"] for t in type_summary], color=colors, alpha=0.8, edgecolor='white')

# Error bars for min/max
for i, t in enumerate(type_summary):
    ax2.plot([t["min_wer"], t["max_wer"]], [i, i], 'k-', linewidth=2, alpha=0.5)
    ax2.plot([t["min_wer"]], [i], 'k<', markersize=6)
    ax2.plot([t["max_wer"]], [i], 'k>', markersize=6)

ax2.set_yticks(y_pos)
ax2.set_yticklabels([f"{t['type']}\n(n={t['count']})" for t in type_summary], fontsize=9)
ax2.set_xlabel("Word Error Rate (%)", fontsize=11)
ax2.set_title("Average WER by Microphone Type\n(bars show range)", fontsize=13, fontweight='bold')
ax2.invert_yaxis()

# Add price info
for i, (bar, t) in enumerate(zip(bars, type_summary)):
    price_str = f"~${t['avg_price']:.0f}" if t['avg_price'] else ""
    ax2.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
             f"{t['avg_wer']:.2f}% {price_str}", va='center', fontsize=9)

# 3. Head-to-head: Conference vs Boundary vs Gooseneck
ax3 = axes[1, 0]

focus_types = ["USB Speakerphone", "Boundary Microphone", "USB Gooseneck", "Condenser Gooseneck"]
focus_samples = [s for s in samples if s["type"] in focus_types]

if focus_samples:
    y_pos = np.arange(len(focus_samples))
    colors = [type_colors.get(s["type"], "#bdc3c7") for s in focus_samples]

    bars = ax3.barh(y_pos, [s["wer"] for s in focus_samples], color=colors, alpha=0.8, edgecolor='white')
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels([f"{s['name']}\n({s['type']})" for s in focus_samples], fontsize=9)
    ax3.set_xlabel("Word Error Rate (%)", fontsize=11)
    ax3.set_title("Head-to-Head: Conference vs Boundary vs Gooseneck", fontsize=13, fontweight='bold')
    ax3.invert_yaxis()

    for i, (bar, s) in enumerate(zip(bars, focus_samples)):
        price_str = f"${s['price']}" if s['price'] else ""
        ax3.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                 f"{s['wer']:.2f}% {price_str}", va='center', fontsize=9)

# 4. Value analysis (WER per dollar)
ax4 = axes[1, 1]

priced_samples = [s for s in samples if s["price"] and s["price"] > 0]
# Calculate "error cost" - how much error per dollar (lower is better value)
for s in priced_samples:
    s["wer_per_dollar"] = s["wer"] / s["price"] * 10  # Normalized

priced_samples.sort(key=lambda x: x["wer_per_dollar"], reverse=True)  # Best value at bottom

y_pos = np.arange(len(priced_samples))
colors = [type_colors.get(s["type"], "#bdc3c7") for s in priced_samples]

bars = ax4.barh(y_pos, [s["wer_per_dollar"] for s in priced_samples], color=colors, alpha=0.8, edgecolor='white')
ax4.set_yticks(y_pos)
ax4.set_yticklabels([f"{s['name']}" for s in priced_samples], fontsize=9)
ax4.set_xlabel("WER per $10 spent (lower = better value)", fontsize=11)
ax4.set_title("Value Analysis: Best Bang for Buck\n(lower bars = better value)", fontsize=13, fontweight='bold')
ax4.invert_yaxis()

for i, (bar, s) in enumerate(zip(bars, priced_samples)):
    ax4.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
             f"${s['price']} -> {s['wer']:.1f}%", va='center', fontsize=8)

# Add type legend
handles = [plt.Rectangle((0,0),1,1, color=c, alpha=0.8) for c in type_colors.values()]
labels = list(type_colors.keys())
fig.legend(handles, labels, loc='center right', bbox_to_anchor=(1.12, 0.5), fontsize=9, title="Mic Type")

plt.suptitle("Microphone Type Comparison for Speech-to-Text Accuracy", fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()

output_path = SPECTROGRAMS_DIR / "type_comparison_analysis.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Generated: {output_path}")

# Print summary
print("\n" + "=" * 70)
print("MICROPHONE TYPE RANKINGS (by average WER)")
print("=" * 70)
for t in type_summary:
    price_str = f"~${t['avg_price']:.0f}" if t['avg_price'] else "N/A"
    print(f"{t['type']:<25} Avg WER: {t['avg_wer']:.2f}% (range: {t['min_wer']:.2f}-{t['max_wer']:.2f}%) Price: {price_str}")
