# Fly_in

*This project has been created as part of the 42 curriculum by daniviei.*

## Description

**Fly_in** is a drone-routing simulator: a network of *hubs* (landing pads) is
connected by *links*, and a fleet of drones must travel from a **start** hub
to a **goal** hub, one step (turn) at a time, while respecting capacity
limits on both hubs and links.

The network, its zones, and the number of drones are described in a simple
text configuration file. The program parses and validates that file, builds
an internal graph, computes the least-congested path for every drone at
every turn, and then renders the whole simulation live in a 2D isometric
window built with `pygame`.

The goal of the project is to explore:

- **Graph modeling and pathfinding** — representing a real-world-like
  logistics network as a weighted graph and routing multiple agents through
  it without violating capacity constraints.
- **Config parsing and validation** — turning free-form text into strongly
  typed, validated objects (`pydantic` models), with clear error reporting
  for malformed input.
- **Real-time visualization** — animating multiple independent agents on a
  shared map, with an interactive control panel (start / stop / reverse /
  reset).

It is conceptually similar to classic "ants through a colony" pathfinding
exercises, reframed here as a small drone-delivery network.

## Instructions

### Requirements

- Python 3.10+
- A `requirements.txt` at the project root (installed automatically by the
  Makefile) — includes `pygame` and `pydantic`.
- A configuration file describing the map (see example below), passed as
  the program's first argument.

### Setup and execution

The project ships with a `Makefile` that manages a local virtual
environment:

| Command            | Description                                                        |
|---------------------|---------------------------------------------------------------------|
| `make venv`         | Creates the `fly_venv` virtual environment and installs dependencies |
| `make install`      | (Re)installs dependencies from `requirements.txt` into the venv     |
| `make run`          | Runs the simulator on `level.txt` (`gui.py level.txt`)              |
| `make debug`        | Runs the simulator under `pdb` for debugging                        |
| `make lint`         | Runs `flake8` and `mypy` (relaxed flags)                            |
| `make lint-strict`  | Runs `flake8` and `mypy --strict`                                   |
| `make clean`        | Removes `__pycache__` and `.mypy_cache` directories                 |

Typical first run:

```bash
make venv
source fly_venv/bin/activate
make run          # equivalent to: python gui.py level.txt
```

To run the simulator on a different map, call the GUI entry point directly
with any config file:

```bash
fly_venv/bin/python gui.py path/to/your_map.txt
```

### Controls (in the GUI)

- **Start** — begins moving drones from the start hub toward the goal hub,
  one turn every 60 frames.
- **Stop** — pauses the simulation (positions are preserved).
- **Reverse** — once every drone has reached the goal, replays the recorded
  path backwards, sending every drone back to the start hub.
- **Reset** — reloads the configuration file and restarts the simulation
  from scratch.

## Algorithm choices and implementation strategy

### Configuration parsing (`validate.py`)

The `Parser` class reads the config file line by line and dispatches each
line by keyword:

- `nb_drones: N` — total number of drones to simulate; must be a positive
  integer.
- `*_hub: name x y [zone=... color=... max_drones=...]` — declares a hub.
  Exactly one `start_hub` (name must contain `start`) and one `end_hub`
  (name must contain `goal`) are allowed; duplicates and unknown/duplicate
  hub names raise a `ParserError`.
- `*_connection: hubA-hubB [max_link_capacity=...]` — declares a bidirectional
  link between two existing hubs. Self-connections and duplicate connections
  (in either direction) are rejected.

`ValidateDatas` handles the low-level parsing of the optional `[key=value ...]`
metadata block (zone, color, max_drones, max_link_capacity), rejecting
unknown keys, invalid zones, or malformed values. `Creator` then turns the
validated data into `Hub` / `Connection` `pydantic` objects (`map.py`),
catching `pydantic.ValidationError` and exiting cleanly with a readable
message rather than a stack trace.

This separation (raw parsing → semantic validation → object creation) keeps
error messages close to the actual malformed line while letting the data
model (`pydantic`) enforce structural invariants (e.g. `max_drones >= 1`, a
hub cannot be both `start` and `end`).

### Routing (`map.py` — `Map.find_path_w_dijkstra`)

Each drone's route is *not* fixed in advance: it is recomputed with
**Dijkstra's algorithm** from the drone's current hub every time it needs to
decide its next move (except in "reverse" mode, where drones simply replay
their recorded path backwards). The edge weight between two hubs is not a
static distance — it is a dynamic **congestion-aware cost**:

```
cost(hub) = hub.cost * 2
          + drones_currently_in_hub
          + drones_currently_on_the_incoming_link
          + (extra penalty if the link is already at max capacity)
          + (extra penalty if the hub is already at max capacity)
```

This means drones actively route *around* crowded hubs and saturated links
instead of piling up and deadlocking, without needing a separate flow
optimizer. `blocked` zones are excluded from the graph outright, and a
hard-coded chokepoint (`gate_hell2`) is always skipped, letting a map
designer force detours.

Once a shortest path to the goal is found (or an empty list if the goal is
unreachable), `Map.move_drone()` advances every drone by at most one hop per
turn:

1. Drones already mid-flight (`moving`) or waiting out a cooldown
   (`waiting_turns`) are skipped for this turn.
