# Strata — roadmap and issue tracker

[Strata](https://store.steampowered.com/app/4791200) is a node-based terrain
editor for game developers. Build landscapes from a node graph, erode them,
carve rivers and roads, walk the result at player scale, and export to Unreal
Engine 5, Unity, Godot, O3DE or Leadwerks.

This repository is the public roadmap. **The source lives elsewhere** — what is
here is the plan, and an issue tracker.

- **Found a bug?** [Open an issue](../../issues/new) — include your OS, GPU, and
  what the editor was doing. Crash reports are written to
  `~/.local/state/Strata/` on Linux and `%LOCALAPPDATA%\Strata\` on Windows;
  attaching one helps enormously.
- **Want a feature?** Open an issue describing the problem you are trying to
  solve rather than the feature you have in mind. The use case is what moves
  priorities.
- **Want to vote?** React with 👍 on an existing issue.

---


What is done, what is being worked on, and where this is going. Updated as
things actually change rather than on a schedule.

Dates are when something shipped, not when it was promised. Nothing below is a
commitment to a date — a solo project moves at the speed it moves.

---

## Shipped

### The Rust rewrite — 15 November 2026

Strata was rebuilt from the ground up in Rust. The previous version ran inside
a bundled browser runtime, which capped how fast terrain evaluation could get
no matter what hardware you threw at it. This version talks directly to the
GPU.

- Native **Windows and Linux** builds, including Steam Deck
- Install size went from 288 MB to 75 MB for both platforms combined
- Your existing `.strata` projects open unchanged

### Walk and follow cameras

Inspect terrain at player scale instead of only from orbit, because "is this
hill the right size?" is a question best answered standing at the bottom of it.

### Layer Stack

Up to 12 layers, 21 blend modes, per-layer opacity, masks and visibility.
Photoshop's compositing model adapted for terrain, including `max` and `min`
modes for raising and carving landforms.

### Selectable preview detail — 22 October 2026

Draft (512), Balanced (1024) and Fine (2048) sampling, independent of your
map's physical size. The editor shows the real sample spacing in metres and the
memory cost before you commit to a level.

### Road / Path tool — 16 November 2026

Draw a route and get a grade-limited carriageway that cuts into hills and fills
across dips, with road and shoulder masks for your material stack. Width,
shoulder and maximum grade are authored in metres and percent.

### Progressive evaluation — 17 November 2026

Changing a parameter now redraws immediately at draft quality and refines to
your chosen detail once you stop adjusting. Dragging a slider costs about a
third of what it used to.

---

## In progress

### Siting features from the ground

Walking the terrain is currently read-only: you look, then go back to the
editor to change anything. That loop is being closed.

- **Done** — press `P` while walking to place a Flatten Pin where you stand
- **Next** — adjust a pad's radius without leaving the ground; measure distance
  and slope underfoot; place road waypoints while walking the route

---

## Planned

### Explore a bounded world, then frame what you export

Generate more world than you need, move around until something looks worth
keeping, then draw a box around that region and build it properly — rather
than choosing your map bounds before you have seen anything.

The export box half of this works against today's maps and will likely arrive
first.

### Background evaluation

Progressive evaluation made the editor much more responsive, but evaluation
still runs on the interface thread, so a heavy rebuild can still cause a brief
pause. Moving it off-thread removes that entirely.

### Resizable viewport and graph

Drag the divider between the 3D viewport and the node graph instead of using a
slider in a menu.

### Rivers and lakes

Editable downstream elevation profiles, readable water depth, lake levels, and
a diagnostic for uphill flow. Sea-level water separated from river surfaces.

### Regional biome masks

Reusable masks for grass, rock, snow, riverbanks and wetlands built from
height, slope and moisture, with authored overrides.

### Starter projects

Editable example graphs — island, mountain valley, river basin, rolling
countryside — that preserve their seeds and scale so they reproduce exactly.

---

## Considering

Not committed to, and listed so you can tell me if one of these matters more
than the others.

- **Continent scale.** An England-sized world needs regional generation, not a
  larger width slider. It is a genuine architecture project, and claiming it
  before the systems exist would be dishonest.
- **Send to engine.** One button that places terrain in your engine configured
  correctly, instead of exporting and importing by hand.
- **Stamp library.** Capture a piece of terrain you like and place it again
  elsewhere.
- **Localisation.** Store pages in more languages are coming first; the
  application interface is a larger job.
- **Road meshes, bridges, tunnels.** The Road tool shapes terrain today and
  does not produce geometry.

---

## Known limitations

Written down because finding them yourself after buying is worse.

- **Evaluation can pause the interface** on a complex rebuild at Fine detail.
  Progressive evaluation reduced this; background evaluation will remove it.
- **Higher preview detail does not resolve small features at large scale.** A
  64 km world at 2048 samples still has about 31 m between samples. Resolution
  alone cannot fix that, and the editor tells you the spacing so you are not
  guessing.
- **A road narrower than the sample spacing is drawn wider than authored.** The
  editor warns when this applies rather than quietly giving you a wider road.
- **Rivers crossing a tile boundary can disagree slightly** between tiles in a
  tiled export. The equivalent problem in the Road tool is fixed; the same fix
  for rivers is pending.
- **Export does not yet write a scale manifest**, so engine import still relies
  on preset defaults rather than explicit authored dimensions.
- **Ground-level cameras take over the whole window**, so a single view cannot
  show both the node graph and the terrain at player scale.

---

## Telling me what you want

Priorities here are a judgement call and not a very confident one. If something
in Considering matters to your project, or something in Known limitations is
blocking you, say so — a specific use case changes the order faster than a vote
does.
