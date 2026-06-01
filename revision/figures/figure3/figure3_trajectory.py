"""Figure 3 v2: cleaner layout, no title overlap, better annotation positions."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
import sys
from adaptation_simulation import simulate_directional_then_relaxed

mpl.rcParams.update({
    'font.family': 'serif', 'font.size': 10, 'axes.titlesize': 11,
    'axes.labelsize': 10.5, 'xtick.labelsize': 9.5, 'ytick.labelsize': 9.5,
    'figure.dpi': 150, 'savefig.dpi': 300,
    'axes.spines.top': False, 'axes.spines.right': False,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})

GREEN = '#2D5A3D'; ORANGE = '#D97A2C'; MUTED = '#6B6048'
RULE = '#C9BFA2'; PALE_GREEN = '#C8D9CD'; BLUE_GREEN = '#4A7B5A'

df = simulate_directional_then_relaxed(
    n=4, gamma=0.05, b0=0.3, lambda_b=0.005, rho=0.95, M=1e-3,
    sigma2_0=20.0, n_gen=500
)
peak_idx = df['Ag'].idxmax()
in_channel = df['Ag'] >= 0.75
channel_entry = in_channel.idxmax() if in_channel.any() else None
channel_exit = None
if channel_entry is not None:
    for i in range(channel_entry, len(df)):
        if df['Ag'].iloc[i] >= 0.75:
            channel_exit = i
        else: break

ag_cmap = LinearSegmentedColormap.from_list(
    'ag', ['#FFF9EB', PALE_GREEN, BLUE_GREEN, GREEN], N=256
)

# Wider figure, more space between panels
fig = plt.figure(figsize=(14, 5.0), constrained_layout=True)
gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.2])

# Panel A
ax = fig.add_subplot(gs[0, 0])
gens = df['generation'].values + 1
ax.plot(gens, df['sigma'].values, color=GREEN, linewidth=2.2, zorder=3)
ax.plot(gens, df['b_mag'].values, color=ORANGE, linewidth=2.2, linestyle='--', zorder=3)
ax.set_xscale('log')
ax.set_xlim(1, 500)
ax.set_xlabel('generation')
ax.set_ylabel('magnitude')
ax.set_title(r'$\mathbf{A}$. Variance compresses fast; gradient decays slow', loc='left', pad=10)
ax.tick_params(direction='out', length=4, color=RULE)

ax.text(2.0, df['sigma'].iloc[1]*1.08, r'$\sigma$', color=GREEN, fontsize=12, fontweight='600',
        bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.85))
ax.text(60, df['b_mag'].iloc[60]*1.20, r'$|\mathbf{b}|$', color=ORANGE, fontsize=12, fontweight='600',
        bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.85))

ax.axvline(peak_idx + 1, color=RULE, linewidth=0.8, linestyle=':', alpha=0.8)
y_top = ax.get_ylim()[1]
ax.text(peak_idx + 1.3, y_top*0.94, 'peak\n$\\mathcal{A}_g$', 
        fontsize=8.5, color=MUTED, va='top', style='italic')

# Panel B
ax = fig.add_subplot(gs[0, 1])
if channel_entry is not None and channel_exit is not None:
    ax.axhspan(0.75, 1.0, alpha=0.13, color=PALE_GREEN, zorder=0)
    ax.axvspan(channel_entry + 1, channel_exit + 1, alpha=0.13, color=PALE_GREEN, zorder=0)

ax.plot(gens, df['Ag'].values, color=GREEN, linewidth=2.4, zorder=3)
ax.scatter([peak_idx + 1], [df['Ag'].iloc[peak_idx]],
           s=90, color=ORANGE, edgecolor=GREEN, linewidth=1.5, zorder=4)

ax.axhline(0.75, color=GREEN, linewidth=0.8, linestyle='--', alpha=0.6)
ax.text(1.5, 0.77, r'additive channel ($\mathcal{A}_g \geq 0.75$)',
        fontsize=8.5, color=GREEN, style='italic', va='bottom')

ax.set_xscale('log')
ax.set_xlim(1, 500); ax.set_ylim(0, 1.0)
ax.set_xlabel('generation'); ax.set_ylabel(r'$\mathcal{A}_g$')
ax.set_title(r'$\mathbf{B}$. $\mathcal{A}_g$ rises, plateaus in the channel, then falls', loc='left', pad=10)
ax.tick_params(direction='out', length=4, color=RULE)

ax.annotate('rise\n(variance\ncompresses)', xy=(3, 0.6), xytext=(1.2, 0.20),
            fontsize=9, color=GREEN, fontweight='500', ha='left',
            arrowprops=dict(arrowstyle='->', color=GREEN, lw=0.9))
ax.annotate('peak', xy=(peak_idx + 1, df['Ag'].iloc[peak_idx] + 0.005),
            xytext=(peak_idx + 25, 0.95),
            fontsize=10, color=ORANGE, fontweight='600',
            ha='center', va='bottom',
            arrowprops=dict(arrowstyle='->', color=ORANGE, lw=0.9))
ax.annotate('fall\n($|\\mathbf{b}|\\to 0$)', xy=(400, 0.10), xytext=(150, 0.42),
            fontsize=9, color=GREEN, fontweight='500', ha='left',
            arrowprops=dict(arrowstyle='->', color=GREEN, lw=0.9))

# Panel C - phase portrait
ax = fig.add_subplot(gs[0, 2])
b_range = np.linspace(0.005, df['b_mag'].max() * 1.10, 100)
s_range = np.linspace(0.5, df['sigma'].max() * 1.10, 100)
B_grid, S_grid = np.meshgrid(b_range, s_range)
n_eff = 4; gamma = 0.05
Vlin_grid = B_grid**2 * S_grid**2
Vquad_grid = 0.5 * n_eff * gamma**2 * S_grid**4
Ag_grid = Vlin_grid / (Vlin_grid + Vquad_grid)

cs = ax.contourf(B_grid, S_grid, Ag_grid, levels=20, cmap=ag_cmap, alpha=0.85)
cs_line = ax.contour(B_grid, S_grid, Ag_grid, levels=[0.5, 0.75, 0.9],
                     colors=[MUTED, GREEN, GREEN], linewidths=[0.8, 1.4, 0.8],
                     linestyles=['--', '-', '--'], alpha=0.85)
ax.clabel(cs_line, inline=True, fontsize=8.5, fmt='%.2f')

ax.plot(df['b_mag'].values, df['sigma'].values, color=ORANGE, linewidth=2.4, zorder=3)

# start, peak, end markers with cleaner positioning
ax.scatter([df['b_mag'].iloc[0]], [df['sigma'].iloc[0]],
           s=120, color='white', edgecolor=ORANGE, linewidth=2.0, zorder=4)
ax.scatter([df['b_mag'].iloc[peak_idx]], [df['sigma'].iloc[peak_idx]],
           s=120, color=ORANGE, edgecolor=GREEN, linewidth=2.0, zorder=4)
ax.scatter([df['b_mag'].iloc[-1]], [df['sigma'].iloc[-1]],
           s=100, color=ORANGE, edgecolor='white', linewidth=1.0, zorder=4, marker='X')

# Annotations placed to avoid the colorbar
ax.annotate('start',
            xy=(df['b_mag'].iloc[0], df['sigma'].iloc[0]),
            xytext=(df['b_mag'].iloc[0] - 0.05, df['sigma'].iloc[0] - 0.4),
            fontsize=10, color=MUTED, fontweight='600', ha='right', va='top')
ax.annotate('peak',
            xy=(df['b_mag'].iloc[peak_idx], df['sigma'].iloc[peak_idx]),
            xytext=(df['b_mag'].iloc[peak_idx] - 0.06, df['sigma'].iloc[peak_idx] - 0.6),
            fontsize=10, color=ORANGE, fontweight='600', ha='right', va='top',
            arrowprops=dict(arrowstyle='->', color=ORANGE, lw=0.8))
ax.annotate('end',
            xy=(df['b_mag'].iloc[-1], df['sigma'].iloc[-1]),
            xytext=(df['b_mag'].iloc[-1] + 0.025, df['sigma'].iloc[-1] + 0.3),
            fontsize=10, color=MUTED, fontweight='600')

ax.set_xlim(b_range.min(), b_range.max())
ax.set_ylim(s_range.min(), s_range.max())
ax.set_xlabel(r'gradient magnitude $|\mathbf{b}|$')
ax.set_ylabel(r'genetic standard deviation $\sigma$')
ax.set_title(r'$\mathbf{C}$. Phase portrait: trajectory through the $\mathcal{A}_g$ landscape', loc='left', pad=10)
ax.tick_params(direction='out', length=4, color=RULE)

cbar = fig.colorbar(cs, ax=ax, fraction=0.04, pad=0.025)
cbar.set_label(r'$\mathcal{A}_g$', fontsize=10)
cbar.ax.tick_params(labelsize=8.5)

plt.savefig('figure3_trajectory.pdf', bbox_inches='tight')
plt.savefig('figure3_trajectory.png', bbox_inches='tight', dpi=300)
plt.close()
print("Saved v2")