2. Drones about to enter a `restricted` zone are paused at the **midpoint**
   of the link (`link_pause_pending` / `paused_on_link`) — modeling a
   security checkpoint — and only proceed to the hub on the following turn.
3. Before a drone is allowed to move onto a link, the code checks the link's
   free capacity, the destination hub's free capacity (including drones
   already committed to arriving there this turn, via `drones_coming`), and
   whether another drone is already paused at the restricted-zone midpoint
   ahead of it.
4. `release_start_drones()` staggers the *initial* release of drones from
   the start hub so they don't all flood the first link/hub simultaneously.

`Drone.final_path` records the sequence of hubs actually visited, which is
what "Reverse" mode replays.

### Rendering (`gui.py`)

The world coordinates in the config file are cartesian (`x`, `y`). They are
converted to an isometric projection (`coordenadas_giradas`) and then scaled
and centered to fit the drawable game area (`calc_screen_positions`),
keeping the start→goal axis at roughly 75% of the panel width regardless of
map size. All drawing happens onto a fixed-size virtual surface
(`virtual_window`) that is then smooth-scaled to fit the actual (resizable)
window, so the layout stays consistent across screen sizes.

Hub sprites are generated procedurally rather than stored as flat images:
`Hub.mount_image_hub()` (in `map.py`) composites a base building sprite with
a colored overlay through a grayscale mask (`PIL.Image.composite`), keyed by
`(model, color)` and cached, so each zone/color combination is only rendered
once per run.

## Documentation of the visual representation

The GUI is split into two zones on a single virtual canvas:

- **Game panel (left, ~75% of the width):** the isometric map itself —
  background, links (drawn as magenta/white double lines), hubs (colored,
  zone-specific sprites sized relative to the number of hubs on the map),
  and drones (drawn stacked with a vertical offset when several drones share
  a hub, so they don't overlap).
- **Menu panel (right, ~25% of the width):** a HUD showing the current
  **turn count**, the total number of **drones**, and how many have reached
  the **goal** (`x/N`), plus the four control buttons (Start, Stop, Reverse,
  Reset) and a message area used for transient warnings (e.g. "wait for all
  drones to reach the goal" before reversing).

Drones are animated smoothly between hubs frame-by-frame
(`animate_drones`), rather than teleporting on each simulation turn — this
makes congestion, queuing at restricted-zone checkpoints, and the effect of
the routing algorithm's rerouting decisions visible in real time, which is
the main point of building a GUI around this algorithm rather than only
logging text output.

## Example input and expected output

Example configuration file (`level.txt`):

```
nb_drones: 3

start_hub: start 0 0
normal_hub: b 2 0 [color=blue]
checkpoint_hub: c 4 0 [zone=restricted max_drones=1]
end_hub: goal 6 0

start-b_connection: start-b [max_link_capacity=2]
b-c_connection: b-c [max_link_capacity=1]
c-goal_connection: c-goal [max_link_capacity=2]
```

Running it:

```bash
fly_venv/bin/python gui.py level.txt
```

Expected behavior:

1. A window opens showing 4 hubs laid out isometrically and connected by
   drawn links, with 3 drone sprites stacked at `start`.
2. Clicking **Start** begins the simulation: every 60 frames (one "turn"),
   each idle drone advances one hop along its Dijkstra-computed path.
3. Because `b-c` only allows one drone at a time and `c` (`restricted`,
   `max_drones=1`) only holds one drone at once, the second and third drones
   visibly queue at `b` while the first drone passes through the
   checkpoint at `c` and reaches `goal`.
4. The **GOAL** counter in the menu increments as each drone arrives,
   reading `3/3` once all drones have landed.
5. Clicking **Reverse** (only enabled once `3/3` is reached) sends all
   drones back along their recorded path to `start`.
6. Clicking **Reset** reloads `level.txt` and restarts the whole simulation.

## Resources

### Classic references

- Dijkstra, E. W. (1959). *A Note on Two Problems in Connexion with
  Graphs* — the original shortest-path algorithm this project's routing is
  built on.
- [Pygame documentation](https://www.pygame.org/docs/) — window/surface
  management, event loop, blitting, and font rendering used throughout
  `gui.py`.
- [Pydantic documentation](https://docs.pydantic.dev/) — data validation
  and settings management used for the `Hub`, `Connection`, and `Drone`
  models in `map.py`.
- [Pillow (PIL) documentation](https://pillow.readthedocs.io/) — used for
  compositing colored hub sprites via masks.
- Introductory articles on **isometric (2:1) tile projection**, used as the
  basis for the `coordenadas_giradas` coordinate transform in `gui.py`.

### AI usage

An AI assistant was used during this project for:

- **Prototyping the isometric coordinate transform**: the rotation/scale
  formula in `App.coordenadas_giradas` was worked out with AI assistance
  (noted directly in the source as `# dica do gepeto pro caminho ocupar 75%
  da cidade`) and then adapted and integrated into `calc_screen_positions`.
- **Debugging and reviewing** the Dijkstra congestion-penalty logic and the
  turn-based drone movement/queuing state machine (`move_drone`,
  `animate_drones`) — discussing edge cases such as restricted-zone
  midpoint pauses and start-hub release staggering.
- **Drafting this `README.md`**: summarizing and structuring the project's
  architecture, algorithm, and usage instructions based on the source code.

No AI-generated code was used for core business logic without review; all
suggestions were read, adapted, and tested by the author before being kept.