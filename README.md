# PES 6 — Local Fullscreen

A local copy of the **PES 6 Web Online Port** web client published at [pes6.optijuegos.net](https://pes6.optijuegos.net/), including its WebAssembly engine and data package. This repository stores the data package in four parts (`payload/pes6.pak.parts/`) to stay within GitHub's per-file size limit; the launcher reassembles it automatically before starting the game.

## How to launch

- **Windows:** run `START-GAME.cmd`.
- **Linux/macOS:** run `./start-game.sh`.

The launcher requires **Python 3** and runs `assemble_pak.py` before starting the server. Assembly verifies the package size and SHA-256 hash; if a chunk is missing or modified, the game will not start. The rebuilt file is written to `site/assets/pes6.pak` (352,054,197 bytes). The local HTTP server listens on `127.0.0.1:8765` and uses only the Python standard library, with no `pip` dependencies. Do not open `site/index.html` directly with `file://`: browsers block WebAssembly and the package's range requests that way.

Press **F11** to hide the browser bars as well. On Windows, stop the server by closing its minimized window or running `STOP-GAME.cmd`.

## What to expect

The page displays only the game image, fills the browser's visible area, and starts emulation automatically. The website loading screen and start options have been hidden; the engine still performs the required local file preparation before showing the first frame. The initial configuration selects English and skips the intro.

The first visible menu may be **Game Level**, which is part of PES 6 itself. **Regular** is selected by default. Confirm that choice to continue; the launcher does not choose a difficulty, teams, or start a match on its own.

Single-player mode does not need to fetch the package from the Internet. Online mode still depends on a connection and the original project's relay.

## Compatibility and attribution

Use an up-to-date browser with **WebGL 2** and hardware acceleration enabled. This is the PSP version of PES 6 ported to WebAssembly, not the native PC edition.

Web client and engine: **OptiProjects / PES 6 Web Online Port** — https://pes6.optijuegos.net/. The data comes from the package configured by that site. The original project states that it is not affiliated with Konami; Pro Evolution Soccer and its content belong to their respective rights holders. This copy is intended for local use; **do not redistribute it publicly**.
