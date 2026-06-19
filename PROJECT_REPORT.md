# What I Learned Trying to Fix Solar Power

*A plain-language tour of everything this project discovered — written for someone
who has never thought about solar energy before. No background needed. Every number
here was computed or checked by the code in this repository; I've rounded things off
and swapped jargon for plain words wherever I could.*

---

## If you read only this paragraph

A solar panel today turns about **a fifth** of the sunlight hitting it into
electricity, and at first that sounds like a problem to fix. It mostly isn't. The
deeper I dug, the more the story changed under my feet: the panel is nearly as good
as physics allows, solar electricity is already the **cheapest humanity has ever
made**, and the real obstacles moved somewhere I didn't expect — to *materials*, to
*timing*, to *what we do with the energy*, and (the least glamorous of all) to
*whether anyone bothers to collect the old panels*. The single biggest discovery is
this: **solar's problem is no longer that it's expensive. It's that it's cheapest at
noon, when we need it least.** Fixing *that* — by storing it, by building industries
that run when the sun shines, or even by collecting it in space — is what will
actually change the world. This document is the journey to that conclusion, and the
hard, honest questions I had to face along the way.

---

## Starting from zero: what a solar panel even is

Sunlight is energy. A lot of it: enough falls on the Earth in roughly **one hour**
to power human civilization for a **year**. A solar panel is a flat device, usually
silicon (the stuff in sand and computer chips), that turns some of that sunlight
directly into electricity, with no moving parts and no fuel.

Two words I'll use throughout:

- **Efficiency** — the fraction of the sunlight's energy a panel converts to
  electricity. Today's typical panel is about **20%** efficient.
- **Kilowatt-hour (kWh)** — the standard unit of energy, the thing you're billed
  for. One kWh runs a microwave for about an hour. A typical home uses ~30 kWh a
  day. When I talk about the *cost* of energy I'll use cents per kWh — the number on
  your bill (a US home pays roughly 16¢/kWh).

The question that started everything was simple: **if a panel only captures 20% of
the sunlight, where does the other 80% go — and can we get it back?**

---

## Part one: making solar better (and discovering the limits)

### Discovery 1 — The panel is already close to a hard physical wall

Most of that "lost" 80% isn't waste we can engineer away. It's physics. Sunlight is
a mix of colors; a silicon cell can only neatly use one "size" of energy packet.
Packets too weak (infrared) pass straight through — ~19% gone. Packets too strong
(blue light) get absorbed, but the panel keeps only a fixed slice and the rest turns
to **heat** — ~33% gone. Do the math and the best *any* simple silicon cell could
ever reach is about **33%** (a 1961 result called the Shockley-Queisser limit, which
the code re-derives from scratch). The gap between today's ~20% and that ~33% ceiling
is *small*, and mostly hard physics. **The panel is a solved problem.** (One way
beats the ceiling: stack two cells to catch different colors — a "tandem" — which
already hits 35% in the lab. Hold that thought.)

### Discovery 2 — It was never really about efficiency; it's about cost

If the panel is nearly maxed out, what matters is **money per unit of energy**. I
computed it: a big utility solar farm makes power for about **5.6¢/kWh** — cheaper
than coal or gas, the cheapest electricity ever. The *same panels on a house* cost
about **17.6¢/kWh** — three times more — because on a rooftop the panel is a small
part of the bill; most of it is "soft costs" (permits, paperwork, sales, an
electrician's afternoon). **Cheaper home solar needs less bureaucracy, not a better
cell.**

### Discovery 3 — The real ceiling is the periodic table

To stop climate change we'd need to build solar at ~2 terawatts a year (a terawatt
is a trillion watts). Can we get the *materials*? Every panel needs a little
**silver**, which is rare. Divide world silver production by what each panel needs
and today's panels can only support about **1 terawatt a year** of building — even
taking half the world's silver. Technologies using **tellurium** (rarer than gold)
cap out near 0.006; **indium**, near 0.055. The fix is almost mundane: replace silver
with **copper** (~1/100th the price, ~900× more abundant), which lifts the ceiling
roughly **30-fold**. **A boring material swap matters more than any efficiency
record.** (We'll come back to whether copper is really as good — it's not quite the
free lunch it sounds.)

### Discovery 4 — Every old panel is a future mine

