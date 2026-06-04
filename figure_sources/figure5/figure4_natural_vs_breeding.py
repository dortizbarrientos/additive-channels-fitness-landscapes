"""
figure4_natural_vs_breeding.py
==============================
Figure 4: trajectories of (G, A_g, V_lin, V_quad) for natural and breeding
populations on log time axes, over 1000 generations.

This version uses **episodic** directional pressure for the natural population
(three log-spaced bouts of selection separated by mutation-drift balance) and
**sustained** directional pressure for the breeding population (constant b).
The contrast highlights why breeding programmes enter and persist in the
additive channel while natural populations spend most of their time outside it.

Output: figure4_natural_vs_breeding.{pdf,png}

Design notes
------------
- Nature Genetics formatting: Helvetica/Arial, 183mm full width, pdf.fonttype=42.
- Okabe-Ito colorblind-safe palette: blue=natural, vermillion=breeding,
  bluishgreen=V_lin, orange=V_quad.
- Direct on-axis annotations; no legend boxes.
- Light yellow vertical bands mark natural's episodes.
- Log time axis from generation 1 (avoids log(0) at t=0).
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sim_core import trajectory


# -----------------------------------------------------------------
# Nature Genetics formatting
# -----------------------------------------------------------------
plt.rcParams.update({
    'pdf.fonttype':       42,
    'ps.fonttype':        42,
    'font.family':        'sans-serif',
    'font.sans-serif':    ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size':          7,
    'axes.titlesize':     8,
    'axes.labelsize':     7,
    'xtick.labelsize':    6.5,
    'ytick.labelsize':    6.5,
    'axes.linewidth':     0.6,
    'xtick.major.width':  0.5,
    'ytick.major.width':  0.5,
    'xtick.major.size':   2.0,
    'ytick.major.size':   2.0,
    'lines.linewidth':    1.2,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
})

MM = 1.0 / 25.4

# Okabe-Ito palette
OI = {
    'black':      '#000000',
    'orange':     '#E69F00',
    'skyblue':    '#56B4E9',
    'green':      '#009E73',
    'yellow':     '#F0E442',
    'blue':       '#0072B2',
    'vermillion': '#D55E00',
    'pink':       '#CC79A7',
}
C_NAT   = OI['blue']
C_BRE   = OI['vermillion']
C_LIN   = OI['green']
C_QUAD  = OI['orange']
C_FAINT = '#bbbbbb'


# -----------------------------------------------------------------
# Selection regimes
# -----------------------------------------------------------------
n     = 4
Gamma = 0.20 * np.eye(n)
b_full = np.array([0.30, 0.20, 0.15, 0.10])
G0    = 2.0 * np.eye(n)
N_GEN = 1000

# --- Episode schedule for the natural population ---
EPISODES = [
    (40,   15),   # (centre, half-width)
    (240,  30),
    (700,  60),
]
B_QUIET = 0.05
B_PEAK  = 1.00

def episode_envelope(t):
    """Smooth top-hat envelope in [B_QUIET, B_PEAK] over generation t."""
    amp = B_QUIET
    for tc, hw in EPISODES:
        rise = 1.0 / (1.0 + np.exp(-(t - (tc - hw)) / 4.0))
        fall = 1.0 / (1.0 + np.exp( (t - (tc + hw)) / 4.0))
        amp += (B_PEAK - B_QUIET) * rise * fall
    return min(amp, B_PEAK)

def b_natural(t):
    return episode_envelope(t) * b_full


# -----------------------------------------------------------------
# Run the two simulations
# -----------------------------------------------------------------
br = trajectory(G0=G0, G_genic0=G0, b=b_full, Gamma=Gamma,
                E=0.05 * np.eye(n), M=1e-5 * np.eye(n),
                rho=0.95, Ne=100, n_gen=N_GEN)

nat = trajectory(G0=G0, G_genic0=G0, b=b_natural, Gamma=Gamma,
                 E=0.50 * np.eye(n), M=2e-3 * np.eye(n),
                 rho=0.40, Ne=500, n_gen=N_GEN)

t = np.arange(0, N_GEN + 1)
t_log = t.copy()
t_log[0] = 1


# -----------------------------------------------------------------
# Diagnostics
# -----------------------------------------------------------------
print('Diagnostics for Fig 4 (episodic natural):')
print(f'  Initial A_g (both):                 {br["A_g"][0]:.3f}')
print(f'  Breeding A_g at t=10, 100, 1000:    '
      f'{br["A_g"][10]:.3f}, {br["A_g"][100]:.3f}, {br["A_g"][1000]:.3f}')
print(f'  Natural A_g at episode peaks (40, 240, 700): '
      f'{nat["A_g"][40]:.3f}, {nat["A_g"][240]:.3f}, {nat["A_g"][700]:.3f}')
print(f'  Natural A_g at quiet (10, 100, 400, 950):    '
      f'{nat["A_g"][10]:.4f}, {nat["A_g"][100]:.4f}, '
      f'{nat["A_g"][400]:.4f}, {nat["A_g"][950]:.4f}')
print(f'  Breeding gens with A_g >= 0.8:      '
      f'{int(np.sum(br["A_g"] >= 0.8))}/{N_GEN+1}')
print(f'  Natural  gens with A_g >= 0.8:      '
      f'{int(np.sum(nat["A_g"] >= 0.8))}/{N_GEN+1}')
print(f'  Breeding tr(G) at t=0, 100, 1000:   '
      f'{br["tr_G"][0]:.2f}, {br["tr_G"][100]:.2f}, {br["tr_G"][1000]:.4f}')
print(f'  Natural  tr(G) at t=0, 100, 1000:   '
      f'{nat["tr_G"][0]:.2f}, {nat["tr_G"][100]:.2f}, {nat["tr_G"][1000]:.2f}')


# -----------------------------------------------------------------
# Helper: shade episode bands on a given axis
# -----------------------------------------------------------------
def shade_episodes(ax, alpha=0.13):
    for tc, hw in EPISODES:
        ax.axvspan(max(tc - hw, 1), tc + hw, color=OI['blue'],
                   alpha=alpha, lw=0, zorder=0)


# -----------------------------------------------------------------
# Build the figure
# -----------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(183 * MM, 130 * MM))
(axA, axB), (axC, axD) = axes


# ============ Panel A: tr(G)/n on log time ============
shade_episodes(axA)
axA.plot(t_log, br['tr_G']  / n, color=C_BRE, lw=1.5)
axA.plot(t_log, nat['tr_G'] / n, color=C_NAT, lw=1.5)
axA.set_xscale('log')
axA.set_yscale('log')
axA.set_xlim(1, N_GEN)
axA.set_ylim(1e-3, 5)
axA.set_xlabel('Generation')
axA.set_ylabel(r'$\mathrm{tr}(\mathbf{G})/n$  (mean genetic variance per axis)')
axA.set_title('A. Genetic variance', loc='left', fontweight='bold')

axA.text(15, 2.4, 'Natural\nrelaxes toward\n' + r'$N_e\mathbf{M}$ equilibrium',
         fontsize=6.5, color=C_NAT, ha='center', va='center')
axA.text(35, 0.012, r'Breeding: $\mathbf{G}\to 0$' + '\n(Bulmer dominates)',
         fontsize=6.5, color=C_BRE, ha='center', va='center')

axA.axvline(100, color=C_FAINT, lw=0.4, ls=':', zorder=0)
axA.text(110, 1.5e-3, '~Illinois maize\nhorizon (~100 gens)',
         fontsize=5.5, color='#666', ha='left', va='bottom', zorder=1)


# ============ Panel B: A_g on log time ============
shade_episodes(axB)
axB.axhspan(0.80, 1.00, color=OI['yellow'], alpha=0.22, lw=0)
axB.axhline(0.80, color='#888', lw=0.4, ls='--')
axB.text(1.3, 0.815, r'additive channel ($\mathcal{A}_g \geq 0.8$, illustrative)',
         fontsize=6, color='#555', va='bottom')

axB.plot(t_log, br['A_g'],  color=C_BRE, lw=1.5)
axB.plot(t_log, nat['A_g'], color=C_NAT, lw=1.5)

# Mark when breeding enters channel
ent = int(np.argmax(br['A_g'] >= 0.8))
axB.plot([t_log[ent]], [br['A_g'][ent]], 'o', color=C_BRE, ms=4.5, zorder=5)
axB.annotate(f'enters at gen {ent}',
             xy=(t_log[ent], br['A_g'][ent]),
             xytext=(95, 0.69),
             fontsize=6, color=C_BRE,
             arrowprops=dict(arrowstyle='-', color=C_BRE, lw=0.5))

# Regime labels — breeding label right-aligned at upper right of panel
axB.text(950, 0.93, r'Breeding (sustained $\mathbf{b}$) $\to 1$',
         fontsize=7, color=C_BRE, ha='right', va='top', fontweight='bold')

# Annotate the first natural spike with a short, on-axis label
peak_t = 40
peak_a = nat['A_g'][peak_t]
axB.annotate(
    'Natural — episodic spikes',
    xy=(peak_t, peak_a),
    xytext=(2.5, 0.30),
    fontsize=6.5, color=C_NAT, ha='left', va='center',
    arrowprops=dict(arrowstyle='-', color=C_NAT, lw=0.5),
)

# "Episode" labels on each band
for k, (tc, _) in enumerate(EPISODES):
    axB.text(tc, 0.05, 'episode', fontsize=5.5, color=C_NAT,
             ha='center', va='bottom', style='italic', alpha=0.85)

axB.axvline(100, color=C_FAINT, lw=0.4, ls=':', zorder=0)

axB.set_xscale('log')
axB.set_xlim(1, N_GEN)
axB.set_ylim(0.0, 1.02)
axB.set_xlabel('Generation')
axB.set_ylabel(r'Additivity index  $\mathcal{A}_g$')
axB.set_title(r'B. Additivity index  $\mathcal{A}_g$',
              loc='left', fontweight='bold')


# ============ Panel C: Variance decomposition for NATURAL ============
shade_episodes(axC)
axC.plot(t_log, nat['V_lin'],  color=C_LIN,  lw=1.5)
axC.plot(t_log, nat['V_quad'], color=C_QUAD, lw=1.5, ls='--')
axC.set_xscale('log')
axC.set_xlim(1, N_GEN)
axC.set_ylim(0, 0.36)
axC.set_xlabel('Generation')
axC.set_ylabel(r'Log-fitness variance')
axC.set_title('C. Natural: variance decomposition', loc='left', fontweight='bold')

axC.text(240, nat['V_lin'][240] + 0.025,
         r'$V_\mathrm{lin} = \mathbf{b}^\top \mathbf{G b}$ (spikes with episodes)',
         fontsize=6.5, color=C_LIN, ha='center', va='bottom')
axC.text(120, 0.085,
         r'$V_\mathrm{quad} = \frac{1}{2}\mathrm{tr}[(\mathbf{HG})^2]$' + '\n(slow decline)',
         fontsize=6.5, color=C_QUAD, ha='center', va='top')


# ============ Panel D: Variance decomposition for BREEDING (log y) ============
axD.plot(t_log, br['V_lin'],  color=C_LIN,  lw=1.5)
axD.plot(t_log, br['V_quad'], color=C_QUAD, lw=1.5, ls='--')
axD.set_xscale('log')
axD.set_yscale('log')
axD.set_xlim(1, N_GEN)
axD.set_ylim(1e-7, 2)
axD.set_xlabel('Generation')
axD.set_ylabel(r'Log-fitness variance')
axD.set_title('D. Breeding: variance decomposition (log scale)',
              loc='left', fontweight='bold')

axD.text(40, 0.05, r'$V_\mathrm{lin} \sim \|\mathbf{G}\|$',
         fontsize=7, color=C_LIN, ha='left', va='bottom')
axD.text(40, 5e-3, r'$V_\mathrm{quad} \sim \|\mathbf{G}\|^2$',
         fontsize=7, color=C_QUAD, ha='left', va='top')
axD.text(1.5, 1.3e-7,
         r'$V_\mathrm{quad}$ collapses faster: that is why $\mathcal{A}_g \to 1$.',
         fontsize=6, color='#555', ha='left', va='bottom', style='italic')


plt.subplots_adjust(left=0.075, right=0.985, bottom=0.085, top=0.94,
                    wspace=0.28, hspace=0.42)

out_pdf = '/home/claude/figs/out/figure4_natural_vs_breeding.pdf'
out_png = '/home/claude/figs/out/figure4_natural_vs_breeding.png'
plt.savefig(out_pdf, dpi=400)
plt.savefig(out_png, dpi=200)
print(f'\nSaved: {out_pdf}')
print(f'       {out_png}')
