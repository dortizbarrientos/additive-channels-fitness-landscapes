"""
Figure 2 v5: separate the architecture labels in panel A; cleaner panel B.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    'font.family': 'serif', 'font.size': 10, 'axes.titlesize': 11,
    'axes.labelsize': 10.5, 'xtick.labelsize': 9.5, 'ytick.labelsize': 9.5,
    'figure.dpi': 150, 'savefig.dpi': 300,
    'axes.spines.top': False, 'axes.spines.right': False,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})

GREEN = '#2D5A3D'; ORANGE = '#D97A2C'; MUTED = '#6B6048'
RULE = '#C9BFA2'; PALE_GREEN = '#C8D9CD'; BLUE_GREEN = '#4A7B5A'

df = pd.read_csv('validation_sweep.csv')
g = df[df['dist'] == 'gaussian'].copy()
poly = df[df['dist'] == 'polygenic'].copy()
rare = df[df['dist'] == 'rare_large'].copy()

fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), constrained_layout=True)

# ===== Panel A =====
ax = axes[0]
ax.axvspan(0.75, 1.0, alpha=0.18, color=PALE_GREEN, zorder=0)
ax.plot([0, 1], [0, 1], color=MUTED, linewidth=1, linestyle='--', zorder=1, alpha=0.7)

ax.scatter(rare['Ag'], rare['R2'], s=18, alpha=0.45, color=ORANGE, edgecolor='none', zorder=2)
ax.scatter(poly['Ag'], poly['R2'], s=18, alpha=0.45, color=BLUE_GREEN, edgecolor='none', zorder=3)
ax.scatter(g['Ag'], g['R2'], s=14, alpha=0.55, color=GREEN, edgecolor='none', zorder=4)

ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
ax.set_xlabel(r'analytical $\mathcal{A}_g$')
ax.set_ylabel(r'empirical $R^2$ of linear predictor')
ax.set_title(r'$\mathbf{A}$. The identity $\mathcal{A}_g = R^2$ holds across realistic genetic architectures',
             loc='left', pad=10)
ax.set_aspect('equal', adjustable='box')

ax.text(0.875, 0.04, 'additive\nchannel', ha='center', va='bottom',
        fontsize=8.5, color=GREEN, style='italic')

# Architecture labels — placed in the lower-right corner as a compact key
key_x = 0.04
key_y_top = 0.90
key_dy = 0.07
ax.scatter([key_x + 0.03], [key_y_top], s=30, color=GREEN, edgecolor='none', transform=ax.transAxes, clip_on=False, zorder=5)
ax.text(key_x + 0.07, key_y_top, 'Gaussian (canonical baseline)', fontsize=9.5,
        color=GREEN, fontweight='600', va='center', transform=ax.transAxes)
ax.scatter([key_x + 0.03], [key_y_top - key_dy], s=30, color=BLUE_GREEN, edgecolor='none', transform=ax.transAxes, clip_on=False, zorder=5)
ax.text(key_x + 0.07, key_y_top - key_dy, 'polygenic finite-locus (200 loci, $p=0.5$)', fontsize=9.5,
        color=BLUE_GREEN, fontweight='600', va='center', transform=ax.transAxes)
ax.scatter([key_x + 0.03], [key_y_top - 2*key_dy], s=30, color=ORANGE, edgecolor='none', transform=ax.transAxes, clip_on=False, zorder=5)
ax.text(key_x + 0.07, key_y_top - 2*key_dy, 'rare-large-effect ($p=0.02$, effect $10\\times$)', fontsize=9.5,
        color=ORANGE, fontweight='600', va='center', transform=ax.transAxes)

ax.text(0.97, 0.91, '$y = x$', fontsize=9.5, color=MUTED, style='italic', ha='right', va='top',
        bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.85))

ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.tick_params(direction='out', length=4, color=RULE)

# ===== Panel B =====
ax = axes[1]
ax.axvspan(0.75, 1.0, alpha=0.18, color=PALE_GREEN, zorder=0)

y_floor = 1e-3
ax.scatter(rare['Ag'], np.maximum(rare['ms_diff'], y_floor),
           s=18, alpha=0.4, color=ORANGE, edgecolor='none', zorder=2)
ax.scatter(poly['Ag'], np.maximum(poly['ms_diff'], y_floor),
           s=18, alpha=0.4, color=BLUE_GREEN, edgecolor='none', zorder=3)
ax.scatter(g['Ag'], np.maximum(g['ms_diff'], y_floor),
           s=14, alpha=0.55, color=GREEN, edgecolor='none', zorder=4)

bins = np.linspace(0, 1, 11)
bin_centers = 0.5 * (bins[:-1] + bins[1:])
def bin_med(d):
    return np.array([d.loc[(d['Ag']>=bins[i])&(d['Ag']<bins[i+1]), 'ms_diff'].median()
                     if ((d['Ag']>=bins[i])&(d['Ag']<bins[i+1])).sum()>=3 else np.nan
                     for i in range(len(bins)-1)])

g_med = bin_med(g); poly_med = bin_med(poly); rare_med = bin_med(rare)
v_g = ~np.isnan(g_med); v_p = ~np.isnan(poly_med); v_r = ~np.isnan(rare_med)

# Plot a single combined median line because all three are essentially identical
combined = pd.concat([g, poly, rare])
comb_med = bin_med(combined)
v_c = ~np.isnan(comb_med)
ax.plot(bin_centers[v_c], np.maximum(comb_med[v_c], y_floor),
        color=GREEN, linewidth=2.6, alpha=0.95, marker='o',
        markersize=6, markeredgecolor='white', markeredgewidth=0.8, zorder=7)

ax.set_yscale('log')
ax.set_xlim(-0.02, 1.02); ax.set_ylim(y_floor, 3.0)
ax.set_xlabel(r'analytical $\mathcal{A}_g$')
ax.set_ylabel(r'$\|\Delta\bar{\mathbf{a}}_{\mathrm{linear}} - \Delta\bar{\mathbf{a}}_{\mathrm{full}}\|$  (relative)')
ax.set_title(r'$\mathbf{B}$. Operational claim is robust: linear-only weighting reproduces full outcome',
             loc='left', pad=10)

ax.text(0.875, y_floor * 1.5, 'additive\nchannel', ha='center', va='bottom',
        fontsize=8.5, color=GREEN, style='italic')

# Annotation
ax.text(0.04, 1.6, 'pooled median\n(all three architectures)', fontsize=9.5, color=GREEN, fontweight='600',
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='none', alpha=0.9))

# Show drop with explicit endpoint annotations
g_low_y = np.maximum(comb_med[v_c][1], y_floor)
g_high_y = np.maximum(comb_med[v_c][-2], y_floor)
ax.annotate('', xy=(0.85, g_high_y * 1.15),
            xytext=(0.16, g_low_y * 0.85),
            arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.0,
                           connectionstyle='arc3,rad=-0.2'))
ax.text(0.50, 0.04, f'  ~20× drop  ', fontsize=9.5, color=GREEN, fontweight='600',
        ha='center', va='center', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=GREEN, alpha=0.95, linewidth=1.0))

ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
ax.tick_params(direction='out', length=4, color=RULE)

plt.savefig('figure2_validation.pdf', bbox_inches='tight')
plt.savefig('figure2_validation.png', bbox_inches='tight', dpi=300)
plt.close()
print("Saved v5")
