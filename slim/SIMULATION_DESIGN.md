# SLiM validation: simulation design and background

This document explains the simulation accompanying *Additive Channels in
Curved Fitness Landscapes* (Ortiz-Barrientos & Cooper, GENETICS-2026-309068).
It is the long-form companion to the operational `README.md`. The README
tells you which command to type; this document tells you what the commands
mean and why we made the design choices we made.

Audience: a quantitative geneticist who is comfortable with multivariate
selection theory (Lande, Bulmer, breeding values) but may not have used
SLiM. The goal is that, after reading, you should be able to (i) reproduce
our simulation; (ii) understand each design decision; (iii) modify the
simulation intelligently to test variants; and (iv) decide whether the
results constitute a fair validation of the framework's claims.

---

## 1. What we are testing

The framework we develop in the manuscript states that, under Gaussian
closure of the breeding-value distribution, the *additivity index*

$$
\mathcal{A}_g \;=\; \frac{V_{\text{lin}}}{V_{\text{lin}} + V_{\text{quad}}}
$$

equals the squared correlation $R^2$ between two quantities computed across
a population: the linear predictor

$$
L_i \;=\; \mathbf{b}^{\top}(\mathbf{a}_i - \bar{\mathbf{a}})
$$

and the full local log-fitness $\ell_i = \log W(\mathbf{a}_i)$. Here
$\mathbf{a}_i$ is individual $i$'s breeding-value vector, $\bar{\mathbf{a}}$
the population mean, $\mathbf{b}$ the gradient of log-fitness at
$\bar{\mathbf{a}}$, $\mathbf{H}$ the Hessian, and $\mathbf{G}$ the genetic
covariance matrix; the variances on the right-hand side are
$V_{\text{lin}} = \mathbf{b}^{\top}\mathbf{G}\mathbf{b}$ and
$V_{\text{quad}} = \tfrac{1}{2}\,\text{tr}[(\mathbf{H}\mathbf{G})^2]$.

The identity $\mathcal{A}_g = R^2$ is the framework's central testable
prediction. Any departure from it — under conditions where Gaussian closure
is supposed to hold — would falsify the framework. Conversely, a tight
match across a non-trivial trajectory provides quantitative validation that
the framework's variance partition captures what it claims to capture.

The simulation is designed to test this identity directly. We construct a
population whose breeding-value distribution we can sample, evolve it under
a fitness landscape we have written down explicitly, and then ask: does the
analytical $\mathcal{A}_g$ (computed from the empirical $\mathbf{G}$ and
the analytical $\mathbf{b}$, $\mathbf{H}$) actually predict the empirical
$R^2$ between the linear predictor and the full log-fitness, generation
after generation? That is the question the simulation answers.

A few things this simulation is *not* trying to do. It is not an estimate
of any natural population's $\mathbf{G}$ or fitness landscape. It is not a
demonstration that real populations sit in additive channels. It is a
controlled mathematical validation: under conditions we control, does the
framework's identity hold to within sampling precision? If yes, the
framework's claim is internally consistent. Whether real populations
behave the way the model assumes is a separate empirical question that
must be addressed with field data, not simulation.

## 2. Why simulate at all, and why SLiM

Forward, individual-based simulation is the natural setting to test
predictions about quantitative-genetic dynamics. The framework's quantities
($\mathbf{G}$, $\mathbf{b}$, $\mathbf{H}$, $\mathcal{A}_g$, $R^2$) are
properties of populations, not of single individuals or of allele
frequencies in isolation. We need a tool that tracks each individual's
genotype and breeding value, applies sexual reproduction and recombination
correctly, and lets us prescribe an arbitrary fitness function. Pure
allele-frequency simulators (such as classical diffusion approximations or
multilocus moment-based simulators) lose the individual-level information
we need to compute population $R^2$.

