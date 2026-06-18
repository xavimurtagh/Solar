# solarlab — why solar panels are ~20% efficient, and how to change that

A typical rooftop solar panel converts only about a fifth of the sunlight that
hits it into electricity. **Why?** And **how do we do better?**

This toolkit answers both from first principles — it *computes* the physics
rather than quoting it — and generates a fully cited report with the figures
below. Every number is either calculated here or carried with its source.

```bash
pip install -e ".[dev]"
python -m solarlab report      # Part I: efficiency physics  -> output/REPORT.md + figs 1-5
python -m solarlab economics   # Part II: cost & materials    -> output/REPORT_ECONOMICS.md + figs 6-10
python -m solarlab all         # both reports, all ten figures
python -m solarlab validate    # quick physics + data sanity checks
pytest                         # 66 tests pin the numbers to published values
```

## The short answer

The "~20%" is not one failure but a chain of them, and **only the first rung is
fundamental physics** — everything below it is engineering, and therefore
improvable:

| Stage | Efficiency | What limits it |
|---|---|---|
| Shockley-Queisser limit (silicon) | **33.4%** | sub-bandgap + thermalisation + voltage + fill-factor |
| Practical silicon cell limit | 29.4% | intrinsic Auger recombination |
| Best lab silicon cell | 27.8% | surface/contact recombination, resistance |
| Best commercial module | ~20.7% | cell-to-module packaging |
| **Deployed system (annual AC)** | **~16.8%** | temperature, soiling, wiring, inverter |

![The efficiency waterfall](output/figures/fig2_waterfall.png)

A perfect *single-junction* cell simply cannot beat ~34%: photons below the
bandgap pass through, and the energy of photons above it is lost as heat. These
two losses pull in opposite directions, which is why the limit peaks near
1.34 eV (33.7%) and silicon sits at 33.4%.

![The Shockley-Queisser limit](output/figures/fig1_sq_limit.png)

## How to actually improve it

The toolkit simulates a real rooftop (pvlib, a full 8760-hour year) and ranks
concrete improvements by the extra annual energy each delivers. The standout is
the **tandem cell** — the one lever that raises the cell's *physical ceiling*
rather than recovering system losses, and it is moving from lab to market now.
Perovskite-on-silicon tandems have already passed silicon's single-junction
limit, reaching 35% in the laboratory.

![Improvement levers, ranked](output/figures/fig4_levers.png)

The strategy to change the energy industry is two-front: **push multi-junction
cells to break the physics ceiling**, and **deploy the proven system
engineering** (tracking, bifaciality, cooling, better power electronics) that
stops us wasting what today's cells already make. And because the industry's
real objective is cost per kilowatt-hour, a cheaper 20% panel often beats a
pricier 24% one — efficiency matters most where area or weight is scarce.

See [`output/REPORT.md`](output/REPORT.md) for the full analysis.

## Part II — dollars, space, and the materials ceiling

Efficiency is a vanity metric; the world buys energy in dollars per kilowatt-hour
and, at terawatt scale, in *grams of scarce element per watt*. The second half of
the toolkit (`python -m solarlab economics`) computes:

- **LCOE** that reproduces Lazard 2025 (utility **$56/MWh**, residential
  **$176/MWh**) — and shows energy cost is set by *where* you deploy, not which
  cell. On a roof, **soft costs dominate**, so a better cell barely moves the bill.
- **The cost/space/scale frontier** — efficiency mainly buys *energy density*
  (kWh/m²), which only pays off where area is scarce.
- **The terawatt ceiling** — the constraint no efficiency chart shows. Dividing
  world production of each scarce element by how much each technology needs:

![The terawatt ceiling](output/figures/fig8_ceiling.png)

CdTe is tellurium-limited to **0.006 TW/yr**, heterojunction and perovskite
tandems are indium-limited to **0.055 TW/yr**, and even mainstream silicon is
**silver-limited to ~1.2 TW/yr** — against a need of very roughly **2 TW/yr**.

- **Material substitution as the breakthrough lever.** Swapping silver for
  electroplated **copper** (1/95th the price, ~900× the supply) and indium for
  **zinc** (AZO) lifts the scaling ceiling up to **30×**, while *lowering* material
  cost. The boldest absorbers — kesterite (Cu-Zn-Sn-S) and iron pyrite (FeS₂,
  "fool's gold") — abandon scarce elements entirely.

![Material substitution impact](output/figures/fig9_substitution.png)

The thesis: a *good-enough, abundant, cheap* cell may matter more to
decarbonisation than a record-efficiency scarce one — because we can actually
build 50 TW of it. Full write-up in [`output/REPORT_ECONOMICS.md`](output/REPORT_ECONOMICS.md).

## How it works

| Module | Role |
|---|---|
| `spectrum.py` | AM1.5G spectrum + fast wavelength-domain integrals |
| `sq.py` | Shockley-Queisser detailed-balance limit, losses, tandems |
| `history.py` | seven decades of cited efficiency records + trend analysis |
| `system.py` | explicit pvlib model chain + per-stage loss attribution |
| `levers.py` | one-change-at-a-time improvement simulator |
| `waterfall.py` | the sun → AC efficiency ladder |
| `economics.py` | LCOE, energy-per-dollar, sensitivity, Monte-Carlo |
| `materials.py` | material intensity, the terawatt ceiling, substitution |
| `frontier.py` | the cost / space / scale Pareto frontier |
| `figures.py` / `report.py` / `report_econ.py` / `cli.py` | figures, both reports, entry point |

The physics is validated against published values: the 33.7% peak at 1.34 eV
(Rühle 2016), silicon's ~44 mA/cm² short-circuit current, the ideal two-junction
tandem near 46%, and a loss decomposition that sums to 100% to within 1e-9.

## Caveats

Detailed balance is an *upper bound* (unity quantum efficiency, radiative-only
recombination, one sun, 300 K), not a device simulation. The system model uses a
single TMY3 site and omits angle-of-incidence reflection, snow, and explicit
shading. Record efficiencies are tested by *range*, not exact value, because they
move — verify against the [NREL Best Research-Cell Efficiency chart](https://www.nrel.gov/pv/cell-efficiency.html).

## License

MIT.