Panels last ~30 years, then retire. The global fleet becomes an enormous **"urban
mine"** — hundreds of millions of tonnes of recoverable material. The twist:
recycling *lags* growth (today's retirements were tiny installs from 30 years ago),
so it only covers a small slice while solar is still booming; it dominates only once
growth levels off (around the 2050s). And a catch: cheap shredding recovers the glass
and aluminum but **throws the silver and silicon away** — only careful "high-value"
recycling recovers what matters. (This turns out to hide an even bigger problem — see
Part four.)

### Discovery 5 — Use land twice, and mind the timing

A solar *farm* is mostly the gaps between rows, so what matters is energy per *acre*
— and land can do two jobs. **Agrivoltaics** (raised panels with crops underneath)
out-produces doing either alone. **Vertical panels facing east-west** make a bit less
energy but peak in the *morning and evening* instead of noon — which, it turns out,
is exactly the right instinct. **Floating solar** uses no land and runs cooler.

### Discovery 6 — There is no "best" solar panel

A tool I built to pick the optimal technology taught me the obvious-in-hindsight
truth: the best panel depends on what's scarce *for you*. Small roof? The most
*efficient* panel wins. Plenty of land, fixed budget? The *cheapest* panel wins. The
optimal choice literally flips. Anyone selling "the best solar panel" is skipping the
only question that matters: best *for what*?

### Discovery 7 — Fool's gold might be the future (and we mapped how)

**Iron pyrite** — "fool's gold," just iron and sulfur, dirt-common — *should* make a
~31%-efficient cell but in reality makes a hopeless ~3% one. The problem is a single
failure: it can't hold **voltage** (electrical "pressure" leaks away at its flawed
surface). So I built a repair roadmap — and the model says exactly how far each fix
gets you: clean up the surface (→11%), fix flaws inside the crystal (→17%), then the
decisive move borrowed from other modern cells — wrap it in dedicated collecting
layers so it stops relying on its own broken surface (→**25%**). Have researchers
tried? Yes, for decades; pyrite is stubborn. What the model adds isn't a cure — it's
a precise *target* for each attempt, which is the first thing a serious effort needs.

---

## The turning point: cheap is not the same as valuable

Everything above was about making solar better. Then I hit the discovery that
reorganized the whole project. Solar all generates at once — sunny midday — so the
more you add, the more it floods the market exactly when it's worth least. I modeled
an electricity market and watched it happen: at a small share, each unit of solar is
worth *more* than average; but by ~30% of the grid its worth falls to about **half**,
and by ~45% to about a **quarter**, with **a fifth of all the solar thrown away**
because nothing can use it at noon. This isn't a forecast — Germany's solar value
already fell from 73% to 48% of average in three years, and 2026 is on track to be
the **first year the world installs *less* solar than the year before.** Not because
it got expensive — because we're hitting this wall.