[SLiM](https://messerlab.org/slim/) is a forward-time, individual-based
simulator developed by Haller and Messer that has become the de facto
standard in evolutionary genetics. We chose SLiM for four reasons. First,
it tracks individuals and their full genotypes, which is exactly what we
need to compute breeding values. Second, it implements sexual reproduction,
recombination, drift, and arbitrary user-specified fitness functions
correctly and well. Third, the relevant population-genetic machinery is
written and tested by the simulator's authors — we do not have to vouch
for our own implementation of basic Wright–Fisher dynamics. Fourth, SLiM
is widely recognised by reviewers; saying "we ran a SLiM simulation" comes
with established expectations about correctness and reproducibility.

We could in principle have written a pure Python Wright-Fisher simulator
ourselves, and the dynamics would be the same. But we would then have had
to implement, document, and defend a recombination engine, a Wright-Fisher
sampler, the bookkeeping for diploid sexual mating, and the calling
conventions for fitness — each of which is both standard and
fault-prone. SLiM removes all of that from our concerns and lets us focus
on the diagnostic computation. Python remains the right tool for the
diagnostic layer (numerical linear algebra on the breeding values that
SLiM produces), where its NumPy ecosystem is far cleaner than SLiM's
internal scripting language.

## 3. SLiM in twenty minutes

SLiM is configured by a script written in *Eidos*, a small scripting
language with R-like syntax. The script tells SLiM what genome to
simulate, what population to put on it, what fitness function to apply,
and what to log. SLiM then runs the simulation in time, calling user-
defined "callbacks" at specific points each generation.

Here are the SLiM concepts our script uses, in roughly the order they
appear in our code.

A *mutation type* is a category of mutations sharing parameters such as
dominance coefficient and selection coefficient. We use one mutation type
(`m1`) with dominance 0.5 (additive: heterozygotes have half the effect of
homozygotes) and selection coefficient 0.0. The selection coefficient is
zero because we do not want SLiM to apply per-mutation selection — instead
we will impose selection through a fitness function on the individual's
phenotype, which is what we actually want. Mutations of type `m1` are
therefore neutral as far as SLiM's internal selection machinery is
concerned, but they carry trait-effect information via attribute slots
(`setValue`/`getValue`) that we use to compute breeding values.

A *genomic element* is a region of the chromosome where mutations of a
given type are allowed. We define one genomic element spanning positions
$0$ through $99$ — one position per QTL. The mutation rate is set to zero
because we want to study the dynamics of standing variation only; new
mutations are not introduced during the simulation.

A *haplosome* is one of the two chromosomes a diploid individual carries.
SLiM 5 renamed the older "genome" object to "haplosome" to avoid the
ambiguity between *the genome* (the species-level concept) and *a genome*
(one chromosome of an individual). Each haplosome carries a list of
mutations — the alleles that distinguish it from the reference. An
individual's `individual.haplosomes` returns the two haplosomes; their
`mutations` is the union of mutations across both. To compute a diploid
breeding value, we sum the trait effects of the mutations on both
haplosomes — a non-carrier contributes zero, a heterozygote contributes
$\alpha$, a homozygote contributes $2\alpha$.

A *subpopulation* is a Wright-Fisher population of fixed size. We use one
subpopulation, `p1`, of size $N = 2000$.

The *Wright-Fisher lifecycle* is what SLiM does each tick (generation):

1. `first()` events fire (we don't use any).
2. *Offspring generation*: SLiM produces $N$ offspring by sampling parents
   weighted by their fitness, with sexual reproduction, recombination, and
   (here) no mutation.
3. `early()` events fire. Offspring are now the population.
4. SLiM recalculates fitness for each individual, calling our
   `fitnessEffect()` callback once per individual.
5. `late()` events fire.

The fitness recalculation in step 4 produces the multiplicative weights
that SLiM uses in the *next* tick's offspring generation. So a fitness
value computed in tick $t$ governs which offspring are produced in tick
$t+1$. This is the standard WF semantics; the only thing worth flagging
is the one-tick lag between fitness calculation and selection.

The `fitnessEffect()` callback returns a multiplicative fitness modifier
for the focal individual. Inside the callback, the variable `individual`
is implicitly defined and refers to the individual being evaluated. Our
callback computes the individual's two-trait breeding value from its
mutations, then evaluates a Gaussian fitness function. The returned
multiplier is what SLiM uses for selection.

An *event block* is code that runs at specific ticks. The syntax `1
early() { ... }` runs the block at tick 1, in the early stage. The
syntax `1: late() { ... }` runs the block at every tick from 1 onward, in
the late stage. The syntax `200 late() { ... }` runs the block only at
tick 200. We use all three patterns.

`writeFile(path, content, append=T)` writes a string vector to a file
with each element on its own line. We use it to log per-individual
breeding values once per generation.

## 4. From the framework to the simulation

The framework's mathematical objects map onto simulation choices as
follows.

| Framework object | Mathematical definition | How it appears in the simulation |
| --- | --- | --- |
| Breeding value $\mathbf{a}_i$ | Additive genetic value vector | Sum of allele effects across both haplosomes of individual $i$ |
| Genetic covariance $\mathbf{G}$ | $\text{Cov}(\mathbf{a})$ over the population | Empirical: sample covariance of BVs computed in Python from the simulation output |
| Log-fitness gradient $\mathbf{b}$ | $\nabla \ell\big\vert_{\bar{\mathbf{a}}}$ | Analytical: $\mathbf{b} = -\boldsymbol{\Gamma}(\bar{\mathbf{a}} - \mathbf{z}^*)$ for our quadratic landscape |
| Log-fitness Hessian $\mathbf{H}$ | $\nabla^2 \ell\big\vert_{\bar{\mathbf{a}}}$ | Analytical: $\mathbf{H} = -\boldsymbol{\Gamma}$ (constant) |
| Linear predictor $L_i$ | $\mathbf{b}^{\top}(\mathbf{a}_i - \bar{\mathbf{a}})$ | Computed from analytical $\mathbf{b}$ and empirical centred BVs |
| Full log-fitness $\ell_i$ | $-\tfrac{1}{2}(\mathbf{a}_i - \mathbf{z}^*)^{\top} \boldsymbol{\Gamma} (\mathbf{a}_i - \mathbf{z}^*)$ | Computed from each individual's BV using the prescribed landscape |

A point worth dwelling on: $\mathbf{G}$ is computed *empirically* from the
simulated population, while $\mathbf{b}$ and $\mathbf{H}$ are computed
*analytically* from the prescribed fitness function. This is deliberate.
The framework's claim is that, given a population's $\mathbf{G}$ and the
local geometry $(\mathbf{b}, \mathbf{H})$, the analytical
$\mathcal{A}_g$ predicts the population's $R^2$. We test that claim by
giving the framework the empirical $\mathbf{G}$ (which it would have to
estimate from data in any real application) together with the analytical
$\mathbf{b}$ and $\mathbf{H}$ (which we know exactly because we wrote the
landscape), and seeing whether its prediction matches the empirical
$R^2$ computed independently from the same population.

This conditioning is sometimes raised as a concern: "you knew the answer."
What we *knew* is the fitness landscape — its slope and curvature at any
point. What we *predicted* is the population-level statistic $R^2$. The
simulation does not let us know $R^2$ in advance; we have to compute it
from the simulated population. Knowing the landscape is exactly the
position of someone who has measured selection gradients and curvatures
in the field with Lande-Arnold style regressions; the framework's job is
then to predict whether linear analyses of that population will work. The
simulation tests precisely that prediction.

## 5. The fitness landscape, in full

We use a centred anisotropic Gaussian quadratic stabilising selection
landscape:

$$
W(\mathbf{z}) \;=\; \exp\left[ -\tfrac{1}{2}\,(\mathbf{z} - \mathbf{z}^*)^{\top}
                                 \boldsymbol{\Gamma}\,(\mathbf{z} - \mathbf{z}^*) \right]
$$

with $\boldsymbol{\Gamma} = \text{diag}(\gamma_1, \gamma_2)$ and
$\mathbf{z}^* = (z^*_1, z^*_2)$. Log-fitness is therefore exactly
quadratic:

$$
\ell(\mathbf{z}) \;=\; \log W(\mathbf{z}) \;=\;
-\tfrac{1}{2}\,(\mathbf{z} - \mathbf{z}^*)^{\top}
              \boldsymbol{\Gamma}\,(\mathbf{z} - \mathbf{z}^*) \,.
$$

The gradient and Hessian follow by direct differentiation:

$$
\nabla_{\mathbf{z}} \ell \;=\; -\boldsymbol{\Gamma}(\mathbf{z} - \mathbf{z}^*),
\qquad
\nabla^2_{\mathbf{z}} \ell \;=\; -\boldsymbol{\Gamma}.
$$

Two consequences.

First, because the landscape is exactly quadratic, the second-order Taylor
expansion the framework uses is *exact*, not an approximation. Higher-
order terms vanish identically. This is the cleanest possible test case
for the framework: if the identity $\mathcal{A}_g = R^2$ does not hold
here, it cannot be rescued by appealing to higher-order Taylor terms.

Second, because we have set environmental variance to zero ($\mathbf{E} =
\mathbf{0}$), phenotype equals breeding value: $\mathbf{z}_i =
\mathbf{a}_i$. Selection acts directly on breeding values. This isolates
the BV→fitness curvature claim — the question the framework actually
addresses — from the separate question of how environmental noise affects
selection efficiency. A more elaborate simulation would add $\mathbf{E} >
\mathbf{0}$ and check that the analytical buffering correction (the
$\mathbf{H}_{\mathbf{a}}^{-1} = \mathbf{H}_{\mathbf{z}}^{-1} - \mathbf{E}$
relation in the Lande–Arnold dictionary appendix of the manuscript)
recovers the right answer. We have left that to the full version.

At the population mean $\bar{\mathbf{a}}$, the analytical gradient and
Hessian are therefore $\mathbf{b} = -\boldsymbol{\Gamma}\,(\bar{\mathbf{a}}
- \mathbf{z}^*)$ and $\mathbf{H} = -\boldsymbol{\Gamma}$. The Python
diagnostic (`compute_diagnostics.py`) computes these from the simulation's
prescribed $\boldsymbol{\Gamma}$ and $\mathbf{z}^*$ together with the
generation-by-generation $\bar{\mathbf{a}}$ extracted from the simulated
population.

## 6. Genetic architecture and initial conditions

The genetic architecture is intentionally simple. Two traits, 50 QTL loci
per trait (100 total), no pleiotropy: each locus affects one trait only.
All loci have additive effects with no within-locus dominance and no
between-locus epistasis at the trait level. The genome is conceptual — 100
positions on one chromosome with free recombination between every pair —
which is equivalent to 100 independently inherited unlinked loci.

Allele effects at trait-1 loci are drawn once at the start of the
simulation from a Gaussian: $\alpha^{(1)}_j \sim \mathcal{N}(0, \sigma_1^2)$
for $j = 1, \dots, 50$. After drawing, we *centre* the effects so that
$\sum_j \alpha^{(1)}_j = 0$ exactly. Trait-2 effects are drawn and
centred analogously. Centring matters: without it, the realised sum of 50
random effects has standard deviation $\sigma_1 \sqrt{50} \approx 2.45$ for
$\sigma_1 = 0.346$. With probability around 1/3 the realised sum lies more
than 2 units from zero, which would place the population mean BV
arbitrarily far from where we intended. With centring, the initial
population mean BV is exactly zero by construction. The cost is a 2%
reduction in effective per-locus variance: residuals after subtracting the
sample mean from $n$ Gaussian draws have variance $\sigma^2 (n-1)/n$.

Per-locus effect standard deviations $\sigma_1 = \sqrt{3/25} \approx 0.346$
and $\sigma_2 = \sqrt{1/25} = 0.200$ are chosen so that the initial
genetic covariance matrix at Hardy–Weinberg equilibrium is

$$
\mathbf{G}_0 \;\approx\; \text{diag}(3, 1)
$$

with a 3:1 anisotropy. The arithmetic: at allele frequency $p = 0.5$,
each diploid locus contributes $2 p (1-p) \alpha^2 = 0.5 \alpha^2$ to the
trait variance. With 50 loci per trait and centred effects, the expected
diagonal of $\mathbf{G}$ is $50 \times 0.5 \times \sigma_i^2 = 25
\sigma_i^2$, which gives $25 \times (3/25) = 3$ for trait 1 and $25 \times
(1/25) = 1$ for trait 2.

The optimum is placed at $\mathbf{z}^* = (-2, 0)$, two units from the
initial population mean along trait 1. This means the population starts
with a substantial gradient $\mathbf{b}_0 = -\boldsymbol{\Gamma}
(\bar{\mathbf{a}}_0 - \mathbf{z}^*) = -\boldsymbol{\Gamma}(0 - (-2),\,0)
= (-\gamma_1 \cdot 2,\,0) = (-0.20,\,0)$, with $|\mathbf{b}_0| = 0.20$.
The displacement is along trait 1 only; trait 2 is in the basin of the
optimum from the start.

Why this asymmetry? The setup separates two effects we want the framework
to handle simultaneously. Trait 1 experiences both directional selection
(because $b_1 \neq 0$) and stabilising selection (because $\gamma_1 > 0$).
Trait 2 experiences pure stabilising selection. Watching the framework's
diagnostic across both traits, in the same population at the same time,
is more informative than running them separately.

## 7. Walking through the SLiM script

The script (`slim_sim.slim`) has six blocks. We walk through them in
execution order.

### `initialize()`

Defines simulation-wide parameters and the genomic architecture. SLiM
calls this exactly once before tick 1.

```eidos
defineConstant("N", 2000);
defineConstant("GAMMA_1", 0.10);
defineConstant("GAMMA_2", 0.05);
defineConstant("Z_OPT_1", -2.0);
defineConstant("Z_OPT_2",  0.0);
```

`defineConstant` creates a global constant accessible from every event
block. The `if (!exists("X")) defineConstant("X", default)` pattern
provides a default value that command-line `-d` flags override:

```bash
slim -d "OUTPUT_PATH='output/rep_05.csv'" -d "SEED=2026" slim_sim.slim
```

This is how we will scale to multiple replicates without editing the
script.

```eidos
initializeMutationType("m1", 0.5, "f", 0.0);
m1.convertToSubstitution = F;
```

One mutation type, m1. Dominance 0.5 (additive), selection coefficient
0.0 (neutral on its own — selection is imposed externally by
`fitnessEffect()`). The `convertToSubstitution = F` line is critical: by
default SLiM converts fixed mutations into "substitutions" and removes
them from each individual's mutation list. For a neutral marker that
would be fine, but our mutations carry the trait effects that compose
breeding values — losing them would silently zero out the BV
contribution from any locus that drifts to fixation. We force them to
stay in the segregating set.

```eidos
initializeMutationRate(0);
initializeRecombinationRate(0.5);
```

No new mutations during the simulation: variation is the standing
polymorphism we set up at tick 1. Recombination rate 0.5 between
adjacent positions makes every pair of QTLs free-recombining,
equivalent to 100 unlinked loci. This isolates the dynamics from
linkage effects, which are a separate axis of complication that the
framework's basic claim does not depend on.

### `1 early()`: create the empty population

```eidos
1 early() {
    sim.addSubpop("p1", N);
}
```

Tick 1's early stage creates the population of $N$ diploid individuals.
The individuals exist but carry no mutations yet; their breeding values
are zero. The QTLs are placed in the next block.

### `1 late()`: place QTLs and open the output file

This is the heart of the simulation setup.

```eidos
eff1_all = rnorm(L_PER_TRAIT, 0, SIGMA_1);
eff1_all = eff1_all - mean(eff1_all);
```

Draw 50 trait-1 effects from $\mathcal{N}(0, \sigma_1^2)$, then subtract
the mean so they sum exactly to zero. Centring is done independently for
each trait.

```eidos
target = sample(haps, asInteger(n_haps * 0.5));
new_mut = target.addNewDrawnMutation(m1, i);
new_mut.setValue("eff1", eff1);
new_mut.setValue("eff2", eff2);
```

For each of the 100 loci, we sample half the haplosomes uniformly at
random, then place one mutation at locus $i$ on all of them with a single
call to `addNewDrawnMutation`. Critical point: `addNewDrawnMutation`
called on a vector of haplosomes returns *one* Mutation object that
becomes resident on every haplosome in the vector — not one mutation per
haplosome. This is the standard QTL "shared allele" pattern. The single
mutation object then carries the trait effects via `setValue("eff1", x)`
and `setValue("eff2", y)`. When we later compute an individual's BV by
iterating over its haplosomes' mutations, each carrier of locus $i$
contributes one copy of $\alpha^{(1)}_i$ per haplosome that carries it —
zero, one, or two copies for a non-carrier, heterozygote, or homozygote
respectively. Across the population, allele frequency at every locus is
exactly 0.5 by construction (half the haplosomes carry the mutation).

Why we place QTLs in `late()` rather than `early()`: SLiM emits a warning
when `addNewDrawnMutation` is called from a `first()` or `early()` event
in a Wright-Fisher model, because mutations introduced before offspring
generation can produce subtly inconsistent fitness bookkeeping in tick 1.
For our setup the warning is cosmetic — the simulation runs correctly in
either case — but moving the placement to `late()` is the canonical SLiM
QTL recipe pattern and silences the warning.

### `fitnessEffect()`: the selection function

```eidos
fitnessEffect() {
    muts = individual.haplosomes.mutations;
    z1 = sum(muts.getValue("eff1"));
    z2 = sum(muts.getValue("eff2"));
    
    dx = z1 - Z_OPT_1;
    dy = z2 - Z_OPT_2;
    
    return exp(-0.5 * (GAMMA_1 * dx * dx + GAMMA_2 * dy * dy));
}
```

SLiM calls this once per individual during the fitness recalculation
stage. Inside, `individual` is the focal individual being evaluated.
`individual.haplosomes` returns the two haplosomes of the diploid;
`.mutations` returns the union of mutations carried across both. Summing
`getValue("eff1")` over those mutations yields the trait-1 breeding
value: every locus where the individual is a heterozygote contributes
$\alpha^{(1)}$ once (one haplosome carries the mutation), every
homozygous-carrier locus contributes $\alpha^{(1)}$ twice. The same logic
gives trait-2 BV. Phenotype equals BV here because $\mathbf{E} =
\mathbf{0}$.

The returned value is the multiplicative fitness $W(\mathbf{z})$. SLiM
uses these values to weight parents in the next tick's offspring
generation, so fitness computed in tick $t$ governs reproduction into
tick $t+1$. There is no manipulation of expected family size beyond what
this multiplier dictates; selection is purely viability-based via fitness
weighting.

### `1: late()`: per-generation logging

```eidos
1: late() {
    inds = p1.individuals;
    n = length(inds);
    gen = sim.cycle;
    
    z1_vec = float(n);
    z2_vec = float(n);
    for (i in seqLen(n)) {
        muts = inds[i].haplosomes.mutations;
        z1_vec[i] = sum(muts.getValue("eff1"));
        z2_vec[i] = sum(muts.getValue("eff2"));
    }
    
    lines = string(n);
    for (i in seqLen(n)) {
        lines[i] = gen + "," + i + "," + z1_vec[i] + "," + z2_vec[i];
    }
    
    writeFile(OUTPUT_PATH, lines, append=T);
}
```

The `1:` prefix means "from tick 1 onward, every tick". This block runs
in `late()` of every generation and writes one CSV line per individual.
We compute each individual's two-trait BV (the same way `fitnessEffect()`
does), then build $n$ formatted strings — one per individual — and append
them to the output file.

A subtlety we paid for in development: Eidos's `paste0()` function does
not broadcast vector arguments element-wise the way R's does. Given two
vectors of length $n$, `paste0` concatenates all elements into a single
string of length 1, not element-wise into a string vector of length $n$.
The fix is to build strings explicitly with the `+` operator, which in
Eidos coerces a number to a string when concatenated with one. The
explicit `for` loop is also more transparent for someone reading the
script.

The output CSV grows by 2000 lines per generation. For 200 generations
this is 400,001 lines (header plus $200 \times 2000$ data rows). The file
is still small enough (about 10 MB) that we read it whole in Python.

### `GENS late()`: stop the simulation

```eidos
GENS late() {
    sim.simulationFinished();
}
```

SLiM runs forever by default. `sim.simulationFinished()` tells it to
stop after the current tick. Placing this in `GENS late()` means
"stop at the end of tick `GENS`", which is tick 200 in our PoC.

## 8. The Python diagnostic

`compute_diagnostics.py` reads the SLiM CSV and computes the per-
generation diagnostics. Its core function is
`compute_diagnostics_per_generation`, which loops over generations and
performs the following computation for each.

Read the BVs at this generation as an $N \times 2$ matrix
$\mathbf{A}$. Compute the population mean $\bar{\mathbf{a}} =
\mathbf{A}^{\top}\mathbf{1}/N$ and centred BVs $\Delta\mathbf{A} =
\mathbf{A} - \mathbf{1}\bar{\mathbf{a}}^{\top}$. Compute the empirical
genetic covariance $\hat{\mathbf{G}} = (\Delta\mathbf{A})^{\top}
\Delta\mathbf{A} / (N-1)$ via `np.cov(A, rowvar=False, ddof=1)`. Compute
the analytical local geometry: $\mathbf{H} = -\boldsymbol{\Gamma}$
(constant, set once at the start) and $\mathbf{b} = -\boldsymbol{\Gamma}
(\bar{\mathbf{a}} - \mathbf{z}^*)$.

Compute the variance partition:

$$
V_{\text{lin}} = \mathbf{b}^{\top} \hat{\mathbf{G}} \mathbf{b},
\qquad
V_{\text{quad}} = \tfrac{1}{2} \,\text{tr}\!\left[\big(\mathbf{H} \hat{\mathbf{G}}\big)^2\right],
\qquad
\mathcal{A}_g = \frac{V_{\text{lin}}}{V_{\text{lin}} + V_{\text{quad}}}.
$$

Now compute the empirical $R^2$. For each individual, the linear
predictor and full log-fitness are

$$
L_i = \mathbf{b}^{\top} \Delta\mathbf{a}_i,
\qquad
\ell_i = -\tfrac{1}{2}\,(\mathbf{a}_i - \mathbf{z}^*)^{\top}
                       \boldsymbol{\Gamma}\,(\mathbf{a}_i - \mathbf{z}^*).
$$

The full $\ell_i$ is computed by `np.einsum("ij,jk,ik->i", z_centred,
Gamma, z_centred)` with a leading minus-one-half — a vectorised quadratic
form that handles all $N$ individuals at once. Then $R^2 = [\text{cor}(L,
\ell)]^2$ via `np.corrcoef(L, ell)[0, 1]**2`.

The output CSV from this step has one row per generation with columns
`gen`, `a_bar_1`, `a_bar_2`, `G_11`, `G_22`, `G_12`, `b_1`, `b_2`,
`b_norm`, `V_lin`, `V_quad`, `A_g`, `R2_empirical`, and `Ag_minus_R2`.
The final column is the diagnostic of diagnostics: under exact Gaussian
closure it should be zero up to sampling noise. Any sustained, signed
departure indicates closure has broken.

## 9. Parameter choices, in detail

| Parameter | Value | Reason |
| --- | --- | --- |
| $N$ (population size) | 2000 | Large enough that drift is weak relative to selection; small enough to run in seconds. With $\gamma_1 = 0.1$, $N \gamma_1 = 200 \gg 1$, so selection dominates drift. |
| $L$ (loci per trait) | 50 | Polygenic enough for the central limit theorem to give approximately Gaussian BVs. With 50 contributing loci of comparable effect, the BV distribution should be very nearly Gaussian even before any centering. |
| Recombination rate | 0.5 | Free recombination between every pair of QTLs. Eliminates linkage as a confound; isolates the dynamics from LD effects. |
| Mutation rate | 0 | Standing variation only. Adding mutational input is a separate question we leave for later iterations. |
| $\sigma_1$ (per-locus effect SD, trait 1) | $\sqrt{3/25} \approx 0.346$ | Calibrated so $G_{11}$ at HWE is $\approx 3$. |
| $\sigma_2$ (per-locus effect SD, trait 2) | $\sqrt{1/25} = 0.200$ | Calibrated so $G_{22}$ at HWE is $\approx 1$, giving 3:1 anisotropy. |
| $\gamma_1$ (selection on trait 1) | 0.10 | Weak. The selection coefficient against an individual one BV-SD ($\sqrt{G_{11}} \approx 1.7$) from optimum is $\approx \tfrac{1}{2}\gamma_1 \cdot G_{11} \approx 0.15$ — strong enough to act, weak enough that Gaussian closure should hold. |
| $\gamma_2$ (selection on trait 2) | 0.05 | Half as strong as on trait 1 — anisotropic curvature complementing the anisotropic G. |
| $\mathbf{z}^*$ (optimum) | $(-2, 0)$ | Two units from the centred population mean along trait 1. Initial $|\mathbf{b}|_0 = \gamma_1 \cdot 2 = 0.20$, large enough to drive substantial dynamics. |
| Generations | 200 | Long enough to traverse rise-and-fall of $\mathcal{A}_g$. |

The choice that matters most for the validation is the selection
strength. Too weak, and nothing happens — the population just drifts in
place with $|\mathbf{b}|$ negligible from the start. Too strong, and
Gaussian closure breaks: the BV distribution develops skew under strong
truncating-style selection, $\text{Cov}(L, Q)$ stops being zero, and the
identity $\mathcal{A}_g = R^2$ stops holding exactly. The PoC value
$\gamma_1 = 0.1$ is intentionally in the safe regime for closure.

## 10. The dynamics we expect to see

A back-of-envelope prediction of the trajectory:

The initial state has $\bar{\mathbf{a}} = (0, 0)$ by construction
(centred effects), $\mathbf{G}_0 \approx \text{diag}(3, 1)$,
$\mathbf{b}_0 = (-0.20, 0)$, and $\mathbf{H} = -\text{diag}(0.10, 0.05)$.
The framework's quantities at this state:

$$
V_{\text{lin}} = (-0.20)^2 \cdot 3 + 0^2 \cdot 1 = 0.12,
\qquad
V_{\text{quad}} = \tfrac{1}{2}[(0.10 \cdot 3)^2 + (0.05 \cdot 1)^2] = 0.046,
$$

so $\mathcal{A}_g(0) \approx 0.12 / (0.12 + 0.046) \approx 0.72$. The
population starts inside the additive channel.

Over the first $\sim 30$ generations, two things happen. Selection pulls
$\bar{\mathbf{a}}_1$ from 0 toward $-2$, so $|\mathbf{b}|$ shrinks
roughly exponentially. At the same time, the Bulmer effect compresses
$G_{11}$ — directional plus stabilising selection on trait 1 reduces its
variance — while $G_{22}$ compresses more slowly because trait 2
experiences only weak stabilising pressure. Both $V_{\text{lin}}$ and
$V_{\text{quad}}$ decrease, but at different rates. $V_{\text{quad}}
\propto \|\mathbf{G}\|^2$ shrinks faster than $V_{\text{lin}} \propto
\|\mathbf{G}\|$, so initially $\mathcal{A}_g$ rises. Meanwhile, however,
$|\mathbf{b}|$ is also collapsing because the population is approaching
the optimum, and $V_{\text{lin}} = |\mathbf{b}|^2 \cdot G_{11}$ has the
$|\mathbf{b}|^2$ term going to zero faster than $G_{11}$. So $\mathcal{A}_g$
peaks somewhere in this window, then falls.

By generation $\sim 100$, the population mean is at the optimum,
$|\mathbf{b}| \approx 0$, $V_{\text{lin}} \approx 0$, and
$\mathcal{A}_g \to 0$. The remaining dynamics are mutation-selection-
drift balance maintaining $\mathbf{G}$ around its (compressed) equilibrium
value.

Throughout this entire trajectory — rising, peaking, falling — the
empirical $R^2$ should track $\mathcal{A}_g$ to within sampling noise.
That is the validation.

## 11. Sanity checks: what to look for, what would indicate trouble

The first run of any new simulation deserves a careful look. The
following checks tell us whether the simulation is producing the dynamics
we designed for, and whether the framework's identity is holding.

| Quantity | Expected value | What it tells us |
| --- | --- | --- |
| `a_bar_1` at gen 1 | $\approx 0.0$ | Centring of allele effects worked; population is at the intended starting position |
| `a_bar_2` at gen 1 | $\approx 0.0$ | Same |
| `G_11` at gen 1 | $\approx 2.94$ | Initial variance is at the calibrated value (3.0 minus the 2% centring correction) |
| `G_22` at gen 1 | $\approx 0.98$ | Same |
| `b_norm` at gen 1 | $\approx 0.20$ | The initial gradient is the analytical $\gamma_1 \cdot 2 = 0.20$ |
| Peak `A_g` | $\approx 0.7$–$0.95$ | The population enters the additive channel during active adaptation |
| `A_g` at gen 200 | small ($< 0.1$) | The population reaches the optimum and the directional component vanishes |
| Median `|A_g - R2|` | $< 0.005$ | The framework's identity holds across the whole trajectory |

Failure modes to watch for. If `a_bar_1` is far from zero at gen 1, the
centring step did not run — check the script. If `b_norm` at gen 1 is far
from 0.20, the optimum is not where we placed it, or the population mean
is. If `A_g` rises but `R2_empirical` does not (or vice versa), the two
quantities have diverged: either the BV distribution is too non-Gaussian
for closure to hold, or there is a bug in the diagnostic. If both stay
near zero throughout, selection is not acting strongly enough to move the
population — check $\gamma_1$ and the optimum.

## 12. Reproducibility and citations

Running the simulation requires SLiM 5.2 or later and Python 3.10+ with
NumPy, Pandas, and Matplotlib. The exact versions used for the proof of
concept are pinned in `requirements.txt`. The simulation seed is set via
the `SEED` constant; the default `SEED = 42` reproduces our PoC trajectory
byte-for-byte. To produce alternative replicates, pass a different seed
on the command line:

```bash
slim -d "OUTPUT_PATH='output/rep_05.csv'" -d "SEED=20260103" slim_sim.slim
```

When citing the simulator, please use the official SLiM 5 reference:

> Haller, B.C., Ralph, P.L., and Messer, P.W. (2026). SLiM 5: Eco-
> evolutionary simulations across multiple chromosomes and full
> genomes. *Molecular Biology and Evolution* 43(1), msaf313.

When citing this validation, please cite the manuscript.

## 13. A short Eidos glossary

For readers new to SLiM's scripting language, the operators and
functions used in our script are:

| Eidos token | Meaning |
| --- | --- |
| `defineConstant("X", val)` | Create a global constant `X` with value `val`. |
| `setSeed(s)` | Seed the random number generator. |
| `rnorm(n, mu, sigma)` | Draw `n` Gaussian samples with mean `mu` and SD `sigma`. |
| `mean(x)`, `sum(x)` | Arithmetic mean / sum of a numeric vector. |
| `seqLen(n)` | Vector `0, 1, …, n-1` (zero-indexed, like Python). |
| `sample(x, k)` | Draw `k` elements of `x` without replacement. |
| `sim.cycle` | The current tick (generation) number. |
| `sim.addSubpop(name, size)` | Create a subpopulation of given size. |
| `p1.individuals` | The individuals in subpop `p1`. |
| `individual.haplosomes` | The two haplosomes of an individual. |
| `mut.setValue(key, x)` | Attach an arbitrary attribute to a mutation object. |
| `mut.getValue(key)` | Read it back. |
| `writeFile(path, x, append=T/F)` | Write a string vector to a file. |
| `catn("...")` | Print a line to standard output. |

For a full reference, see chapter 23 (Eidos function reference) of the
SLiM manual, or the [SLiM website](https://messerlab.org/slim/).
