# ASSERT Team Dashboard (prototype)

A green-and-black status board for the ASSERT team at **KTH Royal Institute of
Technology**, Division of Theoretical Computer Science (**TCS**). It is meant to
be shown both on the website (`/dashboard/`) and full-screen on the department
monitor.

## Features

- Live clock in **Stockholm time** (`Europe/Stockholm`), with date.
- One tile per team member, driven by `cells/manifest.json`.
- **Microfrontend cells**: each member owns `cells/<id>/` and fully controls
  what renders inside their tile. Cells load in **sandboxed iframes**
  (`allow-scripts allow-popups`), so a broken or mischievous cell cannot take
  down the board or touch other cells.
- **Monitor mode**: point the department screen at `/dashboard/?monitor=1`.
  The board becomes a rotating kiosk that loops through scenes, 5 minutes each:
  1. splash — team name, Stockholm time, university, department
  2. people — the full roster
  3. one scene per live microfrontend, fullscreen
  4. all microfrontends together

  A thin progress strip at the bottom shows the current scene and what comes
  next. Override the scene length for testing with `&secs=10` (seconds).

## How a member adds their cell

1. Write your prompt in `cells/<your-id>/prompt.md` — a natural-language
   description of what your tile should show. This is the source of truth;
   ask Claude (or any LLM) to generate the cell from it, or write it by hand.
2. Put the result in `cells/<your-id>/index.html`. It must be self-contained
   (inline CSS/JS; it runs sandboxed, same-origin assets under your folder are
   fine). Suggested theme tokens, to keep the board coherent:
   ```css
   --bg: #0b120d;  --ink: #d8f5e0;  --ink-2: #8fbf9f;  --ink-3: #55805f;
   --green: #35e07c;  --green-dim: #1f9e57;  --amber: #e0b435;  --line: #1d3323;
   ```
3. Flip your `"cell": false` to `true` in `cells/manifest.json`.
4. Open a PR. Until then, your tile shows *“awaiting prompt”*.

## Running locally

`fetch()` of the manifest needs an HTTP server — `file://` won't work:

```sh
make serve            # Jekyll, then http://localhost:4000/dashboard/
# or, from the repo root:
python3 -m http.server # http://localhost:8000/dashboard/
```

Example cells so far: `sofia` (terminal session), `martin` (quote cycler),
`aman` (build matrix) — each folder shows its `prompt.md` next to the
generated `index.html`.
