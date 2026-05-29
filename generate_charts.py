import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

# Set a dark theme for a premium corporate look
plt.style.use('dark_background')
sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#121212", "figure.facecolor": "#121212", "grid.color": "#333333", "text.color": "white", "axes.labelcolor": "white", "xtick.color": "white", "ytick.color": "white"})

csv_files = glob.glob('results/bench_*.csv')

fig, axs = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('FastFlowLM NPU Performance Comparison Across Models', fontsize=18, fontweight='bold', color='#00d2ff')

colors = sns.color_palette("husl", len(csv_files))

for idx, file in enumerate(csv_files):
    model_name = os.path.basename(file).replace('bench_', '').replace('_20260528.csv', '')
    try:
        df = pd.read_csv(file)
        if df.empty:
            continue
        axs[0].plot(df['context_length_k'], df['prefill_avg_toks_per_s'], marker='o', linewidth=2, color=colors[idx], label=model_name)
        axs[1].plot(df['context_length_k'], df['decoding_avg_toks_per_s'], marker='s', linewidth=2, color=colors[idx], label=model_name)
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Chart 1: Prefill Speed
axs[0].set_title('Prefill Phase Speed', fontsize=14)
axs[0].set_xlabel('Context Length (K Tokens)', fontsize=12)
axs[0].set_ylabel('Tokens / Second', fontsize=12)
axs[0].legend(loc='best', fontsize=10)

# Chart 2: Decoding Speed
axs[1].set_title('Decoding Phase Speed', fontsize=14)
axs[1].set_xlabel('Context Length (K Tokens)', fontsize=12)
axs[1].set_ylabel('Tokens / Second', fontsize=12)
axs[1].legend(loc='best', fontsize=10)

plt.tight_layout()

os.makedirs('assets', exist_ok=True)
plt.savefig('assets/fastflowlm_dashboard.png', dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
print("FastFlowLM Dashboard generated successfully.")
