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
*timing*, and ultimately to *what we do with the energy*. The single biggest
discovery is this: **solar's problem is no longer that it's expensive. It's that
it's cheapest at noon, when we need it least.** Fixing *that* — by storing it, by
building industries that run when the sun shines, or even by collecting it in space
— is what will actually change the world. This document is the journey to that
conclusion.

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
  for. One kWh runs a microwave for about an hour, or a laptop for a couple of
  days. A typical home uses ~30 kWh a day. When I talk about the *cost* of energy,
  I'll use cents per kWh — the number on your electricity bill (a US home pays
  roughly 16¢/kWh).

The question that started everything was simple: **if a panel only captures 20% of
the sunlight, where does the other 80% go — and can we get it back?**

---

## Discovery 1: The panel is already close to a hard physical wall

It turns out most of that "lost" 80% isn't waste we can engineer away. It's
physics.

Sunlight is a mix of colors, each carrying a different amount of energy. A silicon
solar cell can only neatly use one "size" of energy packet:

- **Packets that are too weak** (redder light, and infrared we can't see) pass
  straight through the panel and do nothing — that's about **19%** of the energy
  gone.
- **Packets that are too strong** (bluer light) *do* get absorbed, but the panel
  can only keep a fixed amount from each one; the excess instantly turns into
  **heat** — about another **33%** gone.

These two losses pull in opposite directions (fix one, worsen the other), and when
you do the math, the best *any* simple silicon cell could ever achieve is about
**33%**. This isn't an engineering guess — it's a 1961 physics result called the
*Shockley-Queisser limit*, and the code in this project re-derives it from scratch
and lands on the same number.

So the honest "waterfall" from sunlight to the electricity in your wall looks like
this:

| Stage | Efficiency | What's lost getting to the next step |
|---|---|---|
| Perfect physics limit (silicon) | **33%** | the unavoidable color mismatch above |
| Best a real silicon cell can do | 29% | tiny material imperfections |
| Best cell ever made in a lab | 28% | manufacturing reality |
| A panel you can actually buy | ~21% | wiring the cells into a glass panel |
| A whole rooftop system, over a year | **~17%** | heat, dust, shading, the inverter, cabling |

**The takeaway that reframed the whole project:** the gap between 20% and the ~33%
ceiling is *small*, and most of it is hard physics, not laziness. We are not
leaving most of the energy on the table. The panel is a solved problem.

There *is* one way to beat the ceiling: stack two different cells on top of each
other so they catch different colors — a "tandem." That pushes the limit up toward
~45%, and real tandem cells have already hit **35%** in the lab. Hold that thought;
it comes back.

---

## Discovery 2: It was never really about efficiency — it's about cost

If the panel is nearly maxed out, what actually matters? **Money per unit of
energy.** The industry measures this as the *levelized cost of energy* (LCOE) —
basically, add up everything a solar farm costs over its 25-30 year life, divide by
all the electricity it makes, and you get a price per kWh.

When I computed it, the result was striking:

- A big **utility-scale** solar farm: about **5.6¢/kWh** — cheaper than coal or
  gas, the cheapest electricity ever generated at scale.
- The **same panels on a house**: about **17.6¢/kWh** — three times more.

Same panel. Triple the cost. Why? Because for a rooftop system the panel is a small
part of the bill — most of it is "soft costs": permits, paperwork, sales,
scaffolding, an electrician's afternoon. **If you want cheaper home solar, you
don't need a better cell. You need less bureaucracy.** That was the first hint that
the interesting problems had moved *off* the panel.

---

## Discovery 3: The real ceiling isn't efficiency or cost — it's the periodic table

Here's where it got genuinely surprising. To stop climate change, the world needs
to build solar at a colossal rate — very roughly **2 terawatts per year** (a
terawatt is a trillion watts; the whole world installed about half a terawatt in a
recent record year). Can we even get the *materials*?

Every panel needs a little of certain elements. The most important is **silver**
(used for the fine lines that carry current off each cell). Silver is rare. When I
divided the world's annual silver production by how much each panel needs, today's
silicon panels can only support about **1 terawatt per year** of building — even if
solar took *half* of all the silver mined on Earth. Other promising technologies
are worse: the ones using **tellurium** (rarer than gold) cap out around 0.006
TW/year; ones using **indium** around 0.055.

So the binding constraint on saving the climate with solar isn't efficiency, and
often isn't even money — it's **grams of a scarce element per panel**.

The good news: there's a fix, and it's almost mundane. Replace the silver with
**copper** (about 1/100th the price, and we mine ~900× more of it). That single
swap lifts the ceiling roughly **30-fold** *and* makes panels cheaper. It's already
being commercialized. **A boring material substitution matters more for the climate
than any efficiency record.** That reframed "innovation" for me entirely.

---

## Discovery 4: Every old panel is a future mine

If scarce materials are the wall, recycling is a way through it — but with a twist I
didn't anticipate. A solar panel lasts ~30 years, then retires. The global fleet
installed today becomes an enormous **"urban mine"** of silver, silicon, and copper
in the 2040s and 2050s — on the order of **200 million tonnes** of recoverable
material.

The twist: **recycling can't rescue the growth phase.** Because the panels retiring
today were installed 30 years ago, when we built very little, recycled material only
covers a small slice of what we need while solar is still growing explosively. It's
only once growth *levels off* (my model puts the crossover around **2058**) that the
retired fleet can supply most of the demand and the material ceiling melts away.

And there's a catch worth shouting about: the cheap, common way to recycle a panel
shreds it and recovers the glass and aluminum frame — but **throws the silver and
silicon away**. Only the more careful (and currently rarer) "high-value" recycling
recovers the elements that actually matter. **We have to build the right kind of
recycling *before* the wave of old panels arrives**, or we'll bury the very
materials we're short of.

---

## Discovery 5: Stop thinking about panels, start thinking about land — and time

A solar *farm* is mostly the empty space between rows of panels. So the real
question for big installations isn't energy per panel, it's **energy per acre** —
and land can often do two jobs at once:

- **Agrivoltaics** — raise the panels and grow crops or graze sheep underneath. You
  lose a little electricity but keep most of the farming, and the shared land
  out-produces doing either alone by ~50%.
- **Vertical panels facing east-west** — stand them on edge like fences. They make
  a bit less total energy, but here's the clever part: instead of all peaking at
  noon, they peak in the **morning and evening** — exactly when people get up and
  come home, and when solar is otherwise scarce. (This quietly previews the big
  insight coming next.)
- **Floating solar** — put it on reservoirs. No land at all, and the water cools
  the panels enough to boost output a few percent.

The lesson: "using solar well" is partly about *space*, and partly — it turns out —
about *timing*.

---

## Discovery 6: There is no "best" solar panel

I built a little tool that picks the optimal technology given your constraints, and
it taught me something I now think is obvious in hindsight: **the best panel depends
entirely on what's scarce for you.**

- If you have a **small roof** (space is the limit), the most *efficient* panel
  wins, even though it costs more — because every square meter has to count.
- If you have **plenty of land but a fixed budget**, the *cheapest* panel wins —
  because your dollars buy the most total capacity.

The optimal choice literally flips depending on which wall you hit first. Anyone
selling you "the best solar panel" is skipping the only question that matters: best
*for what*?

---

## Discovery 7: Fool's gold might be the future

A fun tangent that turned serious. **Iron pyrite** — "fool's gold," literally just
iron and sulfur, two of the most common and cheapest elements on Earth — is a
fantastic sunlight absorber with an ideal color match. By the physics, it *should*
make a ~31%-efficient cell. In reality it makes a hopeless ~3% one.

I modeled why, and it comes down to a single failure: pyrite can't hold **voltage**.
Tiny defects at its surface drain away the electrical "pressure" before you can use
it. Cure that one problem — and it's a materials-science challenge, not a physics
impossibility — and pyrite could reach **22-25%**: a perfectly good panel made from
dirt-common ingredients with no scarcity ceiling at all. It's a long shot worth
taking, because the payoff is a panel the whole planet could build without limit.

---

## The turning point: cheap is not the same as valuable

Everything so far was about making solar better, cheaper, more abundant. Then I hit
the discovery that reorganized the entire project — and it's the one most people
(including me, at first) miss.

Solar all generates at the same time: the middle of a sunny day. The more solar you
add, the more it floods the market at noon, and the less each kilowatt-hour is
worth *at that moment*. I modeled an electricity market and watched it happen: when
solar supplies a small share of the grid, each unit is worth *more* than average
(it shows up during busy daylight). But:

- By the time solar provides ~30% of the grid, its average worth has fallen to
  about **half** of average.
- By ~45%, it's down to about a **quarter**, and roughly **a fifth of all the solar
  energy gets thrown away** ("curtailed") because nothing can use it at noon.

This isn't a prediction — it's already happening. In Germany, the value of solar
power dropped from 73% of the average price to 48% in just three years. And 2026 is
on track to be the **first year ever that the world installs *less* solar than the
year before** — not because it got expensive, but because we're hitting this wall.

**The picture in one image:** solar carves a deep dip into midday electricity prices
while the evening peak — after the sun sets, when everyone's home — stays sky-high
and completely out of solar's reach. Cheap electrons, arriving at the wrong time.

This is the real frontier. And it has exactly three answers.

---

## Answer 1: Store it (firming)

The obvious fix: put the cheap midday flood into batteries and release it after
dark, turning solar into "always-on" power. I simulated this hour by hour for a full
year. The result: **round-the-clock solar-plus-battery already costs about 7¢/kWh**
at a sunny site — cheaper than a *new* gas or coal plant. Dispatchable solar isn't a
future promise; it beats burning things today.

But there's a cliff. Getting from "reliable 90% of the time" to "reliable 99% of the
time" roughly *doubles* the cost, because covering the occasional week of clouds
needs a huge, mostly-idle pile of batteries. **Chasing 100% solar-only is the most
expensive energy you can buy.** The smart move is to store the easy 80-90% and
handle the rest another way.

---

## Answer 2: Use it — make molecules, not just electrons (the inversion)

This is, to me, the most exciting idea in the whole project, and the biggest change
in how we might *use* solar.

For 150 years, power plants followed our demand — we flipped a switch, they burned
more fuel. Solar can't do that; its timing is fixed by the sky. So instead of
forcing solar to behave like a power plant, **flip the logic: build industries that
run when the sun shines and rest when it doesn't.**

When midday electricity is nearly free, you stop trying to store those electrons and
start using them to *make things*:

- **Hydrogen**, by splitting water — a clean fuel and the raw material for much of
  heavy industry. Cheap solar already makes it for a competitive price.
- **Ammonia** (fertilizer), **synthetic fuels**, and **green steel** — a tenth of
  the world's carbon emissions, made from sunlight instead of fossils.
- **Fresh water**, by desalinating seawater for a few cents a tonne.
- **Carbon removal**, sucking CO₂ out of the air at the cost of cheap power.

The beautiful part: these flexible factories can *eat the glut*. In my model, adding
flexible hydrogen production cut solar's wasted energy from a third down to a tenth
— and turned that waste into fuel. **The "too much solar at noon" problem and the
"where do we get clean hydrogen" problem are the same problem, and they cancel each
other out.** Solar stops being a way to light bulbs and becomes the feedstock for
the physical economy, whenever the sun is up.

---

## Answer 3: Escape the night entirely (solar in space)

The most radical answer: if the problem is that the sun sets, go where it never
does. A solar satellite in orbit gets sunlight ~95% of the time, with no atmosphere
or clouds dimming it, and beams the power down to Earth by radio waves.

It sounds like science fiction, and at today's rocket prices it is — wildly
uneconomic. But I found the cost is dominated by *one* thing: the price of launching
weight to orbit. And that price is falling fast. At the launch costs the next
generation of rockets is targeting (~$100 per kilogram), space-based solar pencils
out to roughly **3.5-10¢/kWh** — competitive with firm solar on the ground.
**Space solar isn't a physics problem; it's a launch-cost bet**, and the bet is
already in motion.

---

## Where it's all going

Underneath every chart in this project is one quiet engine: **Wright's law.** Every
time the world *doubles* the total amount of solar ever built, the price drops by a
roughly constant fraction. It's held for fifty years across a thousand-fold drop in
price, and the data fits it almost perfectly.

Run that forward and the panel itself heads toward *nearly free*. But — echoing
Discovery 2 — the price of solar *energy* doesn't fall to zero with it. It flattens
out around **2¢/kWh**, because once the panel costs nothing, what you're paying for
is everything *around* it: the land, the wiring, the labor, the permits. **The
frontier of cheap energy has permanently moved off the cell and onto the system.**

---

## The big takeaways (the whole project in nine lines)

1. **The panel is nearly maxed out.** ~20% in the field is close to the ~33% physics
   ceiling; most of the "loss" is unavoidable.
2. **Cost, not efficiency, is what matters** — and cost is set by *where* you install
   solar (and by paperwork), far more than by *which* panel.
3. **The hidden wall is materials.** Scarce metals like silver and tellurium cap how
   fast we can build; swapping in abundant copper matters more than any efficiency
   record.
4. **Recycling eventually dissolves the materials wall** — but only after growth
   slows, and only if we build the *right* (high-value) recycling first.
5. **Use land twice** (crops, water, vertical fences) and you get more out of the
   same ground — and better-timed power.
6. **There is no single best panel** — only the best one for whatever's scarce for
   you: space or money.
7. **The biggest discovery: cheap ≠ valuable.** Solar's electrons are worth least
   exactly when there's most of them (midday), and that — not cost — is the wall the
   world is hitting now.
8. **The fix is to stop shaping solar to fit our demand, and start shaping our
   demand to fit the sun** — store it, or better yet build flexible industries
   (hydrogen, fuels, water, carbon removal) that feast on cheap midday power.
9. **Solar is already the cheapest energy ever made,** and getting cheaper. The work
   ahead isn't a better panel. It's reorganizing what we build *around* it.

---

## A personal note to close

I came into this expecting to find a story about a clever new material that would
make panels twice as good. That story doesn't exist, and chasing it would miss the
point. What I found instead is more hopeful and more demanding at once: **the hard
part of solar is no longer the technology — it's the imagination.** We already have
electricity too cheap to meter for a few hours each sunny day. The question that
will define the next few decades isn't "how do we make solar better?" It's "what
kind of world do we build for a sun that pours out nearly-free energy on its own
schedule, not ours?"

A world that answers that — that learns to make its fuel, its water, its steel, and
its computation in the hours the sun is shining — gets an abundance the age of coal
and oil could never imagine. Not because we invented a magic panel. Because we
finally learned to use the one we already have.

---

*Everything above is drawn from the eleven analyses in this repository, each of which
computes its numbers from physics and economics rather than asserting them, and
checks them against real-world 2026 data. For the technical versions, see the
`output/REPORT_*.md` files; for the deep synthesis, see
[`output/REPORT_FUTURE.md`](output/REPORT_FUTURE.md). To reproduce all of it from
scratch: `pip install -e ".[dev]" && python -m solarlab all`.*