The picture: solar carves a deep dip into midday prices while the evening peak (after
sunset, when everyone's home) stays sky-high and out of solar's reach. Cheap
electrons, arriving at the wrong time. This is the real frontier, and it has exactly
three answers.

### Answer 1 — Store it

Put the midday flood in batteries, release it after dark. I simulated this hour by
hour: **round-the-clock solar-plus-battery already costs about 7¢/kWh** at a sunny
site — cheaper than a *new* gas or coal plant. But there's a cliff: going from
"reliable 90% of the time" to "99%" roughly *doubles* the cost, because covering rare
cloudy weeks needs a huge, mostly-idle pile of batteries. **Chasing 100% solar-only
is the most expensive energy you can buy.**

So I dug into *why* that cliff is there — and it turns out "storage" is the wrong
word, because there isn't one storage problem; there are two, and they need totally
different machines. The trick is that every way of storing energy has **two** prices:
how fast it can charge and discharge (per kilowatt), and how much it can hold (per
kilowatt-hour). A lithium battery is cheap to charge fast but **expensive to hold a
lot** — perfect for a few hours, hopeless for weeks. So:

- **Storing for a few hours** (noon → night) is essentially *solved* — lithium
  batteries do it cheaply and efficiently, which is why they're booming.
- **Storing for days** (a windless, cloudy stretch) is the awkward middle — new
  technologies like "iron-air" (rusting and un-rusting iron) or heating cheap rock
  are emerging but young.
- **Storing for months** (sunny summer → dark winter) is the real wall. A lithium
  battery's cost *explodes* — from about $124 to make power for an hour-scale store
  up to **$5,000** for a season-scale one. The only thing cheap enough to hold energy
  for months is **hydrogen** (made by splitting water, stored in underground caverns),
  even though it wastes more than half the energy — because if you barely use it, what
  matters is the cost to *hold* it, not the efficiency.

The bottleneck, then, isn't "storage" — it's **long-duration** storage, and the fix
is to stop using one tool for every job: lithium for hours, iron and heat for days,
hydrogen for seasons. And two things genuinely surprised me. First, when the energy
you're storing is *free* (the curtailed midday glut nobody wanted), efficiency stops
mattering at all — so the cheapest, leakiest store wins even for short jobs. Second,
the cheapest "storage" is often **not storing electricity at all** — it's using it the
instant it arrives (the next section), or storing the *product* — hydrogen, heat,
fresh water — which are all far cheaper to keep than electrons. Store the molecule,
not the electron.

### Answer 2 — Use it: make molecules, not just electrons

This is the most exciting idea in the project. For 150 years, power plants followed
our demand (flip a switch, burn more fuel). Solar can't — its timing is fixed by the
sky. So **flip the logic: build industries that run when the sun shines.** When
midday power is nearly free, you stop storing electrons and start *making things* —
and here's exactly how that works, step by step.

The pivot is **splitting water**: run a solar current through water and it tears into
hydrogen and oxygen. That hydrogen is the master key, and almost everything else is
built from it:

- **Fertilizer:** combine the hydrogen with nitrogen pulled from the air → ammonia,
  which already grows about half the world's food (today made from fossil gas).
- **Steel:** today we strip oxygen from iron ore with coal, which dumps CO₂. Use
  hydrogen instead and the *exhaust becomes water*. Same steel, no carbon.
- **Fuels for planes and ships:** capture CO₂ from the air, react it with the
  hydrogen → jet fuel, diesel, methanol, built molecule by molecule.
- **Fresh water:** electric pumps push seawater through a fine membrane that blocks
  the salt — a few kWh buys a tonne of drinking water.
- **Carbon removal & heat:** fans and chemistry pull CO₂ from the air; cheap power
  charges "thermal batteries" (heated firebricks) that warm factories all night.

The pattern: every one is a **flexible** load, happy to run hard at noon and rest at
night — designed *around* solar's rhythm. And it solves two problems at once: the
"too much solar at noon" problem and the "where do we get clean fuel" problem are the
*same* problem, and they cancel out. **Solar stops being a way to light bulbs and
becomes the feedstock for the physical economy whenever the sun is up.**

### Answer 3 — Escape the night: solar in space

The radical answer: if the problem is that the sun sets, go where it never does. A
solar satellite gets sunlight ~95% of the time and beams the power down by radio
waves. I dug into the hard questions:

- **Does launching it wreck the climate?** No — the rocket emissions pay back in
  about **3 months**, and over its life it's *cleaner per kWh than a rooftop panel*
  (because it runs almost constantly). The real worry is rocket soot high in the
  atmosphere if we launch a lot, which nobody has fully measured.
- **How does the energy get down?** Through a chain (electricity → microwaves →
  through the air → a ground antenna → electricity) that delivers about **60%** of
  what's collected. The beam is deliberately weak and spread out — a mesh you could
  farm under, not a death ray.
- **What about dead satellites, meteors, repairs?** Dead ones get pushed to a
  "graveyard" orbit — and can't really be recycled, which is a genuine downside.
  Meteor strikes cost a sliver of a modular array, not the whole thing. Repairs would
  be robotic.
- **Could it power the whole world?** No. The catch is *weight*: powering the entire
  world this way would need ~**240 rocket launches a day for 30 years** — absurd. Its
  honest role is the **premium slice** terrestrial solar is worst at: firm, 24/7
  power for high-latitude cities or remote industry. A complement, not a replacement.

---

## Part four: the honest second look — does any of this really hold up?

After all that, I went back and stress-tested the project's own cheerful claims. This
is where it got uncomfortable, and more interesting.

### Is copper really a free swap for silver?

I'd called copper-for-silver a near-free win. Modeling it properly (not just price,
but performance and lifespan): on **efficiency**, copper is fine — even slightly
*better* (it makes finer lines that shade the cell less). On **lifespan**, there's a
real question: copper can poison silicon if it seeps in (so it needs a thin barrier
layer) and it corrodes more than silver, and we only have a few years of field data
versus silver's thirty. And on **cost**, the surprise: at the whole-system level
copper *barely* beats silver, and a tiny reliability slip erases the saving — because
silver is only ~1% of a system's cost. **So copper's real value was never cheaper
energy. It's that you simply can't build tens of terawatts on silver, at any price.**
The case for copper is abundance, not the bill. (We were right to push copper, wrong
about why.)

### Can solar ever be *truly* renewable, or will we run out?

This was the question that worried me most, and the answer is reassuring with a real
catch. First, the good news: **metals don't wear out.** Unlike a plastic bottle
(which downcycles) the silver and copper in an old panel refine back to *original
purity* and work again in a brand-new panel — the same atom, ready for another 30
years. The only loss is what we fail to recover.

But do we run out? I modeled a mature world running on 50 terawatts of solar:

- **Silver, no recycling:** it would eat 87% of all silver mined each year and
  **exhaust known reserves in about 30 years.** Called that way, it is *not*
  renewable — it's a resource cliff.
- **Silver, recycled well:** fresh demand drops to ~13% of production and the runway
  stretches to ~**190 years.**
- **Copper:** an effectively *infinite* runway.

So solar *can* be truly renewable — but it's a **choice**, resting on two things:
**recycle tightly, and move to abundant metals.** Scarce silver is a bootstrap, not
a destiny.

### The least glamorous discovery — and maybe the most important

There's a hidden assumption buried in "recycle tightly": that the old panels actually
get *collected*. They mostly don't. Around the world, only ~10-20% of retired panels
formally reach a recycler; the rest are landfilled, exported, or abandoned. And when
I made collection the variable it really is, the whole recycling story hinged on it:

- **Below ~50% collection — where most of the world sits — recycling barely helps**;
  the multi-century runway collapses back toward the 30-year cliff. The world's best
  recycling technology is worthless on a pile of panels nobody picked up.
- The reason collection is low is brutally simple economics: a tonne of old panels
  holds about **$536** of recoverable material, but the person holding it just sees a
  choice between *paying* ~$280 to recycle or ~$75 to dump it. **Landfill is cheaper,
  so without a rule, the panel gets dumped.**
- A cruel twist: the silver is what makes a panel *worth* recycling. As we thrift
  silver away and switch to copper (the very fix for the supply ceiling), the
  recovery value drops by two-thirds — so the copper era will need *more* collection
  policy, not less.

The fix isn't a technology. It's **rules and logistics** — make the manufacturer
responsible for the old panel (the EU already does this, and gets ~80% collection),
add a refundable deposit, ban PV from landfills. We spent fifteen analyses on
physics, cost, materials, and orbits. The thing most likely to decide whether solar
is *truly* renewable is whether a **truck shows up to collect the old panels.**

---

## Where it's all going

Underneath every chart is one engine: **Wright's law** — each time the world doubles
the total solar ever built, the price drops by a roughly constant fraction. It's held
for fifty years. Run it forward and the panel heads toward *nearly free* — but the
price of solar *energy* flattens out around **2¢/kWh**, because once the panel costs
nothing, you're paying for everything *around* it (land, wiring, labor, permits). The
frontier of cheap energy has permanently moved off the cell and onto the system.

---

## The big takeaways

1. **The panel is nearly maxed out** (~20% vs a ~33% physics ceiling); most "loss" is
   unavoidable.
2. **Cost, not efficiency, is what matters** — and it's set by *where* you install,
   and by paperwork.
3. **The hidden wall is materials**; swapping scarce silver for abundant copper
   matters more than any efficiency record — though copper's real value is abundance,
   not a cheaper bill, and its long-term reliability is still being proven.
4. **Solar can be truly renewable — but only with a tight recycling loop *and*
   abundant metals.** On scarce silver alone it's a 30-year cliff.
5. **And recycling only works if the old panels get collected** — today they mostly
   don't, and that mundane logistics problem may be the highest-leverage climate fix
   in this whole report.
6. **There's no single best panel** — only the best one for whatever's scarce for you.
7. **The biggest discovery: cheap ≠ valuable.** Solar's electrons are worth least
   exactly when there's most of them (midday) — and that, not cost, is the wall the
   world is hitting now.
8. **The fix is to shape our demand around the sun** — store it, or build flexible
   industries (hydrogen, fuels, water, carbon removal) that feast on cheap midday
   power.
9. **Solar is already the cheapest energy ever made,** and getting cheaper. The work
   ahead isn't a better panel — it's reorganizing what we build *around* it.

**And the thread that ties the whole second half together:** every hard question —
copper vs silver, recycling, pyrite, demand, space — returned the same verdict.
**Abundance, circularity, and flexibility beat scarcity, consumption, and rigidity.**
A solar civilization works when it's built from common atoms, kept in a closed loop,
and run on flexible demand — not when it mines rare metals, dumps them after one use,
and waits for the sun to behave like coal.

---

## A personal note to close

I came into this expecting a story about a clever new material that would make panels
twice as good. That story doesn't exist, and chasing it would miss the point. What I
found instead is more hopeful and more demanding at once: **the hard part of solar is
no longer the technology — it's the imagination, and the follow-through.** We already
have electricity too cheap to meter for a few hours each sunny day. The questions that
will define the next few decades aren't "how do we make solar better?" They're "what
do we build to use a nearly-free sun?" and — humblingly — "will we bother to send a
truck for the old panels?"

A world that answers those gets an abundance the age of coal and oil could never
imagine. Not because we invented a magic panel. Because we finally learned to use,
reuse, and build around the one we already have.

---

*Everything above is drawn from the seventeen analyses in this repository, each of which
computes its numbers from physics and economics rather than asserting them, and checks
them against real-world 2026 data. For the technical versions, see the
`output/REPORT_*.md` files; for the deep synthesis, see
[`output/REPORT_FUTURE.md`](output/REPORT_FUTURE.md). To reproduce all of it:
`pip install -e ".[dev]" && python -m solarlab all`.*
